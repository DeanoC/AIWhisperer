#!/usr/bin/env python3
"""Demo script to test async agent functionality after server restart."""

import asyncio
import json
import websockets
from datetime import datetime


async def demo_sync_mail_complex():
    """Demo complex multi-step sync mail task."""
    print("\n=== Demo 1: Complex Multi-Step Task ===")
    print("Alice delegates complex analysis to Debbie\n")
    
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Start session
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "startSession",
            "params": {"userId": "demo_user", "sessionParams": {}}
        }))
        
        # Wait for session start
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 1:
                session_id = data["result"]["sessionId"]
                print(f"Session started: {session_id}")
                break
        
        # Send complex task
        message = """Use send_mail_with_switch to send this task to Debbie:
        'Please analyze the ai_whisperer/tools directory and provide a report:
        1. Count Python files
        2. List tool categories
        3. Find mail-related tools
        4. Summarize findings'"""
        
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "sendMessage",
            "params": {"sessionId": session_id, "message": message}
        }))
        
        print("Task sent to Debbie...")
        print("Waiting for analysis...\n")
        
        # Collect responses
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < 10:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                
                if data.get("method") == "agent.switched":
                    params = data["params"]
                    print(f"🔄 Agent switch: {params['from']} → {params['to']}")
                
                elif data.get("method") == "ChannelMessageNotification":
                    content = data["params"].get("content", "")
                    agent = data["params"].get("metadata", {}).get("agentId", "?")
                    if content and len(content) > 2:
                        print(f"💬 Agent {agent.upper()}: {content[:100]}...")
                        
            except asyncio.TimeoutError:
                continue
        
        print("\n✅ Complex task demo complete!")


async def demo_async_agents():
    """Demo async agent capabilities."""
    print("\n\n=== Demo 2: Async Agent Wake/Sleep ===")
    print("Creating async agents that work independently\n")
    
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        request_id = 1
        
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
            # Wait for response with matching ID
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                if data.get("id") == req["id"]:
                    return data
        
        # Start session
        session_resp = await send_request("startSession", {
            "userId": "demo_user",
            "sessionParams": {}
        })
        session_id = session_resp["result"]["sessionId"]
        print(f"Session started: {session_id}")
        
        # Try to create async agent
        print("\nCreating async Debbie...")
        try:
            create_resp = await send_request("async.createAgent", {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            })
            
            print(f"DEBUG: Response: {create_resp}")
            
            if "error" in create_resp:
                error_msg = create_resp.get('error', {})
                if isinstance(error_msg, dict):
                    print(f"❌ Error: {error_msg.get('message', error_msg)}")
                else:
                    print(f"❌ Error: {error_msg}")
                print("\n⚠️  Async agent methods not available.")
                print("Please restart the server to enable async functionality.")
                return
            
            print("✅ Async Debbie created!")
            
            # Put to sleep
            print("\nPutting Debbie to sleep for 5 seconds...")
            await send_request("async.sleepAgent", {
                "sessionId": session_id,
                "agentId": "d",
                "durationSeconds": 5
            })
            
            # Check state
            states_resp = await send_request("async.getAgentStates", {
                "sessionId": session_id
            })
            
            agents = states_resp["result"]["agents"]
            print(f"Agent states: {json.dumps(agents, indent=2)}")
            
            print("\nWaiting for automatic wake...")
            await asyncio.sleep(6)
            
            # Check state again
            states_resp = await send_request("async.getAgentStates", {
                "sessionId": session_id
            })
            
            agents = states_resp["result"]["agents"]
            print(f"Agent states after wake: {json.dumps(agents, indent=2)}")
            
            # Stop agent
            await send_request("async.stopAgent", {
                "sessionId": session_id,
                "agentId": "d"
            })
            
            print("\n✅ Async agent demo complete!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n⚠️  Make sure the server has been restarted to load async handlers.")


async def main():
    """Run all demos."""
    print("=== AIWhisperer Async Agents Demo ===")
    print(f"Starting at {datetime.now()}\n")
    
    # Demo 1: Sync mail (should work)
    await demo_sync_mail_complex()
    
    # Demo 2: Async agents (requires server restart)
    await demo_async_agents()
    
    print("\n\n=== Demo Complete ===")
    print("If async demos failed, please:")
    print("1. Stop the current server")
    print("2. Restart with the same command")
    print("3. Run this demo again")


if __name__ == "__main__":
    asyncio.run(main())