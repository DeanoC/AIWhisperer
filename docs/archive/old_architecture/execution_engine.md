# Execution Engine Documentation

## Overview

The Execution Engine is a core component responsible for orchestrating and executing tasks defined within a plan. Its primary role is to process a sequence of tasks, manage their execution state, handle dependencies between tasks, and manage errors that occur during execution. It interacts closely with the State Manager to maintain the state of the overall plan and individual tasks.

## Integration with Logging and Monitoring

The Execution Engine's operations are thoroughly logged and can be observed via the AIWhisperer's monitoring interface. This includes the initiation of tasks, state transitions (e.g., from "pending" to "running", "completed", or "failed"), dependency evaluations, and any errors encountered during execution. This detailed logging is crucial for understanding the engine's behavior and for debugging purposes.

For comprehensive information on the logging and monitoring capabilities, refer to the [Logging and Monitoring Documentation](./logging_monitoring.md).

## Key Components

Based on the design and implementation, the key components and concepts are:

* **ExecutionEngine Class**: The main class that encapsulates the execution logic.
* **State Manager**: An external component (injected dependency) responsible for persisting and retrieving the state of tasks and their results.
* **Terminal Monitor**: An external component (injected dependency) responsible for displaying execution progress and logs in the terminal.
* **Configuration**: The global configuration dictionary, providing settings like AI service details.
* **Task Queue**: Internally, the `ExecutionEngine` processes tasks from a list which can be thought of as a queue, executing them in the order provided by the plan.
* **Agent Type Handlers**: A dispatch table (`self.agent_type_handlers`) used to route tasks to specialized handler methods based on the task's `agent_spec.type`.
* **AI Service Interaction (`OpenRouterAIService`)**: For tasks requiring AI communication, the engine utilizes an instance of the `OpenRouterAIService` class (from `src/ai_whisperer/ai_service_interaction.py`). This component handles direct communication with the OpenRouter service.
* **Error Handling**: Mechanisms within the `execute_plan` method and individual task handlers to catch exceptions during task execution and update the task state accordingly.

## Processing a Plan (Workflow)

The `ExecutionEngine` processes a plan, which is expected to be a list of task definitions, typically provided by a Plan Parser. The execution flow is as follows:

1. **Initialization**: The `execute_plan` method receives the plan data. It initializes an internal task queue (a list) with the tasks from the plan.
2. **Sequential Execution**: The engine iterates through the tasks in the queue sequentially.
3. **State Initialization**: For each task, its state is initially set to "pending" using the State Manager.
4. **Dependency Check**: Before executing a task, the engine checks if it has any dependencies (`depends_on`). If dependencies exist, it queries the State Manager for the status of each dependent task.
5. **Execution or Skipping**:
    * If a task has no dependencies, or if all its dependencies have a status of "completed", the task's state is updated to "in-progress", and the task execution logic is invoked via the internal `_execute_single_task` method.
    * If any dependency is not "completed", the task's state is set to "skipped", and the reason is recorded. The engine then moves to the next task without executing the current one.
6. **State and Result Update**: Upon completion of a task (either successfully or with an error), the State Manager is updated with the final state ("completed" or "failed") and any resulting output.
7. **Continuation**: The engine continues this process until all tasks in the plan have been processed.

## Interaction with the State Manager

The Execution Engine relies heavily on the State Manager for persistent state management. It uses the State Manager to:

* Set and update the state of individual tasks (e.g., "pending", "in-progress", "completed", "failed", "skipped").
* Retrieve the status of tasks, particularly for checking dependencies.
* Store the results or output generated by completed tasks.
* Retrieve the results of tasks, which can be used by subsequent tasks.

The `ExecutionEngine` is initialized with a `state_manager` instance, ensuring this dependency is met.

## Handling Task Dependencies

Task dependencies are specified in the plan using the `depends_on` field, which is a list of `subtask_id`s of tasks that must be completed before the current task can run. The `execute_plan` method checks these dependencies by querying the State Manager for the status of each dependent task. A task is only executed if all its dependencies have a status of "completed". Otherwise, the task is marked as "skipped".

## Error Handling

The Execution Engine implements robust error handling. Exceptions occurring during task execution are caught, logged, and the task's state is updated to "failed" in the State Manager. The engine is designed to continue processing subsequent tasks even if a task fails, allowing for partial plan execution. Specific error handling for AI interaction tasks is detailed in the "Agent Task Handling" section.

## Agent Task Handling

The `ExecutionEngine` uses a dispatch mechanism to handle different types of tasks based on their `agent_spec.type`. The internal `_execute_single_task` method routes the task to the appropriate handler method.

### Handling AI Interaction Tasks (`_handle_ai_interaction`)

This method is invoked for tasks with `agent_spec.type` set to `"ai_interaction"`. It orchestrates the communication with an AI service.

