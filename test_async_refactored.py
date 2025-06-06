#!/usr/bin/env python
"""Test async agent creation with the refactored implementation."""

import asyncio
import json
import websockets
import time


async def receive_response(websocket, request_id):
    """Receive response, handling notifications."""
    while True:
        response = await websocket.recv()
        result = json.loads(response)
        
        # Skip notifications
        if "method" in result and not result.get("id"):
            print(f"[Notification] {result['method']}: {result.get('params', {})}")
            continue
            
        # Check if this is our response
        if result.get("id") == request_id:
            return result
            
        print(f"[Unexpected response] {result}")


async def test_async_agent():
    """Test creating and managing async agents."""
    
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Start session
        session_msg = {
            "jsonrpc": "2.0",
            "method": "startSession",
            "params": {
                "userId": "test-user",
                "sessionParams": {"model": "google/gemini-2.5-flash-preview-05-20:thinking"}
            },
            "id": str(time.time())
        }
        
        request_id = session_msg["id"]
        await websocket.send(json.dumps(session_msg))
        result = await receive_response(websocket, request_id)
        
        if "error" in result:
            print("Error starting session:", result["error"])
            return
            
        session_id = result.get("result", {}).get("sessionId")
        if not session_id:
            print("No session ID in response")
            return
        print("✅ Session started:", session_id)
        
        # Test 1: Create an async agent
        create_msg = {
            "jsonrpc": "2.0",
            "method": "async.createAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            },
            "id": str(time.time())
        }
        
        request_id = create_msg["id"]
        await websocket.send(json.dumps(create_msg))
        result = await receive_response(websocket, request_id)
        
        if "error" in result:
            print("❌ Error creating agent:", result["error"])
            print("   Message:", result.get("message", "No message"))
            return
        else:
            print("✅ Async agent created:", result)
        
        # Test 2: Get agent states
        get_states_msg = {
            "jsonrpc": "2.0",
            "method": "async.getAgentStates",
            "params": {
                "sessionId": session_id
            },
            "id": str(time.time())
        }
        
        request_id = get_states_msg["id"]
        await websocket.send(json.dumps(get_states_msg))
        result = await receive_response(websocket, request_id)
        
        if "error" in result:
            print("❌ Error getting states:", result["error"])
        else:
            print("✅ Agent states:", json.dumps(result["result"], indent=2))
        
        # Test 3: Send a task to the agent
        send_task_msg = {
            "jsonrpc": "2.0",
            "method": "async.sendTaskToAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": "What tools do you have access to?",
                "context": {"test": True}
            },
            "id": str(time.time())
        }
        
        request_id = send_task_msg["id"]
        await websocket.send(json.dumps(send_task_msg))
        result = await receive_response(websocket, request_id)
        
        if "error" in result:
            print("❌ Error sending task:", result["error"])
        else:
            print("✅ Task sent successfully:", result)
        
        # Wait a bit for processing
        await asyncio.sleep(3)
        
        # Check agent states again
        request_id = get_states_msg["id"]
        await websocket.send(json.dumps(get_states_msg))
        result = await receive_response(websocket, request_id)
        
        if "error" not in result:
            print("✅ Agent states after task:", json.dumps(result["result"], indent=2))
        
        # Test 4: Stop the agent
        stop_msg = {
            "jsonrpc": "2.0",
            "method": "async.stopAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d"
            },
            "id": str(time.time())
        }
        
        request_id = stop_msg["id"]
        await websocket.send(json.dumps(stop_msg))
        result = await receive_response(websocket, request_id)
        
        if "error" in result:
            print("❌ Error stopping agent:", result["error"])
        else:
            print("✅ Agent stopped successfully")
        
        print("\n✨ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_async_agent())
