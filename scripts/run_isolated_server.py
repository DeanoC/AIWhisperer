#!/usr/bin/env python3
"""
Test script to start an isolated server and test plan endpoints.
"""

import sys
import os
import time
import threading
import requests
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_isolated_server():
    """Start an isolated server on a different port."""
    try:
        from batch.server_manager import ServerManager
        
        print("Starting isolated server...")
        server_manager = ServerManager()
        
        # Start server on port 8001 to avoid conflicts
        port = 8001
        server_manager.start_server(port=port, background=True)
        
        print(f"Server starting on port {port}...")
        time.sleep(3)  # Give server time to start
        
        return port
        
    except Exception as e:
        print(f"Error starting server: {e}")
        return None

def test_plan_endpoints(port):
    """Test the plan endpoints via HTTP JSON-RPC."""
    base_url = f"http://localhost:{port}"
    
    print(f"\nTesting plan endpoints on {base_url}")
    
    # Test plan.list endpoint
    print("\n=== Testing plan.list ===")
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "plan.list",
            "params": {},
            "id": 1
        }
        
        response = requests.post(f"{base_url}/rpc", json=payload, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"JSON-RPC Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error testing plan.list: {e}")
    
    # Test plan.read endpoint
    print("\n=== Testing plan.read ===")
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "plan.read",
            "params": {"plan_name": "agent-e-executioner-plan-2025-05-31"},
            "id": 2
        }
        
        response = requests.post(f"{base_url}/rpc", json=payload, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text[:500]}...")  # Truncate long response
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print(f"Plan data available: {bool(result['result'])}")
            else:
                print(f"JSON-RPC Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error testing plan.read: {e}")

def test_websocket_connection(port):
    """Test WebSocket connection that the frontend uses."""
    print(f"\n=== Testing WebSocket Connection ===")
    try:
        import websocket
        
        ws_url = f"ws://localhost:{port}/ws"
        print(f"Attempting WebSocket connection to: {ws_url}")
        
        def on_message(ws, message):
            print(f"Received: {message}")
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            print("WebSocket connection opened")
            # Send a plan.list request
            request = {
                "jsonrpc": "2.0",
                "method": "plan.list",
                "params": {},
                "id": 1
            }
            ws.send(json.dumps(request))
        
        ws = websocket.WebSocketApp(ws_url,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        # Run for a short time to test connection
        ws.run_forever(timeout=5)
        
    except ImportError:
        print("websocket-client not installed, skipping WebSocket test")
    except Exception as e:
        print(f"WebSocket test error: {e}")

if __name__ == "__main__":
    print("=== TESTING ISOLATED SERVER FOR PLAN UI ===")
    
    # Start isolated server
    port = start_isolated_server()
    
    if port:
        # Test HTTP endpoints
        test_plan_endpoints(port)
        
        # Test WebSocket connection
        test_websocket_connection(port)
        
        print(f"\n=== TEST COMPLETE ===")
        print(f"If the endpoints work, update your frontend to use: http://localhost:{port}")
        print(f"WebSocket URL should be: ws://localhost:{port}/ws")
    else:
        print("Failed to start isolated server")
