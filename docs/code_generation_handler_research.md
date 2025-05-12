# Code Generation Handler Research & Design

This document outlines the research findings and proposed design for the `code_generation` task type handler within the AI Whisperer execution engine.

## 1. Introduction

The `code_generation` task type is responsible for instructing an AI agent to generate or modify code based on provided requirements, context, and constraints. This handler plays a crucial role in automating software development tasks within the AI Whisperer framework. It needs to integrate seamlessly with the existing execution engine, leverage AI capabilities effectively, and incorporate validation steps, including test execution.

**References:**

* RFC: [`project_dev/rfc/code_generator_task_type.md`](project_dev/rfc/code_generator_task_type.md)
* Subtask Schema: [`src/ai_whisperer/schemas/subtask_schema.json`](src/ai_whisperer/schemas/subtask_schema.json)
* Execution Engine: [`src/ai_whisperer/execution_engine.py`](src/ai_whisperer/execution_engine.py)
* Agent Handlers: [`src/ai_whisperer/agent_handlers/`](src/ai_whisperer/agent_handlers/)

## 2. Handler Requirements

Based on the RFC and existing architecture:

* **Integration:** The handler must register with the `ExecutionEngine`'s `agent_type_handlers` dictionary ([`src/ai_whisperer/execution_engine.py:111`](src/ai_whisperer/execution_engine.py:111)).
* **AI Instruction:** It must formulate precise prompts for an AI agent, incorporating subtask details, context, and necessary tools.
* **Context Awareness:** The handler and the instructed AI must be able to examine project files for context and potential code reuse.
* **Test Execution:** The handler must be capable of triggering and interpreting the results of test commands specified in the subtask.
* **State Management:** It must update task status and store results/conversation history using the `StateManager`.

## 3. Proposed Design

### 3.1. Handler Signature & Registration

* **Location:** [`src/ai_whisperer/agent_handlers/code_generation.py`](src/ai_whisperer/agent_handlers/code_generation.py)
* **Function:** `def handle_code_generation(engine, task_definition, task_id):`
* **Registration (in [`execution_engine.py`](src/ai_whisperer/execution_engine.py)):**

    ```python
    # Import the handler function
    from .agent_handlers.code_generation import handle_code_generation

    # In the ExecutionEngine __init__ method
    self.agent_type_handlers = {
        # Existing handlers...
        "code_generation": lambda task_definition, task_id: handle_code_generation(self, task_definition, task_id),
    }
    ```

### 3.2. Inputs & Outputs

* **Inputs:**
  * `engine`: The `ExecutionEngine` instance (provides access to config, monitor, state\_manager, AI API, tools).
  * `task_definition`: The JSON object for the `code_generation` subtask, conforming to [`src/ai_whisperer/schemas/subtask_schema.json`](src/ai_whisperer/schemas/subtask_schema.json). Key fields include:
    * `description`: High-level goal.
    * `instructions`: Specific steps for the AI.
    * `input_artifacts`: Paths to files/directories for context/modification.
    * `output_artifacts`: Paths for generated/modified files.
    * `constraints`: Rules for generation (e.g., style, language version).
    * `validation_criteria`: Test commands or validation descriptions.
  * Project Context: Relevant files/structures identified by the handler or AI via tools.
* **Outputs:**
  * Generated/Modified Files: Written to paths specified in `output_artifacts`.
  * Test Results: Status (pass/fail), command output stored potentially as part of the task result.
  * Task State: Updated to `completed` or `failed` in `StateManager`.
  * Task Result: Stored in `StateManager`, potentially including paths to output artifacts and test summaries.
  * Conversation History: User prompt and AI response (including tool calls and usage info) stored via `StateManager`.

### 3.3. AI Interaction Strategy

1. **Context Gathering:**
    * Read `input_artifacts`. If an artifact is a file, read its content. If it's a directory, generate a tree structure (similar to [`ai_interaction.py`](src/ai_whisperer/agent_handlers/ai_interaction.py:58)).
2. **Prompt Construction:**
    * Start with a base system prompt tailored for `code_generation`. This prompt should emphasize:
        * Strict adherence to the `instructions`.
        * Examining `input_artifacts` and potentially other project files (`read_file`, `list_files`, `search_files`) for context and reuse opportunities.
        * Following `constraints`.
        * Generating code that fulfills the `description`.
        * Awareness that generated code will be validated/tested as per `validation_criteria`.
    * Append the specific `instructions` from the subtask.
    * Append the gathered context from `input_artifacts`.
    * Append the full subtask JSON (`raw_text`) for complete reference.
