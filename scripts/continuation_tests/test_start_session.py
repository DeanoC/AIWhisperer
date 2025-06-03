#!/usr/bin/env python3
"""Test startSession to debug the issue"""

import asyncio
import json
import websockets

async def test_start_session():
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Test startSession
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "startSession",
                "params": {
                    "userId": "test_user",
                    "sessionParams": {"language": "en"}
                }
            }
            
            print(f"Sending: {json.dumps(request, indent=2)}")
            await websocket.send(json.dumps(request))
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"Received: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("Timeout waiting for response!")
                
                # Try to receive any pending messages
                try:
                    while True:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        print(f"Pending message: {msg}")
                except asyncio.TimeoutError:
                    print("No more pending messages")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_start_session())