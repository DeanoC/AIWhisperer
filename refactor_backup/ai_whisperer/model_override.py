"""
Model override utilities for testing different models without modifying config.yaml
"""

import os
from typing import Dict, Optional, Any
from pathlib import Path
import json
import yaml
from copy import deepcopy


class ModelOverride:
    """Manages model overrides for testing and development"""
    
    def __init__(self, base_config: Dict[str, Any]):
        """Initialize with base configuration"""
        self.base_config = deepcopy(base_config)
        self.original_model = base_config.get("openrouter", {}).get("model")
        
    def apply_override(self, model_name: str, additional_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Apply model override to configuration
        
        Args:
            model_name: The model to use (e.g., "openai/gpt-4o")
            additional_params: Additional parameters to override
            
        Returns:
            Modified configuration
        """
        config = deepcopy(self.base_config)
        
        # Ensure openrouter section exists
        if "openrouter" not in config:
            config["openrouter"] = {}
        
        # Override model
        config["openrouter"]["model"] = model_name
        
        # Apply model-specific defaults
        model_defaults = self._get_model_defaults(model_name)
        if model_defaults:
            # Merge params
            if "params" not in config["openrouter"]:
                config["openrouter"]["params"] = {}
            config["openrouter"]["params"].update(model_defaults.get("params", {}))
            
            # Add capabilities info
            config["model_capabilities"] = model_defaults.get("capabilities", {})
        
        # Apply additional overrides
        if additional_params:
            for key, value in additional_params.items():
                if "." in key:
                    # Handle nested keys like "openrouter.params.temperature"
                    self._set_nested_value(config, key, value)
                else:
                    config[key] = value
        
        return config
    
    def _get_model_defaults(self, model_name: str) -> Optional[Dict]:
        """Get default parameters for a specific model"""
        model_defaults = {
            # OpenAI models
            "openai/gpt-4o": {
                "params": {
                    "max_tokens": 4096,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": True,
                    "supports_structured_output": True,
                    "continuation_style": "multi_tool"
                }
            },
            "openai/gpt-4o-mini": {
                "params": {
                    "max_tokens": 16384,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": True,
                    "supports_structured_output": True,
                    "continuation_style": "multi_tool"
                }
            },
            
            # Anthropic models
            "anthropic/claude-3-5-sonnet-latest": {
                "params": {
                    "max_tokens": 8192,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": True,
                    "supports_structured_output": False,
                    "continuation_style": "multi_tool"
                }
            },
            "anthropic/claude-3-5-haiku-latest": {
                "params": {
                    "max_tokens": 8192,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": True,
                    "supports_structured_output": False,
                    "continuation_style": "multi_tool"
                }
            },
            
            # Google models
            "google/gemini-2.0-flash-exp": {
                "params": {
                    "max_tokens": 32768,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": False,
                    "supports_structured_output": False,
                    "continuation_style": "single_tool"
                }
            },
            "google/gemini-1.5-pro": {
                "params": {
                    "max_tokens": 32768,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": False,
                    "supports_structured_output": False,
                    "continuation_style": "single_tool"
                }
            },
            "google/gemini-1.5-flash": {
                "params": {
                    "max_tokens": 32768,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": False,
                    "supports_structured_output": False,
                    "continuation_style": "single_tool"
                }
            },
            
            # Meta models
            "meta-llama/llama-3.1-70b-instruct": {
                "params": {
                    "max_tokens": 8192,
                    "temperature": 0.7
                },
                "capabilities": {
                    "supports_multi_tool": True,
                    "supports_structured_output": False,
                    "continuation_style": "multi_tool"
                }
            }
        }
        
        return model_defaults.get(model_name)
    
    def _set_nested_value(self, config: Dict, key_path: str, value: Any):
        """Set a nested value in config using dot notation"""
        keys = key_path.split(".")
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    @classmethod
    def from_env(cls, base_config: Dict[str, Any]) -> Optional['ModelOverride']:
        """
        Create ModelOverride from environment variables
        
        Environment variables:
        - AIWHISPERER_MODEL: Override model name
        - AIWHISPERER_MODEL_PARAMS: JSON string of additional params
        """
        model_name = os.environ.get("AIWHISPERER_MODEL")
        if not model_name:
            return None
        
        override = cls(base_config)
        
        # Parse additional params from env
        params_json = os.environ.get("AIWHISPERER_MODEL_PARAMS")
        additional_params = {}
        if params_json:
            try:
                additional_params = json.loads(params_json)
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in AIWHISPERER_MODEL_PARAMS: {params_json}")
        
        # Apply override
        config = override.apply_override(model_name, additional_params)
        
        # Return new instance with overridden config
        return cls(config)
    
    def save_override_config(self, path: Path):
        """Save the overridden configuration to a file"""
        with open(path, 'w') as f:
            yaml.dump(self.base_config, f, default_flow_style=False)


def get_model_from_config(config: Dict[str, Any]) -> str:
    """Extract model name from configuration"""
    return config.get("openrouter", {}).get("model", "unknown")


def apply_model_override_to_session(session_manager, model_name: str):
    """Apply model override to an existing session manager"""
    # Update config
    if hasattr(session_manager, 'config'):
        override = ModelOverride(session_manager.config)
        session_manager.config = override.apply_override(model_name)
    
    # Update any existing agents
    for agent_id, agent in session_manager.agents.items():
        if hasattr(agent, 'config') and hasattr(agent.config, 'model_name'):
            agent.config.model_name = model_name