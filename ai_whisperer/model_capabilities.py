"""
Model capabilities configuration for AIWhisperer.
Defines which models support multi-tool calling and other advanced features.

Capabilities:
- multi_tool: Can call multiple tools in one response
- parallel_tools: Can execute tools in parallel
- max_tools_per_turn: Maximum number of tools that can be called at once
- structured_output: Supports JSON Schema validated responses
- quirks: Model-specific limitations or behaviors

Known Quirks:
- no_tools_with_structured_output: Model cannot use structured output when tools are enabled
  (e.g., Gemini models return "Function calling with response mime type: 'application/json' is unsupported")
- structured_output_hidden: Model supports structured output but reports it doesn't in capability tests
  (e.g., Anthropic Claude 3.5+ models support it via OpenRouter despite reporting otherwise)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Model capability definitions
MODEL_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    # OpenAI models
    "openai/gpt-4": {
        "multi_tool": False,  # Testing shows it only supports single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False,  # Original GPT-4 doesn't support structured outputs
        "quirks": {}
    },
    "openai/gpt-4-turbo": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,  # Can likely do more, but tested with 2
        "structured_output": False,  # GPT-4 Turbo doesn't support structured outputs
        "quirks": {}
    },
    "openai/gpt-4o": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # GPT-4o supports structured outputs
        "quirks": {}
    },
    "openai/gpt-4o-mini": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # GPT-4o-mini supports structured outputs
        "quirks": {}
    },
    "openai/gpt-3.5-turbo": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False,  # GPT-3.5 doesn't support structured outputs
        "quirks": {}
    },
    "openai/gpt-4.1": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": True,
        "quirks": {}
    },
    "openai/gpt-4.1-mini": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": True,
        "quirks": {}
    },
    
    # Anthropic models (Claude)
    "anthropic/claude-3-opus": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    "anthropic/claude-3-sonnet": {
        "multi_tool": False,  # Testing shows it only supports single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,  # Testing shows it does support structured output via OpenRouter
        "quirks": {}
    },
    "anthropic/claude-3-5-sonnet": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Testing shows it does support structured output via OpenRouter
        "quirks": {}
    },
    "anthropic/claude-3-5-sonnet-latest": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    "anthropic/claude-3-haiku": {
        "multi_tool": False,  # Testing shows it only supports single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False,
        "quirks": {}
    },
    "anthropic/claude-3-5-haiku": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    "anthropic/claude-3-5-haiku-latest": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    "anthropic/claude-3.5-sonnet": {
        "multi_tool": False,  # Claude 3.5 Sonnet is single-tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    "anthropic/claude-sonnet-4": {
        "multi_tool": True,  # Claude 4 Sonnet supports multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    "anthropic/claude-4-opus": {
        "multi_tool": True,  # Claude 4 Opus should support multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    "anthropic/claude-2.1": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 5,
        "structured_output": False,
        "quirks": {}
    },
    "anthropic/claude-3.7-sonnet": {
        "multi_tool": False,  # Testing shows it only supports single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,  # Supports via OpenRouter despite reporting otherwise
        "quirks": {"structured_output_hidden": True}
    },
    
    # Google models
    "google/gemini-pro": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-1.5-pro": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-1.5-flash": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-2.5-flash-preview": {
        "multi_tool": True,  # Gemini 2.5 supports multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-2.5-flash-preview-05-20:thinking": {
        "multi_tool": True,  # Gemini 2.5 supports multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-2.5-flash-preview-04-17": {
        "multi_tool": True,  # Gemini 2.5 supports multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-2.5-flash-preview-05-20": {
        "multi_tool": True,  # Gemini 2.5 supports multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-2.5-pro-preview": {
        "multi_tool": True,  # Gemini 2.5 supports multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    "google/gemini-flash-1.5": {
        "multi_tool": False,  # Testing shows no tool support
        "parallel_tools": False,
        "max_tools_per_turn": 0,
        "structured_output": True,
        "quirks": {}
    },
    "google/gemini-flash-1.5-8b": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": True,  # Supports via response_mime_type
        "quirks": {"no_tools_with_structured_output": True}
    },
    
    # Meta models
    "meta-llama/llama-3-70b-instruct": {
        "multi_tool": True,  # Testing shows it does support multiple tools
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False,
        "quirks": {}
    },
    "meta-llama/llama-3.3-70b-instruct": {
        "multi_tool": False,  # Testing shows single tool only
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,
        "quirks": {}
    },
    
    # Fireworks models (support structured outputs according to docs)
    "fireworks/mixtral-8x7b-instruct": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,
        "quirks": {}
    },
    "fireworks/mixtral-8x22b-instruct": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True,
        "quirks": {}
    },
    
    # Mistral models
    "mistralai/mistral-7b-instruct": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": False,
        "quirks": {}
    },
    "mistralai/mistral-nemo": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": True,
        "quirks": {}
    },
    "mistralai/mixtral-8x7b-instruct": {
        "multi_tool": False,  # No tool support in testing
        "parallel_tools": False,
        "max_tools_per_turn": 0,
        "structured_output": True,
        "quirks": {}
    },
    
    # DeepSeek models
    "deepseek/deepseek-chat-v3-0324": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 2,  # Tested with 2
        "structured_output": False,
        "quirks": {}
    },
    
    # Default for unknown models
    "default": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False,
        "quirks": {}
    }
}

def get_model_capabilities(model_name: str) -> Dict[str, Any]:
    """
    Get capabilities for a specific model.
    
    Args:
        model_name: The model identifier (e.g., "openai/gpt-4")
        
    Returns:
        Dictionary of model capabilities
    """
    # Try exact match first
    if model_name in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model_name]
    
    # Try prefix match (e.g., "openai/gpt-4-0613" matches "openai/gpt-4")
    for model_prefix, capabilities in MODEL_CAPABILITIES.items():
        if model_prefix != "default" and model_name.startswith(model_prefix):
            return capabilities
    
    # Log warning when using default capabilities
    logger.warning(
        f"Model '{model_name}' not found in MODEL_CAPABILITIES configuration. "
        f"Using default single-tool capabilities. Consider adding this model to the configuration."
    )
    
    # Return default capabilities
    return MODEL_CAPABILITIES["default"]

def supports_multi_tool(model_name: str) -> bool:
    """
    Check if a model supports multiple tool calls in one turn.
    
    Args:
        model_name: The model identifier
        
    Returns:
        True if model supports multi-tool calling
    """
    capabilities = get_model_capabilities(model_name)
    return capabilities.get("multi_tool", False)

def supports_structured_output(model_name: str) -> bool:
    """
    Check if a model supports structured output with JSON Schema validation.
    
    Args:
        model_name: The model identifier
        
    Returns:
        True if model supports structured output
    """
    capabilities = get_model_capabilities(model_name)
    return capabilities.get("structured_output", False)

def has_quirk(model_name: str, quirk_name: str) -> bool:
    """
    Check if a model has a specific quirk.
    
    Args:
        model_name: The model identifier
        quirk_name: The quirk to check for
        
    Returns:
        True if model has the specified quirk
    """
    capabilities = get_model_capabilities(model_name)
    quirks = capabilities.get("quirks", {})
    return quirks.get(quirk_name, False)