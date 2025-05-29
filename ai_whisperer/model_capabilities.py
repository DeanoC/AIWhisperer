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
        "max_tools_per_turn": 10
    },
    "openai/gpt-4-turbo": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10
    },
    "openai/gpt-3.5-turbo": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10
    },
    
    # Anthropic models (Claude)
    "anthropic/claude-3-opus": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10
    },
    "anthropic/claude-3-sonnet": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10
    },
    "anthropic/claude-3-haiku": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 10
    },
    "anthropic/claude-2.1": {
        "multi_tool": True,
        "parallel_tools": True,
        "max_tools_per_turn": 5
    },
    
    # Google models
    "google/gemini-pro": {
        "multi_tool": False,  # Single tool per turn
        "parallel_tools": False,
        "max_tools_per_turn": 1
    },
    "google/gemini-2.5-flash-preview": {
        "multi_tool": False,  # Based on observed behavior
        "parallel_tools": False,
        "max_tools_per_turn": 1
    },
    
    # Meta models
    "meta-llama/llama-3-70b-instruct": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1
    },
    
    # Default for unknown models
    "default": {
        "multi_tool": False,
        "parallel_tools": False,
        "max_tools_per_turn": 1
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