"""
Optimized tool registration that supports lazy loading.
"""

import logging
logger = logging.getLogger(__name__)

def register_all_tools(tool_registry, lazy: bool = True) -> None:
    """
    Register all tools with the registry.
    
    With lazy loading enabled, this just ensures the registry knows about
    all tools without actually loading them.
    
    Args:
        tool_registry: The tool registry instance
        lazy: If True, tools are registered for lazy loading
    """
    if lazy:
        # With lazy loading, the registry already knows about tools from specs
        logger.info("Tool registry initialized with lazy loading enabled")
        return
    
    # If not lazy, we need to explicitly load all tools
    # This is handled by the registry itself when lazy_loading=False
    logger.info("Loading all tools (lazy loading disabled)")
    
def register_category(tool_registry, category: str, lazy: bool = True) -> None:
    """
    Register all tools in a specific category.
    
    Args:
        tool_registry: The tool registry instance
        category: The category to register
        lazy: If True, tools are registered for lazy loading
    """
    if lazy:
        logger.info(f"Category '{category}' registered for lazy loading")
        return
    
    # Force load tools in this category
    tools = tool_registry.get_tools_by_category(category)
    logger.info(f"Loaded {len(tools)} tools from category '{category}'")

def preload_essential_tools(tool_registry) -> None:
    """
    Preload only the most essential tools for better startup performance.
    """
    essential_tools = [
        "get_file_content",
        "write_file",
        "execute_command",
        "list_directory",
    ]
    
    for tool_name in essential_tools:
        tool = tool_registry.get_tool(tool_name)
        if tool:
            logger.debug(f"Preloaded essential tool: {tool_name}")
