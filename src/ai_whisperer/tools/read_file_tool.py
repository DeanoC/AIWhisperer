import os
from typing import Dict, Any

from src.ai_whisperer.tools.base_tool import AITool

class ReadFileTool(AITool):
    @property
    def name(self) -> str:
        return 'read_text_file'

    @property
    def description(self) -> str:
        return 'Reads the content of a specified text file.'

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The path to the text file to read.'
                }
            },
            'required': ['file_path']
        }

    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the `read_text_file` tool to read the content of a text file.
        Provide the file path as the `file_path` parameter.
        Ensure the file path is within the project directory and is a text file.
        """

    def execute(self, arguments: Dict[str, Any]) -> str:
        file_path = arguments.get('file_path')
        if not file_path:
            return "Error: 'file_path' argument is missing."

        # Assume file_path is relative to the project directory
        project_dir = os.path.abspath('.')
        abs_file_path = os.path.join(project_dir, file_path)

        # Basic check for common text file extensions
        text_extensions = ['.txt', '.md', '.py', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.js', '.csv']
        if not any(abs_file_path.lower().endswith(ext) for ext in text_extensions):
             return f"Error: File type not supported. Only text files are allowed."

        # Further validation to prevent reading outside the project directory
        # after joining the paths. This handles cases like '../' in the input.
        if not os.path.abspath(abs_file_path).startswith(project_dir):
             return f"Error: Access denied. File path '{file_path}' resolves outside the project directory."

        try:
            with open(abs_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            return f"Error: File not found at '{file_path}'."
        except PermissionError:
            return f"Error: Permission denied to read file at '{file_path}'."
        except Exception as e:
            return f"Error reading file '{file_path}': {e}"