#!/usr/bin/env python3
"""Simple test script to test Alice's responses"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.extensions.conversation_replay import ServerManager
from ai_whisperer.extensions.conversation_replay.websocket_client import WebSocketClient


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
    
    alice_responses = []
    
    try:
        # Create WebSocket client
        ws_client = WebSocketClient(server_url)
        
        # Set up notification handler to capture all messages
        async def notification_handler(notification):
            method = notification.get("method", "")
            params = notification.get("params", {})
            
            print(f"\n[NOTIFICATION] {method}")
            
            if method == "ChannelMessageNotification":
                content = params.get("content", "")
                channel = params.get("channel", "")
                print(f"  Channel: {channel}")
                print(f"  Content: {content[:200]}...")
                alice_responses.append({
                    "channel": channel,
                    "content": content
                })
        
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
        
        # Extract session ID correctly
        session_id = start_response.get("sessionId")
        if not session_id:
            print(f"Full response: {json.dumps(start_response, indent=2)}")
            raise Exception("No sessionId in response")
            
        print(f"Session ID: {session_id}")
        
        # Wait a moment for introduction
        await asyncio.sleep(2)
        
        # Send test message
        print("\nSending test message: 'What's the current status of my workspace?'")
        response = await ws_client.send_request(
            method="sendUserMessage",
            params={"sessionId": session_id, "message": "What's the current status of my workspace?"},
            request_id=2
        )
        print(f"Message sent. Response: {response.get('status')}")
        
        # Wait for Alice to process and respond
        print("\nWaiting for Alice to respond...")
        await asyncio.sleep(5)
        
        # Print all collected responses
        print("\n=== Alice's Responses ===")
        for i, resp in enumerate(alice_responses):
            print(f"\nResponse {i+1} ({resp['channel']}):")
            print(resp['content'])
        
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