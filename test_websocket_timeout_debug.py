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
async def test_websocket_timeout_simulation():
    """
    Test timeout simulation in pytest environment.
    This should help us isolate the timeout-specific issue.
    """
    uri = "ws://127.0.0.1:8000/ws"
    session_id = None
    msg_id = 1
    
    print(f"[TEST] Starting WebSocket timeout test to {uri}")
    print(f"[TEST] Current event loop: {asyncio.get_running_loop()}")
    
    received_messages = []
    
    try:
        # Use a timeout to prevent hanging
        async with asyncio.timeout(60):  # 60 second timeout for the entire test
            async with websockets.connect(uri) as websocket:
                print(f"[TEST] WebSocket connected successfully")
                
                # Start session
                start_req = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "method": "startSession",
                    "params": {"userId": "timeout_test_user", "sessionParams": {"language": "en"}}
                }
                print(f"[TEST] Sending startSession: {start_req}")
                await websocket.send(json.dumps(start_req))
                msg_id += 1
                
                # Wait for sessionId with timeout
                async with asyncio.timeout(10):  # 10 seconds for session start
                    while True:
                        print(f"[TEST] Waiting for session message...")
                        msg = json.loads(await websocket.recv())
                        received_messages.append(msg)
                        print(f"[TEST] Received: {msg}")
                        
                        if msg.get("result") and msg["result"].get("sessionId"):
                            session_id = msg["result"]["sessionId"]
                            print(f"[TEST] Got session ID: {session_id}")
                            break
                
                assert session_id, "Session ID not received."
                
                # Send the timeout simulation message
                user_msg = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "method": "sendUserMessage",
                    "params": {"sessionId": session_id, "message": "simulate_timeout"}
                }
                print(f"[TEST] Sending timeout simulation message: {user_msg}")
                await websocket.send(json.dumps(user_msg))
                msg_id += 1
                
                # Wait for timeout notification or error
                print(f"[TEST] Waiting for timeout notification...")
                timeout_received = False
                message_count = 0
                
                async with asyncio.timeout(45):  # 45 seconds for timeout response
                    while not timeout_received and message_count < 20:
                        try:
                            print(f"[TEST] Waiting for message {message_count + 1}...")
                            msg = json.loads(await websocket.recv())
                            received_messages.append(msg)
                            message_count += 1
                            print(f"[TEST] Received message {message_count}: {msg}")
                            
                            # Check for timeout-related notifications
                            if msg.get("method") == "SessionStatusNotification":
                                if "timeout" in str(msg.get("params", {})).lower():
                                    print(f"[TEST] Found timeout in SessionStatusNotification!")
                                    timeout_received = True
                                    break
                            elif msg.get("method") == "ErrorNotification":
                                if "timeout" in str(msg.get("params", {})).lower():
                                    print(f"[TEST] Found timeout in ErrorNotification!")
                                    timeout_received = True
                                    break
                            elif msg.get("error"):
                                if "timeout" in str(msg.get("error", {})).lower():
                                    print(f"[TEST] Found timeout in error response!")
                                    timeout_received = True
                                    break
                            
                            # Add a small delay between message checks
                            await asyncio.sleep(0.5)
                            
                        except websockets.ConnectionClosed as e:
                            print(f"[TEST] WebSocket connection closed: {e}")
                            break
                        except Exception as e:
                            print(f"[TEST] Exception while receiving: {e}")
                            break
                
                print(f"[TEST] Timeout received: {timeout_received}")
                print(f"[TEST] Total messages received: {len(received_messages)}")
                for i, msg in enumerate(received_messages):
                    print(f"[TEST] Message {i+1}: {msg}")
                
                if not timeout_received:
                    print(f"[TEST] No timeout notification received after {message_count} messages")
                    # This is not necessarily a failure - let's see what we got
                
    except asyncio.TimeoutError as e:
        print(f"[TEST] Test timeout occurred: {e}")
        print(f"[TEST] Messages received so far: {received_messages}")
        raise
    except Exception as e:
        print(f"[TEST] Exception occurred: {e}")
        print(f"[TEST] Messages received so far: {received_messages}")
        raise

if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_websocket_timeout_simulation())
