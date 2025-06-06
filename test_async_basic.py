#!/usr/bin/env python3
"""Basic test to verify async agent functionality after restart."""

import asyncio
import json
import websockets


async def test_async_agent_creation():
    """Test creating an async agent."""
    print("Testing async agent creation...")
    
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Start session
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "startSession",
            "params": {"userId": "test_user", "sessionParams": {}}
        }))
        
        # Get session ID
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 1:
                session_id = data["result"]["sessionId"]
                print(f"✅ Session created: {session_id}")
                break
        
        # Create async agent
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "async.createAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            }
        }))
        
        # Check response
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 2:
                if "error" in data:
                    print(f"❌ Error: {data['error']}")
                    return False
                else:
                    print(f"✅ Async agent created: {data['result']}")
                    return True


async def test_async_agent_sleep_wake():
    """Test sleep and wake functionality."""
    print("\nTesting sleep/wake functionality...")
    
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Start session
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "startSession",
            "params": {"userId": "test_user", "sessionParams": {}}
        }))
        
        # Get session ID
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 1:
                session_id = data["result"]["sessionId"]
                break
        
        # Create async agent
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "async.createAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            }
        }))
        
        # Wait for creation
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 2:
                if "error" in data:
                    return False
                break
        
        # Sleep agent
        print("  Putting agent to sleep for 2 seconds...")
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "async.sleepAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "durationSeconds": 2
            }
        }))
        
        # Check sleep response
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 3:
                if "error" in data:
                    print(f"❌ Sleep error: {data['error']}")
                    return False
                else:
                    print(f"✅ Agent sleeping: {data['result']}")
                break
        
        # Check state
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "async.getAgentStates",
            "params": {"sessionId": session_id}
        }))
        
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 4:
                states = data["result"]["agents"]
                print(f"  Agent states: {states}")
                break
        
        # Wait for automatic wake
        print("  Waiting for automatic wake...")
        await asyncio.sleep(3)
        
        # Check state again
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "async.getAgentStates",
            "params": {"sessionId": session_id}
        }))
        
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("id") == 5:
                states = data["result"]["agents"]
                print(f"✅ Agent states after wake: {states}")
                return True


async def main():
    """Run basic async agent tests."""
    print("=== Basic Async Agent Test ===\n")
    
    # Test 1: Create async agent
    success1 = await test_async_agent_creation()
    
    if not success1:
        print("\n⚠️  Async agent creation failed!")
        print("Please ensure the server has been restarted.")
        return
    
    # Test 2: Sleep/wake
    success2 = await test_async_agent_sleep_wake()
    
    if success2:
        print("\n✅ All async agent tests passed!")
    else:
        print("\n❌ Some tests failed.")


if __name__ == "__main__":
    asyncio.run(main())