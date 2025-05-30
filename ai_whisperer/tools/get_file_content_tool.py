"""
Get File Content Tool - Read file content with advanced options
"""
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager
from ai_whisperer.exceptions import FileRestrictionError

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
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the file content reading."""
        file_path_str = arguments.get('path')
        start_line = arguments.get('start_line')
        end_line = arguments.get('end_line')
        preview_only = arguments.get('preview_only', False)
        
        if not file_path_str:
            return "Error: 'path' argument is required."
        
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
            return f"Error: File '{file_path_str}' does not exist."
        
        # Check if it's a file
        if not abs_file_path.is_file():
            return f"Error: Path '{file_path_str}' is not a file."
        
        try:
            # Get file metadata
            file_size = abs_file_path.stat().st_size
            
            # Check if file is likely binary
            if self._is_binary_file(abs_file_path):
                return f"Error: File '{file_path_str}' appears to be a binary file. Use appropriate tools for binary files."
            
            # Read file content
            with open(abs_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Handle preview mode
            if preview_only:
                preview_lines = lines[:200]
                content = self._format_lines_with_numbers(preview_lines, 1)
                
                # Add metadata
                rel_path = os.path.relpath(abs_file_path, workspace_path)
                metadata = [
                    f"File: {rel_path}",
                    f"Total lines: {total_lines}",
                    f"File size: {self._format_size(file_size)}",
                    f"Preview: First 200 lines" if total_lines > 200 else "Preview: Complete file",
                    "-" * 50
                ]
                
                return "\n".join(metadata) + "\n" + content
            
            # Handle line range
            if start_line is not None or end_line is not None:
                # Validate line numbers
                if start_line is not None and start_line > total_lines:
                    return f"Error: start_line ({start_line}) exceeds total lines ({total_lines})."
                
                if end_line is not None and end_line > total_lines:
                    end_line = total_lines
                
                # Convert to 0-based indexing
                start_idx = (start_line - 1) if start_line is not None else 0
                end_idx = end_line if end_line is not None else total_lines
                
                # Ensure valid range
                start_idx = max(0, start_idx)
                end_idx = min(total_lines, end_idx)
                
                if start_idx >= end_idx:
                    return f"Error: Invalid line range. start_line ({start_line}) must be less than end_line ({end_line})."
                
                selected_lines = lines[start_idx:end_idx]
                content = self._format_lines_with_numbers(selected_lines, start_idx + 1)
                
                # Add range info
                rel_path = os.path.relpath(abs_file_path, workspace_path)
                header = f"File: {rel_path} (lines {start_idx + 1}-{end_idx} of {total_lines})\n" + "-" * 50
                
                return header + "\n" + content
            
            # Return full content with line numbers
            content = self._format_lines_with_numbers(lines, 1)
            rel_path = os.path.relpath(abs_file_path, workspace_path)
            header = f"File: {rel_path} ({total_lines} lines)\n" + "-" * 50
            
            return header + "\n" + content
            
        except UnicodeDecodeError:
            return f"Error: Unable to decode file '{file_path_str}'. The file may be binary or use a different encoding."
        except PermissionError:
            return f"Error: Permission denied to read file '{file_path_str}'."
        except Exception as e:
            logger.error(f"Error reading file '{file_path_str}': {e}")
            return f"Error reading file '{file_path_str}': {str(e)}"
    
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