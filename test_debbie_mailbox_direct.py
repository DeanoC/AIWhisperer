#!/usr/bin/env python3
"""
Direct test for Debbie's mailbox checking with forced debug mode.
"""

import asyncio
import json
import websockets
import uuid
from datetime import datetime

async def test_debbie_mailbox():
    """Test Debbie's mailbox checking directly."""
    
    print("\n" + "="*60)
    print("Direct Debbie Mailbox Test")
    print("="*60 + "\n")
    
    # Connect to the WebSocket
    uri = "ws://localhost:5000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Start session
            session_id = str(uuid.uuid4())
            start_msg = {
                "jsonrpc": "2.0",
                "method": "start_session",
                "params": {
                    "session_id": session_id
                },
                "id": 1
            }
            
            await websocket.send(json.dumps(start_msg))
            response = await websocket.recv()
            print(f"Session started: {response}")
            
            # Switch to Alice first
            alice_msg = {
                "jsonrpc": "2.0",
                "method": "send_message",
                "params": {
                    "session_id": session_id,
                    "message": "/switch-agent a"
                },
                "id": 2
            }
            
            await websocket.send(json.dumps(alice_msg))
            # Wait for all responses
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    if data.get("method") == "ai.response":
                        print(f"Alice: {data['params']['response']}")
                        break
                except asyncio.TimeoutError:
                    break
            
            # Send mail with switch
            mail_msg = {
                "jsonrpc": "2.0",
                "method": "send_message",
                "params": {
                    "session_id": session_id,
                    "message": "Use send_mail_with_switch to send a message to Debbie with subject 'Test' and body 'Please perform a system health check and report back.'"
                },
                "id": 3
            }
            
            await websocket.send(json.dumps(mail_msg))
            
            # Collect responses
            debbie_response = None
            alice_final_response = None
            tool_calls_seen = []
            
            start_time = asyncio.get_event_loop().time()
            timeout = 10  # 10 second timeout
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)
                    
                    # Track notifications
                    if data.get("method") == "agent.switched":
                        print(f"Agent switched: {data['params']}")
                    
                    elif data.get("method") == "ai.tool_call":
                        tool_name = data['params'].get('tool_name')
                        tool_calls_seen.append(tool_name)
                        print(f"Tool called: {tool_name}")
                    
                    elif data.get("method") == "ai.response":
                        response_text = data['params']['response']
                        if "debbie" in response_text.lower() or "checking mail" in response_text.lower():
                            debbie_response = response_text
                            print(f"Debbie response: {response_text}")
                        else:
                            alice_final_response = response_text
                            print(f"Alice final: {response_text}")
                    
                except asyncio.TimeoutError:
                    continue
            
            # Report results
            print("\n" + "="*60)
            print("Test Results")
            print("="*60)
            
            print(f"Tool calls seen: {tool_calls_seen}")
            print(f"Debbie made check_mail call: {'check_mail' in tool_calls_seen}")
            print(f"Mail was sent with switch: {'send_mail_with_switch' in tool_calls_seen}")
            
            if debbie_response:
                print(f"\nDebbie's response included:")
                if "check_mail()" in debbie_response:
                    print("  - check_mail() in commentary (NOT a real tool call)")
                if "<tool_code>" in debbie_response:
                    print("  - <tool_code> tags (NOT a real tool call)")
            
            # Close session
            close_msg = {
                "jsonrpc": "2.0",
                "method": "stop_session",
                "params": {
                    "session_id": session_id
                },
                "id": 4
            }
            await websocket.send(json.dumps(close_msg))
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # First ensure server is running
    print("Make sure the server is running with: python -m interactive_server.main")
    print("Press Enter to continue...")
    input()
    
    asyncio.run(test_debbie_mailbox())