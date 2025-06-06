#!/usr/bin/env python3
"""Test to check which WebSocket methods are available."""

import asyncio
import json
import websockets


async def test_methods():
    """Test various WebSocket methods."""
    uri = "ws://localhost:8000/ws"
    
    methods_to_test = [
        "startSession",
        "sendMessage", 
        "stopSession",
        "async.createAgent",
        "async.getAgentStates",
        "workspace.listDirectory",
        "mcp.getServers"
    ]
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket\n")
        
        # Start a session first
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "startSession",
            "params": {"userId": "test_user", "sessionParams": {}}
        }
        
        await websocket.send(json.dumps(req))
        
        # Collect responses
        responses = []
        session_id = None
        
        # Listen for responses for a few seconds
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                resp_data = json.loads(response)
                
                # Extract session ID if present
                if resp_data.get("id") == 1 and "result" in resp_data:
                    session_id = resp_data["result"].get("sessionId")
                    print(f"Got session ID: {session_id}\n")
                    break
                    
        except asyncio.TimeoutError:
            pass
        
        # Now test each method
        for i, method in enumerate(methods_to_test, start=2):
            print(f"Testing method: {method}")
            
            params = {}
            if session_id and method != "startSession":
                params["sessionId"] = session_id
                
            # Add specific params for certain methods
            if method == "async.createAgent":
                params["agentId"] = "d"
            elif method == "workspace.listDirectory":
                params["path"] = "/"
            elif method == "sendMessage":
                params["message"] = "test"
                
            req = {
                "jsonrpc": "2.0",
                "id": i,
                "method": method,
                "params": params
            }
            
            await websocket.send(json.dumps(req))
            
            # Get response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                resp_data = json.loads(response)
                
                if "error" in resp_data:
                    print(f"  ❌ Error: {resp_data['error']['message']}")
                elif "result" in resp_data:
                    print(f"  ✅ Success: Method exists")
                else:
                    print(f"  ⚠️  Notification: {resp_data.get('method', 'Unknown')}")
                    
            except asyncio.TimeoutError:
                print(f"  ⏱️  Timeout: No response")
                
            print()


if __name__ == "__main__":
    print("=== WebSocket Methods Test ===\n")
    asyncio.run(test_methods())