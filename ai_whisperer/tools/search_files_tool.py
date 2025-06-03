"""
Module: ai_whisperer/tools/search_files_tool.py
Purpose: AI tool implementation for search files

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- SearchFilesTool: Tool for searching files within the workspace by name or content.

Usage:
    tool = SearchFilesTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- fnmatch

Related:
- See docs/file-browser-consolidated-implementation.md
- See docs/archive/phase2_consolidation/file_browser_implementation_checklist.md

"""

import os
import re
import fnmatch
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager
from ai_whisperer.core.exceptions import FileRestrictionError

logger = logging.getLogger(__name__)


class SearchFilesTool(AITool):
    """Tool for searching files within the workspace by name or content."""
    
    @property
    def name(self) -> str:
        return "search_files"
    
    @property
    def description(self) -> str:
        return "Search for files by name pattern or content within the workspace."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern. For name search: glob pattern (e.g., '*.py', 'test_*.js'). For content search: text or regex pattern."
                },
                "search_type": {
                    "type": "string",
                    "enum": ["name", "content"],
                    "description": "Type of search to perform.",
                    "default": "name"
                },
                "file_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file extensions to include (e.g., ['.py', '.js']). If empty, searches all files.",
                    "default": []
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000
                },
                "ignore_case": {
                    "type": "boolean",
                    "description": "Whether to ignore case in search (applies to both name and content search).",
                    "default": True
                },
                "search_path": {
                    "type": "string",
                    "description": "Directory to search in (relative to workspace). Defaults to entire workspace.",
                    "default": "."
                }
            },
            "required": ["pattern"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "File System"
    
    @property
    def tags(self) -> List[str]:
        return ["filesystem", "file_search", "analysis"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'search_files' tool to find files in the workspace.
        Parameters:
        - pattern (string, required): Search pattern (glob for names, text/regex for content)
        - search_type (string, optional): 'name' or 'content'. Defaults to 'name'
        - file_types (array, optional): File extensions to include, e.g., ['.py', '.js']
        - max_results (integer, optional): Maximum results to return (1-1000). Defaults to 100
        - ignore_case (boolean, optional): Case-insensitive search. Defaults to True
        - search_path (string, optional): Directory to search in. Defaults to workspace root
        
        Returns a list of matching files with their paths.
        Example usage:
        <tool_code>
        search_files(pattern='*.test.js', search_type='name', file_types=['.js'])
        search_files(pattern='TODO|FIXME', search_type='content', file_types=['.py', '.js'])
        </tool_code>
        """
    
    def execute(self, arguments: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute the file search."""
        # Handle both arguments dict and kwargs patterns
        if arguments is None:
            arguments = {}
        
        # Merge kwargs into arguments, excluding agent context params
        for key, value in kwargs.items():
            if not key.startswith("_"):  # Skip agent context params
                arguments[key] = value
        
        pattern = arguments.get('pattern')
        if not pattern:
            return {
                "error": "'pattern' argument is required.",
                "pattern": None,
                "search_type": None,
                "results": []
            }
        
        search_type = arguments.get('search_type', 'name')
        file_types = arguments.get('file_types', [])
        max_results = arguments.get('max_results', 100)
        ignore_case = arguments.get('ignore_case', True)
        search_path = arguments.get('search_path', '.')
        
        # Validate parameters
        max_results = max(1, min(1000, max_results))
        
        if search_type not in ['name', 'content']:
            return {
                "error": f"Invalid search_type '{search_type}'. Must be 'name' or 'content'.",
                "pattern": pattern,
                "search_type": search_type,
                "results": []
            }
        
        path_manager = PathManager.get_instance()
        
        # Resolve search path
        if search_path == '.':
            base_path = Path(path_manager.workspace_path)
        else:
            base_path = Path(path_manager.workspace_path) / search_path
        
        base_path = base_path.resolve()
        
        # Validate path is within workspace
        if not path_manager.is_path_within_workspace(base_path):
            raise FileRestrictionError(f"Access denied. Search path '{search_path}' is outside the workspace directory.")
        
        if not base_path.exists():
            return {
                "error": f"Search path '{search_path}' does not exist.",
                "pattern": pattern,
                "search_type": search_type,
                "search_path": search_path,
                "results": []
            }
        
        if not base_path.is_dir():
            return {
                "error": f"Search path '{search_path}' is not a directory.",
                "pattern": pattern,
                "search_type": search_type,
                "search_path": search_path,
                "results": []
            }
        
        try:
            if search_type == 'name':
                results = self._search_by_name(base_path, pattern, file_types, max_results, ignore_case)
            else:
                results = self._search_by_content(base_path, pattern, file_types, max_results, ignore_case)
            
            # Format results as structured data
            workspace_path = Path(path_manager.workspace_path)
            formatted_results = []
            
            for file_path in results:
                rel_path = os.path.relpath(file_path, workspace_path)
                stat = file_path.stat()
                formatted_results.append({
                    "path": rel_path,
                    "absolute_path": str(file_path),
                    "size": stat.st_size,
                    "type": "file"
                })
            
            return {
                "pattern": pattern,
                "search_type": search_type,
                "search_path": search_path,
                "file_types": file_types,
                "ignore_case": ignore_case,
                "total_matches": len(results),
                "max_results": max_results,
                "truncated": len(results) == max_results,
                "results": formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return {
                "error": f"Error searching files: {str(e)}",
                "pattern": pattern,
                "search_type": search_type,
                "results": []
            }
    
    def _search_by_name(self, base_path: Path, pattern: str, file_types: List[str], 
                       max_results: int, ignore_case: bool) -> List[Path]:
        """Search for files by name pattern."""
        results = []
        
        # Convert pattern to lowercase if ignoring case
        if ignore_case:
            pattern = pattern.lower()
        
        # Walk through directory tree
        for root, dirs, files in os.walk(base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                # Check file type filter
                if file_types:
                    ext = os.path.splitext(filename)[1]
                    if ext not in file_types:
                        continue
                
                # Match pattern
                match_name = filename.lower() if ignore_case else filename
                if fnmatch.fnmatch(match_name, pattern):
                    results.append(Path(root) / filename)
                    
                    if len(results) >= max_results:
                        return results
        
        return results
    
    def _search_by_content(self, base_path: Path, pattern: str, file_types: List[str],
                          max_results: int, ignore_case: bool) -> List[Path]:
        """Search for files by content pattern."""
        results = []
        
        # Compile regex pattern
        try:
            flags = re.IGNORECASE if ignore_case else 0
            regex = re.compile(pattern, flags)
        except re.error as e:
            # If pattern is not valid regex, escape it and search as literal
            escaped_pattern = re.escape(pattern)
            flags = re.IGNORECASE if ignore_case else 0
            regex = re.compile(escaped_pattern, flags)
        
        # Walk through directory tree
        for root, dirs, files in os.walk(base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                # Check file type filter
                if file_types:
                    ext = os.path.splitext(filename)[1]
                    if ext not in file_types:
                        continue
                
                file_path = Path(root) / filename
                
                # Try to read file content
                try:
                    # Skip binary files
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if regex.search(content):
                        results.append(file_path)
                        
                        if len(results) >= max_results:
                            return results
                            
                except (UnicodeDecodeError, PermissionError, IOError):
                    # Skip files that can't be read as text
                    continue
        
        return results