# Plan to Document `execute_command` Tool

1.  **Locate Insertion Point:**
    *   The new documentation for `execute_command` will be added as a new section in `docs/tool_interface_design.md`.
    *   It will be inserted after the existing "8. Example: `ReadFileTool`" section and before the "9. Conclusion" section.
    *   The new section will be titled "9. Example: `ExecuteCommandTool`".
    *   The existing "9. Conclusion" section will be renumbered to "10. Conclusion".

2.  **Content for the New Section (9. Example: `ExecuteCommandTool`):**
    The content will mirror the style and structure of the `ReadFileTool` example, using information primarily from the source code (`src/ai_whisperer/tools/execute_command_tool.py`) for accuracy regarding the implemented features, and enhancing descriptions for clarity as done in the `ReadFileTool` example.

    ```markdown
    ## 9. Example: `ExecuteCommandTool`

    Here's a conceptual example of an `ExecuteCommandTool`:

    ```python
    import subprocess
    import logging
    from typing import Dict, Any, Optional

    # Assuming AITool is defined as above in a shared module
    # from aiwhisperer.tools.base import AITool

    logger = logging.getLogger(__name__) # Assuming logger is configured

    class ExecuteCommandTool(AITool):
        @property
        def name(self) -> str:
            return "execute_command"

        @property
        def description(self) -> str:
            # Using a more descriptive version for the documentation,
            # aligned with the tool's capabilities.
            return "Executes a system command and returns its standard output, standard error, and return code. Allows specifying a working directory."

        @property
        def parameters_schema(self) -> Dict[str, Any]:
            return {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The CLI command to execute (e.g., \"python script.py --arg\", \"ls -l\")."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "The working directory to execute the command in. Defaults to the AIWhisperer's current workspace directory if not specified.",
                        "default": "." # As per implementation
                    }
                },
                "required": ["command"]
            }

        # category and tags can be included as per source if desired for completeness in this example
        # @property
        # def category(self) -> Optional[str]:
        #     return "System"
        #
        # @property
        # def tags(self) -> list[str]:
        #     return ["cli", "command", "execute", "system"]

        def get_ai_prompt_instructions(self) -> str:
            return """**Tool: `execute_command`**
    *   **Description:** Executes a CLI command on the system and returns its standard output, standard error, and return code.
    *   **Purpose:** Use this tool when you need to run an external program, script, or shell command on the system. This is useful for tasks like compiling code, running scripts (e.g., Python, shell), executing utility commands, or performing automated tasks that involve command-line operations. The command is executed using `shell=True` internally, so shell-specific features like pipes (`|`) or complex redirection (`>>`) within the command string are supported.
    *   **Parameters:**
        *   `command` (string, required): The complete command string to execute (e.g., "python my_script.py --arg1 value1", "ls -l /tmp", "grep 'error' logs.txt | wc -l").
        *   `cwd` (string, optional, default: '.'): The working directory from which to execute the command. If not specified, it defaults to the current workspace directory of the AIWhisperer application.
    *   **Expected Output:** A dictionary containing:
        *   `stdout` (string): The standard output (stdout) captured from the command.
        *   `stderr` (string): The standard error (stderr) captured from the command.
        *   `returncode` (integer): The exit status code of the command. `0` typically indicates success. Non-zero codes usually indicate an error or specific status.
    *   **Example (for AI to understand usage):**
        If you need to list files in the 'src' directory:
        Call: `execute_command` with `command="ls -l src"`
        If you need to run a Python script 'data_processor.py' with an argument, and the script is in a 'scripts' subdirectory:
        Call: `execute_command` with `command="python data_processor.py --input data.csv"`, `cwd="scripts"`
        If you need to find all Python files in the current directory and its subdirectories, then count them:
        Call: `execute_command` with `command="find . -name '*.py' | wc -l"`"""

        async def execute(self, command: str, cwd: str = ".") -> Dict[str, Any]:
            """
            Executes a shell command and returns the output, error, and return code.
            Note: This example uses subprocess.run for simplicity. The actual tool might use asyncio.create_subprocess_exec.
            """
            logger.info(f"Executing command: {command} in directory: {cwd}")
            try:
                # The actual implementation uses shell=True, which is important for how commands are formed.
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    check=False # Do not raise exception for non-zero exit codes
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

        # get_openrouter_tool_definition can be inherited if the base class provides a suitable default.
        def get_openrouter_tool_definition(self) -> Dict[str, Any]:
            return super().get_openrouter_tool_definition()

    ```
    ```

3.  **Update Conclusion Section Numbering:**
    *   Change the heading "9. Conclusion" to "10. Conclusion".