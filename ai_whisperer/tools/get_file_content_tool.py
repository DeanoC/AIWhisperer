"""
Module: ai_whisperer/tools/get_file_content_tool.py
Purpose: AI tool implementation for get file content

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- GetFileContentTool: Tool for reading file content with advanced options like preview mode and line ranges.

Usage:
    tool = GetFileContentTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

Related:
- See docs/file-browser-consolidated-implementation.md
- See docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
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


class GetFileContentTool(AITool):
    """Tool for reading file content with advanced options like preview mode and line ranges."""
    
    @property
    def name(self) -> str:
        return "get_file_content"
    
    @property
    def description(self) -> str:
        return "Read file content with advanced options including line ranges and preview mode."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read (relative to workspace directory)."
                },
                "start_line": {
                    "type": "integer",
                    "description": "The starting line number to read from (1-based).",
                    "minimum": 1,
                    "nullable": True
                },
                "end_line": {
                    "type": "integer",
                    "description": "The ending line number to read to (1-based, inclusive).",
                    "minimum": 1,
                    "nullable": True
                },
                "preview_only": {
                    "type": "boolean",
                    "description": "If true, returns only the first 200 lines with metadata about the full file.",
                    "default": False
                }
            },
            "required": ["path"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "File System"
    
    @property
    def tags(self) -> List[str]:
        return ["filesystem", "file_read", "analysis"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'get_file_content' tool to read file contents with advanced options.
        Parameters:
        - path (string, required): File path relative to workspace
        - start_line (integer, optional): Starting line number (1-based)
        - end_line (integer, optional): Ending line number (1-based, inclusive)
        - preview_only (boolean, optional): Returns first 200 lines with file metadata
        
        This tool provides more control than 'read_file' for handling large files.
        Example usage:
        <tool_code>
        get_file_content(path='src/main.py', preview_only=True)
        get_file_content(path='src/utils.py', start_line=50, end_line=100)
        </tool_code>
        """
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the file content reading."""
        file_path_str = arguments.get('path')
        start_line = arguments.get('start_line')
        end_line = arguments.get('end_line')
        preview_only = arguments.get('preview_only', False)
        
        if not file_path_str:
            return {
                "error": "'path' argument is required.",
                "path": None,
                "content": None,
                "lines": []
            }
        
        path_manager = PathManager.get_instance()
        
        # Resolve path relative to workspace
        workspace_path = Path(path_manager.workspace_path)
        if os.path.isabs(file_path_str):
            abs_file_path = Path(file_path_str)
        else:
            abs_file_path = workspace_path / file_path_str
        
        abs_file_path = abs_file_path.resolve()
        
        # Validate path is within workspace
        if not path_manager.is_path_within_workspace(abs_file_path):
            raise FileRestrictionError(f"Access denied. File path '{file_path_str}' is outside the workspace directory.")
        
        # Check if file exists
        if not abs_file_path.exists():
            return {
                "error": f"File '{file_path_str}' does not exist.",
                "path": file_path_str,
                "content": None,
                "lines": []
            }
        
        # Check if it's a file
        if not abs_file_path.is_file():
            return {
                "error": f"Path '{file_path_str}' is not a file.",
                "path": file_path_str,
                "content": None,
                "lines": []
            }
        
        try:
            # Get file metadata
            file_size = abs_file_path.stat().st_size
            
            # Check if file is likely binary
            if self._is_binary_file(abs_file_path):
                return {
                    "error": f"File '{file_path_str}' appears to be a binary file. Use appropriate tools for binary files.",
                    "path": file_path_str,
                    "content": None,
                    "lines": [],
                    "is_binary": True
                }
            
            # Read file content
            with open(abs_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Handle preview mode
            if preview_only:
                preview_lines = lines[:200]
                formatted_lines = [
                    {
                        "line_number": i + 1,
                        "content": line.rstrip('\n')
                    }
                    for i, line in enumerate(preview_lines)
                ]
                
                rel_path = os.path.relpath(abs_file_path, workspace_path)
                
                return {
                    "path": file_path_str,
                    "absolute_path": str(abs_file_path),
                    "relative_path": rel_path,
                    "exists": True,
                    "size": file_size,
                    "size_formatted": self._format_size(file_size),
                    "total_lines": total_lines,
                    "preview_mode": True,
                    "preview_lines": len(preview_lines),
                    "truncated": total_lines > 200,
                    "content": ''.join(preview_lines),
                    "lines": formatted_lines
                }
            
            # Handle line range
            if start_line is not None or end_line is not None:
                # Validate line numbers
                if start_line is not None and start_line > total_lines:
                    return {
                        "error": f"start_line ({start_line}) exceeds total lines ({total_lines}).",
                        "path": file_path_str,
                        "content": None,
                        "lines": [],
                        "total_lines": total_lines
                    }
                
                if end_line is not None and end_line > total_lines:
                    end_line = total_lines
                
                # Convert to 0-based indexing
                start_idx = (start_line - 1) if start_line is not None else 0
                end_idx = end_line if end_line is not None else total_lines
                
                # Ensure valid range
                start_idx = max(0, start_idx)
                end_idx = min(total_lines, end_idx)
                
                if start_idx >= end_idx:
                    return {
                        "error": f"Invalid line range. start_line ({start_line}) must be less than end_line ({end_line}).",
                        "path": file_path_str,
                        "content": None,
                        "lines": []
                    }
                
                selected_lines = lines[start_idx:end_idx]
                formatted_lines = [
                    {
                        "line_number": start_idx + i + 1,
                        "content": line.rstrip('\n')
                    }
                    for i, line in enumerate(selected_lines)
                ]
                
                rel_path = os.path.relpath(abs_file_path, workspace_path)
                
                return {
                    "path": file_path_str,
                    "absolute_path": str(abs_file_path),
                    "relative_path": rel_path,
                    "exists": True,
                    "size": file_size,
                    "size_formatted": self._format_size(file_size),
                    "total_lines": total_lines,
                    "range": {
                        "start": start_idx + 1,
                        "end": end_idx,
                        "lines_read": len(selected_lines)
                    },
                    "content": ''.join(selected_lines),
                    "lines": formatted_lines
                }
            
            # Return full content
            formatted_lines = [
                {
                    "line_number": i + 1,
                    "content": line.rstrip('\n')
                }
                for i, line in enumerate(lines)
            ]
            
            rel_path = os.path.relpath(abs_file_path, workspace_path)
            
            return {
                "path": file_path_str,
                "absolute_path": str(abs_file_path),
                "relative_path": rel_path,
                "exists": True,
                "size": file_size,
                "size_formatted": self._format_size(file_size),
                "total_lines": total_lines,
                "content": ''.join(lines),
                "lines": formatted_lines
            }
            
        except UnicodeDecodeError:
            return {
                "error": f"Unable to decode file '{file_path_str}'. The file may be binary or use a different encoding.",
                "path": file_path_str,
                "content": None,
                "lines": [],
                "is_binary": True
            }
        except PermissionError:
            return {
                "error": f"Permission denied to read file '{file_path_str}'.",
                "path": file_path_str,
                "content": None,
                "lines": []
            }
        except Exception as e:
            logger.error(f"Error reading file '{file_path_str}': {e}")
            return {
                "error": f"Error reading file '{file_path_str}': {str(e)}",
                "path": file_path_str,
                "content": None,
                "lines": []
            }
    
    def _format_lines_with_numbers(self, lines: List[str], start_num: int) -> str:
        """Format lines with line numbers."""
        formatted_lines = []
        for i, line in enumerate(lines):
            line_num = start_num + i
            # Remove trailing newline for formatting, will be added back
            line_content = line.rstrip('\n')
            formatted_lines.append(f"{line_num:4d} | {line_content}")
        return "\n".join(formatted_lines)
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is likely binary by reading first few bytes."""
        try:
            # Try to read as text first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(512)
                return False  # If we can read as UTF-8, it's not binary
            except UnicodeDecodeError:
                pass
            
            # Fall back to binary check
            with open(file_path, 'rb') as f:
                chunk = f.read(512)
                
            # Check for null bytes
            if b'\x00' in chunk:
                return True
            
            # Check if most bytes are non-printable ASCII
            # Allow high bytes for UTF-8
            printable = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in (9, 10, 13) or byte >= 128)
            if len(chunk) > 0 and printable / len(chunk) < 0.7:
                return True
                
            return False
        except:
            return False
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{size}{unit}"
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"