# Code Generation Handler Technical Design

## 1. Introduction

This document provides the detailed technical design for the `code_generation` task type handler within the AI Whisperer execution engine. It builds upon the research outlined in [`docs/code_generation_handler_research.md`](docs/code_generation_handler_research.md) and considers the existing architecture of the [`ExecutionEngine`](src/ai_whisperer/execution_engine.py), [`ai_service_interaction`](src/ai_whisperer/ai_service_interaction.py), and [`ToolRegistry`](src/ai_whisperer/tools/tool_registry.py).

The handler is responsible for managing the interaction with an AI agent to generate or modify code according to specified instructions, context, and constraints, including executing validation tests.

## 2. Handler Structure and Registration

* **Location:** The handler function will reside in a new file: [`src/ai_whisperer/agent_handlers/code_generation.py`](src/ai_whisperer/agent_handlers/code_generation.py)
* **Signature:**

    ```python
    # src/ai_whisperer/agent_handlers/code_generation.py
    from src.ai_whisperer.execution_engine import ExecutionEngine
    from src.ai_whisperer.exceptions import TaskExecutionError
    from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType
    from src.ai_whisperer.tools.tool_registry import ToolRegistry # Assuming ToolRegistry is accessible
    from pathlib import Path
    import json
    import traceback
    from datetime import datetime, timezone

    # Potentially import build_ascii_directory_tree if needed
    from src.ai_whisperer.utils import build_ascii_directory_tree

    def handle_code_generation(engine: ExecutionEngine, task_definition: dict, task_id: str):
        """
        Handles the execution of a 'code_generation' task.

        Orchestrates AI interaction, tool execution (including file I/O and tests),
        and state management for code generation subtasks.
        """
        logger = engine.config.get('logger', None) # Get logger from engine config
        if logger:
            logger.info(f"Starting code_generation handler for task: {task_id}")
        engine.monitor.add_log_message(
            LogMessage(
                LogLevel.INFO, ComponentType.AGENT_HANDLER, "code_gen_start",
                f"Starting code generation handler for task {task_id}.", subtask_id=task_id
            )
        )

        # --- Main Handler Logic (detailed in sections below) ---
        try:
            # 1. Context Gathering
            prompt_context = _gather_context(engine, task_definition, task_id, logger)

            # 2. Prompt Construction
            initial_prompt = _construct_initial_prompt(engine, task_definition, task_id, prompt_context, logger)

            # 3. AI Interaction & Tool Execution Loop
            final_result, conversation_history = _run_ai_interaction_loop(engine, task_definition, task_id, initial_prompt, logger)

            # 4. Test Execution / Validation
            validation_passed, validation_details = _execute_validation(engine, task_definition, task_id, logger)

            # 5. Final Result Processing & State Update
            if validation_passed:
                final_task_result = {
                    "message": "Code generation completed and validation passed.",
                    "ai_result": final_result, # Could be final AI message or tool outputs
                    "validation_details": validation_details
                }
                if logger:
                    logger.info(f"Task {task_id} completed successfully.")
                engine.monitor.add_log_message(
                    LogMessage(
                        LogLevel.INFO, ComponentType.AGENT_HANDLER, "code_gen_success",
                        f"Code generation task {task_id} completed and validated successfully.", subtask_id=task_id,
                        details=validation_details
                    )
                )
                # StateManager update happens in the main engine loop upon successful return
                return final_task_result # Return structured result
            else:
                error_message = f"Code generation task {task_id} failed validation."
                if logger:
                    logger.error(f"{error_message} Details: {validation_details}")
                engine.monitor.add_log_message(
                    LogMessage(
                        LogLevel.ERROR, ComponentType.AGENT_HANDLER, "code_gen_validation_failed",
                        error_message, subtask_id=task_id, details=validation_details
                    )
                )
                raise TaskExecutionError(error_message, details=validation_details)

        except TaskExecutionError as e:
            # Logged within the function that raised it or here
            if logger:
                 logger.error(f"TaskExecutionError in handle_code_generation for {task_id}: {e}", exc_info=True)
            # Re-raise for the main engine loop to catch and set task state to failed
            raise e
        except Exception as e:
            error_message = f"Unexpected error in handle_code_generation for task {task_id}: {e}"
            if logger:
                logger.error(error_message, exc_info=True)
            engine.monitor.add_log_message(
                LogMessage(
                    LogLevel.CRITICAL, ComponentType.AGENT_HANDLER, "code_gen_unexpected_error",
                    error_message, subtask_id=task_id, details={"error": str(e), "traceback": traceback.format_exc()}
                )
            )
            # Raise as TaskExecutionError for consistent handling
            raise TaskExecutionError(error_message) from e

    # --- Helper Functions (Private to the handler module) ---

    def _gather_context(engine, task_definition, task_id, logger) -> str:
        # ... Implementation to read input_artifacts (files/dirs) ...
        # Use build_ascii_directory_tree for directories
        # Log errors but try to continue
        pass # Placeholder

    def _construct_initial_prompt(engine, task_definition, task_id, prompt_context, logger) -> str:
        # ... Implementation to build the prompt ...
        # Combine base prompt, instructions, context, constraints, raw task JSON
        pass # Placeholder

    def _run_ai_interaction_loop(engine, task_definition, task_id, initial_prompt, logger) -> (dict, list):
        # ... Implementation for the main loop ...
        # - Manage conversation history
        # - Call engine.openrouter_api.call_chat_completion
        # - Check response type (content vs tool_calls)
        # - If tool_calls:
        #   - Get ToolRegistry instance: tool_registry = ToolRegistry()
        #   - Iterate through calls:
        #     - Get tool instance: tool_instance = tool_registry.get_tool(tool_name)
        #     - Execute tool: tool_output = tool_instance.execute(**args)
        #     - Log tool execution via engine.monitor
        #     - Format tool result message
        #     - Append user, assistant (tool_call), and tool result messages to history
        #   - Continue loop (call API again)
        # - If content:
        #   - Append user and assistant (content) messages to history
        #   - Return final AI result and history
        # - Handle API/Tool errors, potentially raising TaskExecutionError
        pass # Placeholder

    def _execute_validation(engine, task_definition, task_id, logger) -> (bool, dict):
        # ... Implementation for validation ...
        # - Check task_definition['validation_criteria']
        # - If commands exist:
        #   - Get ToolRegistry instance: tool_registry = ToolRegistry()
        #   - Get execute_command tool: cmd_tool = tool_registry.get_tool('execute_command')
        #   - Loop through commands:
        #     - Execute: result = cmd_tool.execute(command=cmd)
        #     - Log via engine.monitor
        #     - Check result['exit_code']
        #     - Store command, exit code, stdout, stderr in validation_details
        #   - Return overall pass/fail and details
        # - If descriptive: Log a warning, return True (for now)
        # - Handle errors during command execution
        pass # Placeholder

    ```

