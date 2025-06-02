import pytest
from unittest.mock import MagicMock

# Assume you have a JSON-RPC test client for your websocket server
# For illustration, we'll use a mock client interface
@pytest.fixture
def jsonrpc_client():
    # Replace with your actual test client setup
    client = MagicMock()
    return client

def test_agent_list(jsonrpc_client):
    # Simulate calling agent.list
    jsonrpc_client.call_method.return_value = {
        "agents": [
            {"agent_id": "P", "name": "Patricia the Planner"},
            {"agent_id": "T", "name": "Tessa the Tester"}
        ]
    }
    result = jsonrpc_client.call_method("agent.list", {})
    assert "agents" in result
    assert any(a["agent_id"] == "P" for a in result["agents"])
    assert any(a["agent_id"] == "T" for a in result["agents"])

def test_session_switch_agent(jsonrpc_client):
    jsonrpc_client.call_method.return_value = {"success": True, "current_agent": "T"}
    result = jsonrpc_client.call_method("session.switch_agent", {"agent_id": "T"})
    assert result["success"]
    assert result["current_agent"] == "T"

def test_session_current_agent(jsonrpc_client):
    jsonrpc_client.call_method.return_value = {"current_agent": "P"}
    result = jsonrpc_client.call_method("session.current_agent", {})
    assert result["current_agent"] == "P"

def test_session_handoff(jsonrpc_client):
    jsonrpc_client.call_method.return_value = {"success": True, "from_agent": "P", "to_agent": "T"}
    result = jsonrpc_client.call_method("session.handoff", {"to_agent": "T"})
    assert result["success"]
    assert result["from_agent"] == "P"
    assert result["to_agent"] == "T"
