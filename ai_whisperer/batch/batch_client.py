"""
Batch client core integration for Debbie the Debugger.
Coordinates server, websocket, and script processing for batch execution.
"""

import sys
import os
import json
import logging
from .server_manager import ServerManager
from .websocket_client import WebSocketClient
from .script_processor import ScriptProcessor, ScriptFileNotFoundError

logger = logging.getLogger(__name__)


class BatchClient:
    def __init__(self, script_path, server_port=None, ws_uri=None, dry_run=False):
        self.script_path = script_path
        self.server_manager = ServerManager(port=server_port)
        self.script_processor = ScriptProcessor(script_path)
        self.ws_uri = ws_uri
        self.ws_client = None
        self.dry_run = dry_run

    async def _perform_dry_run(self):
        """Loads script and prints commands for a dry run."""
        print(f"[DEBUG] Entering dry-run mode, echoing commands:")
        self.script_processor.load_script() # Ensure script is loaded for dry run
        while True:
            cmd = self.script_processor.get_next_command()
            if cmd is None:
                break
            print(f"[DRYRUN] {cmd}")

    async def _connect_websocket(self, max_attempts=3):
        """Connects to the WebSocket server with retry logic."""
        if not self.ws_uri: # Use default if not provided
            self.ws_uri = f"ws://localhost:{self.server_manager.port}/ws"
        self.ws_client = WebSocketClient(self.ws_uri)

        attempts = 0
        while True:
            try:
                await self.ws_client.connect()
                logger.info(f"WebSocket connected to {self.ws_uri}")
                return
            except Exception as e:
                attempts += 1
                logger.warning(f"WebSocket connection attempt {attempts} failed for {self.ws_uri}: {e}")
                if attempts >= max_attempts:
                    logger.error(f"Failed to connect to WebSocket {self.ws_uri} after {max_attempts} attempts.")
                    raise
                await asyncio.sleep(1 + attempts) # Basic backoff

    async def _start_rpc_session(self, initial_msg_id: int, user_id: str = "batch_user") -> tuple[str, int]:
        """Starts an RPC session and returns the session ID and next message ID."""
        session_id = None
        msg_id = initial_msg_id
        start_req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "startSession",
            "params": {"userId": user_id, "sessionParams": {"language": "en"}}
        }
        if not self.ws_client or not self.ws_client.connection:
            # This should ideally not be reached if _connect_websocket was successful
            logger.error("_start_rpc_session: WebSocket client not connected.")
            raise ConnectionError("WebSocket client not connected before starting session.")

        await self.ws_client.connection.send(json.dumps(start_req))

        # Wait for sessionId
        # TODO: Add a timeout for this loop to prevent indefinite blocking
        while not session_id:
            msg = await self.ws_client.connection.recv()
            try:
                parsed = json.loads(msg)
                # Ensure the response corresponds to the sent message ID
                if isinstance(parsed, dict) and parsed.get("id") == msg_id and parsed.get("result") and parsed["result"].get("sessionId"):
                    session_id = parsed["result"]["sessionId"]
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message while waiting for session ID for msg_id {msg_id}: {msg}")
            except Exception as e: # Catch other potential errors during message processing
                logger.error(f"Error processing message while waiting for session ID for {msg_id}: {e} - Message: {msg}")
                # Depending on the error, might need to break or re-raise

        if not session_id: # If loop finishes and session_id is still None
            logger.error(f"Failed to obtain session ID after sending startSession (msg_id: {msg_id}).")
            raise RuntimeError("Failed to obtain session ID from server.")

        print(f"[DEBUG] Session started: {session_id}")
        return session_id, msg_id + 1

    async def _process_script_commands(self, session_id: str, initial_msg_id: int) -> int:
        """Processes commands from the script and sends them as user messages."""
        msg_id = initial_msg_id
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
            if not self.ws_client or not self.ws_client.connection: # Should be connected by now
                logger.error("_process_script_commands: WebSocket client not connected.")
                raise ConnectionError("WebSocket client not connected during command processing.")
            await self.ws_client.connection.send(json.dumps(req))
            msg_id += 1
            # Optionally: wait for response/notification here if needed
        return msg_id

    async def _stop_rpc_session(self, session_id: str, current_msg_id: int):
        """Sends the stopSession message to the server."""
        msg_id = current_msg_id
        stop_req = {
            "jsonrpc": "2.0",
            "id": msg_id, # Use current msg_id for the stop request
            "method": "stopSession",
            "params": {"sessionId": session_id}
        }
        if not self.ws_client or not self.ws_client.connection:
            logger.warning("_stop_rpc_session: WebSocket client not connected or already closed.")
            # Depending on desired strictness, could raise ConnectionError here
            return # Cannot send stop if not connected

        await self.ws_client.connection.send(json.dumps(stop_req))
        print(f"[DEBUG] stopSession sent for session: {session_id}, msg_id: {msg_id}")
        # Optionally, wait for a response to stopSession if the protocol guarantees one

    async def run(self):
        print(f"[DEBUG] BatchClient.run: script_path={self.script_path} cwd={os.getcwd()} dry_run={self.dry_run}")
        if not os.path.isfile(self.script_path):
            print(f"Error: Script file not found: {self.script_path}", file=sys.stderr)
            raise ScriptFileNotFoundError(f"Script file not found: {self.script_path}")

        if self.dry_run:
            await self._perform_dry_run()
            return

        session_id = None # Ensure session_id is defined for the finally block
        msg_id = 1      # Initial message ID

        try:
            self.script_processor.load_script() # Load script content first

            self.server_manager.start_server() # Start local server

            await self._connect_websocket() # Connect to WebSocket

            session_id, msg_id = await self._start_rpc_session(initial_msg_id=msg_id) # Start RPC session

            msg_id = await self._process_script_commands(session_id, msg_id) # Process script commands

            await self._stop_rpc_session(session_id, msg_id) # Stop RPC session

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
