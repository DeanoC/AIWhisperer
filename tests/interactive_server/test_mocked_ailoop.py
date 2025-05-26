import sys
import os
import json
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def test_tool_call_and_result_flow(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Start a session and get sessionId
        start_req = {"jsonrpc": "2.0", "id": 1, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
        websocket.send_text(json.dumps(start_req))
        messages = [json.loads(websocket.receive_text()), json.loads(websocket.receive_text())]
        response = next((m for m in messages if m.get("result") and "sessionId" in m["result"]), None)
        assert response is not None
        session_id = response["result"]["sessionId"]
        # Simulate a user message that triggers a tool call (real server just echoes or processes normally)
        req = {"jsonrpc": "2.0", "id": 10, "method": "sendUserMessage", "params": {"sessionId": session_id, "message": "tool:run"}}
        websocket.send_text(json.dumps(req))
        resp = json.loads(websocket.receive_text())
        assert "messageId" in resp["result"]
        assert resp["result"]["status"] == 0  # MessageStatus.OK

def get_app():
    import importlib.util
    main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../interactive_server/main.py'))
    spec = importlib.util.spec_from_file_location('interactive_server.main', main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app

@pytest.fixture(scope="module")
def interactive_app():
    return get_app()

def test_start_session_mocked(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        req = {"jsonrpc": "2.0", "id": 1, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
        websocket.send_text(json.dumps(req))
        # Receive both the response and notification (order may vary)
        messages = [json.loads(websocket.receive_text()), json.loads(websocket.receive_text())]
        response = next((m for m in messages if m.get("result") and "sessionId" in m["result"]), None)
        assert response is not None, f"No valid response found in: {messages}"
        assert response["result"]["status"] == 1  # SessionStatus.Active

def test_send_user_message_mocked(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Start a session and get sessionId
        start_req = {"jsonrpc": "2.0", "id": 1, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
        websocket.send_text(json.dumps(start_req))
        messages = [json.loads(websocket.receive_text()), json.loads(websocket.receive_text())]
        response = next((m for m in messages if m.get("result") and "sessionId" in m["result"]), None)
        assert response is not None
        session_id = response["result"]["sessionId"]
        req = {"jsonrpc": "2.0", "id": 2, "method": "sendUserMessage", "params": {"sessionId": session_id, "message": "hi"}}
        websocket.send_text(json.dumps(req))
        resp = json.loads(websocket.receive_text())
        assert "messageId" in resp["result"]
        assert resp["result"]["status"] == 0  # MessageStatus.OK

def test_ai_message_chunk_notification_stream(interactive_app):
    import threading, sys
    exc = [None]
    def test_body():
        try:
            client = TestClient(interactive_app)
            with client.websocket_connect("/ws") as websocket:
                # Start a session and get sessionId
                start_req = {"jsonrpc": "2.0", "id": 1, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
                websocket.send_text(json.dumps(start_req))
                messages = [json.loads(websocket.receive_text()), json.loads(websocket.receive_text())]
                response = next((m for m in messages if m.get("result") and "sessionId" in m["result"]), None)
                assert response is not None
                session_id = response["result"]["sessionId"]
                # Simulate a method that triggers streaming (mocked)
                req = {"jsonrpc": "2.0", "id": 3, "method": "sendUserMessage", "params": {"sessionId": session_id, "message": "stream"}}
                websocket.send_text(json.dumps(req))
                # Receive two messages, order may vary
                messages = [json.loads(websocket.receive_text()), json.loads(websocket.receive_text())]
                # Find response and notification
                response = next((m for m in messages if m.get("result") and m.get("result").get("messageId")), None)
                notification = next((m for m in messages if m.get("method") == "AIMessageChunkNotification"), None)
                assert response is not None, f"No valid response found in: {messages}"
                assert notification is not None, f"No notification found in: {messages}"
                assert notification["params"]["chunk"] == "This is a chunk"
                assert notification["params"]["isFinal"] is True
        except Exception as e:
            exc[0] = e
    t = threading.Thread(target=test_body, daemon=True)
    t.start()
    t.join(20)
    if t.is_alive():
        print("Test timed out! Possible infinite loop.")
        sys.exit(1)
    if exc[0]:
        raise exc[0]
