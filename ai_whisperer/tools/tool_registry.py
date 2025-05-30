import logging
import re
from typing import Dict, Any, List, Optional, Set

# Assuming AITool is defined in base_tool.py
from .base_tool import AITool
from .tool_set import ToolSetManager

logger = logging.getLogger(__name__)

# Actual registration of tools is not done here. 
# The plan_runner.py is the standard place for adding tools for running plans

class ToolRegistry:
    """
    Central registry for managing AI-usable tools.
    Implemented as a singleton.
    """
    _instance: Optional['ToolRegistry'] = None
    _registered_tools: Dict[str, AITool]
    _tool_set_manager: Optional[ToolSetManager]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._registered_tools = {}
            cls._instance._tool_set_manager = None
            # Tool discovery/loading will be implemented later
            # cls._instance._load_tools()
        return cls._instance

    def register_tool(self, tool: AITool):
        """Registers a single tool instance."""
        if not isinstance(tool, AITool):
            logger.warning(f"Attempted to register non-AITool object: {type(tool)}. Skipping.")
            return

        if tool.name in self._registered_tools:
            logger.warning(f"Tool '{tool.name}' already registered. Skipping duplicate.")
            return

        self._registered_tools[tool.name] = tool
        logger.info(f"Tool '{tool.name}' registered successfully.")
    
    def unregister_tool(self, tool_name: str):
        """Unregisters a tool by name."""
        if tool_name in self._registered_tools:
            del self._registered_tools[tool_name]
            logger.info(f"Tool '{tool_name}' unregistered successfully.")
        else:
            logger.warning(f"Tool '{tool_name}' not found in registry.")

    def reset_tools(self):
        """Clears all registered tools."""
        self._registered_tools.clear()
        logger.info("All registered tools have been cleared.")

    def get_tool_by_name(self, name: str) -> Optional[AITool]:
        """Retrieves a specific tool by its unique name."""
        return self._registered_tools.get(name)

    def get_all_tools(self) -> List[AITool]:
        """Returns a list of all registered AITool instances."""
        return list(self._registered_tools.values())

    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of Openrouter-compatible JSON definitions for all tools.
        """
        return [tool.get_openrouter_tool_definition() for tool in self.get_all_tools()]

    def get_all_ai_prompt_instructions(self) -> str:
        """
        Returns a consolidated string of AI prompt instructions for all tools.
        """
        instructions = [tool.get_ai_prompt_instructions() for tool in self.get_all_tools()]
        return "\n\n".join(instructions)

    def get_filtered_tools(self, criteria: Dict[str, Any]) -> List[AITool]:
        """
        Retrieves a list of tools matching the given criteria.
        Example criteria: {"tags": ["file_io"], "category": "Utility", "name_pattern": "read_.*"}
        """
        filtered_list = []

        for tool in self.get_all_tools():
            match = True

            # Filter by tags (match ANY tag, not ALL)
            if "tags" in criteria:
                tool_tags = set(getattr(tool, 'tags', []))
                filter_tags = set(criteria["tags"])
                if not tool_tags.intersection(filter_tags):
                    match = False

            # Filter by category
            if match and "category" in criteria:
                tool_category = getattr(tool, 'category', None)
                if tool_category != criteria["category"]:
                    match = False

            # Filter by name pattern
            if match and "name_pattern" in criteria:
                try:
                    if not re.match(criteria["name_pattern"], tool.name):
                        match = False
                except re.error:
                    logger.warning(f"Invalid regex pattern '{criteria['name_pattern']}' for name_pattern filter.")
                    # Decide how to handle invalid regex - here we treat it as no match
                    match = False


            if match:
                filtered_list.append(tool)
        return filtered_list
    
    def initialize_tool_sets(self, config_path: Optional[str] = None) -> None:
        """Initialize the tool set manager with configuration.
        
        Args:
            config_path: Path to tool_sets.yaml file. If None, uses default location.
        """
        self._tool_set_manager = ToolSetManager(config_path)
        logger.info("Tool set manager initialized")
    
    def get_tool_set_manager(self) -> Optional[ToolSetManager]:
        """Get the tool set manager instance.
        
        Returns:
            ToolSetManager instance or None if not initialized
        """
        if self._tool_set_manager is None:
            # Auto-initialize with default config if not already done
            self.initialize_tool_sets()
        return self._tool_set_manager
    
    def register_tool_set(self, name: str, tools: List[str], 
                         tags: Optional[List[str]] = None,
                         deny_tags: Optional[List[str]] = None,
                         inherits: Optional[List[str]] = None) -> None:
        """Register a new tool set programmatically.
        
        Args:
            name: Name of the tool set
            tools: List of tool names in this set
            tags: Optional list of tags to include
            deny_tags: Optional list of tags to exclude
            inherits: Optional list of parent tool set names
        """
        if self._tool_set_manager is None:
            self.initialize_tool_sets()
        
        # This would require extending ToolSetManager to support dynamic registration
        # For now, tool sets are defined in YAML only
        logger.warning("Dynamic tool set registration not yet implemented. Use tool_sets.yaml instead.")
    
    def get_tools_by_set(self, set_name: str) -> List[AITool]:
        """Get all tools belonging to a tool set.
        
        Args:
            set_name: Name of the tool set
            
        Returns:
            List of AITool instances in the set
        """
        manager = self.get_tool_set_manager()
        if not manager:
            return []
        
        # Get tool names from the set
        tool_names = manager.get_tools_for_set(set_name)
        tags = manager.get_tags_for_set(set_name)
        deny_tags = manager.get_deny_tags_for_set(set_name)
        
        # Collect tools by name
        tools = []
        for tool_name in tool_names:
            tool = self.get_tool_by_name(tool_name)
            if tool:
                tools.append(tool)
        
        # Also collect tools by tags
        if tags:
            tag_tools = self.get_filtered_tools({"tags": list(tags)})
            for tool in tag_tools:
                if tool not in tools:
                    tools.append(tool)
        
        # Filter out tools with denied tags
        if deny_tags:
            tools = [tool for tool in tools 
                    if not any(tag in getattr(tool, 'tags', []) for tag in deny_tags)]
        
        return tools
    
    def get_tools_for_agent(self, tool_sets: Optional[List[str]] = None,
                           tags: Optional[List[str]] = None,
                           allow_tools: Optional[List[str]] = None,
                           deny_tools: Optional[List[str]] = None) -> List[AITool]:
        """Get tools for an agent based on tool sets, tags, and allow/deny lists.
        
        This implements the precedence: deny > allow > tool_sets/tags
        
        Args:
            tool_sets: List of tool set names
            tags: List of tags to filter by
            allow_tools: Explicit list of allowed tool names
            deny_tools: Explicit list of denied tool names
            
        Returns:
            List of AITool instances the agent can use
        """
        all_tools = set()
        
        # Start with tool sets
        if tool_sets:
            for set_name in tool_sets:
                set_tools = self.get_tools_by_set(set_name)
                all_tools.update(set_tools)
        
        # Add tools by tags
        if tags:
            tag_tools = self.get_filtered_tools({"tags": tags})
            all_tools.update(tag_tools)
        
        # Apply allow list (if specified, only these tools are allowed)
        if allow_tools:
            allowed_names = set(allow_tools)
            all_tools = {tool for tool in all_tools if tool.name in allowed_names}
        
        # Apply deny list (always takes precedence)
        if deny_tools:
            denied_names = set(deny_tools)
            all_tools = {tool for tool in all_tools if tool.name not in denied_names}
        
        return list(all_tools)

# Provide a convenient way to access the singleton instance
def get_tool_registry() -> ToolRegistry:
    """Returns the singleton instance of the ToolRegistry."""
    return ToolRegistry()