* **Registration (in [`src/ai_whisperer/execution_engine.py`](src/ai_whisperer/execution_engine.py)):**

    ```python
    # src/ai_whisperer/execution_engine.py

    # ... other imports ...
    from .agent_handlers.code_generation import handle_code_generation # Add this import

    class ExecutionEngine:
        def __init__(self, state_manager: StateManager, monitor: TerminalMonitor, config: dict):
            # ... existing init code ...

            # Import agent handler functions
            from .agent_handlers.ai_interaction import handle_ai_interaction
            from .agent_handlers.planning import handle_planning
            from .agent_handlers.validation import handle_validation
            from .agent_handlers.no_op import handle_no_op
            # No need to import handle_code_generation again here if imported above

            # Initialize the agent type handler table
            self.agent_type_handlers = {
                "ai_interaction": lambda task_definition, task_id: handle_ai_interaction(self, task_definition, task_id),
                "planning": lambda task_definition, task_id: handle_planning(self, task_definition, task_id),
                "validation": lambda task_definition, task_id: handle_validation(self, task_definition, task_id),
                "no_op": lambda task_definition, task_id: handle_no_op(self, task_definition, task_id),
                "code_generation": lambda task_definition, task_id: handle_code_generation(self, task_definition, task_id), # Add this line
            }
            # ... rest of init code ...
    ```

