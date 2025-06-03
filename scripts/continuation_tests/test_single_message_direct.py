#!/usr/bin/env python3
"""Direct test to debug batch mode issues"""

import asyncio
import json
import websockets
import subprocess
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_whisperer.core.config import load_config

async def test_simple_message():
    # Load config
    config = load_config("config/main.yaml")
    print(f"✅ Config loaded")
    
    # Start server
    print("\n🚀 Starting server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "interactive_server.main", "--port", "8765", "--config", "config/main.yaml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    start_time = time.time()
    server_ready = False
    while time.time() - start_time < 10:
        if server_process.poll() is not None:
            print("❌ Server process died!")
            stdout, _ = server_process.communicate()
            print(stdout)
            return
        
        # Check server output
        line = server_process.stdout.readline()
        if line:
            print(f"   Server: {line.strip()}")
            if "Application startup complete" in line or "Uvicorn running on" in line:
                server_ready = True
                break
    
    if not server_ready:
        print("❌ Server didn't start in time")
        server_process.terminate()
        return
    
    print("✅ Server ready!")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8765/ws"
        print(f"\n🔌 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Test 1: Start session
            print("\n📤 Starting session...")
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "startSession",
                "params": {
                    "userId": "test_user",
                    "sessionParams": {"language": "en"}
                }
            }
            
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Response: {data}")
            
            if "error" in data:
                print(f"❌ Error starting session: {data['error']}")
                return
            
            session_id = data.get("result", {}).get("sessionId")
            if not session_id:
                print("❌ No session ID in response!")
                return
            
            print(f"✅ Session started: {session_id}")
            
            # Test 2: Send simple message
            print("\n📤 Sending message: What is 2 + 2?")
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "sendUserMessage",
                "params": {
                    "sessionId": session_id,
                    "message": "What is 2 + 2?"
                }
            }
            
            await websocket.send(json.dumps(request))
            
            # Collect responses
            print("📥 Collecting responses...")
            responses = []
            start_time = time.time()
            
            while time.time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)
                    
                    if "method" in data:
                        # Notification
                        method = data["method"]
                        params = data.get("params", {})
                        
                        if method == "AIMessageChunkNotification":
                            chunk = params.get("chunk", "")
                            is_final = params.get("isFinal", False)
                            print(f"   Chunk: {chunk}", end="")
                            if is_final:
                                print("\n   ✅ Final chunk received")
                                break
                        else:
                            print(f"   Notification: {method}")
                    else:
                        # RPC response
                        print(f"   RPC Response: {data}")
                        
                except asyncio.TimeoutError:
                    continue
            
            print("\n✅ Test complete!")
            
    finally:
        # Stop server
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    asyncio.run(test_simple_message())