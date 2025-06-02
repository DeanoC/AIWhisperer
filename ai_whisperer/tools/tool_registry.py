"""
Lazy-loading tool registry for improved performance.
This replaces the original tool_registry.py with on-demand loading.
"""

import logging
import importlib
from typing import Dict, Any, List, Optional, Set
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.tools.tool_set import ToolSetManager

logger = logging.getLogger(__name__)

class LazyToolRegistry:
    """
    Central registry for managing AI-usable tools with lazy loading.
    Tools are only imported and instantiated when first accessed.
    """
    _instance: Optional['LazyToolRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LazyToolRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._registered_tools: Dict[str, AITool] = {}
        self._tool_specs: Dict[str, Dict[str, Any]] = {}
        self._loaded_tools: Set[str] = set()
        self._tool_set_manager = ToolSetManager()
        self._path_manager = None
        self._initialized = True
        
        # Initialize tool specifications (without importing)
        self._init_tool_specs()
        
        logger.info("Initialized lazy tool registry")
    
    def _init_tool_specs(self):
        """Initialize tool specifications for lazy loading."""
        # File operation tools
        self._tool_specs.update({
            "read_file": {
                "module": "ai_whisperer.tools.read_file_tool",
                "class": "ReadFileTool",
                "category": "file_ops"
            },
            "write_file": {
                "module": "ai_whisperer.tools.write_file_tool",
                "class": "WriteFileTool",
                "category": "file_ops"
            },
            "execute_command": {
                "module": "ai_whisperer.tools.execute_command_tool",
                "class": "ExecuteCommandTool",
                "category": "file_ops"
            },
            "list_directory": {
                "module": "ai_whisperer.tools.list_directory_tool",
                "class": "ListDirectoryTool",
                "category": "file_ops"
            },
            "search_files": {
                "module": "ai_whisperer.tools.search_files_tool",
                "class": "SearchFilesTool",
                "category": "file_ops"
            },
            "get_file_content": {
                "module": "ai_whisperer.tools.get_file_content_tool",
                "class": "GetFileContentTool",
                "category": "file_ops"
            },
            
            # Analysis tools
            "find_pattern": {
                "module": "ai_whisperer.tools.find_pattern_tool",
                "class": "FindPatternTool",
                "category": "analysis"
            },
            "python_ast_json": {
                "module": "ai_whisperer.tools.python_ast_json_tool",
                "class": "PythonASTJSONTool",
                "category": "analysis"
            },
            "find_similar_code": {
                "module": "ai_whisperer.tools.find_similar_code_tool",
                "class": "FindSimilarCodeTool",
                "category": "analysis"
            },
            
            # Project structure tools
            "get_project_structure": {
                "module": "ai_whisperer.tools.get_project_structure_tool",
                "class": "GetProjectStructureTool",
                "category": "project"
            },
            "workspace_stats": {
                "module": "ai_whisperer.tools.workspace_stats_tool",
                "class": "WorkspaceStatsTool",
                "category": "project"
            },
            
            # RFC tools
            "create_rfc": {
                "module": "ai_whisperer.tools.create_rfc_tool",
                "class": "CreateRFCTool",
                "category": "rfc"
            },
            "read_rfc": {
                "module": "ai_whisperer.tools.read_rfc_tool",
                "class": "ReadRFCTool",
                "category": "rfc"
            },
            "update_rfc": {
                "module": "ai_whisperer.tools.update_rfc_tool",
                "class": "UpdateRFCTool",
                "category": "rfc"
            },
            "list_rfcs": {
                "module": "ai_whisperer.tools.list_rfcs_tool",
                "class": "ListRFCsTool",
                "category": "rfc"
            },
            
            # Plan tools
            "create_plan_from_rfc": {
                "module": "ai_whisperer.tools.create_plan_from_rfc_tool",
                "class": "CreatePlanFromRFCTool",
                "category": "plan"
            },
            "read_plan": {
                "module": "ai_whisperer.tools.read_plan_tool",
                "class": "ReadPlanTool",
                "category": "plan"
            },
            "list_plans": {
                "module": "ai_whisperer.tools.list_plans_tool",
                "class": "ListPlansTool",
                "category": "plan"
            },
            
            # Codebase analysis
            "analyze_dependencies": {
                "module": "ai_whisperer.tools.analyze_dependencies_tool",
                "class": "AnalyzeDependenciesTool",
                "category": "agent_e"
            },
            "analyze_languages": {
                "module": "ai_whisperer.tools.analyze_languages_tool",
                "class": "AnalyzeLanguagesTool",
                "category": "codebase"
            },
            
            # Web tools
            "web_search": {
                "module": "ai_whisperer.tools.web_search_tool",
                "class": "WebSearchTool",
                "category": "web"
            },
            "fetch_url": {
                "module": "ai_whisperer.tools.fetch_url_tool",
                "class": "FetchURLTool",
                "category": "web"
            },
            
            # Debugging and monitoring tools
            "session_health": {
                "module": "ai_whisperer.tools.session_health_tool",
                "class": "SessionHealthTool",
                "category": "debugging"
            },
            "session_analysis": {
                "module": "ai_whisperer.tools.session_analysis_tool",
                "class": "SessionAnalysisTool",
                "category": "debugging"
            },
            "monitoring_control": {
                "module": "ai_whisperer.tools.monitoring_control_tool",
                "class": "MonitoringControlTool",
                "category": "debugging"
            },
            "session_inspector": {
                "module": "ai_whisperer.tools.session_inspector_tool",
                "class": "SessionInspectorTool",
                "category": "debugging"
            },
            "message_injector": {
                "module": "ai_whisperer.tools.message_injector_tool",
                "class": "MessageInjectorTool",
                "category": "debugging"
            },
            "workspace_validator": {
                "module": "ai_whisperer.tools.workspace_validator_tool",
                "class": "WorkspaceValidatorTool",
                "category": "debugging"
            },
            "python_executor": {
                "module": "ai_whisperer.tools.python_executor_tool",
                "class": "PythonExecutorTool",
                "category": "debugging"
            },
            "script_parser": {
                "module": "ai_whisperer.tools.script_parser_tool",
                "class": "ScriptParserTool",
                "category": "debugging"
            },
            "batch_command": {
                "module": "ai_whisperer.tools.batch_command_tool",
                "class": "BatchCommandTool",
                "category": "debugging"
            },
            "system_health_check": {
                "module": "ai_whisperer.tools.system_health_check_tool",
                "class": "SystemHealthCheckTool",
                "category": "debugging"
            },
            
            # Plan management tools
            "prepare_plan_from_rfc": {
                "module": "ai_whisperer.tools.prepare_plan_from_rfc_tool",
                "class": "PreparePlanFromRFCTool",
                "category": "plan"
            },
            "save_generated_plan": {
                "module": "ai_whisperer.tools.save_generated_plan_tool",
                "class": "SaveGeneratedPlanTool",
                "category": "plan"
            },
            "update_plan_from_rfc": {
                "module": "ai_whisperer.tools.update_plan_from_rfc_tool",
                "class": "UpdatePlanFromRFCTool",
                "category": "plan"
            },
            "move_plan": {
                "module": "ai_whisperer.tools.move_plan_tool",
                "class": "MovePlanTool",
                "category": "plan"
            },
            "delete_plan": {
                "module": "ai_whisperer.tools.delete_plan_tool",
                "class": "DeletePlanTool",
                "category": "plan"
            },
            
            # RFC management tools
            "move_rfc": {
                "module": "ai_whisperer.tools.move_rfc_tool",
                "class": "MoveRFCTool",
                "category": "rfc"
            },
            "delete_rfc": {
                "module": "ai_whisperer.tools.delete_rfc_tool",
                "class": "DeleteRFCTool",
                "category": "rfc"
            },
            
            # Agent E tools
            "decompose_plan": {
                "module": "ai_whisperer.tools.decompose_plan_tool",
                "class": "DecomposePlanTool",
                "category": "agent_e"
            },
            "format_for_external_agent": {
                "module": "ai_whisperer.tools.format_for_external_agent_tool",
                "class": "FormatForExternalAgentTool",
                "category": "agent_e"
            },
            "update_task_status": {
                "module": "ai_whisperer.tools.update_task_status_tool",
                "class": "UpdateTaskStatusTool",
                "category": "agent_e"
            },
            "validate_external_agent": {
                "module": "ai_whisperer.tools.validate_external_agent_tool",
                "class": "ValidateExternalAgentTool",
                "category": "agent_e"
            },
            "recommend_external_agent": {
                "module": "ai_whisperer.tools.recommend_external_agent_tool",
                "class": "RecommendExternalAgentTool",
                "category": "agent_e"
            },
            "parse_external_result": {
                "module": "ai_whisperer.tools.parse_external_result_tool",
                "class": "ParseExternalResultTool",
                "category": "agent_e"
            },
        })
    
    def set_path_manager(self, path_manager):
        """Set the path manager for tools that need it."""
        self._path_manager = path_manager
    
    def _load_tool(self, tool_name: str) -> Optional[AITool]:
        """Load a tool on demand."""
        if tool_name in self._loaded_tools:
            return self._registered_tools.get(tool_name)
        
        # Check if we have a spec for this tool
        spec = None
        for name, tool_spec in self._tool_specs.items():
            if name == tool_name or tool_spec.get("class", "").lower() == tool_name.lower():
                spec = tool_spec
                tool_name = name  # Normalize the name
                break
        
        if not spec:
            logger.warning(f"No specification found for tool: {tool_name}")
            return None
        
        try:
            # Import the module
            module = importlib.import_module(spec["module"])
            
            # Get the tool class
            tool_class = getattr(module, spec["class"])
            
            # Create instance
            tool = tool_class()
            
            # Register it
            self._registered_tools[tool_name] = tool
            self._loaded_tools.add(tool_name)
            
            logger.debug(f"Lazy loaded tool '{tool_name}' from {spec['module']}")
            return tool
            
        except Exception as e:
            logger.error(f"Failed to load tool '{tool_name}': {str(e)}")
            return None
    
    def register_tool(self, tool: AITool) -> None:
        """Register a tool instance."""
        tool_name = tool.name
        self._registered_tools[tool_name] = tool
        self._loaded_tools.add(tool_name)
        logger.debug(f"Registered tool: {tool_name}")
    
    def get_tool(self, name: str) -> Optional[AITool]:
        """Get a tool by name, loading it if necessary."""
        # First check if already loaded
        if name in self._registered_tools:
            return self._registered_tools[name]
        
        # Try to load it
        return self._load_tool(name)
    
    def get_tools_by_names(self, names: List[str]) -> Dict[str, AITool]:
        """Get multiple tools by name."""
        result = {}
        for name in names:
            tool = self.get_tool(name)
            if tool:
                result[name] = tool
        return result
    
    def get_all_tools(self) -> Dict[str, AITool]:
        """Get all registered tools."""
        # In lazy mode, we don't load all tools unless explicitly needed
        # Return only loaded tools
        return self._registered_tools.copy()
    
    def get_all_tool_names(self) -> List[str]:
        """Get names of all available tools (loaded and unloaded)."""
        # Include both loaded tools and specs
        all_names = set(self._registered_tools.keys())
        all_names.update(self._tool_specs.keys())
        return list(all_names)
    
    def get_tools_for_set(self, tool_set_name: str) -> Dict[str, AITool]:
        """Get tools for a specific tool set."""
        tool_names = self._tool_set_manager.get_tools_for_set(tool_set_name)
        if not tool_names:
            return {}
        
        return self.get_tools_by_names(tool_names)
    
    def get_all_ai_prompt_instructions(self) -> str:
        """Get AI prompt instructions for all loaded tools."""
        instructions = []
        for tool in self._registered_tools.values():
            instructions.append(tool.get_ai_prompt_instructions())
        return "\n\n".join(instructions)
    
    def search_tools(self, query: str) -> List[AITool]:
        """Search for tools by name or description."""
        query_lower = query.lower()
        matching_tools = []
        
        # Search in loaded tools
        for name, tool in self._registered_tools.items():
            if (query_lower in name.lower() or 
                query_lower in tool.description.lower()):
                matching_tools.append(tool)
        
        # Search in specs for unloaded tools
        for name, spec in self._tool_specs.items():
            if name not in self._loaded_tools:
                if query_lower in name.lower():
                    # Load the tool if it matches
                    tool = self._load_tool(name)
                    if tool:
                        matching_tools.append(tool)
        
        return matching_tools
    
    def get_loaded_tool_count(self) -> int:
        """Get the number of currently loaded tools."""
        return len(self._loaded_tools)
    
    def get_available_tool_count(self) -> int:
        """Get the total number of available tools."""
        return len(self._tool_specs)
    
    def preload_essential_tools(self):
        """Preload only the most essential tools for better startup."""
        essential_tools = [
            "get_file_content",
            "write_file",
            "execute_command",
            "list_directory",
        ]
        
        for tool_name in essential_tools:
            self._load_tool(tool_name)
        
        logger.info(f"Preloaded {len(essential_tools)} essential tools")
    
    # Backward compatibility methods from original ToolRegistry
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance for testing."""
        if cls._instance is not None:
            cls._instance._registered_tools.clear()
            cls._instance._tool_set_manager = None
        cls._instance = None
    
    def unregister_tool(self, tool_name: str):
        """Unregisters a tool by name."""
        if tool_name in self._registered_tools:
            del self._registered_tools[tool_name]
            self._loaded_tools.discard(tool_name)
            logger.info(f"Tool '{tool_name}' unregistered successfully.")
        else:
            logger.warning(f"Tool '{tool_name}' not found in registry.")
    
    def reset_tools(self):
        """Clears all registered tools."""
        self._registered_tools.clear()
        self._loaded_tools.clear()
        logger.info("All registered tools have been cleared.")
    
    def get_tool_by_name(self, name: str) -> Optional[AITool]:
        """Retrieves a specific tool by its unique name."""
        return self.get_tool(name)
    
    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of Openrouter-compatible JSON definitions for all tools.
        """
        return [tool.get_openrouter_tool_definition() for tool in self.get_all_tools().values()]
    
    def get_filtered_tools(self, criteria: Dict[str, Any]) -> List[AITool]:
        """
        Retrieves a list of tools matching the given criteria.
        Example criteria: {"tags": ["file_io"], "category": "Utility", "name_pattern": "read_.*"}
        """
        filtered_list = []

        for tool in self.get_all_tools().values():
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
                    import re
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

# Singleton accessor
_lazy_registry = None

def get_tool_registry() -> LazyToolRegistry:
    """Get the singleton tool registry instance."""
    global _lazy_registry
    if _lazy_registry is None:
        _lazy_registry = LazyToolRegistry()
    return _lazy_registry

# Backward compatibility alias
ToolRegistry = LazyToolRegistry
