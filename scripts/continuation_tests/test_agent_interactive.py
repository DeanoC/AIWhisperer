#!/usr/bin/env python3
"""Test agent loading and basic interactive functionality"""

import asyncio
import json
import websockets
import subprocess
import time
import sys
import os

async def test_agent_functionality():
    """Test basic agent functionality"""
    
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    print(f"Changed to project root: {project_root}")
    
    # Start the server
    print("Starting interactive server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "interactive_server.main", "--port", "8002", "--config", "config/main.yaml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Give server time to start and check if it's running
    print("Waiting for server to start...")
    for i in range(10):
        time.sleep(1)
        if server_process.poll() is not None:
            # Server exited early
            output = server_process.stdout.read()
            print(f"Server exited with code {server_process.returncode}")
            print(f"Server output:\n{output}")
            return
        print(f"  {i+1}s...")
    print("Server should be running now")
    
    try:
        # Connect to WebSocket
        async with websockets.connect("ws://localhost:8002/ws") as websocket:
            print("Connected to WebSocket")
            
            # Test 1: List agents
            print("\n🧪 Test 1: List agents")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "agent.list",
                "params": {}
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if "result" in data and "agents" in data["result"]:
                agents = data["result"]["agents"]
                print(f"   ✅ Found {len(agents)} agents:")
                for agent in agents:
                    print(f"      - {agent['agent_id']}: {agent['name']}")
            else:
                print("   ❌ Failed to list agents")
            
            # Test 2: Start session
            print("\n🧪 Test 2: Start session")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "startSession",
                "params": {
                    "userId": "test-user",
                    "sessionParams": {}
                }
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if "result" in data and "sessionId" in data["result"]:
                session_id = data["result"]["sessionId"]
                print(f"   ✅ Session started: {session_id}")
            else:
                print("   ❌ Failed to start session")
                return
            
            # Test 3: Check current agent
            print("\n🧪 Test 3: Check current agent")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "session.current_agent",
                "params": {"sessionId": session_id}
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if "result" in data and "current_agent" in data["result"]:
                current_agent = data["result"]["current_agent"]
                print(f"   ✅ Current agent: {current_agent}")
            else:
                print("   ❌ Failed to get current agent")
            
            # Test 4: Switch to Debbie
            print("\n🧪 Test 4: Switch to Debbie")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 4,
                "method": "session.switch_agent",
                "params": {"agent_id": "d", "sessionId": session_id}
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if "result" in data and data["result"].get("success"):
                print(f"   ✅ Switched to agent: {data['result']['current_agent']}")
            else:
                print("   ❌ Failed to switch agent")
            
            # Test 5: Send a message
            print("\n🧪 Test 5: Send a test message")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 5,
                "method": "sendUserMessage",
                "params": {
                    "sessionId": session_id,
                    "message": "Hello Debbie! Can you briefly confirm you're working?"
                }
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Collect AI response chunks
            print("   Waiting for AI response...")
            ai_response = ""
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    chunk_data = json.loads(msg)
                    if chunk_data.get("method") == "AIMessageChunkNotification":
                        chunk = chunk_data["params"].get("chunk", "")
                        ai_response += chunk
                        if chunk_data["params"].get("isFinal"):
                            break
                except asyncio.TimeoutError:
                    break
            
            if ai_response:
                print(f"   ✅ Got AI response: {ai_response[:100]}...")
            else:
                print("   ❌ No AI response received")
            
    finally:
        # Clean up
        print("\nShutting down server...")
        server_process.terminate()
        server_process.wait()
        print("Server shut down")

if __name__ == "__main__":
    asyncio.run(test_agent_functionality())