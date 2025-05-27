import pytest
import threading
import json
import time
from fastapi.testclient import TestClient
from interactive_server.main import app

NUM_CLIENTS = 12

@pytest.mark.timeout(30)
def test_websocket_stress():
    client = TestClient(app)
    results = [None] * NUM_CLIENTS
    errors = [None] * NUM_CLIENTS

    def client_thread(idx):
        try:
            with client.websocket_connect("/ws") as ws:
                # Start session
                req = {"jsonrpc": "2.0", "id": 1, "method": "startSession", "params": {"userId": f"u{idx}", "sessionParams": {"language": "en"}}}
                ws.send_text(json.dumps(req))
                start_msgs = [json.loads(ws.receive_text()), json.loads(ws.receive_text())]
                session_id = None
                for m in start_msgs:
                    if m.get("result") and "sessionId" in m["result"]:
                        session_id = m["result"]["sessionId"]
                assert session_id
                # Send a user message
                user_msg = {"jsonrpc": "2.0", "id": 2, "method": "sendUserMessage", "params": {"sessionId": session_id, "message": f"Hello from client {idx}"}}
                ws.send_text(json.dumps(user_msg))
                # Wait for at least one AI chunk notification
                found_chunk = False
                for _ in range(5):
                    msg = json.loads(ws.receive_text())
                    if msg.get("method") == "AIMessageChunkNotification":
                        found_chunk = True
                        break
                assert found_chunk
                # Stop session
                stop_req = {"jsonrpc": "2.0", "id": 3, "method": "stopSession", "params": {"sessionId": session_id}}
                ws.send_text(json.dumps(stop_req))
                stop_resp = None
                # Loop to filter out notifications until we get the stop response
                for _ in range(10):
                    msg = json.loads(ws.receive_text())
                    # JSON-RPC response to stopSession will have 'result' and 'id' == 3
                    if msg.get("id") == 3 and "result" in msg:
                        stop_resp = msg
                        break
                assert stop_resp is not None, "Did not receive stopSession response"
                assert stop_resp.get("result", {}).get("status") == 2  # Stopped
                results[idx] = True
        except Exception as e:
            errors[idx] = str(e)
            results[idx] = False

    threads = [threading.Thread(target=client_thread, args=(i,)) for i in range(NUM_CLIENTS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(results), f"Some clients failed: {errors}"
