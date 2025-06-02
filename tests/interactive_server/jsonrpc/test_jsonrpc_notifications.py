import pytest
from fastapi.testclient import TestClient
import json
import threading
import time

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

def test_jsonrpc_notification_no_response(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Send a notification (no id)
        request = {"jsonrpc": "2.0", "method": "notify", "params": {"foo": "bar"}}
        websocket.send_text(json.dumps(request))
        # Should not receive a response for notifications
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

def test_jsonrpc_response_for_request(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Send a request (with id)
        request = {"jsonrpc": "2.0", "id": 42, "method": "echo", "params": {"message": "test"}}
        websocket.send_text(json.dumps(request))
        response = json.loads(websocket.receive_text())
        assert response["id"] == 42
        assert response["result"] == "test"
