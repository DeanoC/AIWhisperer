#!/usr/bin/env python3
"""Simple test script to debug conversation replay"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.extensions.conversation_replay import ServerManager
from ai_whisperer.extensions.conversation_replay.websocket_client import WebSocketClient
from ai_whisperer.extensions.conversation_replay.conversation_processor import ConversationProcessor


async def test_alice():
    """Test Alice with a simple message"""
    # Start server
    print("Starting server...")
    manager = ServerManager()
    manager.start_server()
    
    # Wait a bit more for server to be ready
    await asyncio.sleep(3)
    
    server_url = f"ws://127.0.0.1:{manager.port}/ws"
    print(f"Connecting to {server_url}...")
    
    try:
        # Create WebSocket client
        ws_client = WebSocketClient(server_url)
        
        # Set up notification handler
        alice_response = None
        async def notification_handler(notification):
            nonlocal alice_response
            method = notification.get("method", "")
            if method == "ChannelMessageNotification":
                params = notification.get("params", {})
                alice_response = params.get("content", "")
                print(f"\n[NOTIFICATION] Alice says: {alice_response}")
        
        ws_client.set_notification_handler(notification_handler)
        
        await ws_client.connect()
        print("Connected!")
        
        # Start session
        print("\nStarting session...")
        start_response = await ws_client.send_request(
            method="startSession",
            params={"userId": "test_user", "sessionParams": {"language": "en"}},
            request_id=1
        )
        if "result" in start_response:
            session_id = start_response["result"].get("sessionId")
        else:
            print(f"Error starting session: {start_response}")
            return
        print(f"Session ID: {session_id}")
        
        # Send test message
        print("\nSending test message...")
        response = await ws_client.send_request(
            method="sendUserMessage",
            params={"sessionId": session_id, "message": "What's the current status of my workspace?"},
            request_id=2
        )
        print(f"\nAlice's response:\n{response}")
        
        # Wait a bit for notifications
        await asyncio.sleep(2)
        
        # Close connection
        await ws_client.close()
        print("\nConnection closed.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop server
        print("\nStopping server...")
        manager.stop_server()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(test_alice())