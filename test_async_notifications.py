#!/usr/bin/env python3
"""Test async agent WebSocket notifications."""

import asyncio
import json
import time
from websockets import connect


async def test_async_notifications():
    """Test that async agents send proper notifications."""
    ws_url = "ws://localhost:8000/ws"
    notifications_received = []
    
    print("1. Connecting to WebSocket...")
    async with connect(ws_url) as websocket:
        # Start session
        print("2. Starting session...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "startSession",
            "params": {
                "userId": "test-user",
                "sessionParams": {
                    "model": "openai/gpt-4o-mini"
                }
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        
        # Function to collect messages
        async def collect_messages(duration=10):
            """Collect messages for a duration."""
            end_time = time.time() + duration
            session_id = None
            
            while time.time() < end_time:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    msg = json.loads(message)
                    
                    # Handle response to get session ID
                    if msg.get("id") == request_id:
                        session_id = msg["result"]["sessionId"]
                        print(f"   Got session: {session_id}")
                    
                    # Collect notifications
                    elif "method" in msg and "id" not in msg:
                        notifications_received.append(msg)
                        print(f"   [Notification] {msg['method']}")
                        
                        # Print task notifications in detail
                        if msg['method'].startswith('async.task.'):
                            params = msg.get('params', {})
                            print(f"     Agent: {params.get('agent_id')}")
                            print(f"     Task ID: {params.get('task_id')}")
                            
                            if msg['method'] == 'async.task.completed':
                                result = params.get('result', {})
                                if isinstance(result, dict):
                                    print(f"     Final: {result.get('final', 'N/A')}")
                            elif msg['method'] == 'async.task.error':
                                print(f"     Error: {params.get('error', 'Unknown error')}")
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"   Error receiving: {e}")
                    break
            
            return session_id
        
        # Collect initial messages and get session ID
        session_id = await collect_messages(2)
        
        if not session_id:
            print("   ❌ Failed to get session ID")
            return
        
        # Create async agent
        print("\n3. Creating async agent 'd'...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.createAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        await asyncio.sleep(1)  # Wait for response
        
        # Send task to agent
        print("\n4. Sending task to agent...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.sendTask",
            "params": {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": "List 3 tools you have access to, be brief."
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        
        # Collect notifications for task processing
        print("\n5. Waiting for task notifications...")
        await collect_messages(8)
        
        # Stop agent
        print("\n6. Stopping agent...")
        request_id = str(time.time())
        request = {
            "jsonrpc": "2.0",
            "method": "async.stopAgent",
            "params": {
                "sessionId": session_id,
                "agentId": "d"
            },
            "id": request_id
        }
        
        await websocket.send(json.dumps(request))
        await asyncio.sleep(1)
        
    # Summary
    print("\n=== SUMMARY ===")
    print(f"Total notifications received: {len(notifications_received)}")
    
    # Check for expected notifications
    task_notifications = [n for n in notifications_received if n['method'].startswith('async.task.')]
    print(f"Task notifications: {len(task_notifications)}")
    
    for notif in task_notifications:
        print(f"  - {notif['method']}")
    
    # Verify we got the expected notifications
    expected = ['async.task.started', 'async.task.completed']
    received_methods = [n['method'] for n in task_notifications]
    
    print("\n=== VERIFICATION ===")
    for exp in expected:
        if exp in received_methods:
            print(f"✅ {exp}")
        else:
            print(f"❌ {exp} - NOT RECEIVED")
    
    # Check if we got the response content
    completed_notifs = [n for n in task_notifications if n['method'] == 'async.task.completed']
    if completed_notifs:
        result = completed_notifs[0].get('params', {}).get('result', {})
        if result.get('final'):
            print(f"\n✅ Got final response: {result['final'][:100]}...")
        else:
            print(f"\n❌ No final response in completed notification")


if __name__ == "__main__":
    asyncio.run(test_async_notifications())