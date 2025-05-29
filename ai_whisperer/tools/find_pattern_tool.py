"""Tool for finding patterns in files using regex, similar to grep."""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class FindPatternTool(AITool):
    """Tool for searching files for regex patterns with context lines."""
    
    def __init__(self, path_manager: PathManager):
        """Initialize the find pattern tool.
        
        Args:
            path_manager: PathManager instance for validating and resolving paths
        """
        self.path_manager = path_manager
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    @property
    def name(self) -> str:
        return "find_pattern"
        
    @property
    def description(self) -> str:
        return "Search for regex patterns in files with context lines"
        
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern to search for"
                },
                "path": {
                    "type": "string", 
                    "description": "File or directory path to search in (default: workspace root)",
                    "default": "."
                },
                "file_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file extensions to include (e.g., ['.py', '.js'])",
                    "default": []
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines before and after matches",
                    "default": 0,
                    "minimum": 0,
                    "maximum": 10
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matches to return",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether the search is case sensitive",
                    "default": True
                },
                "whole_word": {
                    "type": "boolean",
                    "description": "Match whole words only",
                    "default": False
                },
                "exclude_dirs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Directory names to exclude from search",
                    "default": [".git", "__pycache__", "node_modules", ".venv", "venv"]
                }
            },
            "required": ["pattern"]
        }
        
    @property
    def tags(self) -> List[str]:
        return ["filesystem", "file_search", "analysis", "pattern_matching"]
        
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for AI on how to use this tool."""
        return """Use the find_pattern tool to search for regex patterns in files.
        
Examples:
- Find all function definitions: pattern="def \\w+\\("
- Find imports: pattern="^import|^from"
- Find TODO comments: pattern="TODO|FIXME"
- Find specific words (case insensitive): pattern="error", case_sensitive=false
- Find whole words only: pattern="test", whole_word=true

