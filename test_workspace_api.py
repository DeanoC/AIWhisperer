#!/usr/bin/env python3
"""Test script for workspace API endpoint"""

import asyncio
import json
import websockets

async def test_workspace_api():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Test workspace.getTree method
        request = {
            "jsonrpc": "2.0",
            "method": "workspace.getTree",
            "params": {"path": "."},
            "id": 1
        }
        
        print("Sending request:", json.dumps(request, indent=2))
        await websocket.send(json.dumps(request))
        
        response = await websocket.recv()
        response_json = json.loads(response)
        print("\nReceived response:")
        print(json.dumps(response_json, indent=2))
        
        # Print just the tree if successful
        if "result" in response_json and "tree" in response_json["result"]:
            print("\nFile Tree:")
            print(response_json["result"]["tree"])

if __name__ == "__main__":
    asyncio.run(test_workspace_api())