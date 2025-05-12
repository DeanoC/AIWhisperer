import subprocess
import logging
from typing import Dict, Any, Optional

from .base_tool import AITool

logger = logging.getLogger(__name__)

class ExecuteCommandTool(AITool):
    """
    A tool to execute shell commands on the system.
    """

    @property
    def name(self) -> str:
        return "execute_command"

    @property
    def description(self) -> str:
        return "Executes a CLI command on the system."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The CLI command to execute."
                },
                "cwd": {
                    "type": "string",
                    "description": "The working directory to execute the command in (optional).",
                    "default": "."
                }
            },
            "required": ["command"]
        }

    @property
    def category(self) -> Optional[str]:
        return "System"

    @property
    def tags(self) -> list[str]:
        return ["cli", "command", "execute", "system"]

    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'execute_command' tool to run CLI commands.
        Parameters:
        - command (string, required): The command to execute.
        - cwd (string, optional): The working directory. Defaults to the current workspace directory.
        Returns: A dictionary with 'stdout', 'stderr', and 'returncode'.
        """

    async def execute(self, command: str, cwd: str = ".") -> Dict[str, Any]:
        """
        Executes a shell command and returns the output, error, and return code.
        """
        logger.info(f"Executing command: {command} in directory: {cwd}")
        try:
            # Use shell=True for simplicity with complex commands, but be mindful of security if command comes from untrusted source.
            # In this context, the command comes from the AI model, which is part of the trusted system.
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True, # Capture stdout/stderr as text
                cwd=cwd,
                check=False # Don't raise exception for non-zero exit codes
            )
            logger.info(f"Command execution finished with return code: {result.returncode}")
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except FileNotFoundError:
            logger.error(f"Command not found: {command}")
            return {
                "stdout": "",
                "stderr": f"Error: Command not found: {command}",
                "returncode": 127 # Common return code for command not found
            }
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                "stdout": "",
                "stderr": f"Error executing command: {e}",
                "returncode": 1 # Generic error code
            }