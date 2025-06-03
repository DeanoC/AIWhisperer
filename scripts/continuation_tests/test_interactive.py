#!/usr/bin/env python3
"""Test script to verify interactive server is working with API key"""

import asyncio
import json
import websockets
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_whisperer.core.config import load_config

async def test_session():
    # Load config to check API key
    config = load_config("config/main.yaml")
    print(f"Config loaded successfully")
    print(f"Model: {config['openrouter']['model']}")
    print(f"API key present: {'api_key' in config['openrouter']}")
    
    # Connect to WebSocket
    uri = "ws://localhost:8000/ws"
    print(f"\nConnecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send startSession request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "startSession",
                "params": {
                    "agent_id": "default",
                    "language": "en"
                }
            }
            
            print(f"\nSending: {json.dumps(request, indent=2)}")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\nReceived: {json.dumps(data, indent=2)}")
            
            # Send a simple message
            if "error" not in data:
                message_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "sendMessage",
                    "params": {
                        "message": "Hello! What is 2 + 2?"
                    }
                }
                
                print(f"\nSending message: {message_request['params']['message']}")
                await websocket.send(json.dumps(message_request))
                
                # Collect responses
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(response)
                    print(f"Response: {json.dumps(data, indent=2)}")
                    
                    # Check if we got the final response
                    if data.get("id") == 2:
                        break
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # First check if server is running
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    
    if result != 0:
        print("Interactive server is not running on port 8000")
        print("Please start it with: python -m interactive_server.main")
        sys.exit(1)
    
    asyncio.run(test_session())