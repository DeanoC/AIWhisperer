#!/usr/bin/env python3
"""
Debug script to investigate the plan data issue between Agent P and the frontend.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("🔍 Debugging Plan Data Issue")
    print("=" * 50)
    
    # Check if interactive server is running
    print("\n1. Checking server status...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Server is running: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Check plan data using Agent P tools
    print("\n2. Checking plan data via Agent P...")
    try:
        # Import agent P tools
        from ai_whisperer.agents import get_agent_by_name
        agent_p = get_agent_by_name("patricia")
        if agent_p:
            print(f"✅ Agent P found: {agent_p.name}")
        else:
            print("❌ Agent P not found")
    except Exception as e:
        print(f"❌ Error accessing Agent P: {e}")
    
    # Check plan directory
    print("\n3. Checking plan files...")
    plan_dirs = [
        "plans",
        "data/plans", 
        "output/plans",
        "../plans"
    ]
    
    for plan_dir in plan_dirs:
        plan_path = Path(plan_dir)
        if plan_path.exists():
            print(f"✅ Found plan directory: {plan_path.absolute()}")
            plan_files = list(plan_path.glob("*.json")) + list(plan_path.glob("*.yaml"))
            print(f"   Plan files: {len(plan_files)}")
            for file in plan_files[:5]:  # Show first 5
                print(f"   - {file.name}")
        else:
            print(f"❌ Plan directory not found: {plan_path}")
    
    # Check WebSocket connection
    print("\n4. Testing WebSocket connection...")
    try:
        import websocket
        ws = websocket.create_connection("ws://localhost:8000/ws")
        print("✅ WebSocket connection successful")
        
        # Test plan.list request
        request = {
            "jsonrpc": "2.0",
            "method": "plan.list",
            "params": {},
            "id": 1
        }
        ws.send(json.dumps(request))
        result = ws.recv()
        response = json.loads(result)
        print(f"📋 plan.list response: {response}")
        
        ws.close()
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    # Check frontend environment
    print("\n5. Checking frontend configuration...")
    frontend_env = Path("frontend/.env")
    if frontend_env.exists():
        print(f"✅ Frontend .env file found")
        with open(frontend_env) as f:
            content = f.read()
            print("Environment variables:")
            for line in content.strip().split('\n'):
                if 'WS_URL' in line or 'API' in line:
                    print(f"   {line}")
    else:
        print("❌ Frontend .env file not found")
    
    # Check package.json for start script
    package_json = Path("frontend/package.json")
    if package_json.exists():
        with open(package_json) as f:
            pkg = json.load(f)
            if 'scripts' in pkg and 'start' in pkg['scripts']:
                print(f"✅ Frontend start script: {pkg['scripts']['start']}")
    
    print("\n" + "=" * 50)
    print("Debug complete. Check the output above for issues.")

if __name__ == "__main__":
    main()
