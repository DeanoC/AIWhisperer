import asyncio
import pytest
from unittest.mock import MagicMock, patch

from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext

from ai_whisperer.ai_loop.ai_loopy import AILoop
from ai_whisperer.ai_loop.ai_config import AIConfig

class DummyAIResponseChunk:
    def __init__(self, delta_content=None, finish_reason="stop"):
        self.delta_content = delta_content
        self.finish_reason = finish_reason
        self.delta_tool_call_part = None

async def dummy_stream_chat_completion(messages=None, **kwargs):
    # Simulate a streaming AI response based on the last user message in messages
    user_message = None
    if messages:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break
    if user_message is None:
        user_message = "<no user message>"
    yield DummyAIResponseChunk(delta_content="Processed: " + user_message, finish_reason="stop")

def make_real_ai_loop():
    # Use MagicMock for AIService, ContextManager, DelegateManager
    ai_service = MagicMock()
    ai_service.stream_chat_completion = dummy_stream_chat_completion

    context_manager = MagicMock()
    context_manager.clear_history = MagicMock()
    context_manager.add_message = MagicMock()
    context_manager.get_history = MagicMock(return_value=[
        {"role": "system", "content": "You are a helpful assistant."},
    ])

    from unittest.mock import AsyncMock
    delegate_manager = MagicMock()
    delegate_manager.invoke_notification = AsyncMock()

    config = AIConfig(
        "test",  # api_key
        "gpt-4", # model_id
        model_name="gpt-4",
        provider="openai",
        api_settings={"api_key": "test"},
        generation_params={"temperature": 0.7, "max_tokens": 128},
        tool_permissions=["tool1", "tool2"],
        tool_limits={"tool1": 5},
        context_settings={"max_context_messages": 10}
    )

    return AILoop(
        config=config,
        ai_service=ai_service,
        context_manager=context_manager,
        delegate_manager=delegate_manager,
        get_agent_id=lambda: "test_user"
    )

def make_config():
    return AgentConfig(
        name="TestAgent",
        description="A test agent",
        system_prompt="You are a helpful assistant.",
        model_name="gpt-4",
        provider="openai",
        api_settings={"api_key": "test"},
        generation_params={"temperature": 0.7, "max_tokens": 128},
        tool_permissions=["tool1", "tool2"],
        tool_limits={"tool1": 5},
        context_settings={"max_context_messages": 10}
    )

def make_context():
    return AgentContext(agent_id="test_user", system_prompt="You are a helpful assistant.")

def make_agent(ai_loop=None):
    config = make_config()
    context = make_context()
    return Agent(config=config, context=context, ai_loop=ai_loop or make_real_ai_loop())

def test_agent_initialization_owns_context_and_config():
    config = make_config()
    context = make_context()
    agent = Agent(config=config, context=context, ai_loop=make_real_ai_loop())
    assert agent.config is config
    assert agent.context is context
    assert isinstance(agent.context, AgentContext)
    assert isinstance(agent.config, AgentConfig)

import pytest

@pytest.mark.asyncio
async def test_agent_process_message_returns_response():
    agent = make_agent()
    response = await asyncio.wait_for(agent.process_message("Hello, agent!"), timeout=5)
    assert response is None  # Real AILoop.send_user_message returns None
    # Ensure context_manager.add_message was called with the user message
    user_message = {"role": "user", "content": "Hello, agent!"}
    agent.ai_loop.context_manager.add_message.assert_any_call(user_message, agent_id="test_user")
    await agent.ai_loop.stop_session()

@pytest.mark.asyncio
async def test_agent_context_integration_and_ownership():
    agent = make_agent()
    # Simulate context update
    agent.context.session_id = "sess2"
    response = await asyncio.wait_for(agent.process_message("Test context update"), timeout=5)
    assert agent.context.session_id == "sess2"
    # Ensure context_manager.add_message was called with the updated session context
    user_message = {"role": "user", "content": "Test context update"}
    agent.ai_loop.context_manager.add_message.assert_any_call(user_message, agent_id="test_user")
    await agent.ai_loop.stop_session()

@pytest.mark.asyncio
async def test_agent_configuration_usage():
    agent = make_agent()
    agent.config.temperature = 0.9
    response = await asyncio.wait_for(agent.process_message("Test config usage"), timeout=5)
    # Ensure context_manager.add_message was called with the user message
    user_message = {"role": "user", "content": "Test config usage"}
    agent.ai_loop.context_manager.add_message.assert_any_call(user_message, agent_id="test_user")
    await agent.ai_loop.stop_session()

@pytest.mark.asyncio
async def test_agent_integration_with_ailoop_and_delegates():
    # Test delegate_manager notification integration
    real_loop = make_real_ai_loop()
    agent = make_agent(ai_loop=real_loop)
    response = await asyncio.wait_for(agent.process_message("Delegate test"), timeout=5)
    # Ensure delegate_manager.invoke_notification was called for session start and user_processed
    agent.ai_loop.delegate_manager.invoke_notification.assert_any_call(
        sender=agent.ai_loop, event_type="ai_loop.session_started"
    )
    agent.ai_loop.delegate_manager.invoke_notification.assert_any_call(
        sender=agent.ai_loop, event_type="ai_loop.message.user_processed", event_data="Delegate test"
    )
    await agent.ai_loop.stop_session()

def test_agent_invalid_config_raises():
    with pytest.raises(ValueError):
        Agent(config=None, context=make_context(), ai_loop=make_real_ai_loop())
    with pytest.raises(ValueError):
        Agent(config=make_config(), context=None, ai_loop=make_real_ai_loop())
    with pytest.raises(ValueError):
        Agent(config=make_config(), context=make_context(), ai_loop=None)

@pytest.mark.asyncio
async def test_agent_process_message_handles_errors():
    # Simulate real error from AIService
    class FailingAIService:
        async def stream_chat_completion(self, *args, **kwargs):
            raise RuntimeError("AILoop failure")

    def make_failing_ai_loop():
        context_manager = MagicMock()
        context_manager.clear_history = MagicMock()
        context_manager.add_message = MagicMock()
        context_manager.get_history = MagicMock(return_value=[
            {"role": "system", "content": "You are a helpful assistant."},
        ])
        from unittest.mock import AsyncMock
        delegate_manager = MagicMock()
        delegate_manager.invoke_notification = AsyncMock()
        config = AIConfig(
            "test",  # api_key
            "gpt-4", # model_id
            model_name="gpt-4",
            provider="openai",
            api_settings={"api_key": "test"},
            generation_params={"temperature": 0.7, "max_tokens": 128},
            tool_permissions=["tool1", "tool2"],
            tool_limits={"tool1": 5},
            context_settings={"max_context_messages": 10}
        )
        return AILoop(
            config=config,
            ai_service=FailingAIService(),
            context_manager=context_manager,
            delegate_manager=delegate_manager,
            get_agent_id=lambda: "test_user"
        )

    agent = make_agent(ai_loop=make_failing_ai_loop())
    await asyncio.wait_for(agent.process_message("This will fail"), timeout=5)
    # Check that an error message was added to the context manager
    assert agent.ai_loop.context_manager.add_message.call_args_list[-1][0][0]["role"] == "assistant"
    assert "error" in agent.ai_loop.context_manager.add_message.call_args_list[-1][0][0]["content"].lower()
    await agent.ai_loop.stop_session()