You can specify context lines to see surrounding code, limit file types,
and exclude directories like .git or node_modules."""
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the pattern search.
        
        Returns:
            Dict containing:
                - matches: List of match results
                - total_matches: Total number of matches found
                - files_searched: Number of files searched
                - truncated: Whether results were truncated
        """
        try:
            # Extract parameters
            pattern = kwargs["pattern"]
            path = kwargs.get("path", ".")
            file_types = kwargs.get("file_types", [])
            context_lines = kwargs.get("context_lines", 0)
            max_results = kwargs.get("max_results", 100)
            case_sensitive = kwargs.get("case_sensitive", True)
            whole_word = kwargs.get("whole_word", False)
            exclude_dirs = set(kwargs.get("exclude_dirs", [".git", "__pycache__", "node_modules", ".venv", "venv"]))
            
            # Compile regex pattern
            regex_flags = 0 if case_sensitive else re.IGNORECASE
            if whole_word:
                pattern = r'\b' + pattern + r'\b'
                
            try:
                compiled_pattern = re.compile(pattern, regex_flags)
            except re.error as e:
                return {
                    "error": f"Invalid regex pattern: {e}",
                    "matches": [],
                    "total_matches": 0,
                    "files_searched": 0
                }
                
            # Resolve path
            if path == ".":
                # Use workspace path for current directory
                search_path = self.path_manager.workspace_path or Path.cwd()
            else:
                resolved_path = self.path_manager.resolve_path(path)
                search_path = Path(resolved_path)
                # If it's a relative path, make it relative to workspace
                if not search_path.is_absolute():
                    search_path = (self.path_manager.workspace_path or Path.cwd()) / search_path
            
            if not search_path.exists():
                return {
                    "error": f"Path not found: {path}",
                    "matches": [],
                    "total_matches": 0,
                    "files_searched": 0
                }
                
            # Collect files to search
            files_to_search = []
            if search_path.is_file():
                files_to_search = [search_path]
            else:
                files_to_search = self._collect_files(search_path, file_types, exclude_dirs)
                
            # Search files
            matches = []
            total_matches = 0
            files_searched = 0
            
            for file_path in files_to_search:
                if total_matches >= max_results:
                    break
                    
                file_matches = self._search_file(
                    file_path, 
                    compiled_pattern,
                    context_lines,
                    max_results - total_matches
                )
                
                if file_matches:
                    files_searched += 1
                    for match in file_matches:
                        matches.append(match)
                        total_matches += 1
                        if total_matches >= max_results:
                            break
                            
            # Calculate relative paths for results
            workspace_path = self.path_manager.workspace_path or Path.cwd()
            for match in matches:
                try:
                    match["relative_path"] = str(Path(match["file"]).relative_to(workspace_path))
                except ValueError:
                    match["relative_path"] = match["file"]
                    
            return {
                "matches": matches,
                "total_matches": total_matches,
                "files_searched": files_searched,
                "truncated": total_matches >= max_results,
                "pattern": pattern,
                "case_sensitive": case_sensitive,
                "whole_word": whole_word
            }
            
        except Exception as e:
            logger.error(f"Error in find_pattern: {e}")
            return {
                "error": str(e),
                "matches": [],
                "total_matches": 0,
                "files_searched": 0
            }
            
    def _collect_files(self, directory: Path, file_types: List[str], 
                      exclude_dirs: set) -> List[Path]:
        """Collect files to search, respecting filters.
        
        Args:
            directory: Directory to search in
            file_types: List of file extensions to include
            exclude_dirs: Set of directory names to exclude
            
        Returns:
            List of file paths to search
        """
        files = []
        
        try:
            for item in directory.rglob("*"):
                # Skip excluded directories
                if any(part in exclude_dirs for part in item.parts):
                    continue
                    
                if item.is_file():
                    # Apply file type filter if specified
                    if file_types:
                        if item.suffix.lower() in file_types:
                            files.append(item)
                    else:
                        # Only search text files if no filter specified
                        if self._is_text_file(item):
                            files.append(item)
                            
        except Exception as e:
            logger.warning(f"Error collecting files in {directory}: {e}")
            
        return files
        
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file is likely a text file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is likely text
        """
        text_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h', 
            '.hpp', '.cs', '.rb', '.go', '.rs', '.php', '.swift', '.kt', '.scala',
            '.r', '.R', '.m', '.lua', '.pl', '.sh', '.bash', '.zsh', '.fish',
            '.ps1', '.bat', '.cmd', '.vb', '.sql', '.html', '.htm', '.xml', 
            '.css', '.scss', '.sass', '.less', '.json', '.yaml', '.yml', '.toml',
            '.ini', '.cfg', '.conf', '.config', '.properties', '.env', '.gitignore',
            '.dockerignore', '.editorconfig', '.eslintrc', '.prettierrc', '.md',
            '.markdown', '.rst', '.txt', '.log', '.csv', '.tsv'
        }
        
        return file_path.suffix.lower() in text_extensions
        
    def _search_file(self, file_path: Path, pattern: re.Pattern,
                    context_lines: int, max_matches: int) -> List[Dict[str, Any]]:
        """Search a single file for pattern matches.
        
        Args:
            file_path: File to search
            pattern: Compiled regex pattern
            context_lines: Number of context lines
            max_matches: Maximum matches to return from this file
            
        Returns:
            List of match dictionaries
        """
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                if len(matches) >= max_matches:
                    break
                    
                match = pattern.search(line)
                if match:
                    # Get context lines
                    start_idx = max(0, i - context_lines)
                    end_idx = min(len(lines), i + context_lines + 1)
                    
                    context_before = []
                    context_after = []
                    
                    if context_lines > 0:
                        context_before = [
                            {
                                "line_number": j + 1,
                                "content": lines[j].rstrip()
                            }
                            for j in range(start_idx, i)
                        ]
                        
                        context_after = [
                            {
                                "line_number": j + 1,
                                "content": lines[j].rstrip()
                            }
                            for j in range(i + 1, end_idx)
                        ]
                        
                    matches.append({
                        "file": str(file_path),
                        "line_number": i + 1,
                        "line": line.rstrip(),
                        "match_start": match.start(),
                        "match_end": match.end(),
                        "matched_text": match.group(0),
                        "context_before": context_before,
                        "context_after": context_after
                    })
                    
        except Exception as e:
            logger.debug(f"Error searching file {file_path}: {e}")
            
        return matches