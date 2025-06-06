#!/usr/bin/env python3
"""Test async agents with correct method names."""

import asyncio
import json
import time
from websockets import connect


async def wait_for_response(websocket, request_id):
    """Wait for a response with specific ID, ignoring notifications."""
    while True:
        message = json.loads(await websocket.recv())
        
        # Skip notifications (they have method but no id)
        if "method" in message and "id" not in message:
            print(f"   [Notification] {message['method']}: {message.get('params', {})}")
            continue
            
        # Check if this is our response
        if message.get("id") == request_id:
            return message
            
        print(f"   [Unexpected message] {message}")


async def test_async_agents():
    """Test async agent functionality with correct method names."""
    ws_url = "ws://localhost:8000/ws"
    
    print("1. Connecting to WebSocket...")
    async with connect(ws_url) as websocket:
        # Start session
        print("2. Starting session...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "startSession",
            "params": {
                "userId": "test-user",
                "sessionParams": {
                    "model": "google/gemini-2.5-flash-preview-05-20:thinking"
                }
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        response = await wait_for_response(websocket, request_id)
        print(f"   Session started: {response}")
        
        session_id = response["result"]["sessionId"]
        
        # Create async agent
        print("\n3. Creating async agent 'd'...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.createAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        response = await wait_for_response(websocket, request_id)
        print(f"   Response: {response}")
        
        if "error" in response:
            print(f"   ❌ Error creating agent: {response['error']}")
            return
        
        # Get agent states
        print("\n4. Getting agent states...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.getAgentStates",
            "params": {
                "sessionId": session_id
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        response = await wait_for_response(websocket, request_id)
        print(f"   States: {json.dumps(response.get('result', {}), indent=2)}")
        
        # Send task using CORRECT method name
        print("\n5. Sending task to agent (using async.sendTask)...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.sendTask",  # Correct method name!
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": "What tools do you have access to?"
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        response = await wait_for_response(websocket, request_id)
        print(f"   Response: {response}")
        
        if "error" in response:
            print(f"   ❌ Error sending task: {response['error']}")
        else:
            print(f"   ✅ Task sent successfully!")
        
        # Wait a bit for processing
        print("\n   Waiting for task processing...")
        await asyncio.sleep(3)
        
        # Get states again to see if task was processed
        print("\n6. Getting agent states after task...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.getAgentStates",
            "params": {
                "sessionId": session_id
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        response = await wait_for_response(websocket, request_id)
        
        if "result" in response:
            states = response["result"].get("agents", {})
            for agent_id, state in states.items():
                print(f"\n   Agent '{agent_id}':")
                print(f"     State: {state['state']}")
                print(f"     Queue: {state['queue_depth']} tasks")
                print(f"     Current: {state['current_task']}")
                print(f"     Last active: {state['last_active']}")
        
        # Stop agent
        print("\n7. Stopping agent...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.stopAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d"
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        response = await wait_for_response(websocket, request_id)
        print(f"   Response: {response}")
        
        print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_async_agents())