import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from interactive_server.session_manager import InteractiveSession
from ai_whisperer.agents.factory import AgentFactory
from ai_whisperer.agents.agent import Agent

@pytest.fixture
def session_id():
    return "test-session"

@pytest.fixture
def websocket():
    return MagicMock()

@pytest.fixture
def config():
    return {"agent": {"preset_name": "default"}}

@pytest.fixture
def agent_mock():
    agent = AsyncMock(spec=Agent)
    agent.process_message = AsyncMock(return_value="mocked-response")
    return agent

@pytest.fixture
def agent_factory_mock(agent_mock):
    with patch("ai_whisperer.agents.factory.AgentFactory.create_agent", return_value=agent_mock):
        yield AgentFactory

@pytest.mark.asyncio
async def test_session_creates_agent_on_start(agent_factory_mock, session_id, websocket, config):
    session = InteractiveSession(session_id, websocket, config)
    await session.start_ai_session()
    assert hasattr(session, "agents")
    assert len(session.agents) == 1
    assert session.active_agent is not None

@pytest.mark.asyncio
async def test_session_routes_message_to_active_agent(agent_factory_mock, session_id, websocket, config, agent_mock):
    session = InteractiveSession(session_id, websocket, config)
    await session.start_ai_session()
    response = await session.send_user_message("hello")
    agent_mock.process_message.assert_awaited_with("hello")
    assert response == "mocked-response"

@pytest.mark.asyncio
async def test_session_lifecycle_cleanup(agent_factory_mock, session_id, websocket, config):
    session = InteractiveSession(session_id, websocket, config)
    await session.start_ai_session()
    await session.cleanup()
    assert session.agents == {}
    assert session.active_agent is None

@pytest.mark.asyncio
async def test_agent_switching(agent_factory_mock, session_id, websocket, config, agent_mock):
    session = InteractiveSession(session_id, websocket, config)
    await session.start_ai_session()
    # Add a second agent
    agent2 = AsyncMock(spec=Agent)
    agent2.process_message = AsyncMock(return_value="response2")
    session.agents["agent2"] = agent2
    session.active_agent = agent2
    response = await session.send_user_message("switch-test")
    agent2.process_message.assert_awaited_with("switch-test")
    assert response == "response2"

@pytest.mark.asyncio
async def test_switch_agent_method(agent_factory_mock, session_id, websocket, config, agent_mock):
    session = InteractiveSession(session_id, websocket, config)
    await session.start_ai_session()
    agent2 = AsyncMock(spec=Agent)
    session.agents["agent2"] = agent2
    session.switch_agent("agent2")
    assert session.active_agent == agent2

@pytest.mark.asyncio
async def test_switch_agent_invalid(agent_factory_mock, session_id, websocket, config):
    session = InteractiveSession(session_id, websocket, config)
    await session.start_ai_session()
    with pytest.raises(ValueError):
        session.switch_agent("nonexistent")

@pytest.mark.asyncio
async def test_error_handling_on_agent_message(agent_factory_mock, session_id, websocket, config, agent_mock, caplog):
    agent_mock.process_message.side_effect = Exception("fail")
    session = InteractiveSession(session_id, websocket, config)
    await session.start_ai_session()
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            await session.send_user_message("should fail")
    assert any(
        "Failed to send message to agent in session test-session: fail" in record.getMessage()
        for record in caplog.records
    )