* **Configuration**: AI configurations are determined by merging global settings (from `self.config['openrouter']`) with any task-specific `ai_config` provided in the task's `agent_spec`.
* **AI Service Initialization**: An instance of `OpenRouterAIService` is created using the merged configuration. `ConfigError` is handled if essential AI configurations (like the API key) are missing.

* **Input Processing & Prompt Construction**:
  * Extracts `instructions` and `input_artifacts` from the task definition and agent specification.
  * Reads the content of specified input artifact files.
  * Constructs the prompt for the AI based on the following priority:
    1. Agent-specific default prompt + Task instructions
    2. Agent-specific default prompt only
    3. Task instructions only (embedded within the global default prompt)
    4. Global default prompt only
  * If no suitable prompt is found based on this hierarchy, an error is raised.
  * For specific tasks like those in the `simple_country_test`, there is specialized logic:
    * `ask_country`: Uses the content of `landmark_selection.md` to form the prompt.
    * `ask_capital`: Uses the content of `country_validation_result.md` and proceeds with the AI call only if country validation passed.
    * `ask_landmark_in_capital`: Uses `landmark_selection.md` and `capital_validation_result.md`, proceeding only if capital validation passed.
  * If prerequisite validation steps fail, the AI call for dependent tasks is skipped, and this is noted in the output artifact.
* **Conversation History Management**: A `messages_history` list is built by retrieving the prompt and response from previously completed `"ai_interaction"` tasks stored in the `StateManager`. This history is included in the AI request to maintain conversation context.
* **AI Service Call**: The `OpenRouterAIService` instance is used to call either `stream_chat_completion` (for streaming responses) or `chat_completion` (for non-streaming), passing the constructed prompt, conversation history, and AI parameters.
* **Response Handling & Storage**: The AI's textual response is processed. The result, typically a dictionary containing the original `prompt` and the AI `response`, is stored using the `StateManager`. The AI's response is also written to an output artifact file if specified in `agent_spec.output_artifacts`.
* **Error Handling**: Catches specific exceptions from `OpenRouterAIService` (e.g., `OpenRouterAIServiceError`, `OpenRouterAuthError`, `OpenRouterRateLimitError`, `OpenRouterConnectionError`). These errors are logged, and a `TaskExecutionError` is raised to mark the task as failed.

### Handling Planning Tasks (`_handle_planning`)

This method is responsible for executing tasks with `agent_spec.type` set to `"planning"`. Currently, it includes specific logic for the `select_landmark` task, which involves creating the `landmark_selection.md` file with a predefined landmark.

### Handling Validation Tasks (`_handle_validation`)

This method handles tasks with `agent_spec.type` set to `"validation"`. It includes specific logic for the `simple_country_test` validation tasks (`validate_country`, `validate_capital`, and `validate_landmark_in_capital`). This involves reading AI responses from files generated by previous tasks, performing validation checks (e.g., checking for keywords like "France" or "Paris"), and creating validation result files (e.g., `country_validation_result.md`) indicating success or failure.

## API Documentation

### `class ExecutionEngine`

Executes tasks defined in a plan, managing state and handling dependencies.

#### `__init__(self, state_manager, monitor, config)`

Initializes the `ExecutionEngine`.

* **Parameters**:
  * `state_manager`: An object responsible for managing the state of tasks. Expected to have methods like `set_task_state`, `get_task_status`, `store_task_result`, and `get_task_result`.
  * `monitor`: An object responsible for displaying execution progress and logs (`TerminalMonitor`).
  * `config`: The global configuration dictionary.
* **Raises**:
  * `ValueError`: If `state_manager`, `monitor`, or `config` is `None`.

#### `execute_plan(self, plan_data)`

Executes the given plan sequentially.

* **Parameters**:
  * `plan_data` (`dict`): The plan data, typically from a PlanParser, containing a list of task definitions under the key `"plan"`.
* **Returns**:
  * `None`: The method modifies state via the `state_manager` and does not return a value.

#### `_execute_single_task(self, task_definition)`

Internal method that dispatches task execution to the appropriate agent-specific handler based on `task_definition['agent_spec']['type']`.

* **Parameters**:
  * `task_definition` (`dict`): The definition of the task to execute.
* **Returns**:
  * `any`: The result of the task execution, as returned by the specific agent handler.
* **Raises**:
  * `TaskExecutionError`: If the task execution fails within the handler.

#### `get_task_status(self, task_id)`

Returns the status of a specific task.

* **Parameters**:
  * `task_id` (`str`): The ID of the task.
* **Returns**:
  * `str` or `None`: The status of the task (e.g., "pending", "in-progress", "completed", "failed", "skipped"), or `None` if the task ID is not found in the state manager.

#### `get_task_result(self, task_id)`

Returns the intermediate result of a specific task.

* **Parameters**:
  * `task_id` (`str`): The ID of the task.
* **Returns**:
  * `any` or `None`: The result of the task, or `None` if the task ID is not found, the task is not completed, or the task produced no result.
