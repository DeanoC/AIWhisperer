#!/usr/bin/env python3
"""Direct WebSocket test to debug the issue"""

import asyncio
import json
import websockets
import subprocess
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

async def test_websocket():
    # Start server
    print("Starting server...")
    server = subprocess.Popen(
        [sys.executable, "-m", "interactive_server.main", "--config", "config/main.yaml", "--port", "7777"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server
    time.sleep(5)
    
    try:
        uri = "ws://localhost:7777/ws"
        print(f"\nConnecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Collect all messages in background
            messages = []
            async def collect_messages():
                try:
                    async for msg in websocket:
                        data = json.loads(msg)
                        messages.append(data)
                        print(f"\nReceived: {json.dumps(data, indent=2)}")
                except Exception as e:
                    print(f"Message collection error: {e}")
            
            # Start collecting messages
            collector_task = asyncio.create_task(collect_messages())
            
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
            
            print(f"\nSending startSession...")
            await websocket.send(json.dumps(request))
            
            # Wait a bit for responses
            await asyncio.sleep(5)
            
            # Find the response
            print(f"\nReceived {len(messages)} messages total")
            response = None
            for msg in messages:
                if msg.get("id") == 1:
                    response = msg
                    break
            
            if response and "result" in response:
                session_id = response["result"].get("sessionId")
                print(f"\n✅ Got session ID: {session_id}")
                
                # Now test a simple message
                request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "sendUserMessage",
                    "params": {
                        "sessionId": session_id,
                        "message": "Who are you?"
                    }
                }
                
                print(f"\nSending message: Who are you?")
                await websocket.send(json.dumps(request))
                
                # Wait for response
                await asyncio.sleep(10)
                
                print(f"\n✅ Test complete! Received {len(messages)} messages")
            else:
                print(f"\n❌ No valid response to startSession")
            
            # Cancel collector
            collector_task.cancel()
            
    finally:
        print("\nStopping server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    asyncio.run(test_websocket())