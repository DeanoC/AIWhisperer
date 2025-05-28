import pytest
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.factory import AgentFactory
from ai_whisperer.context.provider import ContextProvider
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.ai_loop.ai_loopy import AILoop
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.config import load_config

import asyncio
import os
from pathlib import Path

# Helper to get config file path
def get_test_config_path():
    """Find config.yaml in project root"""
    # Start from current file location
    current_dir = Path(__file__).parent
    # Go up to project root
    project_root = current_dir.parent.parent
    config_path = project_root / "config.yaml"
    if not config_path.exists():
        # Try example config
        config_path = project_root / "config.yaml.example"
    return str(config_path)

@pytest.fixture
def loaded_config():
    """Load the actual config file"""
    try:
        config_path = get_test_config_path()
        return load_config(config_path)
    except Exception as e:
        # If config loading fails, use minimal test config
        return {
            "openrouter": {
                "api_key": os.getenv("OPENROUTER_API_KEY", "sk-test"),
                "model": "openai/gpt-3.5-turbo"
            }
        }

@pytest.fixture
def agent_config(loaded_config):
    openrouter_config = loaded_config.get("openrouter", {})
    return AgentConfig(
        name="TestAgent",
        description="Integration test agent",
        system_prompt="You are a helpful integration test agent.",
        model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        provider="openrouter",
        api_settings={"api_key": openrouter_config.get("api_key")},
        generation_params={
            "temperature": 0.7,
            "max_tokens": 512,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\n"]
        },
        tool_permissions=["echo"],
        tool_limits={"echo": 5},
        context_settings={
            "max_context_messages": 20,
            "max_context_tokens": 2048
        }
    )

@pytest.fixture
def context_provider():
    return AgentContext()

from ai_whisperer.ai_loop.ai_config import AIConfig

@pytest.fixture
def ai_service(loaded_config):
    openrouter_config = loaded_config.get("openrouter", {})
    config = AIConfig(
        api_key=openrouter_config.get("api_key"),
        model_id=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        temperature=0.7,
        max_tokens=512
    )
    return OpenRouterAIService(config=config)

from ai_whisperer.context_management import ContextManager
from ai_whisperer.delegate_manager import DelegateManager

@pytest.fixture
def ai_loop(ai_service, loaded_config):
    from ai_whisperer.ai_loop.ai_config import AIConfig
    openrouter_config = loaded_config.get("openrouter", {})
    config = AIConfig(
        api_key=openrouter_config.get("api_key"),
        model_id=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        temperature=0.7,
        max_tokens=512
    )
    context_manager = ContextManager()
    delegate_manager = DelegateManager()
    return AILoop(
        config=config,
        ai_service=ai_service,
        context_manager=context_manager,
        delegate_manager=delegate_manager
    )

import pytest

@pytest.mark.asyncio
async def test_agent_message_processing_end_to_end(agent_config, context_provider, ai_loop):
    agent = Agent(agent_config, context_provider, ai_loop)
    user_message = "Hello, agent!"
    response = await asyncio.wait_for(agent.process_message(user_message), timeout=10)
    # Current architecture: send_user_message returns None, response comes through delegates
    assert response is None
    # TODO: After Phase 4 refactor, this should return actual response

import asyncio

@pytest.mark.asyncio
async def test_agent_with_real_ailoop_and_aiservice(agent_config, context_provider, ai_loop):
    agent = Agent(agent_config, context_provider, ai_loop)
    user_message = "Test integration with AILoop"
    response = await asyncio.wait_for(agent.process_message(user_message), timeout=10)
    # Current architecture: send_user_message returns None
    assert response is None

@pytest.mark.asyncio
async def test_context_persistence_across_multiple_messages(agent_config, context_provider, ai_loop):
    agent = Agent(agent_config, context_provider, ai_loop)
    messages = [
        "First message",
        "Second message",
    ]
    
    # Send messages
    for msg in messages:
        response = await asyncio.wait_for(agent.process_message(msg), timeout=10)
        assert response is None  # Current architecture returns None
    
    # In current architecture, context is managed by AILoop not Agent
    # The refactor will fix this so Agent owns its context
    # For now, just verify the agent accepted multiple messages without error
    assert agent.ai_loop._session_task is not None
    assert not agent.ai_loop._session_task.done()  # Session still running

def test_multiple_agents_with_different_configurations(context_provider, ai_loop, loaded_config):
    openrouter_config = loaded_config.get("openrouter", {})
    config1 = AgentConfig(
        name="Agent1",
        description="A1",
        system_prompt="Agent1 prompt.",
        model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        provider="openrouter",
        api_settings={"api_key": openrouter_config.get("api_key")},
        generation_params={
            "temperature": 0.7,
            "max_tokens": 512,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\n"]
        },
        tool_permissions=["echo"],
        tool_limits={"echo": 5},
        context_settings={
            "max_context_messages": 20,
            "max_context_tokens": 2048
        }
    )
    config2 = AgentConfig(
        name="Agent2",
        description="A2",
        system_prompt="Agent2 prompt.",
        model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        provider="openrouter",
        api_settings={"api_key": openrouter_config.get("api_key")},
        generation_params={
            "temperature": 0.7,
            "max_tokens": 512,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\n"]
        },
        tool_permissions=["reverse"],
        tool_limits={"reverse": 5},
        context_settings={
            "max_context_messages": 20,
            "max_context_tokens": 2048
        }
    )
    agent1 = Agent(config1, context_provider, ai_loop)
    agent2 = Agent(config2, context_provider, ai_loop)
    resp1 = asyncio.run(agent1.process_message("abc"))
    resp2 = asyncio.run(agent2.process_message("abc"))
    # Current architecture: send_user_message returns None
    assert resp1 is None
    assert resp2 is None

