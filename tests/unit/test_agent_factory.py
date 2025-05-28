import pytest

from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext

from ai_whisperer.agents.factory import AgentFactory

class DummyModel:
    def __init__(self, name):
        self.name = name

@pytest.fixture
def basic_config():
    return AgentConfig(
        name="test_agent",
        description="A test agent",
        model_name="gpt-3.5-turbo",
        provider="openai",
        system_prompt="You are a helpful assistant.",
        generation_params={"temperature": 0.7},
        api_settings={},
    )

@pytest.fixture
def config_dict():
    return {
        "name": "dict_agent",
        "model_name": "gpt-4",
        "provider": "openai",
        "system_prompt": "You are a coding assistant.",
        "generation_params": {"temperature": 0.2},
        "api_settings": {},
    }

def test_create_agent_from_config(basic_config):
    agent = AgentFactory.create_agent(basic_config)
    assert isinstance(agent, Agent)
    assert agent.config.name == "test_agent"
    assert agent.config.model_name == "gpt-3.5-turbo"
    assert agent.config.provider == "openai"
    assert agent.config.system_prompt == "You are a helpful assistant."
    assert agent.config.generation_params["temperature"] == 0.7

def test_create_agent_from_dict(config_dict):
    agent = AgentFactory.create_agent(config_dict)
    assert isinstance(agent, Agent)
    assert agent.config.name == "dict_agent"
    assert agent.config.model_name == "gpt-4"
    assert agent.config.provider == "openai"
    assert agent.config.system_prompt == "You are a coding assistant."
    assert agent.config.generation_params["temperature"] == 0.2

def test_create_agent_with_different_models():
    configs = [
        AgentConfig(
            name="openai_agent",
            description="desc",
            model_name="gpt-4",
            provider="openai",
            system_prompt="A",
            api_settings={},
            generation_params={}
        ),
        AgentConfig(
            name="anthropic_agent",
            description="desc",
            model_name="claude-3",
            provider="anthropic",
            system_prompt="B",
            api_settings={},
            generation_params={}
        ),
        AgentConfig(
            name="dummy_agent",
            description="desc",
            model_name="dummy",
            provider="custom",
            system_prompt="C",
            api_settings={},
            generation_params={}
        ),
    ]
    for cfg in configs:
        agent = AgentFactory.create_agent(cfg)
        assert isinstance(agent, Agent)
        assert agent.config.model_name == cfg.model_name
        assert agent.config.provider == cfg.provider

def test_agent_validation_missing_required_fields():
    # Missing name
    invalid_cfg = {
        "model": "gpt-4",
        "provider": "openai",
        "prompt": "Missing name"
    }
    with pytest.raises(ValueError) as exc:
        AgentFactory.create_agent(invalid_cfg)
    assert "name" in str(exc.value)

    # Missing model
    invalid_cfg2 = {
        "name": "no_model",
        "provider": "openai",
        "system_prompt": "Missing model"
    }
    with pytest.raises(ValueError) as exc:
        AgentFactory.create_agent(invalid_cfg2)
    assert "model_name" in str(exc.value)

def test_agent_validation_invalid_model():
    from ai_whisperer.agents.config import AgentConfigError
    invalid_cfg = {
        "name": "bad_model",
        "model_name": None,
        "provider": "openai",
        "system_prompt": "Invalid model"
    }
    with pytest.raises(AgentConfigError) as exc:
        AgentFactory.create_agent(invalid_cfg)
    assert "model_name" in str(exc.value)

def test_error_on_invalid_config_type():
    with pytest.raises(TypeError):
        AgentFactory.create_agent(12345)  # Not a dict or AgentConfig

def test_register_and_create_from_template():
    template = AgentConfig(
        name="template_agent",
        description="A template agent",
        model_name="gpt-4",
        provider="openai",
        system_prompt="Template prompt.",
        api_settings={},
        generation_params={"temperature": 0.1}
    )
    AgentFactory.register_template("default", template)
    agent = AgentFactory.create_agent_from_template("default", name="templated_agent", description="templated", model_name="gpt-4", system_prompt="Template prompt.", api_settings={}, generation_params={"temperature": 0.1})
    assert isinstance(agent, Agent)
    assert agent.config.name == "templated_agent"
    assert agent.config.model_name == "gpt-4"
    assert agent.config.system_prompt == "Template prompt."
    assert agent.config.generation_params["temperature"] == 0.1

def test_error_on_unknown_template():
    with pytest.raises(KeyError):
        AgentFactory.create_agent_from_template("nonexistent")

def test_create_agent_with_custom_params():
    cfg = {
        "name": "custom_agent",
        "description": "custom agent",
        "model_name": "gpt-4",
        "provider": "openai",
        "system_prompt": "Custom params.",
        "api_settings": {},
        "generation_params": {"temperature": 0.9, "max_tokens": 512}
    }
    agent = AgentFactory.create_agent(cfg)
    assert agent.config.generation_params["temperature"] == 0.9
    assert agent.config.generation_params["max_tokens"] == 512

def test_agent_factory_supports_presets():
    preset = {
        "model_name": "gpt-3.5-turbo",
        "description": "preset agent",
        "provider": "openai",
        "system_prompt": "Preset prompt.",
        "api_settings": {},
        "generation_params": {"temperature": 0.3}
    }
    AgentFactory.register_preset("quick", preset)
    agent = AgentFactory.create_agent_from_preset("quick", name="preset_agent", description="preset agent", model_name="gpt-3.5-turbo", system_prompt="Preset prompt.", api_settings={}, generation_params={"temperature": 0.3})
    assert agent.config.name == "preset_agent"
    assert agent.config.model_name == "gpt-3.5-turbo"
    assert agent.config.system_prompt == "Preset prompt."
    assert agent.config.generation_params["temperature"] == 0.3