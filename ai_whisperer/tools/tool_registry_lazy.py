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
                "category": "codebase"
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
            
            # Add more tools as needed...
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
