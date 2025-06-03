#!/usr/bin/env python3
"""Direct WebSocket test to debug startSession issue"""

import asyncio
import json
import websockets
import subprocess
import time
import sys

async def test_websocket():
    # Start server
    print("Starting server...")
    server_process = subprocess.Popen([
        sys.executable, "-m", "interactive_server.main",
        "--host", "127.0.0.1", "--port", "8001"
    ], env={**os.environ, "AIWHISPERER_CONFIG": "config/main.yaml"})
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        uri = "ws://127.0.0.1:8001/ws"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send startSession
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "startSession",
                "params": {
                    "userId": "test_user",
                    "sessionParams": {"language": "en"}
                }
            }
            
            print(f"Sending: {json.dumps(request)}")
            await websocket.send(json.dumps(request))
            
            # Receive messages with timeout
            messages_received = []
            try:
                while len(messages_received) < 5:  # Collect up to 5 messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    print(f"Received: {json.dumps(data, indent=2)}")
                    
                    # Check if this is our response
                    if data.get("id") == 1:
                        print("Got startSession response!")
                        break
            except asyncio.TimeoutError:
                print("Timeout waiting for more messages")
            
            print(f"\nTotal messages received: {len(messages_received)}")
            
    finally:
        print("Killing server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    import os
    asyncio.run(test_websocket())