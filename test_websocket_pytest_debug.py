#!/usr/bin/env python3

import asyncio
import json
import pytest
import websockets
import time
import os
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

@pytest.mark.asyncio
async def test_websocket_basic_communication():
    """
    Test basic WebSocket communication in pytest environment.
    This should help us isolate the pytest-specific issue.
    """
    uri = "ws://127.0.0.1:8000/ws"
    session_id = None
    msg_id = 1
    
    print(f"[TEST] Starting WebSocket test to {uri}")
    print(f"[TEST] Current event loop: {asyncio.get_running_loop()}")
    
    received_messages = []
    
    try:
        # Use a timeout to prevent hanging
        async with asyncio.timeout(30):  # 30 second timeout for the entire test
            async with websockets.connect(uri) as websocket:
                print(f"[TEST] WebSocket connected successfully")
                
                # Start session
                start_req = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "method": "startSession",
                    "params": {"userId": "test_user", "sessionParams": {"language": "en"}}
                }
                print(f"[TEST] Sending startSession: {start_req}")
                await websocket.send(json.dumps(start_req))
                msg_id += 1
                
                # Wait for sessionId with timeout
                async with asyncio.timeout(10):  # 10 seconds for session start
                    while True:
                        print(f"[TEST] Waiting for message...")
                        msg = json.loads(await websocket.recv())
                        received_messages.append(msg)
                        print(f"[TEST] Received: {msg}")
                        
                        if msg.get("result") and msg["result"].get("sessionId"):
                            session_id = msg["result"]["sessionId"]
                            print(f"[TEST] Got session ID: {session_id}")
                            break
                
                assert session_id, "Session ID not received."
                
                # Send a simple user message
                user_msg = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "method": "sendUserMessage",
                    "params": {"sessionId": session_id, "message": "Hello, how are you?"}
                }
                print(f"[TEST] Sending user message: {user_msg}")
                await websocket.send(json.dumps(user_msg))
                msg_id += 1
                
                # Wait for response with timeout
                async with asyncio.timeout(15):  # 15 seconds for response
                    response_received = False
                    while not response_received:
                        print(f"[TEST] Waiting for response...")
                        msg = json.loads(await websocket.recv())
                        received_messages.append(msg)
                        print(f"[TEST] Received response: {msg}")
                        
                        # Look for any response (notification or result)
                        if (msg.get("method") and "Notification" in msg["method"]) or msg.get("result"):
                            response_received = True
                            break
                
                print(f"[TEST] Test completed successfully!")
                print(f"[TEST] Total messages received: {len(received_messages)}")
                
    except asyncio.TimeoutError as e:
        print(f"[TEST] Timeout occurred: {e}")
        print(f"[TEST] Messages received so far: {received_messages}")
        raise
    except Exception as e:
        print(f"[TEST] Exception occurred: {e}")
        print(f"[TEST] Messages received so far: {received_messages}")
        raise

if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_websocket_basic_communication())
