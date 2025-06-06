"""Test async agent wake/sleep scheduling."""

import pytest
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List


class TestAsyncWakeSchedule:
    """Test async agent scheduling capabilities."""
    
    @pytest.mark.asyncio
    async def test_scheduled_wake(self):
        """Test agent wakes on schedule to perform tasks."""
        import websockets
        
        uri = "ws://localhost:8000/ws"
        
        async with websockets.connect(uri) as websocket:
            # Helper to send and track requests
            request_id = 1
            
            async def send_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
                nonlocal request_id
                req = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": params
                }
                request_id += 1
                
                await websocket.send(json.dumps(req))
                # Get immediate response
                while True:
                    response = await websocket.recv()
                    resp_data = json.loads(response)
                    if resp_data.get("id") == req["id"]:
                        return resp_data
            
            # Start session
            session_resp = await send_request("startSession", {
                "userId": "test_async_user",
                "sessionParams": {}
            })
            session_id = session_resp["result"]["sessionId"]
            
            # Create async Debbie
            create_resp = await send_request("async.createAgent", {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            })
            
            assert create_resp.get("result", {}).get("success"), "Failed to create agent"
            
            # Put Debbie to sleep for 3 seconds
            sleep_resp = await send_request("async.sleepAgent", {
                "sessionId": session_id,
                "agentId": "d",
                "durationSeconds": 3
            })
            
            assert sleep_resp.get("result", {}).get("success"), "Failed to sleep agent"
            
            # Check initial state
            states_resp = await send_request("async.getAgentStates", {
                "sessionId": session_id
            })
            
            agents = states_resp.get("result", {}).get("agents", {})
            assert agents.get("d", {}).get("state") == "sleeping", "Agent should be sleeping"
            
            # Wait for wake up
            await asyncio.sleep(4)
            
            # Check state after wake
            states_resp = await send_request("async.getAgentStates", {
                "sessionId": session_id
            })
            
            agents = states_resp.get("result", {}).get("agents", {})
            assert agents.get("d", {}).get("state") != "sleeping", "Agent should have woken up"
            
            # Stop agent
            await send_request("async.stopAgent", {
                "sessionId": session_id,
                "agentId": "d"
            })
            
            # Stop session
            await send_request("stopSession", {
                "sessionId": session_id
            })
    
    @pytest.mark.asyncio
    async def test_wake_check_mail_no_messages(self):
        """Test agent wakes, checks mail, finds none, goes back to sleep."""
        import websockets
        
        uri = "ws://localhost:8000/ws"
        
        async with websockets.connect(uri) as websocket:
            request_id = 1
            
            async def send_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
                nonlocal request_id
                req = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": params
                }
                request_id += 1
                
                await websocket.send(json.dumps(req))
                while True:
                    response = await websocket.recv()
                    resp_data = json.loads(response)
                    if resp_data.get("id") == req["id"]:
                        return resp_data
            
            # Start session
            session_resp = await send_request("startSession", {
                "userId": "test_async_user",
                "sessionParams": {}
            })
            session_id = session_resp["result"]["sessionId"]
            
            # Create async Debbie
            await send_request("async.createAgent", {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            })
            
            # Send task to check mail when waking
            await send_request("async.sendTask", {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": "Check your mailbox using check_mail(). If no messages, report 'No mail found' and go to sleep for 5 seconds."
            })
            
            # Wait for task processing
            await asyncio.sleep(2)
            
            # Collect notifications
            notifications = []
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if data.get("method") == "ChannelMessageNotification":
                        notifications.append(data["params"])
            except asyncio.TimeoutError:
                pass
            
            # Verify agent checked mail and reported no messages
            assert any("no mail" in str(n).lower() for n in notifications), \
                "Expected 'no mail' message"
            
            # Stop agent
            await send_request("async.stopAgent", {
                "sessionId": session_id,
                "agentId": "d"
            })
            
            await send_request("stopSession", {
                "sessionId": session_id
            })
    
    @pytest.mark.asyncio
    async def test_wake_process_mail(self):
        """Test agent wakes, finds mail, and processes it."""
        import websockets
        
        uri = "ws://localhost:8000/ws"
        
        async with websockets.connect(uri) as websocket:
            request_id = 1
            
            async def send_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
                nonlocal request_id
                req = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": params
                }
                request_id += 1
                
                await websocket.send(json.dumps(req))
                while True:
                    response = await websocket.recv()
                    resp_data = json.loads(response)
                    if resp_data.get("id") == req["id"]:
                        return resp_data
            
            # Start session
            session_resp = await send_request("startSession", {
                "userId": "test_async_user",
                "sessionParams": {}
            })
            session_id = session_resp["result"]["sessionId"]
            
            # Create async Debbie
            await send_request("async.createAgent", {
                "sessionId": session_id,
                "agentId": "d",
                "autoStart": True
            })
            
            # First, use Alice to send mail to Debbie's mailbox
            await send_request("sendMessage", {
                "sessionId": session_id,
                "message": "Use send_mail tool to send a message to Debbie asking 'What is 20 + 30?'"
            })
            
            await asyncio.sleep(2)
            
            # Now wake Debbie to check mail
            await send_request("async.wakeAgent", {
                "sessionId": session_id,
                "agentId": "d",
                "reason": "mail_check"
            })
            
            # Send task to check and process mail
            await send_request("async.sendTask", {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": "Check your mailbox and process any messages you find."
            })
            
            # Wait for processing
            await asyncio.sleep(3)
            
            # Collect responses
            responses = []
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    responses.append(json.loads(msg))
            except asyncio.TimeoutError:
                pass
            
            # Verify Debbie processed the math question
            notifications = [r for r in responses if r.get("method") == "ChannelMessageNotification"]
            assert any("50" in str(n) for n in notifications), \
                "Expected answer '50' in responses"
            
            # Stop agent
            await send_request("async.stopAgent", {
                "sessionId": session_id,
                "agentId": "d"
            })
            
            await send_request("stopSession", {
                "sessionId": session_id
            })


if __name__ == "__main__":
    # Run tests
    asyncio.run(TestAsyncWakeSchedule().test_scheduled_wake())
    print("✅ Scheduled wake test passed")
    
    asyncio.run(TestAsyncWakeSchedule().test_wake_check_mail_no_messages())
    print("✅ Wake check mail (no messages) test passed")
    
    asyncio.run(TestAsyncWakeSchedule().test_wake_process_mail())
    print("✅ Wake process mail test passed")