3. **Tool Provisioning:**
    * Ensure the AI model is called with the necessary tools enabled:
        * `read_file`: Examine existing code/artifacts.
        * `write_file`: Create/overwrite output files.
        * `apply_diff`: Make targeted modifications.
        * `insert_content`: Add code blocks.
        * `search_files`: Find relevant code/dependencies.
        * `execute_command`: Run linters, formatters, build steps, tests.
        * `list_files`: Explore directory contents.
4. **AI Call & Response Handling:**
    * Use `engine.openrouter_api.call_chat_completion` with the constructed prompt, conversation history (`engine._collect_ai_history`), and enabled tools.
    * Process the response:
        * If `tool_calls` are present: Execute the requested tools sequentially using the `ToolRegistry` (logic likely needs to be extracted from [`execution_engine.py`](src/ai_whisperer/execution_engine.py) or reimplemented/shared). Store tool outputs. *Crucially, the handler must manage the tool execution loop if the AI requires multiple tool interactions.*
        * If text `content` is present: Treat as the final response or intermediate reasoning.
        * Store the conversation turn (user prompt, assistant response/tool calls, usage info) in the `StateManager`.
5. **Output Artifact Generation:**
    * Ensure the AI uses `write_file` or `apply_diff` to create/modify the files specified in `output_artifacts`. The handler might need to verify these files exist after the AI interaction, although ideally, the AI confirms completion via its response or tool usage.

### 3.4. Test Integration Plan (Handler Expectations)

1. **Trigger:** After the AI interaction phase appears complete (e.g., no more tool calls requested, final confirmation message), the handler checks the `validation_criteria` field in the `task_definition`.
2. **Execution:**
    * If `validation_criteria` contains executable commands (e.g., `["pytest tests/test_feature.py"]`, `["npm run test"]`):
        * The handler uses the `execute_command` tool to run each command.
        * Capture the exit code, stdout, and stderr for each command.
    * If `validation_criteria` contains descriptive checks:
        * This scenario is less defined. The handler might attempt basic file checks (e.g., existence of `output_artifacts`) or potentially require a subsequent `validation` task type handled by a dedicated validation agent/handler. For this initial `code_generation` handler, focus will be on executing commands.
3. **Result Interpretation:**
    * **Primary Check:** A non-zero exit code from any test command signifies failure.
    * **Output Parsing (Optional):** The handler could perform basic parsing of stdout/stderr for keywords like "FAIL", "ERROR", "passed" to provide a more detailed result summary.
    * **"Faked" Test Detection:** As per user feedback, this is out of scope for the initial implementation. The handler will assume tests run via `execute_command` are legitimate. Future enhancements could involve analyzing test file content or output heuristics.
4. **Outcome:**
    * If all validation commands pass (exit code 0): The `code_generation` task is marked as `completed`. Test results (summary, logs) are stored.
    * If any validation command fails: The `code_generation` task is marked as `failed`. Test failure details (command, exit code, output) are stored.
    * *(Future Enhancement):* Implement a retry loop where test failures are fed back to the AI for fixing.

### 3.5. Code Reuse & File Examination

* **Prompting:** The base prompt explicitly directs the AI to prioritize reuse.
* **Tooling:** The AI uses `read_file`, `list_files`, and `search_files` on `input_artifacts` or other relevant project paths (potentially discovered via `list_files`) to find existing code, understand context, and identify dependencies.
* **Handler Context:** The handler provides initial context by reading/listing `input_artifacts` before the first AI call.

## 4. Considerations & Future Work

* **Tool Execution Logic:** The logic for executing tool calls needs to be robustly implemented, either within this handler or as a shared utility accessible by handlers. It must handle potential sequences of tool calls.
* **Error Handling:** Implement comprehensive error handling for AI API calls, tool execution failures, file I/O errors, and test command failures.
* **Complex Validation:** Handling descriptive `validation_criteria` or complex validation logic might require interaction with a dedicated `validation` handler/task type in the future.
* **Feedback Loop:** Implementing a retry mechanism where test failures are fed back to the AI for correction would significantly enhance robustness.
* **Security:** Be mindful of security implications when using `execute_command`, especially regarding the commands specified in `validation_criteria`. Ensure commands are run in appropriate environments and potentially sandboxed.
* **Cost/Token Management:** Long code generation tasks involving multiple tool calls and extensive context could become expensive. Monitor token usage.
