# AI Loop Refactor Analysis (Subtask a332a074)

## 1. Introduction

This document analyzes the current implementation of `ai_whisperer/ai_loop.py` to understand its dependencies on `ai_whisperer/execution_engine.py` and `ai_whisperer/state_management.py`. The goal is to identify key areas for refactoring to make the AI loop a standalone, general-purpose component, decoupled from these specific modules where appropriate, and capable of supporting interactive sessions with streaming, primarily leveraging the `DelegateManager` for external interaction and control.

## 2. Dependencies on `ExecutionEngine`

The `ai_loop.py` module, specifically the `run_ai_loop` function, exhibits several dependencies on the `ExecutionEngine` instance passed to it.

**Key Dependencies:**

* **Configuration Access:**
  * The AI loop retrieves various configuration parameters directly from `engine.config`. This includes:
    * AI temperature: `engine.config.get('ai_temperature', ...)` ([`ai_whisperer/ai_loop.py:96`](ai_whisperer/ai_loop.py:96), [`ai_whisperer/ai_loop.py:347`](ai_whisperer/ai_loop.py:347))
    * AI model identifiers: `engine.config.get('openrouter', {}).get('model')`, `engine.config.get('ai_model')`, `engine.config.get('model')` ([`ai_whisperer/ai_loop.py:105-108`](ai_whisperer/ai_loop.py:105-108), [`ai_whisperer/ai_loop.py:352-355`](ai_whisperer/ai_loop.py:352-355))
* **AI Service Interaction:**
  * The loop directly calls `engine.openrouter_api.call_chat_completion(...)` for all interactions with the AI model ([`ai_whisperer/ai_loop.py:112`](ai_whisperer/ai_loop.py:112), [`ai_whisperer/ai_loop.py:359`](ai_whisperer/ai_loop.py:359)). This tightly couples the loop to the `OpenRouterAIService` implementation.
  * It accesses `engine.openrouter_api.tools` for debugging purposes ([`ai_whisperer/ai_loop.py:99-100`](ai_whisperer/ai_loop.py:99-100)), which is specific to the `OpenRouterAIService` structure.
* **Global Shutdown Event:**
  * The loop checks `engine.shutdown_event.is_set()` to handle graceful termination ([`ai_whisperer/ai_loop.py:165`](ai_whisperer/ai_loop.py:165), [`ai_whisperer/ai_loop.py:167`](ai_whisperer/ai_loop.py:167)). This relies on a shutdown mechanism managed by the `ExecutionEngine`.
* **Delegate Manager Context:**
  * The `engine` instance is passed as a contextual argument to `delegate_manager.invoke_notification()` and `delegate_manager.invoke_control()` calls within the AI loop (e.g., [`ai_whisperer/ai_loop.py:82`](ai_whisperer/ai_loop.py:82), [`ai_whisperer/ai_loop.py:153`](ai_whisperer/ai_loop.py:153)). The `DelegateManager` itself is designed as a system-wide mechanism for observation and control, decoupled from specific UI implementations. While the `engine` object provides context to delegates, the refactored loop should ensure that any context passed to delegates it invokes is appropriately scoped and doesn't unnecessarily expose internals if a more focused context suffices.

**Nature of Dependencies:**
The dependencies on `ExecutionEngine` are primarily for accessing shared services (AI API, configuration) and global state (shutdown event). The `ExecutionEngine` acts as a service locator and context provider for some AI loop operations.

## 3. Dependencies on `StateManager` (and `ContextManager`)

The `ai_loop.py` directly depends on the `ContextManager` interface for managing conversation history. Its relationship with `StateManager` is indirect.

**Key Dependencies/Interactions:**

* **Direct Dependency on `ContextManager`:**
  * The `run_ai_loop` function receives a `context_manager: ContextManager` instance as an argument ([`ai_whisperer/ai_loop.py:19`](ai_whisperer/ai_loop.py:19)).
  * It uses `ContextManager` methods extensively:
    * `context_manager.clear_history()` ([`ai_whisperer/ai_loop.py:58`](ai_whisperer/ai_loop.py:58))
    * `context_manager.add_message(...)` (multiple locations, e.g., [`ai_whisperer/ai_loop.py:134`](ai_whisperer/ai_loop.py:134))
    * `context_manager.get_history()` (multiple locations, e.g., [`ai_whisperer/ai_loop.py:339`](ai_whisperer/ai_loop.py:339))
* **Indirect Relationship with `StateManager`:**
  * `ai_loop.py` itself does not directly instantiate or call methods on `StateManager`.
  * The `ContextManager` instance it receives is typically managed and persisted by `StateManager`. The `ExecutionEngine` is responsible for initializing `StateManager` ([`ai_whisperer/execution_engine.py:34`](ai_whisperer/execution_engine.py:34)) and potentially retrieving/providing the task-specific `ContextManager` to the `ai_loop`.
  * `StateManager` includes logic to serialize and deserialize `ContextManager` instances for persistence ([`ai_whisperer/state_management.py:106-132`](ai_whisperer/state_management.py:106-132), [`ai_whisperer/state_management.py:199`](ai_whisperer/state_management.py:199)).

**Nature of Dependencies:**
The primary dependency is on the `ContextManager` abstraction for handling conversation history. The `ai_loop` is decoupled from the persistence concerns of this history, which are handled by `StateManager` (via `ExecutionEngine`).

