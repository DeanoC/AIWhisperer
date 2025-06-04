"""Read File Tool - Reads file contents with structured output."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager
from ai_whisperer.core.exceptions import FileRestrictionError

logger = logging.getLogger(__name__)


class ReadFileTool(AITool):
    """Tool for reading file contents with structured output."""

    @property
    def name(self) -> str:
        return 'read_file'

    @property
    def description(self) -> str:
        return 'Reads the content of a specified file within the workspace directory.'

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the file to read (relative to the workspace directory).'
                },
                'start_line': {
                    'type': 'integer',
                    'description': 'The starting line number to read from (1-based).',
                    'nullable': True
                },
                'end_line': {
                    'type': 'integer',
                    'description': 'The ending line number to read to (1-based, inclusive).',
                    'nullable': True
                }
            },
            'required': ['path']
        }

    @property
    def category(self) -> Optional[str]:
        return "File System"

    @property
    def tags(self) -> List[str]:
        return ["filesystem", "file_read", "analysis"]

    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'read_file' tool to read the content of text files in the workspace.
        Parameters:
        - path (string, required): File path relative to workspace root
        - start_line (integer, optional): Starting line number (1-based)
        - end_line (integer, optional): Ending line number (1-based, inclusive)
        
        Returns structured data with file content and metadata.
        Example usage:
        <tool_code>
        read_file(path='README.md', start_line=1, end_line=50)
        </tool_code>
        """

    def execute(self, arguments: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute file reading and return structured data."""
        # Handle both arguments dict and kwargs patterns
        if arguments is None:
            arguments = {}
        
        # Merge kwargs into arguments, excluding agent context params
        for key, value in kwargs.items():
            if not key.startswith("_"):  # Skip agent context params
                arguments[key] = value
        
        file_path_str = arguments.get('path')
        start_line = arguments.get('start_line')
        end_line = arguments.get('end_line')

        if not file_path_str:
            return {
                "error": "'path' argument is missing.",
                "path": None,
                "content": None,
                "lines": []
            }

        path_manager = PathManager.get_instance()
        
        # Handle both absolute and relative paths
        file_path = Path(file_path_str)
        if file_path.is_absolute():
            abs_file_path = file_path
        else:
            abs_file_path = Path(path_manager.workspace_path) / file_path
        
        abs_file_path = abs_file_path.resolve()

        # Validate if the file path is within the workspace
        if not path_manager.is_path_within_workspace(abs_file_path):
            return {
                "error": f"Access denied. File path '{file_path_str}' is outside the workspace directory.",
                "path": file_path_str,
                "content": None,
                "lines": []
            }

        try:
            # Check if file exists
            if not abs_file_path.exists():
                return {
                    "error": f"File not found: '{file_path_str}'",
                    "path": file_path_str,
                    "content": None,
                    "lines": []
                }
            
            # Check if it's a file
            if not abs_file_path.is_file():
                return {
                    "error": f"Path is not a file: '{file_path_str}'",
                    "path": file_path_str,
                    "content": None,
                    "lines": []
                }
            
            # Read the file
            with open(abs_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Get file info
            stat = abs_file_path.stat()
            total_lines = len(lines)
            
            # Adjust for 0-based indexing
            start_index = start_line - 1 if start_line is not None and start_line > 0 else 0
            end_index = end_line if end_line is not None and end_line > 0 else total_lines

            # Ensure indices are within bounds
            start_index = max(0, start_index)
            end_index = min(total_lines, end_index)

            # Get the requested lines
            if start_line is not None or end_line is not None:
                content_lines = lines[start_index:end_index]
                actual_start = start_index + 1
                actual_end = end_index
            else:
                content_lines = lines
                actual_start = 1
                actual_end = total_lines

            # Format lines with line numbers
            formatted_lines = []
            for i, line in enumerate(content_lines):
                line_number = start_index + i + 1
                formatted_lines.append({
                    "line_number": line_number,
                    "content": line.rstrip('\n')  # Remove trailing newline
                })

            # Also provide raw content for convenience
            raw_content = ''.join(content_lines)

            return {
                "path": file_path_str,
                "absolute_path": str(abs_file_path),
                "exists": True,
                "size": stat.st_size,
                "total_lines": total_lines,
                "range": {
                    "start": actual_start,
                    "end": actual_end,
                    "lines_read": len(content_lines)
                },
                "content": raw_content,
                "lines": formatted_lines
            }

        except PermissionError:
            return {
                "error": f"Permission denied to read file '{file_path_str}'.",
                "path": file_path_str,
                "content": None,
                "lines": []
            }
        except UnicodeDecodeError:
            return {
                "error": f"File '{file_path_str}' is not a text file or has encoding issues.",
                "path": file_path_str,
                "content": None,
                "lines": []
            }
        except Exception as e:
            logger.error(f"Error reading file '{file_path_str}': {e}")
            return {
                "error": f"Error reading file: {str(e)}",
                "path": file_path_str,
                "content": None,
                "lines": []
            }