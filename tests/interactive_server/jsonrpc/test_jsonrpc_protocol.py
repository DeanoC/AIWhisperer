import pytest
from fastapi.testclient import TestClient
import json

@pytest.fixture(scope="module")
def interactive_app():
    import importlib.util
    import os
    main_path = 'd:/Projects/AIWhisperer/interactive_server/main.py'
    if not os.path.isfile(main_path):
        pytest.skip('main.py does not exist yet')
    spec = importlib.util.spec_from_file_location('interactive_server.main', main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'app'):
        pytest.skip('FastAPI app not defined in main.py')
    return module.app

def test_jsonrpc_request_response(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Send a valid JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "echo",
            "params": {"message": "hello"}
        }
        websocket.send_text(json.dumps(request))
        response = websocket.receive_text()
        data = json.loads(response)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert data["result"] == "hello"

def test_jsonrpc_invalid_request(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Send an invalid JSON-RPC request (missing method)
        request = {"jsonrpc": "2.0", "id": 2}
        websocket.send_text(json.dumps(request))
        response = websocket.receive_text()
        data = json.loads(response)
        assert data["error"]["code"] == -32600  # Invalid Request
        assert data["id"] == 2

def test_jsonrpc_notification(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Send a JSON-RPC notification (no id)
        request = {"jsonrpc": "2.0", "method": "notify", "params": {"foo": "bar"}}
        websocket.send_text(json.dumps(request))
        # Should not receive a response for notifications
        import time
        import threading
        result = []
        def try_receive():
            try:
                result.append(websocket.receive_text())
            except Exception:
                pass
        t = threading.Thread(target=try_receive)
        t.start()
        t.join(timeout=0.5)
        assert not result, "Should not receive a response for notifications"
