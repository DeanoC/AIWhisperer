import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager
from ai_whisperer.exceptions import FileRestrictionError

class ReadFileTool(AITool):
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
        Use the `read_file` tool to read the content of a file within the workspace directory.
        Provide the file path as the `path` parameter.
        Optionally, provide `start_line` and `end_line` to read a specific range of lines.
        Ensure the file path is within the workspace directory.
        """

    def execute(self, arguments: Dict[str, Any]) -> str:
        file_path_str = arguments.get('path')
        start_line = arguments.get('start_line')
        end_line = arguments.get('end_line')

        if not file_path_str:
            return "Error: 'path' argument is missing."

        path_manager = PathManager.get_instance()
        abs_file_path = Path(file_path_str).resolve()

        # Validate if the file path is within the workspace
        if not path_manager.is_path_within_workspace(abs_file_path):
            raise FileRestrictionError(f"Access denied. File path '{file_path_str}' is outside the workspace directory.")

        try:
            with open(abs_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Adjust for 0-based indexing
            start_index = start_line - 1 if start_line is not None and start_line > 0 else 0
            end_index = end_line if end_line is not None and end_line > 0 else len(lines)

            # Ensure indices are within bounds
            start_index = max(0, start_index)
            end_index = min(len(lines), end_index)

            # Read specific lines if start_line or end_line are provided
            if start_line is not None or end_line is not None:
                 content_lines = lines[start_index:end_index]
            else:
                 content_lines = lines # Read all lines if no range is specified

            # Format output with line numbers
            formatted_content = ""
            for i, line in enumerate(content_lines):
                original_line_number = start_index + i + 1
                formatted_content += f"{original_line_number} | {line}"

            return formatted_content.strip()

        except FileNotFoundError:
            # Re-raise FileNotFoundError so the test can catch it
            raise
        except PermissionError:
            return f"Error: Permission denied to read file at '{file_path_str}'."
        except FileRestrictionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file '{file_path_str}': {e}"