"""
Module: ai_whisperer/tools/tool_registration_lazy.py
Purpose: Lazy registration support for tool registry

This module provides a modified registration approach that supports
lazy loading. Tools are only imported when actually needed.
"""

import logging
from typing import Optional

from .tool_registry import get_tool_registry
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)


def register_all_tools(path_manager: Optional[PathManager] = None) -> None:
    """
    Initialize the tool registry for lazy loading.
    
    With lazy loading, tools are not imported at startup.
    Instead, they are loaded on-demand when first accessed.
    
    Args:
        path_manager: Optional PathManager instance for tools that need it
    """
    tool_registry = get_tool_registry()
    
    # If no path_manager provided, create one
    if path_manager is None:
        path_manager = PathManager()
    
    # Set path manager for tools that need it
    tool_registry.set_path_manager(path_manager)
    
    # Only preload essential tools for better startup performance
    tool_registry.preload_essential_tools()
    
    logger.info(f"Tool registry initialized with {tool_registry.get_available_tool_count()} available tools, "
                f"{tool_registry.get_loaded_tool_count()} preloaded")


def register_tool_category(category: str, path_manager: Optional[PathManager] = None) -> None:
    """
    Force loading of tools from a specific category.
    
    This is useful when you know you'll need all tools from a category
    and want to load them upfront instead of on-demand.
    
    Args:
        category: Category name (e.g., 'file_ops', 'rfc', 'debugging')
        path_manager: Optional PathManager instance
    """
    tool_registry = get_tool_registry()
    
    if path_manager is None:
        path_manager = PathManager()
    
    # Map old category names to new ones for backward compatibility
    category_map = {
        'file': 'file_ops',
        'analysis': 'analysis',
        'rfc': 'rfc',
        'plan': 'plan',
        'codebase': 'codebase',
        'web': 'web',
        'debugging': 'debugging',
        'mailbox': 'mailbox',
        'agent_e': 'agent_e',
    }
    
    new_category = category_map.get(category, category)
    
    # Get all tool specs for this category
    loaded_count = 0
    for name, spec in tool_registry._tool_specs.items():
        if spec.get('category') == new_category:
            if tool_registry.get_tool(name):  # This triggers lazy loading
                loaded_count += 1
    
    logger.info(f"Loaded {loaded_count} tools from category '{category}'")