# Implementation Plan: Enhancing AIWhisperer for Real AI Interaction

## 1. Introduction

*   **Purpose**: To enable the AIWhisperer runner to interact with a real AI service (specifically Openrouter) for tasks designated as `"ai_interaction"`. This will allow the `simple_country_test` to pass using actual AI-generated responses.
*   **Scope**: This plan details the necessary modifications to the AIWhisperer execution engine and related components. It covers code changes, data flow, error handling, and configuration.
*   **Based on**: Findings from [`./project_dev/in_dev/implement_enough_for_test_country/analysis_summary.md`](./project_dev/in_dev/implement_enough_for_test_country/analysis_summary.md).

## 2. Core Component Modifications: `ExecutionEngine`

*   **File**: [`src/ai_whisperer/execution_engine.py`](./src/ai_whisperer/execution_engine.py)
*   **Method**: `_execute_single_task`
*   **Logic**:
    *   Identify tasks where `task_def.agent_spec.type == "ai_interaction"`.
    *   Extract necessary information for the AI:
        *   Prompt/instructions from `task_def.instructions`.
        *   Content of input artifacts specified in `task_def.input_artifacts` (requiring resolution of paths and reading file contents).
    *   Retrieve conversation history/context from the `StateManager` if the task depends on previous AI interactions.
    *   Delegate the actual AI call to the `AIServiceInteraction` module (see section 3).
    *   Pass the prompt, input artifact content, conversation context, and relevant AI configuration (e.g., model choice, parameters from task or global config) to the `AIServiceInteraction` module.
    *   Receive the AI's response from the `AIServiceInteraction` module.
    *   Format this response as the task's result.
    *   Update the task's state (e.g., to 'COMPLETED') and store its result via the `StateManager`.

## 3. AI Interaction Module: `AIServiceInteraction`

*   **File**: [`src/ai_whisperer/ai_service_interaction.py`](./src/ai_whisperer/ai_service_interaction.py) (This existing module will likely be enhanced).
*   **Responsibilities**:
    *   Encapsulate all direct communication with the AI service (Openrouter).
    *   Define or enhance a method, for example: `execute_ai_interaction(prompt: str, input_artifacts_content: Dict[str, str], conversation_history: List[Dict[str,str]], ai_config: Dict) -> str`.
    *   Construct the request payload for the Openrouter API, including the model, messages (prompt, history, and potentially system messages), and other parameters like temperature, max tokens.
    *   Handle API authentication using the Openrouter API key (fetched from global configuration via `ConfigManager`).
    *   Execute the HTTP API call to Openrouter.
    *   Process the API response:
        *   Extract the relevant content from the AI's reply.
        *   Handle potential API errors or non-successful HTTP status codes.
    *   Implement support for streaming responses from Openrouter, as highlighted in the RFC ([`./project_dev/rfc/simple_run_test_country.md`](./project_dev/rfc/simple_run_test_country.md)), to potentially provide intermediate feedback or handle long responses.

## 4. Configuration Management

*   **Files**:
    *   [`src/ai_whisperer/config.py`](./src/ai_whisperer/config.py) (for `ConfigManager`)
    *   Global configuration files (e.g., `config.yaml` or a dedicated AI service configuration file).
*   **Requirements**:
    *   Securely store and access the Openrouter API key.
    *   Allow specification of default AI model preferences (e.g., model ID, temperature, max tokens) that can be overridden at the task level if needed.
    *   The `AIServiceInteraction` module will use the `ConfigManager` to fetch these settings.

## 5. Data Flow for AI Interaction

The following diagram illustrates the sequence of operations for an `ai_interaction` task:

```mermaid
sequenceDiagram
    participant EE as ExecutionEngine
    participant SM as StateManager
    participant CM as ConfigManager
    participant AIM as AIServiceInteraction
    participant OR as Openrouter

    EE->>SM: Get Task Definition & Dependencies
    SM-->>EE: Task Definition (type: ai_interaction), Resolved Input Artifacts
    EE->>SM: Get Conversation History (if applicable)
    SM-->>EE: Conversation History
    EE->>AIM: Request AI Interaction (prompt, inputs content, history, task-specific AI params)
    AIM->>CM: Get Global AI Config (API Key, default model, etc.)
    CM-->>AIM: AI Configuration
    AIM->>OR: API Call (constructed prompt, model, API key, etc.)
    OR-->>AIM: AI Response (raw, possibly streamed)
    AIM-->>EE: Processed AI Response (text content)
    EE->>SM: Update Task State (result = AI response, status = COMPLETED)
end
```

## 6. Handling AI Response Variations and Validation

*   As noted in the `analysis_summary.md` and RFC ([`./project_dev/rfc/simple_run_test_country.md`](./project_dev/rfc/simple_run_test_country.md)), AI responses can vary.
*   The primary responsibility for handling these variations lies with the validation steps defined in the test plan (e.g., [`./tests/simple_run_test_country/simple_run_test_country_aiwhisperer_config.json`](./tests/simple_run_test_country/simple_run_test_country_aiwhisperer_config.json)). These steps should be designed for flexibility (e.g., using regex, keyword matching, or semantic similarity if advanced).
*   The `ExecutionEngine` will pass the AI's textual response to these validation steps as an input artifact or directly as data.
*   The `AIServiceInteraction` module should ensure it captures the complete and accurate textual response from the AI.
*   Detailed logging of AI prompts and responses by the `AIServiceInteraction` or `ExecutionEngine` will be crucial for debugging validation logic.
*   No direct changes to the existing validation logic within the `simple_country_test` are planned in this phase, assuming they are designed as per the RFC's flexibility requirement.

## 7. Error Handling and Resilience

