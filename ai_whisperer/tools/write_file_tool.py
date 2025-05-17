import logging
import pathlib
from typing import Any, Dict

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.delegate_manager import DelegateManager
from user_message_delegate import UserMessageLevel
from ai_whisperer.path_management import PathManager
from ai_whisperer.exceptions import FileRestrictionError

logger = logging.getLogger(__name__)

class WriteFileTool(AITool):
    @property
    def name(self) -> str:
        return "write_to_file"

    @property
    def description(self) -> str:
        return "Writes content to a specified file path within the output directory. Overwrites the file if it exists. Creates parent directories if they do not exist."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to write (relative to the output directory)."
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file."
                },
                "line_count": {
                    "type": "integer",
                    "description": "The total number of lines in the file after writing.",
                    "nullable": True
                }
            },
            "required": ["path", "content"]
        }

    def execute(self, path: str, content: str, line_count: int = None) -> Dict[str, Any]:
        """
        Writes the provided content to the specified file path.

        Args:
            path: The path to the file to write (relative to the output directory).
            content: The content to write to the file.
            line_count: The total number of lines in the file after writing (optional).

        Returns:
            A dictionary indicating success or failure, including the resolved file path on success.
        """

        if not path:
            return {"status": "error", "message": "'path' argument is missing."}
        if content is None:
            return {"status": "error", "message": "'content' argument is missing."}

        path_manager = PathManager.get_instance()
        # Normalize the path: if absolute, use as-is; if the first part matches output dir name, strip it; else, join to output_path
        input_path = pathlib.Path(path)
        output_dir = pathlib.Path(path_manager.output_path)
        if input_path.is_absolute():
            abs_file_path = input_path.resolve()
        else:
            input_parts = input_path.parts
            output_dir_name = output_dir.name
            if input_parts and input_parts[0] == output_dir_name:
                input_path = pathlib.Path(*input_parts[1:])
            abs_file_path = (output_dir / input_path).resolve()
        logger.info(f"[WriteFileTool] Writing file. path arg: '{path}', resolved: '{abs_file_path}', output_dir: '{output_dir}'")

        # Validate if the file path is within the output directory
        if not path_manager.is_path_within_output(abs_file_path):
            raise FileRestrictionError(f"Access denied. File path '{path}' is outside the allowed output directory.")
        try:
            # Ensure the parent directory exists
            parent_dir = abs_file_path.parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured parent directory exists for {path}: {parent_dir}")

            with open(abs_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Successfully wrote content to {abs_file_path}")
            return {"status": "success", "message": f"Content successfully written to {abs_file_path}", "resolved_path": str(abs_file_path)}
        except FileRestrictionError as e:
            logger.error(f"File restriction error writing to file {path}: {e}")
            return {"status": "error", "message": f"Error writing to file {path}: {e}"}
        except IOError as e:
            logger.error(f"IO error writing to file {path}: {e}")
            return {"status": "error", "message": f"Error writing to file {path}: {e}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred while writing to {path}: {type(e).__name__} - {e}")
            return {"status": "error", "message": f"An unexpected error occurred while writing to {path}: {type(e).__name__} - {e}"}

    def get_ai_prompt_instructions(self) -> str:
        """
        Returns instructions for the AI on how to use this tool.
        """
        return """
        Use the 'write_to_file' tool to write content to a file within the output directory.
        This tool is useful for creating new files or overwriting existing ones with specific content.
        Provide the 'path' parameter with the desired path to the file (relative to the output directory).
        Provide the 'content' parameter with the exact content you want to write into the file.
        Optionally, provide 'line_count' with the total number of lines in the file.
        Ensure the file path is within the output directory.
        Example usage:
        <tool_code>
        write_to_file(path='my_output.txt', content='Generated report data.', line_count=1)
        </tool_code>
        """