## 3. Inputs and Outputs

* **Inputs:**
  * `engine`: The `ExecutionEngine` instance, providing access to `config`, `monitor`, `state_manager`, `openrouter_api`.
  * `task_definition`: The JSON object for the `code_generation` subtask. Key fields:
    * `description`: High-level goal.
    * `instructions`: Specific steps for the AI.
    * `input_artifacts`: List of file/directory paths for context or modification.
    * `output_artifacts`: List of file paths expected to be created/modified.
    * `constraints`: Rules for generation (e.g., style guides, language versions).
    * `validation_criteria`: List of shell commands for testing/validation, or descriptive criteria (initially focus on commands).
    * `raw_text`: The raw JSON text of the subtask definition.
  * `task_id`: The unique identifier for the subtask.
* **Outputs (Implicit via Engine/Tools, Explicit via Return Value):**
  * **File System:** Generated or modified files as specified by AI using `write_file`, `apply_diff`, `insert_content` tools, targeting paths ideally related to `output_artifacts`.
  * **State Manager:**
    * Conversation history (user prompts, assistant responses/tool calls, tool results, timestamps, usage info) stored via `engine.state_manager.store_conversation_turn`.
    * Task status (`completed` or `failed`) set by the `ExecutionEngine` based on the handler's return/exception.
    * Final task result stored via `engine.state_manager.store_task_result`. This will be the structured dictionary returned by the handler on success.
  * **Return Value (on success):** A dictionary containing a summary message, the final AI result (content or last tool outputs), and structured validation details. Example:

        ```json
        {
          "message": "Code generation completed and validation passed.",
          "ai_result": { "content": "Final confirmation message from AI." }, // Or last tool outputs
          "validation_details": {
            "commands_executed": [
              {
                "command": "pytest tests/test_new_feature.py",
                "exit_code": 0,
                "stdout": "...",
                "stderr": ""
              }
            ],
            "overall_status": "passed"
          }
        }
        ```

  * **Exception (on failure):** A `TaskExecutionError` is raised, which the `ExecutionEngine` catches to set the task state to `failed`. The exception may contain details about the failure (e.g., validation output).

## 4. Interaction Flow

The handler orchestrates the following steps:

```mermaid
sequenceDiagram
    participant EE as ExecutionEngine
    participant CGH as CodeGenHandler
    participant Ctx as ContextGathering (_gather_context)
    participant Prompt as PromptConstruction (_construct_initial_prompt)
    participant AI_Loop as AI Interaction Loop (_run_ai_interaction_loop)
    participant AISvc as AIService (engine.openrouter_api)
    participant Tools as ToolRegistry/Tools
    participant Validate as Validation (_execute_validation)
    participant SM as StateManager (engine.state_manager)

    EE->>+CGH: handle_code_generation(engine, task_def, task_id)
    CGH->>+Ctx: _gather_context(...)
    Ctx-->>-CGH: prompt_context
    CGH->>+Prompt: _construct_initial_prompt(...)
    Prompt-->>-CGH: initial_prompt
    CGH->>+AI_Loop: _run_ai_interaction_loop(initial_prompt)
    AI_Loop->>SM: Get/Build History (implicitly)
    AI_Loop->>+AISvc: call_chat_completion(prompt, history, tools_def)
    AISvc-->>-AI_Loop: Response (Tool Calls)
    AI_Loop->>SM: store_conversation_turn(user_prompt)
    AI_Loop->>SM: store_conversation_turn(assistant_tool_calls)
    AI_Loop->>+Tools: Get Tool("write_file")
    Tools-->>-AI_Loop: tool_instance
    AI_Loop->>Tools: tool_instance.execute(...)
    Note over Tools: File is written
    Tools-->>-AI_Loop: tool_output
    AI_Loop->>SM: store_conversation_turn(tool_result)
    AI_Loop->>AI_Loop: Update History
    AI_Loop->>+AISvc: call_chat_completion(updated_history)
    AISvc-->>-AI_Loop: Response (Content)
    AI_Loop->>SM: store_conversation_turn(user_prompt)
    AI_Loop->>SM: store_conversation_turn(assistant_content)
    AI_Loop-->>-CGH: final_ai_result, history
    CGH->>+Validate: _execute_validation(...)
    Validate->>Tools: Get Tool("execute_command")
    Validate->>Tools: tool_instance.execute(command="pytest ...")
    Note over Tools: Test command runs
    Tools-->>-Validate: command_output (exit_code, stdout, stderr)
    Validate-->>-CGH: validation_passed=True, validation_details
    CGH-->>-EE: Return final_task_result
```

