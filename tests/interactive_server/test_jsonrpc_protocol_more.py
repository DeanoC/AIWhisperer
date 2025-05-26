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

def test_jsonrpc_method_not_found(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        request = {"jsonrpc": "2.0", "id": 10, "method": "does_not_exist"}
        websocket.send_text(json.dumps(request))
        response = json.loads(websocket.receive_text())
        assert response["error"]["code"] == -32601
        assert response["error"]["message"] == "Method not found"
        assert response["id"] == 10

def test_jsonrpc_parse_error(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("not a json string")
        response = json.loads(websocket.receive_text())
        assert response["error"]["code"] == -32700  # Parse error
        assert response["error"]["message"] == "Parse error"
        assert response["id"] is None

def test_jsonrpc_invalid_params(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # 'add' is not a registered tool/method, so this simulates an invalid tool call
        request = {"jsonrpc": "2.0", "id": 11, "method": "add", "params": {"a": 1}}
        websocket.send_text(json.dumps(request))
        response = json.loads(websocket.receive_text())
        assert response["error"]["code"] == -32601  # Method not found (invalid tool)
        assert response["error"]["message"] == "Method not found"
        assert response["id"] == 11
