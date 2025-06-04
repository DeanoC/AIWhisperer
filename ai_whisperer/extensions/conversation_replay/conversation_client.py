"""
Conversation replay client for AIWhisperer.
Coordinates server, websocket, and conversation processing for replaying recorded conversations.

This is NOT batch processing! This replays conversations with AI agents.
"""

import sys
import os
import logging
import asyncio
from ai_whisperer.extensions.conversation_replay.server_manager import ServerManager
from ai_whisperer.extensions.conversation_replay.websocket_client import WebSocketClient
from ai_whisperer.extensions.conversation_replay.conversation_processor import ConversationProcessor, ConversationFileNotFoundError

logger = logging.getLogger(__name__)

class ConversationReplayClient:
    def __init__(self, conversation_path, server_port=None, ws_uri=None, dry_run=False):
        self.conversation_path = conversation_path
        self.server_manager = ServerManager(port=server_port)
        self.conversation_processor = ConversationProcessor(conversation_path)
        self.ws_uri = ws_uri
        self.ws_client = None
        self.dry_run = dry_run

    async def run(self):
        # Check conversation file exists before running
        print(f"🎬 Starting conversation replay...")
        print(f"   💬 Conversation: {self.conversation_path}")
        print(f"   📁 Working directory: {os.getcwd()}")
        print(f"   🧪 Dry run: {self.dry_run}")
        
        if not os.path.isfile(self.conversation_path):
            print(f"❌ Error: Conversation file not found: {self.conversation_path}", file=sys.stderr)
            raise ConversationFileNotFoundError(f"Conversation file not found: {self.conversation_path}")
        try:
            print(f"   📖 Loading conversation...")
            self.conversation_processor.load_conversation()
            print(f"   ✅ Conversation loaded: {len(self.conversation_processor.messages)} messages")
            
            if self.dry_run:
                print(f"🧪 Dry-run mode: Showing messages without sending")
                while True:
                    msg = self.conversation_processor.get_next_message()
                    if msg is None:
                        break
                    print(f"   [DRYRUN] {msg}")
                print(f"✅ Dry-run completed")
                return
            
            print(f"   🚀 Starting conversation replay server...")
            self.server_manager.start_server()
            
            # Reinitialize logging with the conversation replay server port
            from ai_whisperer.core import logging as core_logging
            core_logging.setup_logging(port=self.server_manager.port)
            
            if not self.ws_uri:
                self.ws_uri = f"ws://localhost:{self.server_manager.port}/ws"
            print(f"   🔌 Connecting to WebSocket: {self.ws_uri}")
            self.ws_client = WebSocketClient(self.ws_uri)
            
            # Set up notification handler to capture agent responses
            async def notification_handler(notification):
                method = notification.get("method", "unknown")
                params = notification.get("params", {})
                print(f"   🔔 Agent notification: {method}")
                if params:
                    # Print relevant parts of agent's response
                    if "message" in params:
                        print(f"   💬 Agent says: {params['message']}")
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
            print(f"   🎭 Starting AI session...")
            user_id = "conversation_user"
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

            # --- Send each message from the conversation ---
            total_messages = len(self.conversation_processor.messages)
            print(f"   🎬 Replaying {total_messages} messages...")
            message_count = 0
            while True:
                msg = self.conversation_processor.get_next_message()
                if msg is None:
                    break
                message_count += 1
                print(f"   [{message_count}/{total_messages}] 📤 Sending: {msg}")
                
                # Use send_request to properly handle the request/response flow
                try:
                    response = await self.ws_client.send_request(
                        method="sendUserMessage",
                        params={"sessionId": session_id, "message": msg},
                        request_id=msg_id
                    )
                    # Extract just the AI response for display
                    ai_response = response.get('ai_response', '')
                    tool_calls = response.get('tool_calls', [])
                    
                    # Clean up JSON if present
                    if ai_response and isinstance(ai_response, str):
                        if ai_response.strip().startswith('{') and '"final"' in ai_response:
                            try:
                                import json
                                parsed = json.loads(ai_response)
                                if 'final' in parsed:
                                    ai_response = parsed['final']
                            except:
                                pass
                    
                    # Show cleaned response
                    if tool_calls:
                        print(f"   [{message_count}/{total_messages}] ✅ Response: {ai_response} (+ {len(tool_calls)} tool calls)")
                    else:
                        print(f"   [{message_count}/{total_messages}] ✅ Response: {ai_response}")
                    
                    # Give agent time to process and send notifications
                    print(f"   [{message_count}/{total_messages}] ⏳ Waiting for agent to process...")
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"   [{message_count}/{total_messages}] ❌ Error: {e}")
                
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
            print("✅ Conversation replay completed successfully!")

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
