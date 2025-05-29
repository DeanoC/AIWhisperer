"""
Batch client core integration for Billy the Batcher.
Coordinates server, websocket, and script processing for batch execution.
"""

import sys
import os
import json
from .server_manager import ServerManager
from .websocket_client import WebSocketClient
from .script_processor import ScriptProcessor


class BatchClient:
    def __init__(self, script_path, server_port=None, ws_uri=None, dry_run=False):
        self.script_path = script_path
        self.server_manager = ServerManager(port=server_port)
        self.script_processor = ScriptProcessor(script_path)
        self.ws_uri = ws_uri
        self.ws_client = None
        self.dry_run = dry_run

    async def run(self):
        # Check script file exists before running
        print(f"[DEBUG] BatchClient.run: script_path={self.script_path} cwd={os.getcwd()} dry_run={self.dry_run}")
        if not os.path.isfile(self.script_path):
            print(f"Error: Script file not found: {self.script_path}", file=sys.stderr)
            raise ScriptFileNotFoundError(f"Script file not found: {self.script_path}")
        try:
            self.script_processor.load_script()
            if self.dry_run:
                print(f"[DEBUG] Entering dry-run mode, echoing commands:")
                while True:
                    cmd = self.script_processor.get_next_command()
                    if cmd is None:
                        break
                    print(f"[DRYRUN] {cmd}")
                return
            self.server_manager.start_server()
            if not self.ws_uri:
                self.ws_uri = f"ws://localhost:{self.server_manager.port}/ws"
            self.ws_client = WebSocketClient(self.ws_uri)
            # Retry websocket connect up to 3 times
            ws_connect_attempts = 0
            while True:
                try:
                    await self.ws_client.connect()
                    break
                except Exception as e:
                    ws_connect_attempts += 1
                    if ws_connect_attempts >= 3:
                        raise

            # --- Start session ---
            user_id = "batch_user"
            session_id = None
            msg_id = 1
            start_req = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": "startSession",
                "params": {"userId": user_id, "sessionParams": {"language": "en"}}
            }
            await self.ws_client.connection.send(json.dumps(start_req))
            # Wait for sessionId
            while not session_id:
                msg = await self.ws_client.connection.recv()
                try:
                    parsed = json.loads(msg)
                except Exception:
                    parsed = msg
                if isinstance(parsed, dict) and parsed.get("result") and parsed["result"].get("sessionId"):
                    session_id = parsed["result"]["sessionId"]
            print(f"[DEBUG] Session started: {session_id}")
            msg_id += 1

            # --- Send each command as a user message ---
            while True:
                cmd = self.script_processor.get_next_command()
                if cmd is None:
                    break
                print(cmd)  # Echo command to stdout for CLI visibility
                req = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "method": "sendUserMessage",
                    "params": {"sessionId": session_id, "message": cmd}
                }
                await self.ws_client.connection.send(json.dumps(req))
                msg_id += 1
                # Optionally: wait for response/notification here if needed

            # --- Stop session ---
            stop_req = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": "stopSession",
                "params": {"sessionId": session_id}
            }

            await self.ws_client.connection.send(json.dumps(stop_req))
            print(f"[DEBUG] stopSession sent for session: {session_id}")
            print("Batch complete.")

        finally:
            # Always cleanup
            if self.ws_client:
                try:
                    await self.ws_client.close()
                except Exception:
                    pass
            try:
                self.server_manager.stop_server()
            except Exception:
                pass
