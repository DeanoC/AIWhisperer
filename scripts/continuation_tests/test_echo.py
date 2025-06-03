#!/usr/bin/env python3
"""Simple echo test to verify WebSocket is working"""

import asyncio
import json
import websockets

async def test_echo():
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Test echo
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "echo",
                "params": {"message": "Hello World"}
            }
            
            print(f"Sending: {json.dumps(request)}")
            await websocket.send(json.dumps(request))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Assuming server is already running on port 8000
    asyncio.run(test_echo())