"""
Batch client core integration for Debbie the Debugger.
Coordinates server, websocket, and script processing for batch execution.
"""

import sys
import os
import json
import logging
import asyncio
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

    async def run(self):
        # Check script file exists before running
        print(f"🎬 Starting batch execution...")
        print(f"   📄 Script: {self.script_path}")
        print(f"   📁 Working directory: {os.getcwd()}")
        print(f"   🧪 Dry run: {self.dry_run}")
        
        if not os.path.isfile(self.script_path):
            print(f"❌ Error: Script file not found: {self.script_path}", file=sys.stderr)
            raise ScriptFileNotFoundError(f"Script file not found: {self.script_path}")
        try:
            print(f"   📖 Loading script...")
            self.script_processor.load_script()
            print(f"   ✅ Script loaded: {len(self.script_processor.commands)} commands")
            
            if self.dry_run:
                print(f"🧪 Dry-run mode: Echoing commands without execution")
                while True:
                    cmd = self.script_processor.get_next_command()
                    if cmd is None:
                        break
                    print(f"   [DRYRUN] {cmd}")
                print(f"✅ Dry-run completed")
                return
            
            print(f"   🚀 Starting batch server...")
            self.server_manager.start_server()
            
            # Reinitialize logging with the batch server port
            from ai_whisperer import logging_custom
            logging_custom.setup_logging(port=self.server_manager.port)
            
            if not self.ws_uri:
                self.ws_uri = f"ws://localhost:{self.server_manager.port}/ws"
            print(f"   🔌 Connecting to WebSocket: {self.ws_uri}")
            self.ws_client = WebSocketClient(self.ws_uri)
            
            # Set up notification handler to capture Debbie's responses
            async def notification_handler(notification):
                method = notification.get("method", "unknown")
                params = notification.get("params", {})
                print(f"   🔔 Debbie notification: {method}")
                if params:
                    # Print relevant parts of Debbie's response
                    if "message" in params:
                        print(f"   💬 Debbie says: {params['message']}")
                    elif "content" in params:
                        print(f"   📝 Content: {params['content']}")
                    elif "toolOutput" in params:
                        print(f"   🔧 Tool output: {params['toolOutput']}")
                    else:
                        print(f"   📊 Data: {params}")
            
            self.ws_client.set_notification_handler(notification_handler)
            # Retry websocket connect up to 3 times
            ws_connect_attempts = 0
            while True:
                try:
                    print(f"   ⏳ Connecting to WebSocket (attempt {ws_connect_attempts + 1}/3)...")
                    await self.ws_client.connect()
                    print(f"   ✅ WebSocket connected successfully")
                    break
                except Exception as e:
                    ws_connect_attempts += 1
                    print(f"   ❌ WebSocket connection failed: {e}")
                    if ws_connect_attempts >= 3:
                        print(f"   💥 Failed to connect after 3 attempts")
                        raise

            # --- Start session ---
            print(f"   🎭 Starting Debbie session...")
            user_id = "batch_user"
            msg_id = 1
            try:
                start_response = await self.ws_client.send_request(
                    method="startSession",
                    params={"userId": user_id, "sessionParams": {"language": "en"}},
                    request_id=msg_id
                )
                session_id = start_response.get("sessionId")
                if not session_id:
                    raise Exception(f"No sessionId in response: {start_response}")
                print(f"   ✅ Session started: {session_id}")
                msg_id += 1
            except Exception as e:
                print(f"   ❌ Failed to start session: {e}")
                raise

            # --- Send each command as a user message ---
            total_commands = len(self.script_processor.commands)
            print(f"   🎬 Executing {total_commands} commands...")
            command_count = 0
            while True:
                cmd = self.script_processor.get_next_command()
                if cmd is None:
                    break
                command_count += 1
                print(f"   [{command_count}/{total_commands}] 📤 Sending: {cmd}")
                
                # Use send_request to properly handle the request/response flow
                try:
                    response = await self.ws_client.send_request(
                        method="sendUserMessage",
                        params={"sessionId": session_id, "message": cmd},
                        request_id=msg_id
                    )
                    print(f"   [{command_count}/{total_commands}] ✅ Response received: {response}")
                    
                    # Give Debbie time to process and send notifications
                    print(f"   [{command_count}/{total_commands}] ⏳ Waiting for Debbie to process...")
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"   [{command_count}/{total_commands}] ❌ Error: {e}")
                
                msg_id += 1

            # --- Stop session ---
            try:
                stop_response = await self.ws_client.send_request(
                    method="stopSession",
                    params={"sessionId": session_id},
                    request_id=msg_id
                )
                print(f"   ✅ Session stopped: {session_id} - {stop_response}")
            except Exception as e:
                print(f"   ⚠️ Error stopping session: {e}")
            print("✅ Batch execution completed successfully!")

        finally:
            # Always cleanup
            print(f"   🧹 Cleaning up...")
            if self.ws_client:
                try:
                    print(f"   🔌 Closing WebSocket connection...")
                    await self.ws_client.close()
                except Exception as e:
                    print(f"   ⚠️ Error closing WebSocket: {e}")
            try:
                self.server_manager.stop_server()
            except Exception as e:
                print(f"   ⚠️ Error stopping server: {e}")
            print(f"✅ Cleanup completed")
