import logging
import re
from typing import Dict, Any, List, Optional

# Assuming AITool is defined in base_tool.py
from .base_tool import AITool

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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._registered_tools = {}
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

            # Filter by tags
            if "tags" in criteria:
                tool_tags = getattr(tool, 'tags', [])
                if not all(tag in tool_tags for tag in criteria["tags"]):
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

    def reload_tools(self):
        """Clears existing tools and re-runs the discovery and registration process."""
        self._registered_tools.clear()
        # Tool discovery/loading will be implemented later
        # self._load_tools()

# Provide a convenient way to access the singleton instance
def get_tool_registry() -> ToolRegistry:
    """Returns the singleton instance of the ToolRegistry."""
    return ToolRegistry()