**Detailed Steps:**

1. **Initialization:** Get logger, log handler start.
2. **Context Gathering (`_gather_context`):**
    * Iterate through `task_definition['input_artifacts']`.
    * If an artifact path points to a file, read its content using `Path.read_text()`. Handle potential `FileNotFoundError` or `IOError` (log warning, continue).
    * If an artifact path points to a directory, generate a directory tree structure string using a utility function like `build_ascii_directory_tree` (similar to [`ai_interaction.py`](src/ai_whisperer/agent_handlers/ai_interaction.py:58)). Handle potential errors during tree generation.
    * Concatenate file contents and directory structures into a `prompt_context` string, clearly labeling each part.
3. **Prompt Construction (`_construct_initial_prompt`):**
    * Define a base system prompt specifically for code generation, emphasizing adherence to instructions, constraints, code reuse, file examination (using available tools), and awareness of upcoming validation.
    * Append `task_definition['instructions']`.
    * Append the gathered `prompt_context`.
    * Append `task_definition['constraints']` (clearly labeled).
    * Append the full `task_definition['raw_text']` for the AI's reference.
4. **AI Interaction & Tool Execution Loop (`_run_ai_interaction_loop`):**
    * Initialize `conversation_history` (list of message dicts). Start with the `initial_prompt` as the first user message.
    * **Loop:**
        * Call `engine.openrouter_api.call_chat_completion` with the current `conversation_history`, model/params from `engine.config` (or task-specific overrides if implemented later). Note: Tool definitions are automatically included by `call_chat_completion`.
        * Store the user prompt message in the state manager via `engine.state_manager.store_conversation_turn`.
        * **Process Response:**
            * Check the type of the returned `result`.
            * **If `result` contains `tool_calls`:**
                * Store the assistant message (with `tool_calls`) via `engine.state_manager.store_conversation_turn`.
                * Append the assistant message to the local `conversation_history`.
                * Get the `ToolRegistry` instance: `tool_registry = ToolRegistry()`.
                * Iterate through each `tool_call` in `result['tool_calls']`:
                    * Extract `tool_name` and `tool_arguments` (parse JSON arguments string). Handle potential parsing errors.
                    * Get the tool instance: `tool_instance = tool_registry.get_tool(tool_name)`. Handle `ToolNotFound` errors.
                    * Execute the tool: `tool_output = tool_instance.execute(**tool_arguments)`. Catch potential execution exceptions. Log execution via `engine.monitor`.
                    * Format the `tool_output` into a message dictionary (role: `tool`, `tool_call_id`, `content`: stringified output).
                    * Store the tool result message via `engine.state_manager.store_conversation_turn`.
                    * Append the tool result message to the local `conversation_history`.
                * Continue the loop (make the next API call with the updated history).
            * **If `result` is content (string):**
                * Store the assistant message (with `content`) via `engine.state_manager.store_conversation_turn`.
                * Append the assistant message to the local `conversation_history`.
                * Break the loop. Return the final content string and the complete `conversation_history`.
            * **Handle API Errors:** Catch exceptions from `call_chat_completion` (`OpenRouterAPIError`, etc.) and raise `TaskExecutionError`.
            * **Handle Tool Errors:** Catch exceptions during tool execution, log them, potentially format an error message to send back to the AI in the next turn, or raise `TaskExecutionError` immediately depending on severity.
