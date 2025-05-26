import pytest
import asyncio
from fastapi import FastAPI, WebSocket
from starlette.testclient import TestClient

# Placeholder for import; will be updated when the actual app is implemented
import importlib.util
import os

@pytest.fixture(scope="module")
def interactive_app():
    main_path = 'd:/Projects/AIWhisperer/interactive_server/main.py'
    if not os.path.isfile(main_path):
        pytest.skip('main.py does not exist yet')
    spec = importlib.util.spec_from_file_location('interactive_server.main', main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Expecting the FastAPI app to be named 'app' in main.py
    if not hasattr(module, 'app'):
        pytest.skip('FastAPI app not defined in main.py')
    return module.app

def test_websocket_route_exists(interactive_app):
    import json
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        # Send a JSON-RPC echo request
        request = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "echo",
            "params": {"text": "ping"}
        }
        websocket.send_text(json.dumps(request))
        response = websocket.receive_text()
        data = json.loads(response)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-1"
        assert data["result"] == {"text": "ping"}

# Additional tests for multiple clients and lifecycle will be added after the endpoint exists.import pytest
import sys
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Dynamically import the interactive_server.main if it exists
main_path = os.path.join(os.path.dirname(__file__), '../../interactive_server/main.py')
main_path = os.path.abspath(main_path)

@pytest.mark.skipif(not os.path.isfile(main_path), reason="main.py does not exist yet")
def test_websocket_route_exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location('interactive_server.main', main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = getattr(module, 'app', None)
    assert isinstance(app, FastAPI), "main.py must define a FastAPI instance named 'app'"
    client = TestClient(app)
    # Try connecting to /ws and /interactive, one should exist
    found = False
    for route in ['/ws', '/interactive']:
        with client.websocket_connect(route) as websocket:
            found = True
            break
    assert found, "No WebSocket endpoint found at /ws or /interactive"

def test_websocket_multiple_clients(interactive_app):
    import json
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as ws1, client.websocket_connect("/ws") as ws2:
        req1 = {"jsonrpc": "2.0", "id": "c1", "method": "echo", "params": {"text": "client1"}}
        req2 = {"jsonrpc": "2.0", "id": "c2", "method": "echo", "params": {"text": "client2"}}
        ws1.send_text(json.dumps(req1))
        ws2.send_text(json.dumps(req2))
        resp1 = json.loads(ws1.receive_text())
        resp2 = json.loads(ws2.receive_text())
        assert resp1["jsonrpc"] == "2.0"
        assert resp1["id"] == "c1"
        assert resp1["result"] == {"text": "client1"}
        assert resp2["jsonrpc"] == "2.0"
        assert resp2["id"] == "c2"
        assert resp2["result"] == {"text": "client2"}

def test_websocket_lifecycle(interactive_app):
    import json
    client = TestClient(interactive_app)
    with client.websocket_connect("/ws") as websocket:
        request = {
            "jsonrpc": "2.0",
            "id": "lifecycle-1",
            "method": "echo",
            "params": {"text": "lifecycle test"}
        }
        websocket.send_text(json.dumps(request))
        response = websocket.receive_text()
        data = json.loads(response)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "lifecycle-1"
        assert data["result"] == {"text": "lifecycle test"}
    # If no exception, connect/disconnect lifecycle is handled
