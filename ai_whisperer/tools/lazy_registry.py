"""
Lazy tool registry for performance optimization.
Loads tools on-demand rather than at startup.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import importlib
import logging
import json

from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class LazyToolRegistry:
    """
    A registry that loads tools lazily to improve startup performance.
    Tools are only imported and instantiated when first accessed.
    """
    
    def __init__(self):
        """Initialize the lazy registry."""
        self._tool_specs: Dict[str, Dict[str, Any]] = {}
        self._loaded_tools: Dict[str, AITool] = {}
        self._loading_errors: Dict[str, str] = {}
        self._manifest_loaded = False
        
    def _load_manifest(self):
        """Load tool manifest if not already loaded."""
        if self._manifest_loaded:
            return
            
        # Define tool specifications
        # This could be loaded from a JSON file for easier maintenance
        self._tool_specs = {
            # File and content tools
            "get_file_content": {
                "module": "ai_whisperer.tools.get_file_content_tool",
                "class": "GetFileContentTool",
                "description": "Read file contents",
                "category": "file"
            },
            "write_file": {
                "module": "ai_whisperer.tools.write_file_tool",
                "class": "WriteFileTool",
                "description": "Write content to files",
                "category": "file"
            },
            "list_directory": {
                "module": "ai_whisperer.tools.list_directory_tool",
                "class": "ListDirectoryTool",
                "description": "List directory contents",
                "category": "file"
            },
            "search_files": {
                "module": "ai_whisperer.tools.search_files_tool",
                "class": "SearchFilesTool",
                "description": "Search for files",
                "category": "file"
            },
            
            # Code analysis tools
            "python_ast_json": {
                "module": "ai_whisperer.tools.python_ast_json_tool",
                "class": "PythonASTJSONTool",
                "description": "Convert Python AST to JSON",
                "category": "analysis"
            },
            "analyze_dependencies": {
                "module": "ai_whisperer.tools.analyze_dependencies_tool",
                "class": "AnalyzeDependenciesTool",
                "description": "Analyze code dependencies",
                "category": "analysis"
            },
            
            # Execution tools
            "execute_command": {
                "module": "ai_whisperer.tools.execute_command_tool",
                "class": "ExecuteCommandTool",
                "description": "Execute shell commands",
                "category": "execution"
            },
            "python_executor": {
                "module": "ai_whisperer.tools.python_executor_tool",
                "class": "PythonExecutorTool",
                "description": "Execute Python code",
                "category": "execution"
            },
            
            # Planning tools
            "create_rfc": {
                "module": "ai_whisperer.tools.create_rfc_tool",
                "class": "CreateRFCTool",
                "description": "Create RFC documents",
                "category": "planning"
            },
            "create_plan_from_rfc": {
                "module": "ai_whisperer.tools.create_plan_from_rfc_tool",
                "class": "CreatePlanFromRFCTool",
                "description": "Convert RFC to execution plan",
                "category": "planning"
            },
            
            # Add more tools as needed...
        }
        
        self._manifest_loaded = True
        logger.info(f"Loaded manifest with {len(self._tool_specs)} tool specifications")
    
    def register_tool_spec(self, name: str, module: str, class_name: str, 
                          description: str = "", category: str = "general"):
        """Register a tool specification without loading it."""
        self._tool_specs[name] = {
            "module": module,
            "class": class_name,
            "description": description,
            "category": category
        }
    
    def _load_tool(self, name: str) -> Optional[AITool]:
        """Load a tool on demand."""
        if name in self._loaded_tools:
            return self._loaded_tools[name]
            
        if name in self._loading_errors:
            logger.warning(f"Tool {name} previously failed to load: {self._loading_errors[name]}")
            return None
            
        if name not in self._tool_specs:
            logger.error(f"Tool {name} not found in registry")
            return None
            
        spec = self._tool_specs[name]
        
        try:
            # Import the module
            module = importlib.import_module(spec["module"])
            
            # Get the tool class
            tool_class = getattr(module, spec["class"])
            
            # Instantiate the tool
            tool = tool_class()
            
            # Cache it
            self._loaded_tools[name] = tool
            logger.debug(f"Loaded tool {name} from {spec['module']}")
            
            return tool
            
        except Exception as e:
            error_msg = f"Failed to load tool {name}: {str(e)}"
            logger.error(error_msg)
            self._loading_errors[name] = error_msg
            return None
    
    def get_tool(self, name: str) -> Optional[AITool]:
        """Get a tool by name, loading it if necessary."""
        self._load_manifest()
        return self._load_tool(name)
    
    def list_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools without loading them."""
        self._load_manifest()
        return {
            name: {
                "description": spec["description"],
                "category": spec["category"],
                "loaded": name in self._loaded_tools
            }
            for name, spec in self._tool_specs.items()
        }
    
    def get_tools_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get tools by category without loading them."""
        self._load_manifest()
        return {
            name: spec
            for name, spec in self._tool_specs.items()
            if spec.get("category") == category
        }
    
    def preload_tools(self, tool_names: List[str]):
        """Preload specific tools."""
        for name in tool_names:
            self._load_tool(name)
    
    def get_loaded_tools(self) -> Dict[str, AITool]:
        """Get all currently loaded tools."""
        return self._loaded_tools.copy()
    
    def clear_cache(self):
        """Clear loaded tools to free memory."""
        self._loaded_tools.clear()
        logger.info("Cleared tool cache")
    
    def generate_manifest_file(self, output_path: str = "tool_manifest.json"):
        """Generate a manifest file for all tools."""
        self._load_manifest()
        
        manifest = {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "tools": self._tool_specs
        }
        
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Generated tool manifest at {output_path}")

# Singleton instance
_lazy_registry = None

def get_lazy_registry() -> LazyToolRegistry:
    """Get the singleton lazy registry instance."""
    global _lazy_registry
    if _lazy_registry is None:
        _lazy_registry = LazyToolRegistry()
    return _lazy_registry
