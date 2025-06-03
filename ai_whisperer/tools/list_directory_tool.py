"""
Module: ai_whisperer/tools/list_directory_tool.py
Purpose: AI tool implementation for list directory

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- ListDirectoryTool: Tool for listing files and directories within the workspace.

Usage:
    tool = ListDirectoryTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

Related:
- See docs/file-browser-consolidated-implementation.md
- See docs/archive/phase2_consolidation/file_browser_implementation_checklist.md

"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager
from ai_whisperer.core.exceptions import FileRestrictionError

logger = logging.getLogger(__name__)


class ListDirectoryTool(AITool):
    """Tool for listing files and directories within the workspace."""
    
    @property
    def name(self) -> str:
        return "list_directory"
    
    @property
    def description(self) -> str:
        return "Lists files and directories in a workspace path with optional recursive traversal."
    
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
        
        Returns a structured listing showing files and directories with their types.
        Example usage:
        <tool_code>
        list_directory(path='src', recursive=True, max_depth=2)
        </tool_code>
        """
    
    def execute(self, arguments: Dict[str, Any] = None, **kwargs) -> str:
        """Execute the directory listing."""
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
            raise FileRestrictionError(f"Access denied. Path '{path}' is outside the workspace directory.")
        
        # Check if path exists
        if not target_path.exists():
            return f"Error: Path '{path}' does not exist."
        
        # Check if it's a directory
        if not target_path.is_dir():
            return f"Error: Path '{path}' is not a directory."
        
        try:
            if recursive:
                return self._list_recursive(target_path, max_depth, include_hidden, current_depth=0)
            else:
                return self._list_flat(target_path, include_hidden)
        except PermissionError:
            return f"Error: Permission denied to read directory '{path}'."
        except Exception as e:
            logger.error(f"Error listing directory '{path}': {e}")
            return f"Error listing directory '{path}': {str(e)}"
    
    def _list_flat(self, directory: Path, include_hidden: bool) -> str:
        """List directory contents in a flat format."""
        items = []
        
        try:
            entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for entry in entries:
                # Skip hidden files if not requested
                if not include_hidden and entry.name.startswith('.'):
                    continue
                    
                if entry.is_dir():
                    items.append(f"[DIR]  {entry.name}/")
                else:
                    # Get file size
                    try:
                        size = entry.stat().st_size
                        size_str = self._format_size(size)
                        items.append(f"[FILE] {entry.name} ({size_str})")
                    except:
                        items.append(f"[FILE] {entry.name}")
            
            if not items:
                return "Directory is empty."
                
            # Add header with directory path
            workspace_path = PathManager.get_instance().workspace_path
            rel_path = os.path.relpath(directory, workspace_path)
            if rel_path == '.':
                header = "Contents of workspace root:"
            else:
                header = f"Contents of {rel_path}:"
                
            return f"{header}\n" + "\n".join(items)
            
        except Exception as e:
            raise e
    
    def _list_recursive(self, directory: Path, max_depth: int, include_hidden: bool, current_depth: int = 0, prefix: str = "") -> str:
        """List directory contents recursively in tree format."""
        if current_depth > max_depth:
            return ""
            
        items = []
        
        # Add directory name if not root level
        if current_depth == 0:
            workspace_path = PathManager.get_instance().workspace_path
            rel_path = os.path.relpath(directory, workspace_path)
            if rel_path == '.':
                items.append("Workspace root:")
            else:
                items.append(f"{rel_path}:")
        
        try:
            entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for i, entry in enumerate(entries):
                # Skip hidden files if not requested
                if not include_hidden and entry.name.startswith('.'):
                    continue
                
                is_last = i == len(entries) - 1
                
                # Create tree characters
                if current_depth > 0:
                    connector = "└── " if is_last else "├── "
                    item_prefix = prefix + connector
                    next_prefix = prefix + ("    " if is_last else "│   ")
                else:
                    item_prefix = ""
                    next_prefix = ""
                
                if entry.is_dir():
                    items.append(f"{item_prefix}{entry.name}/")
                    
                    # Recurse into subdirectory
                    if current_depth < max_depth:
                        sub_items = self._list_recursive(
                            entry, max_depth, include_hidden, 
                            current_depth + 1, next_prefix
                        )
                        if sub_items:
                            items.append(sub_items)
                else:
                    # Add file with size
                    try:
                        size = entry.stat().st_size
                        size_str = self._format_size(size)
                        items.append(f"{item_prefix}{entry.name} ({size_str})")
                    except:
                        items.append(f"{item_prefix}{entry.name}")
            
            return "\n".join(filter(None, items))
            
        except Exception as e:
            raise e
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{size}{unit}"
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"