5. **Test Execution / Validation (`_execute_validation`):**
    * Check `task_definition['validation_criteria']`.
    * If it's a list and contains strings (assumed to be commands):
        * Initialize `validation_details = {"commands_executed": [], "overall_status": "pending"}`.
        * Get `ToolRegistry` and the `execute_command` tool instance.
        * Loop through each command string:
            * Execute the command using `cmd_tool.execute(command=cmd)`. Catch execution errors.
            * Store the command, exit code, stdout, and stderr in the `commands_executed` list within `validation_details`.
            * If `exit_code != 0`, set `overall_status = "failed"`.
        * If the loop completes without failures, set `overall_status = "passed"`.
        * Return `(overall_status == "passed", validation_details)`.
    * If `validation_criteria` is empty or not command-based: Log a warning, return `(True, {"message": "No executable validation criteria found."})`.
6. **Final Result Processing:**
    * If validation passed, construct the success result dictionary. Log success. Return the result.
    * If validation failed, construct an error message including details. Log the error. Raise `TaskExecutionError` with the details.

## 5. Data Structures

* **Conversation History:** List of dictionaries, adhering to the OpenAI/OpenRouter message format: `{"role": "user" | "assistant" | "system" | "tool", "content": "...", "tool_calls": [...], "tool_call_id": "..."}`. Timestamps and usage info should be added by `store_conversation_turn`.
* **Validation Details:** Dictionary stored within the final task result or error details.

    ```json
    {
      "commands_executed": [
        {
          "command": "shell command string",
          "exit_code": 0, // or non-zero
          "stdout": "command standard output",
          "stderr": "command standard error"
        }
        // ... more commands ...
      ],
      "overall_status": "passed" | "failed" | "skipped" // Skipped if no commands run
    }
    ```

## 6. Code Reuse and Context Handling

* **Prompting:** The initial prompt explicitly instructs the AI to examine provided context (`input_artifacts`) and use available tools (`read_file`, `search_files`, `list_files`) to understand the existing codebase and identify opportunities for reuse before generating new code.
* **Context Provision:** The handler preprocesses `input_artifacts` (reading files, listing directories) to provide immediate context within the first prompt.
* **Tool Availability:** The AI has access to file system tools, allowing it to dynamically explore the project structure and content beyond the initially provided artifacts if necessary.

## 7. Test Integration

* The `_execute_validation` helper function is responsible for this.
* It parses the `validation_criteria` field of the subtask definition.
* It currently focuses on executing shell commands found in the list.
* It uses the registered `execute_command` tool.
* It captures the `exit_code`, `stdout`, and `stderr` for each command.
* A non-zero `exit_code` from any command marks the validation as failed.
* The results are structured in the `validation_details` dictionary.
* Failure during validation leads to the handler raising a `TaskExecutionError`, causing the `ExecutionEngine` to mark the task as `failed`.

## 8. Error Handling

The handler must gracefully handle potential errors:

* **Configuration Errors:** Handled during `ExecutionEngine` initialization.
* **Artifact Reading Errors:** Logged as warnings by `_gather_context`, allowing the process to continue if possible.
* **AI Service Errors:** `OpenRouterAPIError`, `OpenRouterAuthError`, `OpenRouterRateLimitError`, `OpenRouterConnectionError` caught during `call_chat_completion` in the loop; raise `TaskExecutionError`.
* **Tool Execution Errors:** Errors during `tool_instance.execute()` (including `execute_command` for tests) should be caught. Log the error. Depending on the tool and error, either raise `TaskExecutionError` immediately or potentially format an error message to feed back to the AI. Test command failures specifically result in a `failed` validation status and `TaskExecutionError`.
* **JSON Parsing Errors:** Handle errors when parsing tool arguments or potentially structured AI responses. Raise `TaskExecutionError`.
* **Unexpected Errors:** A general `except Exception` block should catch unforeseen issues, log them critically, and raise `TaskExecutionError`.

## 9. Future Considerations

* **Retry Logic:** Implement retries for failed test commands by feeding the failure details back into the AI interaction loop.
* **Descriptive Validation:** Enhance `_execute_validation` to handle non-command criteria, potentially requiring another AI call for assessment.
* **Tool Error Feedback:** Improve handling of tool execution errors to provide more informative feedback to the AI instead of always failing the task immediately.
* **Security:** Ensure `execute_command` usage is appropriately sandboxed or restricted if running untrusted commands.
* **Cost/Token Limits:** Implement checks within the interaction loop to prevent excessive token usage.
