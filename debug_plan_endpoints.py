#!/usr/bin/env python3
"""
Debug script for testing plan endpoints
"""
import json
import requests
import time
import sys

def test_plan_endpoints(port):
    """Test the plan endpoints on the given port"""
    base_url = f"http://127.0.0.1:{port}"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Server health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False
    
    # Test plan.list via JSON-RPC
    rpc_payload = {
        "jsonrpc": "2.0",
        "method": "plan.list",
        "params": {},
        "id": 1
    }
    
    try:
        response = requests.post(
            f"{base_url}/ws",  # Check if this is the right endpoint
            json=rpc_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"📋 plan.list response: {response.status_code}")
        print(f"📋 Response body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 JSON data: {json.dumps(data, indent=2)}")
        
    except Exception as e:
        print(f"❌ plan.list failed: {e}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8000  # Default port
    
    print(f"🔍 Testing plan endpoints on port {port}")
    test_plan_endpoints(port)
