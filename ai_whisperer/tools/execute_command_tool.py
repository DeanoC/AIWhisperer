"""
Module: ai_whisperer/tools/execute_command_tool.py
Purpose: AI tool implementation for execute command

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- ExecuteCommandTool: 

Usage:
    tool = ExecuteCommandTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- subprocess
- base_tool

"""

import subprocess
import logging
import sys
from typing import Dict, Any, Optional, List

from ai_whisperer.tools.base_tool import AITool
import threading # Import threading for Event

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
    def tags(self) -> List[str]:
        return ["code_execution", "utility"]

    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'execute_command' tool to run CLI commands.
        Parameters:
        - command (string, required): The command to execute.
        - cwd (string, optional): The working directory. Defaults to the current workspace directory.
        Returns: A dictionary with 'stdout', 'stderr', and 'returncode'.
        """

    def execute(self, command: str, cwd: str = ".", shutdown_event: Optional[threading.Event] = None, **kwargs) -> Dict[str, Any]:
        """
        Executes a shell command and returns the output, error, and return code.
        Checks for shutdown_event during execution.
        """
        # Filter out agent context parameters
        agent_params = {k: v for k, v in kwargs.items() if k.startswith('_')}
        if agent_params:
            logger.debug(f"Agent context: {agent_params}")
        logger.info(f"Executing command: {command} in directory: {cwd}")
        process = None
        stdout_output = ""
        stderr_output = ""
        returncode = None

        try:
            # Use Popen for non-blocking execution and polling
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Capture stdout/stderr as text
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0 # Allows sending Ctrl+C on Windows
            )

            # Poll the process and check for shutdown event
            while process.poll() is None:
                if shutdown_event and shutdown_event.is_set():
                    logger.info(f"Shutdown event set. Terminating command: {command}")
                    # Terminate the process group on Windows to kill the shell and its children
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
                    else:
                        process.terminate() # Or process.kill() for a harder kill
                    stderr_output += "\nCommand terminated by shutdown signal."
                    returncode = -1 # Indicate interruption
                    break # Exit the polling loop

                # Read output without blocking indefinitely
                try:
                    stdout_chunk = process.stdout.read(1024)
                    if stdout_chunk:
                        stdout_output += stdout_chunk
                        # Optionally log or display stdout chunks in real-time
                        # logger.debug(f"CMD STDOUT: {stdout_chunk.strip()}")
                except IOError:
                    # Handle case where pipe is closed unexpectedly
                    pass

                try:
                    stderr_chunk = process.stderr.read(1024)
                    if stderr_chunk:
                        stderr_output += stderr_chunk
                        # Optionally log or display stderr chunks in real-time
                        # logger.debug(f"CMD STDERR: {stderr_chunk.strip()}")
                except IOError:
                    # Handle case where pipe is closed unexpectedly
                    pass
                
            # If the loop exited because the process finished (not terminated by shutdown)
            if returncode is None:
                 returncode = process.returncode
                 # Read any remaining output after the process has finished
                 stdout_output += process.stdout.read()
                 stderr_output += process.stderr.read()

            logger.info(f"Command execution finished with return code: {returncode}")
            return {
                "stdout": stdout_output,
                "stderr": stderr_output,
                "returncode": returncode
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
            # Attempt to terminate the process if it was started
            if process and process.poll() is None:
                 try:
                     if sys.platform == "win32":
                         subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
                     else:
                         process.terminate()
                 except Exception as term_e:
                     logger.error(f"Error terminating process after exception: {term_e}")

            return {
                "stdout": stdout_output, # Include any output read before the error
                "stderr": f"Error executing command: {e}\n{stderr_output}", # Include error and any stderr read
                "returncode": 1 # Generic error code
            }
        finally:
            # Ensure process is cleaned up if it was started
            if process and process.poll() is None:
                 try:
                     if sys.platform == "win32":
                         subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
                     else:
                         process.terminate()
                 except Exception as term_e:
                     logger.error(f"Error terminating process in finally block: {term_e}")
            if process:
                 # Close pipes to release resources
                 if process.stdout:
                     process.stdout.close()
                 if process.stderr:
                     process.stderr.close()
