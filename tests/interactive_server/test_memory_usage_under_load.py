
import asyncio
import json
import pytest
import websockets
import tracemalloc
from tests.interactive_server.performance_metrics_utils import MetricsCollector

import pytest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_memory_usage_under_load():
    """
    Open multiple WebSocket sessions, send messages, and check memory usage does not grow unbounded.
    """
    uri = "ws://127.0.0.1:8000/ws"
    session_ids = []
    msg_id = 1
    num_sessions = 8
    num_messages = 10
    metrics = MetricsCollector(csv_path="memory_usage_metrics.csv")
    tracemalloc.start()
    websockets_list = []
    try:
        # Open sessions
        for i in range(num_sessions):
            ws = await websockets.connect(uri)
            websockets_list.append(ws)
            start_req = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": "startSession",
                "params": {"userId": f"user_{i}", "sessionParams": {"language": "en"}}
            }
            await ws.send(json.dumps(start_req))
            msg_id += 1
        # Collect session IDs
        for ws in websockets_list:
            for _ in range(10):
                msg = json.loads(await ws.recv())
                if msg.get("result") and msg["result"].get("sessionId"):
                    session_ids.append(msg["result"]["sessionId"])
                    break
        assert len(session_ids) == num_sessions
        # Send messages in all sessions
        for j in range(num_messages):
            for i, ws in enumerate(websockets_list):
                user_msg = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "method": "sendUserMessage",
                    "params": {"sessionId": session_ids[i], "message": f"ping {j}"}
                }
                metrics.start_timer(f"user_msg_{i}_{j}")
                await ws.send(json.dumps(user_msg))
                msg_id += 1
        # Wait for responses
        for i, ws in enumerate(websockets_list):
            for j in range(num_messages):
                for _ in range(10):
                    msg = json.loads(await ws.recv())
                    if msg.get("result") and msg["result"].get("messageId"):
                        metrics.stop_timer(f"user_msg_{i}_{j}")
                        break
                    if msg.get("method") == "AIMessageChunkNotification":
                        metrics.stop_timer(f"user_msg_{i}_{j}")
                        break
        # Check memory usage
        current, peak = tracemalloc.get_traced_memory()
        print(f"Current memory usage: {current / 1024 / 1024:.2f} MB; Peak: {peak / 1024 / 1024:.2f} MB")
        metrics.record_memory(current, peak)
        assert peak < 500 * 1024 * 1024, "Peak memory usage exceeded 500MB (adjust threshold as needed)"
    finally:
        for ws in websockets_list:
            await ws.close()
        tracemalloc.stop()
        metrics.save()
