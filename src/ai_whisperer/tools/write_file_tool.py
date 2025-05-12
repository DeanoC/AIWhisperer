import logging
from typing import Any, Dict

from src.ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class WriteTextFileTool(AITool):
    def __init__(self, config: Dict[str, Any] = None):
        # Configuration can be added here if needed in the future
        pass

    @property
    def name(self) -> str:
        return "write_text_file"

    @property
    def description(self) -> str:
        return "Writes text content to a specified file path. Overwrites the file if it exists. The directory containing the file must already exist."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to write. Must be a valid file path within the accessible file system. The directory must exist."
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write to the file."
                }
            },
            "required": ["file_path", "content"]
        }

    async def execute(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Writes the provided content to the specified file path.

        Args:
            file_path: The path to the file to write.
            content: The content to write to the file.

        Returns:
            A dictionary indicating success or failure.
        """
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            logger.info(f"Successfully wrote content to {file_path}")
            return {"status": "success", "message": f"Content successfully written to {file_path}"}
        except IOError as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            return {"status": "error", "message": f"Error writing to file {file_path}: {e}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred while writing to {file_path}: {e}")
            return {"status": "error", "message": f"An unexpected error occurred while writing to {file_path}: {e}"}

    def get_ai_prompt_instructions(self) -> str:
        """
        Returns instructions for the AI on how to use this tool.
        """
        return """
        Use the 'write_text_file' tool to write text content to a file.
        This tool is useful for creating new files or overwriting existing ones with specific text.
        Provide the 'file_path' parameter with the desired path to the file (e.g., 'src/my_module/my_file.txt').
        Provide the 'content' parameter with the exact text you want to write into the file.
        Ensure the directory for the file already exists before using this tool.
        Example usage:
        <tool_code>
        print(tools.write_text_file(file_path='output.txt', content='Hello, world!'))
        </tool_code>
        """