## 4. Key Areas for Refactoring in `ai_loop.py`

To achieve a standalone, general-purpose AI loop, the following areas require refactoring:

1. **Decouple from `ExecutionEngine` Specifics:**
    * **Configuration:**
        * **Action:** Pass necessary configurations (e.g., AI model, temperature, API details) directly to the AI loop or through a dedicated configuration object, instead of accessing `engine.config`.
    * **AI Service Interaction:**
        * **Action:** Introduce an abstract `AIService` interface. The AI loop will interact with this interface, which will be responsible for the specifics of calling different AI providers (e.g., OpenRouter, OpenAI). The current `engine.openrouter_api` calls would be replaced by calls to this interface.
        * **Action:** Tool schemas/definitions required for AI calls should be obtained via a more abstract mechanism, possibly directly from the `ToolRegistry` but formatted by the `AIService` implementation for the target AI.
    * **Shutdown Event:**
        * **Action:** The loop should accept a generic `threading.Event` or `asyncio.Event` for shutdown signals, or define its own API for stopping, which can be triggered via `DelegateManager`.

2. **Leverage `DelegateManager` for Interaction and Control:**
    * **Current:** The AI loop uses `DelegateManager` for notifications (e.g., `ai_loop_started`, `ai_response_received`) and control (e.g., `ai_loop_request_pause`).
    * **Action:** The refactored AI loop should continue to integrate deeply with the `DelegateManager` as the primary mechanism for external observation (e.g., streaming updates, state changes) and control (pause, resume, stop, receiving user messages for interactive sessions).
    * **Action:** The context provided to delegates invoked by the loop (currently the `engine` object) should be reviewed. If the full `engine` context is not required by delegates reacting to AI loop events, a more focused context object (e.g., an `AILoopContext` or specific event data) should be passed to minimize coupling.

3. **Decouple from `StateManager` (Persistence Concerns):**
    * **Current State:** The loop correctly uses a `ContextManager` instance passed to it. This is good.
    * **Action (Confirmation):** Ensure the loop remains dependent only on the `ContextManager` *interface* and does not assume anything about its persistence. The component *using* the AI loop would be responsible for providing a `ContextManager` and handling its persistence if needed.

4. **Support Interactive Sessions with Streaming:**
    * **AI Service Interaction for Streaming:**
        * **Action:** Modify the `AIService` interface (and its implementations) to support streaming responses (e.g., yielding tokens, partial tool calls).
    * **Loop Logic for Streaming:**
        * **Action:** Refactor the AI loop to be asynchronous (e.g., using `async def` and `await`).
        * **Action:** Adapt the loop's internal logic to process partial responses incrementally as they arrive from the streaming `AIService`. This includes updating conversation history and invoking delegates (via `DelegateManager`) for partial updates.
    * **Tool Call Streaming:**
        * **Action:** Design how streamed tool call information is handled and processed.

5. **Enhance General Purpose Capabilities:**
    * **System Prompt:**
        * **Action:** Make the system prompt configurable, passed in as an argument or part of the AI loop's configuration, instead of being hardcoded ([`ai_whisperer/ai_loop.py:67-73`](ai_whisperer/ai_loop.py:67-73)).
    * **Tool Usage Instructions:**
        * **Action:** Abstract the way tool definitions and their AI-facing descriptions are provided to the loop. It should not be tightly coupled to the current `ToolRegistry`'s `get_ai_prompt_instructions` method.
    * **Error Handling and Reporting:**
        * **Action:** Provide more configurable error handling and allow the loop to report errors back to its caller (potentially via `DelegateManager` or return values) in a structured way, beyond just raising `TaskExecutionError`.
    * **Tool Execution (Optional Decoupling):**
        * **Action (Consider):** For maximum generality, consider an option where the AI loop identifies a tool call but delegates the actual execution of the tool to the calling component (perhaps signaled via `DelegateManager`). The loop would then pass the tool execution result back to the AI. The current fallback for plain text tool calls ([`ai_whisperer/ai_loop.py:408-439`](ai_whisperer/ai_loop.py:408-439)) should also be made more generic or configurable.

6. **Internal Control Mechanisms:**
    * **Action:** Internal mechanisms for pause/resume (like `_ai_loop_pause_event` and `_ai_loop_paused` - [`ai_whisperer/ai_loop.py:53-54`](ai_whisperer/ai_loop.py:53-54)) will be managed by the loop in response to control signals received via `DelegateManager`.

## 5. Conclusion

The current `ai_loop.py` is coupled with `ExecutionEngine` for configuration, AI service access, and global state like shutdown events. Its dependency on `StateManager` is indirect, primarily relying on a `ContextManager` instance for conversation history. The `DelegateManager` is already used for some notifications and control.

Refactoring will involve:

* Injecting dependencies like configuration and an abstract AI service interface.
* Strengthening the use of `DelegateManager` as the primary channel for external interaction, control (pause, stop, messages), and observation (streaming data).
* Making system prompts and tool handling more generic.
* Implementing asynchronous operations to support streaming.

These changes will enable the AI loop to function as a more versatile and reusable component, suitable for various interactive and streaming AI applications, well-integrated with the project's `DelegateManager` philosophy.
