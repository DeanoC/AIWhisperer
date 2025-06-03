"""List Directory Tool - Lists contents of directories with structured output."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ai_whisperer.tools.base_tool import AITool as BaseTool
from ai_whisperer.utils.path import PathManager
from ai_whisperer.core.exceptions import FileRestrictionError

logger = logging.getLogger(__name__)


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents with structured output."""
    
    @property
    def name(self) -> str:
        return "list_directory"
    
    @property
    def description(self) -> str:
        return "Lists the contents of a directory in the workspace"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path to list (relative to workspace root). Defaults to workspace root if not provided.",
                    "default": "."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list directories recursively.",
                    "default": False
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for recursive listing (only used if recursive=True).",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Whether to include hidden files/directories (starting with '.').",
                    "default": False
                }
            },
            "required": []
        }
    
    @property
    def category(self) -> Optional[str]:
        return "File System"
    
    @property
    def tags(self) -> List[str]:
        return ["filesystem", "directory_browse", "analysis"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'list_directory' tool to explore the workspace file structure.
        Parameters:
        - path (string, optional): Directory to list, relative to workspace root. Defaults to '.'
        - recursive (boolean, optional): List subdirectories recursively. Defaults to False
        - max_depth (integer, optional): Maximum depth for recursive listing (1-10). Defaults to 3
        - include_hidden (boolean, optional): Include hidden files/directories. Defaults to False
        
        Returns a structured listing with file/directory information.
        Example usage:
        <tool_code>
        list_directory(path='src', recursive=True, max_depth=2)
        </tool_code>
        """
    
    def execute(self, arguments: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute the directory listing and return structured data."""
        # Handle both arguments dict and kwargs patterns
        if arguments is None:
            arguments = {}
        
        # Merge kwargs into arguments, excluding agent context params
        for key, value in kwargs.items():
            if not key.startswith("_"):  # Skip agent context params
                arguments[key] = value
        
        path = arguments.get('path', '.')
        recursive = arguments.get('recursive', False)
        max_depth = arguments.get('max_depth', 3)
        include_hidden = arguments.get('include_hidden', False)
        
        # Validate max_depth
        max_depth = max(1, min(10, max_depth))
        
        path_manager = PathManager.get_instance()
        
        # Resolve the path relative to workspace
        if path == '.':
            target_path = Path(path_manager.workspace_path)
        else:
            target_path = Path(path_manager.workspace_path) / path
            
        # Ensure absolute path
        target_path = target_path.resolve()
        
        # Validate path is within workspace
        if not path_manager.is_path_within_workspace(target_path):
            return {
                "error": f"Access denied. Path '{path}' is outside the workspace directory.",
                "path": path,
                "entries": []
            }
        
        # Check if path exists
        if not target_path.exists():
            return {
                "error": f"Path '{path}' does not exist.",
                "path": path,
                "entries": []
            }
        
        # Check if it's a directory
        if not target_path.is_dir():
            return {
                "error": f"Path '{path}' is not a directory.",
                "path": path,
                "entries": []
            }
        
        try:
            # Get relative path for display
            workspace_path = Path(path_manager.workspace_path)
            rel_path = os.path.relpath(target_path, workspace_path)
            if rel_path == '.':
                rel_path = ""  # Root directory
            
            if recursive:
                entries = self._list_recursive(target_path, max_depth, include_hidden)
            else:
                entries = self._list_flat(target_path, include_hidden)
            
            return {
                "path": rel_path,
                "entries": entries,
                "total_files": sum(1 for e in entries if e["type"] == "file"),
                "total_directories": sum(1 for e in entries if e["type"] == "directory"),
                "recursive": recursive,
                "max_depth": max_depth if recursive else None
            }
            
        except PermissionError:
            return {
                "error": f"Permission denied to read directory '{path}'.",
                "path": path,
                "entries": []
            }
        except Exception as e:
            logger.error(f"Error listing directory '{path}': {e}")
            return {
                "error": f"Error listing directory: {str(e)}",
                "path": path,
                "entries": []
            }
    
    def _list_flat(self, directory: Path, include_hidden: bool) -> List[Dict[str, Any]]:
        """List directory contents in a flat format."""
        entries = []
        
        try:
            sorted_entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for entry in sorted_entries:
                # Skip hidden files if not requested
                if not include_hidden and entry.name.startswith('.'):
                    continue
                
                entry_info = {
                    "name": entry.name,
                    "path": str(entry.relative_to(Path(PathManager.get_instance().workspace_path))),
                    "type": "directory" if entry.is_dir() else "file"
                }
                
                if entry.is_file():
                    try:
                        stat = entry.stat()
                        entry_info["size"] = stat.st_size
                        entry_info["size_formatted"] = self._format_size(stat.st_size)
                        entry_info["modified"] = stat.st_mtime
                    except:
                        entry_info["size"] = None
                        entry_info["size_formatted"] = None
                
                entries.append(entry_info)
            
            return entries
            
        except Exception as e:
            raise e
    
    def _list_recursive(self, directory: Path, max_depth: int, include_hidden: bool, 
                       current_depth: int = 0, base_path: Path = None) -> List[Dict[str, Any]]:
        """List directory contents recursively."""
        if current_depth > max_depth:
            return []
        
        if base_path is None:
            base_path = Path(PathManager.get_instance().workspace_path)
        
        entries = []
        
        try:
            sorted_entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for entry in sorted_entries:
                # Skip hidden files if not requested
                if not include_hidden and entry.name.startswith('.'):
                    continue
                
                entry_info = {
                    "name": entry.name,
                    "path": str(entry.relative_to(base_path)),
                    "type": "directory" if entry.is_dir() else "file",
                    "depth": current_depth
                }
                
                if entry.is_file():
                    try:
                        stat = entry.stat()
                        entry_info["size"] = stat.st_size
                        entry_info["size_formatted"] = self._format_size(stat.st_size)
                        entry_info["modified"] = stat.st_mtime
                    except:
                        entry_info["size"] = None
                        entry_info["size_formatted"] = None
                
                entries.append(entry_info)
                
                # Recurse into subdirectories
                if entry.is_dir() and current_depth < max_depth:
                    sub_entries = self._list_recursive(
                        entry, max_depth, include_hidden, 
                        current_depth + 1, base_path
                    )
                    entries.extend(sub_entries)
            
            return entries
            
        except Exception as e:
            raise e
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{int(size)} {unit}"
                else:
                    return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"