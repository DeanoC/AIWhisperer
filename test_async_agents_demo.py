#!/usr/bin/env python3
"""
Demo script for async agent functionality.

This demonstrates how to use the async agent endpoints via WebSocket.
"""

import asyncio
import json
import websockets
import uuid
from datetime import datetime


async def send_request(websocket, method, params):
    """Send JSON-RPC request and wait for response."""
    request_id = str(uuid.uuid4())
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    
    await websocket.send(json.dumps(request))
    
    # Wait for response
    while True:
        message = await websocket.recv()
        data = json.loads(message)
        
        if data.get("id") == request_id:
            return data
        else:
            # Notification or other message
            print(f"Notification: {data.get('method', 'unknown')}")


async def demo_async_agents():
    """Demonstrate async agent functionality."""
    
    # Connect to WebSocket
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to AIWhisperer WebSocket")
        
        # Start a session
        print("\n1. Starting session...")
        response = await send_request(websocket, "startSession", {
            "userId": "demo_user",
            "sessionParams": {}
        })
        
        session_id = response["result"]["sessionId"]
        print(f"Session started: {session_id}")
        
        # Create async agents
        print("\n2. Creating async agents...")
        
        # Create analyzer agent
        response = await send_request(websocket, "async.createAgent", {
            "sessionId": session_id,
            "agentId": "analyzer",
            "autoStart": True
        })
        print(f"Analyzer agent: {response['result']}")
        
        # Create writer agent
        response = await send_request(websocket, "async.createAgent", {
            "sessionId": session_id,
            "agentId": "writer",
            "autoStart": True
        })
        print(f"Writer agent: {response['result']}")
        
        # Create reviewer agent
        response = await send_request(websocket, "async.createAgent", {
            "sessionId": session_id,
            "agentId": "reviewer",
            "autoStart": False  # Don't start yet
        })
        print(f"Reviewer agent: {response['result']}")
        
        # Check agent states
        print("\n3. Checking agent states...")
        response = await send_request(websocket, "async.getAgentStates", {
            "sessionId": session_id
        })
        print(f"Agent states: {json.dumps(response['result']['agents'], indent=2)}")
        
        # Send task to analyzer
        print("\n4. Sending task to analyzer...")
        response = await send_request(websocket, "async.sendTask", {
            "sessionId": session_id,
            "agentId": "analyzer",
            "prompt": "Analyze the sentiment of customer feedback: 'Great product but shipping was slow'"
        })
        print(f"Task sent: {response['result']}")
        
        # Sleep reviewer agent with wake events
        print("\n5. Setting reviewer to sleep until 'review_ready' event...")
        response = await send_request(websocket, "async.sleepAgent", {
            "sessionId": session_id,
            "agentId": "reviewer",
            "wakeEvents": ["review_ready", "urgent_review"]
        })
        print(f"Sleep result: {response['result']}")
        
        # Start reviewer now
        response = await send_request(websocket, "async.startAgent", {
            "sessionId": session_id,
            "agentId": "reviewer"
        })
        print(f"Reviewer started: {response['result']}")
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        
        # Check states again
        print("\n6. Checking agent states after tasks...")
        response = await send_request(websocket, "async.getAgentStates", {
            "sessionId": session_id
        })
        print(f"Agent states: {json.dumps(response['result']['agents'], indent=2)}")
        
        # Broadcast event to wake reviewer
        print("\n7. Broadcasting 'review_ready' event...")
        response = await send_request(websocket, "async.broadcastEvent", {
            "sessionId": session_id,
            "event": "review_ready",
            "data": {"source": "writer", "document": "analysis_report_v1"}
        })
        print(f"Broadcast result: {response['result']}")
        
        # Final state check
        await asyncio.sleep(1)
        print("\n8. Final agent states...")
        response = await send_request(websocket, "async.getAgentStates", {
            "sessionId": session_id
        })
        print(f"Final states: {json.dumps(response['result']['agents'], indent=2)}")
        
        # Stop session
        print("\n9. Stopping session...")
        response = await send_request(websocket, "stopSession", {
            "sessionId": session_id
        })
        print(f"Session stopped: {response['result']}")


if __name__ == "__main__":
    print("Async Agents Demo")
    print("=================")
    print("Make sure AIWhisperer interactive server is running on port 8000")
    print()
    
    try:
        asyncio.run(demo_async_agents())
    except KeyboardInterrupt:
        print("\nDemo interrupted")
    except Exception as e:
        print(f"\nError: {e}")