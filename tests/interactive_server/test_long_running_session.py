
import asyncio
import json
import pytest
import websockets
import time
from tests.interactive_server.performance_metrics_utils import MetricsCollector

import pytest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_long_running_session_stability():
    """
    Open a WebSocket session, send periodic user messages for 10 minutes (shorten for CI),
    and verify the session remains stable and responsive throughout.
    """
    uri = "ws://127.0.0.1:8000/ws"
    session_id = None
    msg_id = 1
    metrics = MetricsCollector(csv_path="long_running_session_metrics.csv")
    async with websockets.connect(uri) as websocket:
        # Start session
        start_req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "startSession",
            "params": {"userId": "test_user", "sessionParams": {"language": "en"}}
        }
        metrics.start_timer("start_session")
        await websocket.send(json.dumps(start_req))
        msg_id += 1
        # Wait for sessionId
        for _ in range(10):
            msg = json.loads(await websocket.recv())
            if msg.get("result") and msg["result"].get("sessionId"):
                session_id = msg["result"]["sessionId"]
                metrics.stop_timer("start_session")
                break
        assert session_id, "Session ID not received."
        # Send periodic user messages
        for i in range(30):  # 30 iterations, ~20s total (short for CI)
            user_msg = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": "sendUserMessage",
                "params": {"sessionId": session_id, "message": f"ping {i}"}
            }
            metrics.start_timer(f"user_msg_{i}")
            await websocket.send(json.dumps(user_msg))
            msg_id += 1
            # Wait for response or chunk notification
            got_response = False
            for _ in range(10):
                msg = json.loads(await websocket.recv())
                if msg.get("result") and msg["result"].get("messageId"):
                    got_response = True
                    metrics.stop_timer(f"user_msg_{i}")
                    break
                if msg.get("method") == "AIMessageChunkNotification":
                    got_response = True
                    metrics.stop_timer(f"user_msg_{i}")
                    break
            if not got_response:
                metrics.record_error("no_response")
            assert got_response, f"No response for user message {i}"
            await asyncio.sleep(0.5)  # Wait before next message
        # Stop session
        stop_req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "stopSession",
            "params": {"sessionId": session_id}
        }
        metrics.start_timer("stop_session")
        await websocket.send(json.dumps(stop_req))
        # Confirm session stopped
        for _ in range(10):
            msg = json.loads(await websocket.recv())
            if msg.get("method") == "SessionStatusNotification" and msg["params"].get("status") == "ended":
                metrics.stop_timer("stop_session")
                break
        # Save metrics
        metrics.save()
