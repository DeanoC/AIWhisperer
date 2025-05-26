import sys
import os
import json
import pytest
import threading
import time
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

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

def test_server_to_client_session_status_notification(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        req = {"jsonrpc": "2.0", "id": 20, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
        websocket.send_text(json.dumps(req))
        messages = []
        def receive_worker():
            try:
                messages.append(json.loads(websocket.receive_text()))
                messages.append(json.loads(websocket.receive_text()))
            except Exception as e:
                messages.append(e)
        t = threading.Thread(target=receive_worker)
        t.start()
        t.join(timeout=5.0)
        if t.is_alive():
            pytest.fail("Test timed out waiting for server messages (startSession)")
        # If an exception was appended, raise it
        for m in messages:
            if isinstance(m, Exception):
                raise m
        response = next((m for m in messages if m.get("result") and "sessionId" in m["result"]), None)
        notification = next((m for m in messages if m.get("method") == "SessionStatusNotification"), None)
        assert response is not None, f"No valid response found in: {messages}"
        assert notification is not None, f"No notification found in: {messages}"
        session_id = response["result"]["sessionId"]
        assert notification["params"]["status"] == 1  # SessionStatus.Active
        assert notification["params"]["sessionId"] == session_id

def test_async_notification_streaming(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Start a session and get sessionId
        start_req = {"jsonrpc": "2.0", "id": 100, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
        websocket.send_text(json.dumps(start_req))
        start_messages = [json.loads(websocket.receive_text()), json.loads(websocket.receive_text())]
        response = next((m for m in start_messages if m.get("result") and "sessionId" in m["result"]), None)
        assert response is not None, f"No valid startSession response found in: {start_messages}"
        session_id = response["result"]["sessionId"]
        # Now send the user message with the real session_id
        req = {"jsonrpc": "2.0", "id": 21, "method": "sendUserMessage", "params": {"sessionId": session_id, "message": "notify:stream"}}
        websocket.send_text(json.dumps(req))
        messages = []
        def receive_worker():
            try:
                messages.append(json.loads(websocket.receive_text()))
                messages.append(json.loads(websocket.receive_text()))
                messages.append(json.loads(websocket.receive_text()))
            except Exception as e:
                messages.append(e)
        t = threading.Thread(target=receive_worker)
        t.start()
        t.join(timeout=5.0)
        if t.is_alive():
            pytest.fail("Test timed out waiting for server messages (sendUserMessage)")
        # If an exception was appended, raise it
        for m in messages:
            if isinstance(m, Exception):
                raise m
        response = next((m for m in messages if m.get("result") and "messageId" in m["result"]), None)
        ai_chunks = [m for m in messages if m.get("method") == "AIMessageChunkNotification"]
        assert response is not None, f"No valid response found in: {messages}"
        assert ai_chunks, f"No AIMessageChunkNotification found in: {messages}"
