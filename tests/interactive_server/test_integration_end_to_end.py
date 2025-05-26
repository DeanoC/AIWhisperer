import sys
import os
import json
import pytest
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

def test_end_to_end_websocket_jsonrpc(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Start a session
        start_req = {"jsonrpc": "2.0", "id": 100, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
        websocket.send_text(json.dumps(start_req))
        messages = [json.loads(websocket.receive_text()), json.loads(websocket.receive_text())]
        response = next((m for m in messages if m.get("result") and "sessionId" in m["result"]), None)
        notification = next((m for m in messages if m.get("method") == "SessionStatusNotification"), None)
        assert response is not None
        assert notification is not None
        session_id = response["result"]["sessionId"]
        # Send a user message
        user_msg = {"jsonrpc": "2.0", "id": 101, "method": "sendUserMessage", "params": {"sessionId": session_id, "message": "hello"}}
        websocket.send_text(json.dumps(user_msg))
        resp = json.loads(websocket.receive_text())
        assert "messageId" in resp["result"]

def test_invalid_jsonrpc_request(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Send invalid JSON
        websocket.send_text("not a json string")
        resp = json.loads(websocket.receive_text())
        assert resp["error"]["code"] == -32700  # Parse error
        # Send invalid JSON-RPC (missing method)
        websocket.send_text(json.dumps({"jsonrpc": "2.0", "id": 200}))
        resp2 = json.loads(websocket.receive_text())
        assert resp2["error"]["code"] == -32600  # Invalid Request
