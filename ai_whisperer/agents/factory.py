from typing import Any, Dict, Optional, Type, Union
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext

class AgentFactory:
    _templates: Dict[str, AgentConfig] = {}
    _presets: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_agent(cls, config: Union[AgentConfig, Dict[str, Any]]) -> Agent:
        if isinstance(config, AgentConfig):
            agent_config = config
        elif isinstance(config, dict):
            agent_config = cls._dict_to_config(config)
        else:
            raise TypeError("AgentFactory.create_agent: config must be AgentConfig or dict")

        cls._validate_config(agent_config)
        # Provide minimal AgentContext and ai_loop mocks for compatibility
        from ai_whisperer.context.agent_context import AgentContext
        class DummyAILoop:
            async def start_session(self, prompt): pass
            async def send_user_message(self, message): return {}
            _session_task = None
        context = AgentContext(agent_config)
        ai_loop = DummyAILoop()
        return Agent(agent_config, context, ai_loop)

    @classmethod
    def _dict_to_config(cls, config_dict: Dict[str, Any]) -> AgentConfig:
        try:
            return AgentConfig(
                name=config_dict["name"],
                description=config_dict.get("description", ""),
                system_prompt=config_dict["system_prompt"],
                model_name=config_dict["model_name"],
                provider=config_dict["provider"],
                api_settings=config_dict.get("api_settings", {}),
                generation_params=config_dict.get("generation_params", {}),
                tool_permissions=config_dict.get("tool_permissions"),
                tool_limits=config_dict.get("tool_limits"),
                context_settings=config_dict.get("context_settings"),
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e.args[0]}")

    @classmethod
    def _validate_config(cls, config: AgentConfig):
        if not config.name or not isinstance(config.name, str):
            raise ValueError("AgentConfig must have a non-empty string 'name'")
        if not config.model_name or not isinstance(config.model_name, str):
            raise ValueError("AgentConfig must have a non-empty string 'model_name'")
        if not config.provider or not isinstance(config.provider, str):
            raise ValueError("AgentConfig must have a non-empty string 'provider'")
        if not config.system_prompt or not isinstance(config.system_prompt, str):
            raise ValueError("AgentConfig must have a non-empty string 'system_prompt'")
        # Legacy check removed: params is no longer a valid AgentConfig attribute
        if config.generation_params is not None and not isinstance(config.generation_params, dict):
            raise ValueError("AgentConfig 'generation_params' must be a dict if provided")

    @classmethod
    def register_template(cls, name: str, config: AgentConfig):
        cls._templates[name] = config

    @classmethod
    def create_agent_from_template(cls, template_name: str, **overrides) -> Agent:
        if template_name not in cls._templates:
            raise KeyError(f"Template '{template_name}' not found")
        base = cls._templates[template_name]
        config_dict = {
            "name": overrides.get("name", base.name),
            "description": overrides.get("description", base.description),
            "model_name": overrides.get("model_name", base.model_name),
            "provider": overrides.get("provider", base.provider),
            "system_prompt": overrides.get("system_prompt", base.system_prompt),
            "api_settings": overrides.get("api_settings", dict(base.api_settings) if base.api_settings else {}),
            "generation_params": overrides.get("generation_params", dict(base.generation_params) if base.generation_params else {}),
            "tool_permissions": overrides.get("tool_permissions", base.tool_permissions),
            "tool_limits": overrides.get("tool_limits", base.tool_limits),
            "context_settings": overrides.get("context_settings", base.context_settings),
        }
        return cls.create_agent(config_dict)

    @classmethod
    def register_preset(cls, name: str, preset: Dict[str, Any]):
        cls._presets[name] = preset

    @classmethod
    def create_agent_from_preset(cls, preset_name: str, name: Optional[str] = None, **overrides) -> Agent:
        if preset_name not in cls._presets:
            raise KeyError(f"Preset '{preset_name}' not found")
        base = dict(cls._presets[preset_name])
        if name:
            base["name"] = name
        base.update(overrides)
        return cls.create_agent(base)