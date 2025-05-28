import pytest
from unittest.mock import MagicMock, patch
from interactive_server import main as jsonrpc_server
from interactive_server.session_manager import InteractiveSessionManager
from interactive_server.message_models import (
    SendUserMessageRequest, SendUserMessageResponse, StartSessionRequest, StartSessionResponse
)
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig

@pytest.fixture
def session_manager():
    # Provide minimal valid agent config for tests
    config = {
        "agent": {
            "name": "test-agent",
            "description": "Test agent",
            "system_prompt": "You are a test agent.",
            "model_name": "test-model",
            "provider": "test-provider",
            "api_settings": {},
            "generation_params": {},
            "tool_permissions": [],
            "tool_limits": {},
            "context_settings": {},
        }
    }
    # Create a new instance for each test to ensure complete isolation
    manager = InteractiveSessionManager(config=config)
    # Patch the module-level session_manager in interactive_server.main
    with patch('interactive_server.main.session_manager', new=manager):
        yield manager

@pytest.fixture
def agent_config():
    return AgentConfig(name="test-agent", description="A test agent", tools=[])

@pytest.fixture
def agent(agent_config):
    return Agent(agent_config)

@pytest.fixture
async def session(session_manager):
    from unittest.mock import AsyncMock
    websocket = AsyncMock(name="TestWebSocket")
    session_id = await session_manager.create_session(websocket)
    await session_manager.start_session(session_id)
    session = session_manager.get_session(session_id)
    return (session, websocket)

@pytest.mark.asyncio
async def test_route_message_to_correct_session_and_agent(session_manager, session):
    session_obj, websocket = await session
    msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendUserMessage",
        "params": {"sessionId": session_obj.session_id, "message": "hello"}
    }
    response = await jsonrpc_server.process_json_rpc_request(msg, websocket)
    assert response["id"] == 1
    assert "result" in response
    assert response["result"]["status"] is not None

@pytest.mark.asyncio
async def test_agent_selection_and_switching(session_manager, session):
    session_obj, websocket = await session
    agent_config = {
        "name": "test-agent",
        "description": "desc",
        "system_prompt": "Prompt",
        "model_name": "test-model",
        "provider": "test-provider",
        "api_settings": {},
        "generation_params": {},
        "tool_permissions": [],
        "tool_limits": {},
        "context_settings": {},
    }
    from ai_whisperer.agents.factory import AgentFactory
    session_obj.agents["test-agent"] = AgentFactory.create_agent(agent_config)
    msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "session.switch_agent",
        "params": {"agent_id": "test-agent"}
    }
    response = await jsonrpc_server.process_json_rpc_request(msg, websocket)
    assert response["id"] == 2
    assert "result" in response
    assert response["result"]["success"] is True
    assert response["result"]["current_agent"] == "test-agent"
    assert session_obj.active_agent is session_obj.agents["test-agent"]

@pytest.mark.asyncio
async def test_error_on_invalid_session_id(session_manager):
    msg = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "sendUserMessage",
        "params": {"sessionId": "invalid", "message": "hi"}
    }
    from unittest.mock import AsyncMock
    websocket = AsyncMock(name="InvalidWebSocket")
    response = await jsonrpc_server.process_json_rpc_request(msg, websocket)
    assert response["id"] == 3
    assert "error" in response
    assert response["error"]["code"] == -32602
    assert "Invalid session" in response["error"]["message"]

@pytest.mark.asyncio
async def test_error_on_invalid_agent_switch(session_manager, session):
    session_obj, websocket = await session
    msg = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "session.switch_agent",
        "params": {"agent_id": "nonexistent"}
    }
    response = await jsonrpc_server.process_json_rpc_request(msg, websocket)
    assert response["id"] == 4
    assert "error" in response
    assert response["error"]["code"] == -32001 # Custom error code for agent not found
    assert "Agent not found" in response["error"]["message"]

@pytest.mark.asyncio
async def test_api_compatibility_response_format(session_manager, session):
    session_obj, websocket = await session
    msg = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "sendUserMessage",
        "params": {"sessionId": session_obj.session_id, "message": "compat"}
    }
    response = await jsonrpc_server.process_json_rpc_request(msg, websocket)
    assert response["id"] == 5
    assert "result" in response
    assert "status" in response["result"]

@pytest.mark.asyncio
async def test_validation_and_error_messages(session_manager, session):
    session_obj, websocket = await session
    # Missing required param
    msg = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "sendUserMessage",
        "params": {"sessionId": session_obj.session_id}
    }
    response = await jsonrpc_server.process_json_rpc_request(msg, websocket)
    assert response["id"] == 6
    assert "error" in response
    assert response["error"]["code"] == -32602
    assert "Missing required parameter" in response["error"]["message"]

    # Malformed request (missing params)
    bad_msg = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "sendUserMessage"
    }
    response = await jsonrpc_server.process_json_rpc_request(bad_msg, websocket)
    assert response["id"] == 7
    assert "error" in response

# Streaming test would require a streaming handler and async generator, which is not present in the current codebase.
# If/when implemented, add a test for streaming functionality here.