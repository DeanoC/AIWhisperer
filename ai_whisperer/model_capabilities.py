"""
Model capabilities configuration for AIWhisperer.
Defines which models support multi-tool calling and other advanced features.
"""

from typing import Dict, Any

# Model capability definitions
MODEL_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    # OpenAI models
    "openai/gpt-4": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False  # Original GPT-4 doesn't support structured outputs
    },
    "openai/gpt-4-turbo": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False  # GPT-4 Turbo doesn't support structured outputs
    },
    "openai/gpt-4o": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True  # GPT-4o supports structured outputs
    },
    "openai/gpt-4o-mini": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": True  # GPT-4o-mini supports structured outputs
    },
    "openai/gpt-3.5-turbo": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False  # GPT-3.5 doesn't support structured outputs
    },
    
    # Anthropic models (Claude)
    "anthropic/claude-3-opus": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False  # Claude 3 doesn't support OpenAI-style structured outputs
    },
    "anthropic/claude-3-sonnet": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-3-5-sonnet": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-3-5-sonnet-latest": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-3-haiku": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-3-5-haiku": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-3-5-haiku-latest": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-3-haiku": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-3.5-sonnet": {
        "multi_tool": False,  # Claude 3.5 Sonnet is single-tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
    },
    "anthropic/claude-sonnet-4": {
        "multi_tool": True,  # Claude 4 Sonnet supports multiple tools per turn
        "parallel_tools": True,
        "max_tools_per_turn": 10,
        "structured_output": False
    },
    "anthropic/claude-2.1": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 5,
        "structured_output": False
    },
    
    # Google models
    "google/gemini-pro": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
    },
    "google/gemini-2.0-flash-exp": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
    },
    "google/gemini-1.5-pro": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
    },
    "google/gemini-1.5-flash": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
    },
    "google/gemini-2.5-flash-preview": {
        "multi_tool": False,  # Based on observed behavior
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
    },
    
    # Meta models
    "meta-llama/llama-3-70b-instruct": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
    },
    
    # Fireworks models (support structured outputs according to docs)
    "fireworks/mixtral-8x7b-instruct": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True
    },
    "fireworks/mixtral-8x22b-instruct": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": True
    },
    
    # Default for unknown models
    "default": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1,
        "structured_output": False
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