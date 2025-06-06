#!/usr/bin/env python3
"""Test the refactored async agent implementation."""

import asyncio
import websocket
import json
import time

def send_request(ws, method, params):
    """Send a JSON-RPC request and get response."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(time.time())
    }
    
    print(f"\nSending: {method}")
    print(f"Params: {json.dumps(params, indent=2)}")
    
    ws.send(json.dumps(request))
    
    # Keep reading until we get the actual response (not a notification)
    while True:
        msg = json.loads(ws.recv())
        print(f"Received: {json.dumps(msg, indent=2)}")
        
        # Check if this is our response (has matching id)
        if "id" in msg and msg["id"] == request["id"]:
            return msg
        else:
            print("(Notification, waiting for response...)")

def main():
    """Test async agent creation and basic functionality."""
    # Connect to WebSocket
    ws = websocket.create_connection("ws://localhost:8000/ws")
    
    try:
        # 1. Start a session
        print("=== Starting Session ===")
        response = send_request(ws, "startSession", {
            "userId": "test-user",
            "sessionParams": {
                "model": "google/gemini-2.5-flash-preview-05-20:thinking"
            }
        })
        
        if "error" in response:
            print(f"Error starting session: {response['error']}")
            return
            
        session_id = response["result"]["sessionId"]
        print(f"\nSession ID: {session_id}")
        
        # 2. Create async agent
        print("\n=== Creating Async Agent ===")
        response = send_request(ws, "async.createAgent", {
            "sessionId": session_id,
            "agentId": "d",
            "autoStart": False  # Don't start background processor yet
        })
        
        if "error" in response:
            print(f"Error creating agent: {response['error']}")
            return
            
        # 3. Get agent states
        print("\n=== Getting Agent States ===")
        response = send_request(ws, "async.getAgentStates", {
            "sessionId": session_id
        })
        
        # 4. Send a task to the agent
        print("\n=== Sending Task to Agent ===")
        response = send_request(ws, "async.sendTask", {
            "sessionId": session_id,
            "agentId": "d",
            "prompt": "Hello! Can you confirm you're running as an async agent?",
            "context": {"test": True}
        })
        
        # 5. Start the agent processor
        print("\n=== Starting Agent Processor ===")
        response = send_request(ws, "async.startAgent", {
            "sessionId": session_id,
            "agentId": "d"
        })
        
        # Wait a bit for processing
        print("\nWaiting for agent to process task...")
        time.sleep(3)
        
        # 6. Check agent states again
        print("\n=== Final Agent States ===")
        response = send_request(ws, "async.getAgentStates", {
            "sessionId": session_id
        })
        
        # 7. Stop the agent
        print("\n=== Stopping Agent ===")
        response = send_request(ws, "async.stopAgent", {
            "sessionId": session_id,
            "agentId": "d"
        })
        
        print("\n=== Test Complete ===")
        
    finally:
        ws.close()

if __name__ == "__main__":
    main()