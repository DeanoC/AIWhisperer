"""Test async agent inspection and monitoring capabilities."""

import pytest
import json
import asyncio
from typing import Dict, Any, List


class TestAsyncInspection:
    """Test async agent inspection of other agents."""
    
    @pytest.mark.asyncio
    async def test_debbie_inspects_agents(self):
        """Test Debbie monitoring other agents' states."""
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
            
            # Create multiple async agents
            for agent_id in ["d", "e", "p"]:
                await send_request("async.createAgent", {
                    "sessionId": session_id,
                    "agentId": agent_id,
                    "autoStart": True
                })
            
            # Give agents different tasks
            await send_request("async.sendTask", {
                "sessionId": session_id,
                "agentId": "e",
                "prompt": "Count to 10 slowly, pausing 1 second between numbers."
            })
            
            await send_request("async.sleepAgent", {
                "sessionId": session_id,
                "agentId": "p",
                "durationSeconds": 10,
                "wakeEvents": ["urgent"]
            })
            
            # Have Debbie inspect other agents
            await send_request("async.sendTask", {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": """Inspect the current state of all agents in the system.
                Report on:
                1. Which agents are active
                2. Which agents are sleeping
                3. Any agents that might need attention
                Use any available tools to gather this information."""
            })
            
            # Wait for inspection
            await asyncio.sleep(3)
            
            # Collect Debbie's reports
            reports = []
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if (data.get("method") == "ChannelMessageNotification" and 
                        data.get("params", {}).get("metadata", {}).get("agentId") == "d"):
                        reports.append(data["params"])
            except asyncio.TimeoutError:
                pass
            
            # Verify Debbie reported on agent states
            report_content = str(reports)
            assert "e" in report_content or "eamonn" in report_content.lower(), \
                "Expected report on Agent E"
            assert "p" in report_content or "patricia" in report_content.lower(), \
                "Expected report on Agent P"
            assert "sleep" in report_content.lower() or "active" in report_content.lower(), \
                "Expected state information"
            
            # Stop all agents
            for agent_id in ["d", "e", "p"]:
                await send_request("async.stopAgent", {
                    "sessionId": session_id,
                    "agentId": agent_id
                })
            
            await send_request("stopSession", {
                "sessionId": session_id
            })
    
    @pytest.mark.asyncio
    async def test_wake_and_sync_mail(self):
        """Test async agent waking and using sync mail."""
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
            
            # Send task to simulate issue detection and alert
            await send_request("async.sendTask", {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": """Simulate detecting a critical issue:
                1. Report 'CRITICAL: Memory usage at 95%'
                2. Use send_mail_with_switch to alert Alice immediately
                3. Wait for Alice's response
                4. Report the outcome"""
            })
            
            # Wait for sync mail and response
            await asyncio.sleep(5)
            
            # Collect all messages
            messages = []
            agent_switches = []
            
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    messages.append(data)
                    
                    if data.get("method") == "agent.switched":
                        agent_switches.append(data["params"])
                        
            except asyncio.TimeoutError:
                pass
            
            # Verify sync mail flow occurred
            assert any(s["to"] == "a" for s in agent_switches), \
                "Expected switch to Alice"
            assert any(s["from"] == "a" and s["to"] == "d" for s in agent_switches), \
                "Expected switch back to Debbie"
            
            # Verify critical alert was sent
            notifications = [m for m in messages if m.get("method") == "ChannelMessageNotification"]
            assert any("critical" in str(n).lower() for n in notifications), \
                "Expected critical alert"
            
            # Stop agent
            await send_request("async.stopAgent", {
                "sessionId": session_id,
                "agentId": "d"
            })
            
            await send_request("stopSession", {
                "sessionId": session_id
            })
    
    @pytest.mark.asyncio
    async def test_wake_and_async_mail(self):
        """Test async agent sending mail without waiting."""
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
            
            # Create multiple async agents
            for agent_id in ["d", "e", "p"]:
                await send_request("async.createAgent", {
                    "sessionId": session_id,
                    "agentId": agent_id,
                    "autoStart": True
                })
            
            # Have Debbie send async notifications
            await send_request("async.sendTask", {
                "sessionId": session_id,
                "agentId": "d",
                "prompt": """Send status updates to other agents:
                1. Use send_mail to notify Eamonn: 'System check complete - all green'
                2. Use send_mail to notify Patricia: 'No new RFCs to review'
                3. Report 'Notifications sent to all agents'
                Do NOT wait for responses."""
            })
            
            # Wait for mail sending
            await asyncio.sleep(3)
            
            # Check that mail was sent
            notifications = []
            try:
                while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if data.get("method") == "ChannelMessageNotification":
                        notifications.append(data["params"])
            except asyncio.TimeoutError:
                pass
            
            # Verify Debbie sent notifications
            debbie_messages = [n for n in notifications 
                             if n.get("metadata", {}).get("agentId") == "d"]
            assert any("notifications sent" in str(m).lower() for m in debbie_messages), \
                "Expected confirmation of sent notifications"
            
            # Verify no agent switches (async mail doesn't switch)
            switches = [m for m in notifications if m.get("method") == "agent.switched"]
            assert len(switches) == 0, "Async mail should not cause agent switches"
            
            # Stop all agents
            for agent_id in ["d", "e", "p"]:
                await send_request("async.stopAgent", {
                    "sessionId": session_id,
                    "agentId": agent_id
                })
            
            await send_request("stopSession", {
                "sessionId": session_id
            })


if __name__ == "__main__":
    # Run tests
    asyncio.run(TestAsyncInspection().test_debbie_inspects_agents())
    print("✅ Agent inspection test passed")
    
    asyncio.run(TestAsyncInspection().test_wake_and_sync_mail())
    print("✅ Wake and sync mail test passed")
    
    asyncio.run(TestAsyncInspection().test_wake_and_async_mail())
    print("✅ Wake and async mail test passed")