# Documentation Update Plan for Runner Enhancements

This document outlines the plan to update project documentation to reflect the enhancements made to the AIWhisperer runner, particularly focusing on the changes implemented to pass the `simple_country_test`.

## 1. Updates to `./docs/execution_engine.md`

The existing `execution_engine.md` provides a good foundation. The following changes will be made to reflect the enhancements:

*   **`__init__` Method Documentation:**
    *   Update the constructor's signature and parameter descriptions to include `monitor: TerminalMonitor` and `config: dict`.
    *   Explain their roles: `monitor` for displaying execution progress and logs, and `config` for providing global configurations, including AI service details like API keys and default model choices.
    *   Mention the initialization of `self.agent_type_handlers`, a dictionary mapping agent types to their respective handler methods.

*   **"Key Components" Section:**
    *   Add a new bullet point for **"Agent Type Handlers"**:
        *   Explain that the `ExecutionEngine` now uses a dispatch table (`self.agent_type_handlers`) to route tasks to specialized handler methods based on the `agent_spec.type` (e.g., `"ai_interaction"`, `"planning"`, `"validation"`).
    *   Add a new bullet point for **"AI Service Interaction (`OpenRouterAPI`)"**:
        *   Mention that for tasks requiring AI communication, the engine utilizes an instance of the `OpenRouterAPI` class (from `src/ai_whisperer/ai_service_interaction.py`). This component is responsible for the direct communication with the OpenRouter service.

*   **"Processing a Plan (Workflow)" Section:**
    *   Modify step 5, "Execution or Skipping": Clarify that the internal `_execute_single_task` method now acts as a dispatcher. Based on the task's `agent_spec.type`, it calls the appropriate handler (e.g., `_handle_ai_interaction`, `_handle_planning`, `_handle_validation`).

*   **New Major Section: "Agent Task Handling"**
    *   This section will provide details on how tasks with different agent types are processed.
    *   **Sub-section: Handling AI Interaction Tasks (`_handle_ai_interaction`)**
        *   **Purpose**: Explain that this method is invoked for tasks of type `"ai_interaction"` and manages the complete lifecycle of communicating with an AI service.
        *   **Configuration**: Detail how AI configurations are determined by merging global settings (from `self.config['openrouter']`) with any task-specific `ai_config` found in the `agent_spec`.
        *   **AI Service Initialization**: Describe the instantiation of `OpenRouterAPI` using the merged configuration and mention the handling of `ConfigError` if the API key or other essential AI configurations are missing.
        *   **Input Processing & Prompt Construction**:
            *   Explain the extraction of `instructions` from the task definition and `input_artifacts` from the `agent_spec`.
            *   Describe how the content of specified input artifact files is read.
            *   Highlight the specialized prompt construction logic for the `simple_country_test` tasks:
                *   `ask_country`: Uses the content of `landmark_selection.md`.
                *   `ask_capital`: Uses the content of `country_validation_result.md` and proceeds only if country validation passed.
                *   `ask_landmark_in_capital`: Uses `landmark_selection.md` and `capital_validation_result.md`, proceeding only if capital validation passed.
            *   Mention how the system handles scenarios where prerequisite validation steps fail, leading to the AI call being skipped for dependent tasks.
        *   **Conversation History Management**:
            *   Explain how a `messages_history` list is constructed by iterating through the `self.task_queue`. It gathers the prompt and response from previously completed `"ai_interaction"` tasks (results retrieved from `StateManager`) to provide context to the current AI call.
        *   **AI Service Call**:
            *   Describe how the `OpenRouterAPI` instance is used to call either `stream_chat_completion` (for streaming responses) or `chat_completion` (for non-streaming).
            *   Mention that the constructed prompt, conversation history, and AI parameters (model, temperature, etc.) are passed to the AI service.
        *   **Response Handling & Storage**:
            *   Explain how the AI's textual response is processed.
            *   Detail how the result, typically a dictionary containing the original `prompt` sent to the AI and the `response` received, is stored using the `StateManager`.
            *   Describe how the AI's response is written to an output artifact file if specified in `agent_spec.output_artifacts` (e.g., `ai_response_country.txt`).
        *   **Error Handling**: List the specific exceptions from `OpenRouterAPI` that are caught and handled (e.g., `OpenRouterAPIError`, `OpenRouterAuthError`, `OpenRouterRateLimitError`, `OpenRouterConnectionError`). Explain that these are logged and then re-raised as `TaskExecutionError`.
    *   **Sub-section: Handling Planning Tasks (`_handle_planning`)**
        *   Briefly describe its role.
        *   Mention the current specific implementation for the `select_landmark` task, which involves creating the `landmark_selection.md` file with a predefined landmark.
    *   **Sub-section: Handling Validation Tasks (`_handle_validation`)**
        *   Briefly describe its role.
        *   Mention the specific logic for `validate_country`, `validate_capital`, and `validate_landmark_in_capital`. This includes reading AI responses from files generated by previous tasks and creating validation result files (e.g., `country_validation_result.md`).

*   **API Documentation Section:**
    *   Update the description of `_execute_single_task(self, task_definition)`: Clarify that this internal method is no longer a simple placeholder but now serves as a dispatcher to the agent-specific handler methods based on `task_definition['agent_spec']['type']`.
    *   Consider adding brief mentions of the new internal handler methods (`_handle_ai_interaction`, `_handle_planning`, `_handle_validation`) as internal implementation details called by `_execute_single_task`.

*   **General Review**: Perform a general review of the entire document for accuracy and consistency with the implemented changes in `src/ai_whisperer/execution_engine.py`.

## 2. Updates to `./README.md`

The main `README.md` will be updated to include information about the `simple_country_test` and its significance.

*   **New Sub-section (e.g., under "Features" or as a new top-level section like "Core Runner Functionality")**:
    *   **Title Suggestion**: "Demonstrating Core Functionality: The Simple Country Test" or "Runner Capabilities & AI Interaction Testing".
    *   **Content**:
        *   Introduce the enhanced AIWhisperer runner, highlighting its capability to execute complex plans that involve real-time interactions with AI services.
        *   Explain the `simple_country_test` as a key integration test designed to showcase and validate this core functionality.
        *   Describe the purpose of the test: to confirm the runner's ability to:
            *   Orchestrate a sequence of diverse tasks (e.g., planning, AI queries, and validation steps).
            *   Successfully interact with an AI service (OpenRouter) to obtain dynamic responses.
            *   Manage and pass data (as artifacts) between different tasks in the plan.
            *   Maintain conversation history across multiple AI interactions to ensure context awareness.
            *   Execute validation logic based on the outputs received from the AI.
        *   Briefly outline the high-level flow of the `simple_country_test` (e.g., select a landmark, ask AI for its country, validate the country, ask AI for the capital, validate the capital, ask AI if the landmark is in the capital, validate this fact). This will provide a concrete example of the runner's orchestration capabilities.
        *   Emphasize that the successful execution of this test marks a significant milestone, demonstrating the runner's readiness for more complex automated workflows involving AI.