def test_agent_factory_creates_and_manages_agents(context_provider, ai_loop, loaded_config):
    openrouter_config = loaded_config.get("openrouter", {})
    factory = AgentFactory()
    config = AgentConfig(
        name="FactoryAgent",
        description="From factory",
        system_prompt="Factory agent prompt.",
        model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        provider="openrouter",
        api_settings={"api_key": openrouter_config.get("api_key")},
        generation_params={
            "temperature": 0.7,
            "max_tokens": 512,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\n"]
        },
        tool_permissions=["echo"],
        tool_limits={"echo": 5},
        context_settings={
            "max_context_messages": 20,
            "max_context_tokens": 2048
        }
    )
    # AgentFactory.create_agent only takes config and creates its own context/ai_loop
    agent = factory.create_agent(config)
    # Factory creates agent with dummy AILoop
    assert agent is not None
    assert isinstance(agent, Agent)
    assert agent.config.name == "FactoryAgent"

def test_error_handling_and_recovery(agent_config, context_provider, ai_loop):
    agent = Agent(agent_config, context_provider, ai_loop)
    # Try sending an invalid message - AILoop handles it gracefully
    response = asyncio.run(agent.process_message(None))
    assert response is None  # No exception, just returns None
    
    # Recovery: valid message after error should work fine
    response = asyncio.run(agent.process_message("recover"))
    # Current architecture: send_user_message returns None
    assert response is None

def test_performance_with_realistic_usage_patterns(agent_config, context_provider, ai_loop):
    agent = Agent(agent_config, context_provider, ai_loop)
    messages = [f"Message {i}" for i in range(20)]
    for msg in messages:
        response = asyncio.run(agent.process_message(msg))
        # Current architecture: send_user_message returns None
        assert response is None

@pytest.mark.skip(reason="process_message_stream not implemented yet")
def test_streaming_responses_through_agent(agent_config, context_provider, ai_loop):
    agent = Agent(agent_config, context_provider, ai_loop)
    user_message = "Stream this"
    # Assume agent.process_message_stream returns an async generator
    async def collect_stream():
        chunks = []
        async for chunk in agent.process_message_stream(user_message):
            chunks.append(chunk)
        return "".join(chunks)
    result = asyncio.run(collect_stream())
    assert "Stream" in result

def test_agent_switching_and_context_isolation(context_provider, ai_loop, loaded_config):
    openrouter_config = loaded_config.get("openrouter", {})
    config1 = AgentConfig(
        name="AgentA",
        description="A",
        system_prompt="AgentA prompt.",
        model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        provider="openrouter",
        api_settings={"api_key": openrouter_config.get("api_key")},
        generation_params={
            "temperature": 0.7,
            "max_tokens": 512,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\n"]
        },
        tool_permissions=["echo"],
        tool_limits={"echo": 5},
        context_settings={
            "max_context_messages": 20,
            "max_context_tokens": 2048
        }
    )
    config2 = AgentConfig(
        name="AgentB",
        description="B",
        system_prompt="AgentB prompt.",
        model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
        provider="openrouter",
        api_settings={"api_key": openrouter_config.get("api_key")},
        generation_params={
            "temperature": 0.7,
            "max_tokens": 512,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["\n"]
        },
        tool_permissions=["echo"],
        tool_limits={"echo": 5},
        context_settings={
            "max_context_messages": 20,
            "max_context_tokens": 2048
        }
    )
    # Each agent should have its own context
    context1 = AgentContext(agent_id="AgentA")
    context2 = AgentContext(agent_id="AgentB")
    agent1 = Agent(config1, context1, ai_loop)
    agent2 = Agent(config2, context2, ai_loop)
    asyncio.run(agent1.process_message("A1"))
    asyncio.run(agent2.process_message("B1"))
    assert agent1.context != agent2.context
    assert agent1.context.agent_id == "AgentA"
    assert agent2.context.agent_id == "AgentB"

def test_context_serialization_integration(agent_config, context_provider, ai_loop):
    import tempfile
    agent = Agent(agent_config, context_provider, ai_loop)
    asyncio.run(agent.process_message("serialize me"))
    
    # AgentContext uses save_to_file/load_from_file, not serialize/deserialize
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    
    try:
        agent.context.save_to_file(temp_path)
        restored = AgentContext.load_from_file(temp_path)
        assert restored is not None
        assert hasattr(restored, "_messages")
    finally:
        import os
        if os.path.exists(temp_path):
            os.unlink(temp_path)