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

def test_jsonrpc_routing_to_handlers(interactive_app):
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Test 'echo' method
        request = {"jsonrpc": "2.0", "id": 1, "method": "echo", "params": {"message": "hi"}}
        websocket.send_text(json.dumps(request))
        response = json.loads(websocket.receive_text())
        assert response["result"] == "hi"


        # Test 'add' method (should return method not found error)
        request = {"jsonrpc": "2.0", "id": 2, "method": "add", "params": {"a": 2, "b": 3}}
        websocket.send_text(json.dumps(request))
        response = json.loads(websocket.receive_text())
        assert response["error"]["code"] == -32601  # Method not found
        assert response["id"] == 2

        # Test unknown method
        request = {"jsonrpc": "2.0", "id": 3, "method": "unknown_method"}
        websocket.send_text(json.dumps(request))
        response = json.loads(websocket.receive_text())
        assert response["error"]["code"] == -32601  # Method not found
        assert response["id"] == 3
