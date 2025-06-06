#!/usr/bin/env python3
"""Basic test for async agent functionality."""

import asyncio
import json
import websockets
import sys
from datetime import datetime


async def test_async_agents():
    """Test basic async agent operations."""
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Track request IDs
        request_id = 1
        
        # Helper to send request and get response
        async def send_request(method, params):
            nonlocal request_id
            req = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params
            }
            request_id += 1
            
            await websocket.send(json.dumps(req))
            response = await websocket.recv()
            resp_data = json.loads(response)
            print(f"Raw response: {resp_data}")
            return resp_data
        
        # 1. Start session
        print("\n1. Starting session...")
        session_resp = await send_request("startSession", {
            "userId": "test_async_user",
            "sessionParams": {}
        })
        if "result" in session_resp:
            session_id = session_resp["result"]["sessionId"]
        else:
            session_id = session_resp.get("sessionId")
        print(f"Session ID: {session_id}")
        
        # 2. Create async agent for Debbie
        print("\n2. Creating async agent Debbie...")
        create_resp = await send_request("async.createAgent", {
            "sessionId": session_id,
            "agentId": "d",
            "autoStart": True
        })
        print(f"Create response: {create_resp}")
        
        # 3. Check agent states
        print("\n3. Checking agent states...")
        states_resp = await send_request("async.getAgentStates", {
            "sessionId": session_id
        })
        print(f"Agent states: {states_resp}")
        
        # 4. Send a task to Debbie
        print("\n4. Sending task to Debbie...")
        task_resp = await send_request("async.sendTask", {
            "sessionId": session_id,
            "agentId": "d",
            "prompt": "What is 15 + 25? Please calculate and respond."
        })
        print(f"Task response: {task_resp}")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # 5. Check states again
        print("\n5. Checking agent states after task...")
        states_resp = await send_request("async.getAgentStates", {
            "sessionId": session_id
        })
        print(f"Agent states: {states_resp}")
        
        # 6. Put agent to sleep
        print("\n6. Putting Debbie to sleep for 5 seconds...")
        sleep_resp = await send_request("async.sleepAgent", {
            "sessionId": session_id,
            "agentId": "d",
            "durationSeconds": 5,
            "wakeEvents": ["urgent_task"]
        })
        print(f"Sleep response: {sleep_resp}")
        
        # 7. Check states while sleeping
        print("\n7. Checking states while sleeping...")
        states_resp = await send_request("async.getAgentStates", {
            "sessionId": session_id
        })
        print(f"Agent states: {states_resp}")
        
        # 8. Wake agent manually
        print("\n8. Waking Debbie manually...")
        wake_resp = await send_request("async.wakeAgent", {
            "sessionId": session_id,
            "agentId": "d",
            "reason": "manual test wake"
        })
        print(f"Wake response: {wake_resp}")
        
        # 9. Broadcast event
        print("\n9. Broadcasting event...")
        broadcast_resp = await send_request("async.broadcastEvent", {
            "sessionId": session_id,
            "event": "urgent_task",
            "data": {"message": "Test broadcast"}
        })
        print(f"Broadcast response: {broadcast_resp}")
        
        # 10. Stop agent
        print("\n10. Stopping Debbie...")
        stop_resp = await send_request("async.stopAgent", {
            "sessionId": session_id,
            "agentId": "d"
        })
        print(f"Stop response: {stop_resp}")
        
        # 11. Final state check
        print("\n11. Final state check...")
        states_resp = await send_request("async.getAgentStates", {
            "sessionId": session_id
        })
        print(f"Final agent states: {states_resp}")
        
        # Stop session
        print("\n12. Stopping session...")
        stop_session_resp = await send_request("stopSession", {
            "sessionId": session_id
        })
        print(f"Session stopped: {stop_session_resp}")
        
        print("\n✅ Async agent test completed!")


if __name__ == "__main__":
    print("=== Async Agents Basic Test ===")
    print(f"Starting at {datetime.now()}")
    
    try:
        asyncio.run(test_async_agents())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)