"""
Optimized tool registry with lazy loading support.
This version loads tools on-demand to improve startup performance.
"""
from typing import Any, Dict, List, Optional, Set

import logging
import importlib
from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class OptimizedToolRegistry:
    """
    Optimized tool registry that supports lazy loading.
    Tools are only loaded when first accessed.
    """
    
    def __init__(self, lazy_loading: bool = True):
        """
        Initialize the optimized tool registry.
        
        Args:
            lazy_loading: If True, tools are loaded on-demand. If False, all tools are loaded immediately.
        """
        self._tools: Dict[str, AITool] = {}
        self._tool_specs: Dict[str, Dict[str, Any]] = {}
        self._loaded_tools: Set[str] = set()
        self._lazy_loading = lazy_loading
        self._categories: Dict[str, Set[str]] = {}
        
        # Initialize tool specifications
        self._init_tool_specs()
        
        # If not lazy loading, load all tools now
        if not lazy_loading:
            self._load_all_tools()
    
    def _init_tool_specs(self):
        """Initialize tool specifications for lazy loading."""
        # This defines all available tools without importing them
        self._tool_specs = {
            # File operations
            "get_file_content": {
                "module": "ai_whisperer.tools.get_file_content_tool",
                "class": "GetFileContentTool",
                "category": "file",
                "description": "Read file contents"
            },
            "write_file": {
                "module": "ai_whisperer.tools.write_file_tool",
                "class": "WriteFileTool",
                "category": "file",
                "description": "Write content to files"
            },
            "list_directory": {
                "module": "ai_whisperer.tools.list_directory_tool",
                "class": "ListDirectoryTool",
                "category": "file",
                "description": "List directory contents"
            },
            "search_files": {
                "module": "ai_whisperer.tools.search_files_tool",
                "class": "SearchFilesTool",
                "category": "file",
                "description": "Search for files by name or content"
            },
            "find_pattern": {
                "module": "ai_whisperer.tools.find_pattern_tool",
                "class": "FindPatternTool",
                "category": "file",
                "description": "Find patterns in files"
            },
            
            # Code analysis
            "python_ast_json": {
                "module": "ai_whisperer.tools.python_ast_json_tool",
                "class": "PythonASTJSONTool",
                "category": "code_analysis",
                "description": "Convert Python AST to JSON"
            },
            "analyze_dependencies": {
                "module": "ai_whisperer.tools.analyze_dependencies_tool",
                "class": "AnalyzeDependenciesTool",
                "category": "code_analysis",
                "description": "Analyze code dependencies"
            },
            "analyze_languages": {
                "module": "ai_whisperer.tools.analyze_languages_tool",
                "class": "AnalyzeLanguagesTool",
                "category": "code_analysis",
                "description": "Analyze programming languages used"
            },
            
            # Execution
            "execute_command": {
                "module": "ai_whisperer.tools.execute_command_tool",
                "class": "ExecuteCommandTool",
                "category": "execution",
                "description": "Execute shell commands"
            },
            "python_executor": {
                "module": "ai_whisperer.tools.python_executor_tool",
                "class": "PythonExecutorTool",
                "category": "execution",
                "description": "Execute Python code safely"
            },
            
            # Project structure
            "get_project_structure": {
                "module": "ai_whisperer.tools.get_project_structure_tool",
                "class": "GetProjectStructureTool",
                "category": "project",
                "description": "Get project directory structure"
            },
            "workspace_stats": {
                "module": "ai_whisperer.tools.workspace_stats_tool",
                "class": "WorkspaceStatsTool",
                "category": "project",
                "description": "Get workspace statistics"
            },
            
            # Planning tools
            "create_rfc": {
                "module": "ai_whisperer.tools.create_rfc_tool",
                "class": "CreateRFCTool",
                "category": "planning",
                "description": "Create RFC documents"
            },
            "create_plan_from_rfc": {
                "module": "ai_whisperer.tools.create_plan_from_rfc_tool",
                "class": "CreatePlanFromRFCTool",
                "category": "planning",
                "description": "Convert RFC to execution plan"
            },
            
            # Add more tools as needed...
        }
        
        # Build category index
        for tool_name, spec in self._tool_specs.items():
            category = spec.get("category", "general")
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(tool_name)
    
    def _load_tool(self, name: str) -> Optional[AITool]:
        """Load a single tool by name."""
        if name in self._loaded_tools:
            return self._tools.get(name)
        
        if name not in self._tool_specs:
            logger.warning(f"Tool '{name}' not found in registry")
            return None
        
        spec = self._tool_specs[name]
        
        try:
            # Import the module
            module = importlib.import_module(spec["module"])
            
            # Get the tool class
            tool_class = getattr(module, spec["class"])
            
            # Create instance
            tool = tool_class()
            
            # Store it
            self._tools[name] = tool
            self._loaded_tools.add(name)
            
            logger.debug(f"Lazy loaded tool '{name}' from {spec['module']}")
            return tool
            
        except Exception as e:
            logger.error(f"Failed to load tool '{name}': {str(e)}")
            return None
    
    def _load_all_tools(self):
        """Load all tools (used when lazy loading is disabled)."""
        for name in self._tool_specs:
            self._load_tool(name)
    
    def register_tool(self, name: str, tool: AITool) -> None:
        """Register a tool instance directly."""
        self._tools[name] = tool
        self._loaded_tools.add(name)
        logger.debug(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[AITool]:
        """Get a tool by name, loading it if necessary."""
        if self._lazy_loading and name not in self._loaded_tools:
            return self._load_tool(name)
        return self._tools.get(name)
    
    def get_tools_by_names(self, names: List[str]) -> Dict[str, AITool]:
        """Get multiple tools by name."""
        result = {}
        for name in names:
            tool = self.get_tool(name)
            if tool:
                result[name] = tool
        return result
    
    def get_all_tools(self) -> Dict[str, AITool]:
        """Get all tools, loading them if necessary."""
        if self._lazy_loading:
            # Load all tools
            for name in self._tool_specs:
                if name not in self._loaded_tools:
                    self._load_tool(name)
        return self._tools.copy()
    
    def list_available_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self._tool_specs.keys())
    
    def get_tools_by_category(self, category: str) -> Dict[str, AITool]:
        """Get all tools in a category."""
        result = {}
        for name in self._categories.get(category, set()):
            tool = self.get_tool(name)
            if tool:
                result[name] = tool
        return result
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a tool without loading it."""
        if name in self._tool_specs:
            info = self._tool_specs[name].copy()
            info["loaded"] = name in self._loaded_tools
            return info
        return None
    
    def get_loaded_tool_names(self) -> List[str]:
        """Get names of currently loaded tools."""
        return list(self._loaded_tools)
    
    def clear_cache(self):
        """Clear loaded tools to free memory."""
        self._tools.clear()
        self._loaded_tools.clear()
        logger.info("Cleared tool cache")

# Global registry instance
_registry = None

def get_tool_registry(lazy_loading: bool = True) -> OptimizedToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = OptimizedToolRegistry(lazy_loading=lazy_loading)
    return _registry

# Compatibility layer
class ToolRegistry:
    """Compatibility wrapper for the old ToolRegistry interface."""
    
    def __init__(self):
        self._registry = get_tool_registry()
    
    def register_tool(self, name: str, tool: AITool) -> None:
        self._registry.register_tool(name, tool)
    
    def get_tool(self, name: str) -> Optional[AITool]:
        return self._registry.get_tool(name)
    
    def get_tools_by_names(self, names: List[str]) -> Dict[str, AITool]:
        return self._registry.get_tools_by_names(names)
    
    def get_all_tools(self) -> Dict[str, AITool]:
        return self._registry.get_all_tools()
    
    def list_available_tools(self) -> List[str]:
        return self._registry.list_available_tools()
