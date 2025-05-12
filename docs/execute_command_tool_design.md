# Design for `execute_command` Tool

This document outlines the design for the `execute_command` tool, which allows the AI to execute system commands.

## 1. Tool Definition

* **Name:** `execute_command`
* **Description:** "Executes a system command and returns its standard output, standard error, and return code. Allows specifying arguments, a working directory, and a timeout."
* **Category:** "System Execution"
* **Tags:** `["command", "shell", "execute", "process", "system"]`

## 2. Interface Definition

### 2.1. Input Parameters (`parameters_schema`)

The tool accepts the following parameters, defined by the JSON schema below:

```json
{
  "type": "object",
  "properties": {
    "command": {
      "type": "string",
      "description": "The command or program to execute (e.g., 'python', 'ls', 'my_script.sh'). This should be the command itself, without arguments."
    },
    "args": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "A list of arguments to pass to the command. Each argument should be a separate string in the list (e.g., [\"my_script.py\", \"--verbose\"]).",
      "default": []
    },
    "cwd": {
      "type": "string",
      "description": "The working directory from which to execute the command. If not specified, defaults to the AIWhisperer's current workspace directory."
    },
    "timeout": {
      "type": "integer",
      "description": "The maximum time in seconds to allow the command to run. If the command exceeds this time, it will be terminated. Defaults to 60 seconds. Can be set up to a maximum of 120 seconds for the initial version.",
      "default": 60,
      "minimum": 1,
      "maximum": 120
    }
  },
  "required": [
    "command"
  ]
}
```

**Details:**

* **`command`** (string, required): The primary command or executable.
* **`args`** (array of strings, optional): Arguments for the command. Defaults to an empty list.
* **`cwd`** (string, optional): The current working directory for the command execution. If not provided, it will default to the application's current workspace.
* **`timeout`** (integer, optional): Maximum execution time in seconds. Defaults to 60. Minimum 1, Maximum 120 (for the initial version).

### 2.2. Output Structure

The `execute()` method of the tool will return a dictionary with the following structure:

```json
{
  "stdout": "string",
  "stderr": "string",
  "return_code": "integer | null",
  "timed_out": "boolean"
}
```

**Details:**

* **`stdout`** (string): The standard output captured from the command. Will be an empty string if no output or if an error occurred before capturing.
* **`stderr`** (string): The standard error captured from the command. Will be an empty string if no error output or if an error occurred before capturing.
* **`return_code`** (integer | null): The exit status code of the command. `0` typically indicates success. May be `null` or a specific value if the command could not be started (e.g., command not found) or if it timed out (in which case `timed_out` will be `true`).
* **`timed_out`** (boolean): `true` if the command was terminated due to exceeding the specified `timeout`, `false` otherwise.

## 3. Interaction with `base_tool.py`

* A new Python class, `ExecuteCommandTool`, will be created in a new file: `src/ai_whisperer/tools/execute_command_tool.py`.
* `ExecuteCommandTool` will inherit from the `AITool` abstract base class defined in `src/ai_whisperer/tools/base_tool.py`.
* It will implement all abstract properties:
  * `name` (property): Returns `"execute_command"`.
  * `description` (property): Returns the description: "Executes a system command and returns its standard output, standard error, and return code. Allows specifying arguments, a working directory, and a timeout."
  * `parameters_schema` (property): Returns the JSON schema for the input parameters as defined in section 2.1.
* It will implement all abstract methods:
  * `get_ai_prompt_instructions()`: Returns a string containing clear instructions for the AI on how to use this tool (see section 5).
  * `execute(**kwargs)`: This asynchronous method will contain the core logic.
    * It will use Python's `asyncio.create_subprocess_exec` (from the `asyncio.subprocess` module) for non-blocking command execution.
    * It will construct the full command by combining `command` and `args`.
    * It will handle the `cwd` parameter, defaulting to the application's workspace if not provided.
    * It will implement the `timeout` logic, likely using `asyncio.wait_for`.
    * It will capture `stdout` and `stderr` by reading from the subprocess's pipes.
    * It will obtain the `return_code` from the subprocess.
    * It will set the `timed_out` flag appropriately if the timeout is exceeded.
    * It will return the structured output dictionary as defined in section 2.2.

## 4. Registration in `tool_registry.py`

* The `ExecuteCommandTool` class will be imported in `src/ai_whisperer/tools/__init__.py`.
* An instance of `ExecuteCommandTool` will be created.
* This instance will be registered with the global `ToolRegistry` singleton by calling `tool_registry.register_tool(ExecuteCommandTool())` within `src/ai_whisperer/tools/__init__.py` (or a dedicated tool loading/initialization module if the project structure evolves to use one). This makes the tool discoverable and usable by the AIWhisperer system.

## 5. AI Prompt Instructions

