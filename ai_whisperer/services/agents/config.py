from typing import Any, Dict, List, Optional
"""
Module: ai_whisperer/agents/config.py
Purpose: AI agent implementation for specialized task handling

This module implements an AI agent that processes user messages
and executes specialized tasks. It integrates with the tool system
and manages conversation context.

Key Components:
- AgentConfigError: Raised when agent configuration is invalid.
- AgentConfig: Class implementation

Usage:
    agentconfigerror = AgentConfigError()

Related:
- See docs/directory_restriction_strategy.md
- See docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
- See docs/archive/legacy/analysis/path_manager_analysis.md

"""

class AgentConfigError(Exception):
    """Raised when agent configuration is invalid."""

class AgentConfig:
    REQUIRED_FIELDS = [
        "name", "description", "system_prompt",
        "model_name", "provider", "api_settings", "generation_params"
    ]
    GENERATION_PARAM_RANGES = {
        "temperature": (0.0, 1.5),
        "max_tokens": (1, 32768),
        "top_p": (0.0, 1.0),
        "frequency_penalty": (-2.0, 2.0),
        "presence_penalty": (-2.0, 2.0),
    }

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        model_name: str,
        provider: str,
        api_settings: Dict[str, Any],
        generation_params: Dict[str, Any],
        tool_permissions: Optional[List[str]] = None,
        tool_limits: Optional[Dict[str, int]] = None,
        context_settings: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.provider = provider
        self.api_settings = api_settings
        self.generation_params = generation_params
        self.tool_permissions = tool_permissions or []
        self.tool_limits = tool_limits or {}
        self.context_settings = context_settings or {}

        self._validate()

    def _validate(self):
        # Required fields
        for field in self.REQUIRED_FIELDS:
            if getattr(self, field, None) is None:
                raise AgentConfigError(f"Missing required field: {field}")

        # Types
        if not isinstance(self.name, str):
            raise AgentConfigError("name must be a string")
        if not isinstance(self.description, str):
            raise AgentConfigError("description must be a string")
        if not isinstance(self.system_prompt, str):
            raise AgentConfigError("system_prompt must be a string")
        if not isinstance(self.model_name, str):
            raise AgentConfigError("model_name must be a string")
        if not isinstance(self.provider, str):
            raise AgentConfigError("provider must be a string")
        if not isinstance(self.api_settings, dict):
            raise AgentConfigError("api_settings must be a dict")
        if not isinstance(self.generation_params, dict):
            raise AgentConfigError("generation_params must be a dict")
        if not isinstance(self.tool_permissions, list):
            raise AgentConfigError("tool_permissions must be a list")
        if not isinstance(self.tool_limits, dict):
            raise AgentConfigError("tool_limits must be a dict")
        if not isinstance(self.context_settings, dict):
            raise AgentConfigError("context_settings must be a dict")

        # Generation parameter validation
        for param, (min_val, max_val) in self.GENERATION_PARAM_RANGES.items():
            if param in self.generation_params:
                value = self.generation_params[param]
                if not isinstance(value, (int, float)):
                    raise AgentConfigError(f"{param} must be a number")
                if not (min_val <= value <= max_val):
                    raise AgentConfigError(
                        f"{param} must be between {min_val} and {max_val}"
                    )
        # max_tokens must be int
        if "max_tokens" in self.generation_params:
            if not isinstance(self.generation_params["max_tokens"], int):
                raise AgentConfigError("max_tokens must be an integer")
            if self.generation_params["max_tokens"] < 1:
                raise AgentConfigError("max_tokens must be >= 1")

        # tool_permissions must be list of str
        if self.tool_permissions:
            if not all(isinstance(t, str) for t in self.tool_permissions):
                raise AgentConfigError("tool_permissions must be a list of strings")
        # tool_limits must be dict of str:int
        if self.tool_limits:
            for k, v in self.tool_limits.items():
                if not isinstance(k, str) or not isinstance(v, int):
                    raise AgentConfigError("tool_limits must be dict of str:int")

        # context_settings
        if self.context_settings:
            if "max_context_messages" in self.context_settings:
                v = self.context_settings["max_context_messages"]
                if not isinstance(v, int) or v < 1:
                    raise AgentConfigError("max_context_messages must be int >= 1")
            if "max_context_tokens" in self.context_settings:
                v = self.context_settings["max_context_tokens"]
                if not isinstance(v, int) or v < 1:
                    raise AgentConfigError("max_context_tokens must be int >= 1")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "model_name": self.model_name,
            "provider": self.provider,
            "api_settings": self.api_settings,
            "generation_params": self.generation_params,
            "tool_permissions": self.tool_permissions,
            "tool_limits": self.tool_limits,
            "context_settings": self.context_settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        try:
            return cls(
                name=data["name"],
                description=data["description"],
                system_prompt=data["system_prompt"],
                model_name=data["model_name"],
                provider=data["provider"],
                api_settings=data["api_settings"],
                generation_params=data["generation_params"],
                tool_permissions=data.get("tool_permissions"),
                tool_limits=data.get("tool_limits"),
                context_settings=data.get("context_settings"),
            )
        except Exception as e:
            raise AgentConfigError(f"Invalid config: {e}")