*   **Within `AIServiceInteraction`**:
    *   **Network Errors**: Implement retries with exponential backoff for transient network issues (e.g., timeouts, DNS failures) when calling Openrouter.
    *   **Openrouter API Errors**:
        *   Handle 4xx errors (e.g., `401 Unauthorized`, `400 Bad Request`, `429 Rate Limit Exceeded`): Log detailed error messages from the API response. For `429`, respect `Retry-After` headers if present.
        *   Handle 5xx server errors: Log and potentially retry a limited number of times.
    *   Raise specific, informative exceptions to be caught by the `ExecutionEngine`.
*   **Within `ExecutionEngine`**:
    *   Catch exceptions propagated from `AIServiceInteraction`.
    *   Update the task state to 'FAILED' and record the error details in the `StateManager`.
    *   Ensure robust logging of all errors to facilitate debugging.

## 8. Context Management for Multi-Turn Conversations

*   The RFC ([`./project_dev/rfc/simple_run_test_country.md`](./project_dev/rfc/simple_run_test_country.md)) emphasizes "token context handling across turns."
*   For tasks that build on previous AI interactions:
    *   The `ExecutionEngine` must retrieve the relevant conversation history (sequence of user/assistant messages) from the `StateManager`. This implies tasks must declare dependencies on prior AI interaction tasks.
    *   This history will be passed to `AIServiceInteraction`.
    *   `AIServiceInteraction` will format this history appropriately (e.g., as a list of message objects) for the Openrouter API request, ensuring the AI has the necessary context.
    *   The `StateManager` needs to store AI interaction results (both the prompt sent and the response received, or at least the AI's response attributed to the 'assistant' role and the prompt as 'user' role) in a structured way that allows easy reconstruction of this history.

## 9. Testing Strategy (Beyond `simple_country_test`)

*   **Unit Tests**:
    *   For `AIServiceInteraction`:
        *   Mock the Openrouter API (e.g., using `requests_mock`).
        *   Test correct request payload construction for various inputs (prompt, history, parameters).
        *   Test parsing of successful responses.
        *   Test handling of different API error codes and network errors.
        *   Test streaming response handling if implemented.
    *   For `ExecutionEngine._execute_single_task`:
        *   Mock `AIServiceInteraction` to simulate successful AI responses and error conditions.
        *   Verify correct delegation of `ai_interaction` tasks.
        *   Verify correct state updates and result storage via a mocked `StateManager`.
*   **Integration Tests**:
    *   While `simple_country_test` serves as a key integration test, consider adding smaller, focused integration tests for the `AIServiceInteraction` module that make controlled, real calls to a non-production/low-cost Openrouter model. This would specifically test the direct interaction with Openrouter (authentication, basic request/response). This should be designed to be quick and minimize flakiness.

## 10. Potential Challenges & Mitigation

*   **API Rate Limits (Openrouter)**:
    *   *Challenge*: Exceeding API call limits.
    *   *Mitigation*: Implement client-side request throttling. Respect `Retry-After` headers. Log when rate limits are encountered. Consider configurable delay between calls.
*   **AI Response Latency**:
    *   *Challenge*: Long delays waiting for AI responses can impact runner performance.
    *   *Mitigation*: Utilize streaming if Openrouter supports it well for the chosen models. `ExecutionEngine` should log long-running AI calls. For non-interactive scenarios, this might be acceptable, but for interactive use cases, this needs careful management.
*   **Cost Management**:
    *   *Challenge*: Uncontrolled API calls leading to high costs.
    *   *Mitigation*: Log token usage (prompt and completion tokens) for each AI call if the API provides this information. Implement warnings or limits in configuration if necessary for development/testing.
*   **API Key Security**:
    *   *Challenge*: Accidental exposure of API keys.
    *   *Mitigation*: Ensure API keys are strictly managed through configuration files (added to `.gitignore`) or environment variables, and never hardcoded.
*   **Consistency of AI Responses**:
    *   *Challenge*: AI responses are non-deterministic, making exact matching difficult for validation.
    *   *Mitigation*: Rely on flexible validation logic (as planned). Encourage designing prompts that guide the AI towards more structured or predictable output formats where possible, without overly constraining creativity.
*   **Maintaining Conversation Context**:
    *   *Challenge*: Ensuring the correct and complete history is passed to the AI for coherent multi-turn interactions.
    *   *Mitigation*: Rigorous design of how `StateManager` stores interaction history and how `ExecutionEngine` retrieves and passes it. Thorough testing of multi-step plans.

## 11. Assumptions

*   An Openrouter API key is available and will be securely configured for the runner to access.
*   The existing [`src/ai_whisperer/ai_service_interaction.py`](./src/ai_whisperer/ai_service_interaction.py) module is the appropriate component to house the Openrouter communication logic, subject to necessary enhancements.
*   The `StateManager` component is capable of storing and retrieving task results and conversation history in a manner suitable for providing context to subsequent AI calls.
*   The `simple_country_test` plan and its validation steps are fundamentally sound for testing this integration, requiring no major rework beyond the AI interaction enablement.

## 12. Out of Scope for this Plan

*   The actual Python code implementation of the described changes.
*   Modifications to the `simple_country_test` plan files ([`./tests/simple_run_test_country/simple_run_test_country_aiwhisperer_config.json`](./tests/simple_run_test_country/simple_run_test_country_aiwhisperer_config.json)) or its associated validation scripts, unless a critical flaw is discovered that directly prevents the engine integration outlined here.
*   Development of any new UI/UX features for displaying AI interactions or results beyond the existing CLI outputs.
*   Fundamental changes to the plan execution model beyond integrating the AI call.