The `get_ai_prompt_instructions()` method will return a string similar to the following to guide the AI:

```text
Tool Name: execute_command
Description: Executes a system command and returns its standard output, standard error, and return code.
Parameters Schema:
  - command (string, required): The command or program to execute (e.g., "python", "ls"). This should be the command itself, without arguments.
  - args (array of strings, optional): A list of arguments for the command (e.g., ["my_script.py", "--input", "data.txt"]). Defaults to an empty list.
  - cwd (string, optional): The working directory for command execution. If not specified, defaults to the current workspace.
  - timeout (integer, optional): Maximum execution time in seconds (default: 60, min: 1, max: 120 for the initial version). If the command exceeds this, it will be terminated.
Output: A dictionary containing:
  - "stdout" (string): The standard output from the command.
  - "stderr" (string): The standard error from the command.
  - "return_code" (integer or null): The command's exit code (0 usually means success). Null if the command couldn't start or timed out.
  - "timed_out" (boolean): True if the command was terminated due to timeout, false otherwise.
When to use:
  Use this tool when you need to run an external program, script, or shell command on the system.
  For example, to compile code, run a Python script (`command="python", args=["script_name.py"]`), execute a shell utility, or run tests.
  Ensure the 'command' and 'args' are correctly specified as separate entities.
  Be mindful of the working directory ('cwd') if the command relies on relative file paths.
  Specify a 'timeout' if a command has the potential to hang or run for an unexpectedly long time.
  The command is executed directly; shell-specific features like pipes (`|`) or complex redirection (`>>`) within the `command` string itself are not interpreted by a shell unless the command is explicitly a shell (e.g., `command="bash", args=["-c", "ls | grep foo"]`). Prefer to handle complex logic within scripts called by this tool.
```

## 6. Error Handling

* **Command Not Found / Permissions:** If the system cannot find the command or if there are permission issues, `asyncio.create_subprocess_exec` will likely raise an exception (e.g., `FileNotFoundError`, `PermissionError`). The `execute` method should catch these, log them, and return an appropriate output dictionary (e.g., `stdout="", stderr="Error: Command not found/permission denied.", return_code=specific_error_code_or_null, timed_out=false`).
* **Non-Zero Return Codes:** A non-zero `return_code` indicates the command ran but exited with an error status. This is normal behavior and will be reported as such. `stderr` often contains details.
* **Timeout:** If the command times out, `timed_out` will be `true`, and `return_code` might be `null` or a system-specific code indicating termination. `stdout` and `stderr` will contain whatever output was generated before the timeout.

## 7. Security Considerations

* The `execute_command` tool provides powerful capabilities. Since the commands are generated by the AI based on its assigned tasks within the AIWhisperer framework, the primary trust boundary is with the AI's instructions and the overall system's goals.
* Direct execution of arbitrary user-supplied strings is not the intended use case here.
* The tool should not inherently use `shell=True` (or its equivalent in `asyncio.create_subprocess_exec`) unless explicitly invoking a shell like `bash -c "..."`. The `command` and `args` should be passed as a sequence to avoid shell injection vulnerabilities if the input source were less controlled. The current design (separate `command` and `args` list) promotes this safer practice.

## 8. Data Flow Diagram

```mermaid
graph TD
    subgraph AI Interaction
        A[AI determines need to execute command] --> AI_PARAMS{{AI constructs parameters: command, args, cwd, timeout}};
    end

    AI_PARAMS --> TOOL[ExecuteCommandTool];

    subgraph Tool Execution
        TOOL -- Validates parameters --> LOGIC{execute() method};
        LOGIC -- Uses asyncio.create_subprocess_exec with command & args --> SUBPROCESS[System Subprocess in specified cwd];
        SUBPROCESS -- stdout stream --> CAPTURE_STDOUT[Capture stdout];
        SUBPROCESS -- stderr stream --> CAPTURE_STDERR[Capture stderr];
        SUBPROCESS -- process.wait() for exit code --> CAPTURE_RC[Capture return_code];
        LOGIC -- Manages asyncio.wait_for(SUBPROCESS) --> TIMEOUT_STATUS[Determine timed_out status];
    end

    CAPTURE_STDOUT --> RESULT_DICT{Output Dictionary};
    CAPTURE_STDERR --> RESULT_DICT;
    CAPTURE_RC --> RESULT_DICT;
    TIMEOUT_STATUS --> RESULT_DICT;

    RESULT_DICT -- {stdout, stderr, return_code, timed_out} --> AI_RESULT[AI receives structured output];

    style TOOL fill:#f9f,stroke:#333,stroke-width:2px
    style LOGIC fill:#ccf,stroke:#333,stroke-width:2px
```

This design provides a robust foundation for the `execute_command` tool, aligning with the project's existing architecture and addressing the requirements for command execution.
