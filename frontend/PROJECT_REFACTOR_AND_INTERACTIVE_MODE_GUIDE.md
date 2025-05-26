# Project Refactor and Interactive Mode Guide

## 1. Overview of Current State

The codebase is in a significant refactoring phase, primarily focused on improving the AI loop and associated components. The delegate system (`DelegateManager`) is a central piece, facilitating communication and control between different parts of the application. The previous Textual-based interactive mode has been abandoned, and a new JSON-RPC over WebSocket interface to a TypeScript frontend is planned.

Based on the current unit tests, here's a breakdown of component status:

* **AILoop (`ai_whisperer.ai_loop.ai_loopy.AILoop`):**
  * This is a core focus of the refactor. Tests (`test_ai_loop.py`, `test_ai_loop_delegates.py`, `test_refactored_ai_loop.py`) show active development.
  * It heavily utilizes the delegate system for notifications (session start/end, errors, AI message chunks, tool calls, status changes) and control (start, stop, pause, resume, send user message, provide tool result). This is an excellent foundation for the new interactive mode.
  * Async operations and tool handling are being integrated.
  * `test_refactored_ai_loop.py` appears to be the most current test suite for `AILoop`.
  * **Status:** _DONE_

* **Execution Engine (`ai_whisperer.execution_engine.ExecutionEngine`):**
  * Interacts with `AILoop` and also uses the delegate system for notifications (`engine_started`, `engine_stopped`, `task_execution_started`, etc.) and control (`engine_request_pause`, `engine_request_stop`).
  * Tests are adapting to async changes.
  * **Status:** _IN PROGRESS_

* **CLI (`ai_whisperer.cli`):**
  * Standard CLI argument parsing (`test_cli.py`) seems partially functional and is important for launching the application (e.g., starting the WebSocket server).
  * Interactive CLI tests (`test_cli_interactive.py`) are heavily skipped or broken, directly reflecting the removal of the old Textual UI. `InteractiveUIBase` is likely obsolete.
  * **Status:** _PARTIALLY DONE_

* **AI Service (`ai_whisperer.ai_service.openrouter_ai_service.OpenRouterAIService`):**
  * Appears relatively stable and well-tested, focusing on OpenRouter.
  * Handles streaming, tool definitions, and various advanced OpenRouter features.
  * **Status:** _DONE_

* **Tools (`ai_whisperer.tools`):**
  * A base `AITool` class and `ToolRegistry` are in place.
  * Basic file operation tools (`ReadFileTool`, `WriteFileTool`) and command execution (`ExecuteCommandTool`) are tested.
  * The AILoop correctly delegates tool execution and processes results.
  * **Status:** _DONE_

* **State & Context Management:**
  * `StateManager` (`test_state_management.py`) is functional for saving/loading task states, results, and conversation history.
  * `ContextManager` (`test_context_manager.py`) handles basic conversation history.
  * **Status:** _DONE_

* **Logging & Prompts:**
  * A custom logging structure (`LogMessage`, `ComponentType` in `test_logging.py`) is defined.
  * `PromptSystem` (`test_prompt_system.py`) is in place for loading and resolving prompts.
  * **Status:** _DONE_

* **Other Components:**
  * **Plan Ingestion/Parsing (`ParserPlan`):** Under development for handling single-file and overview plans.
  * **Postprocessing (`postprocessing.*`):** Scripted postprocessing steps are being developed and tested.
  * **Agent Handlers (e.g., `code_generation`):** Integrating `AILoop` for AI interactions.
  * **Subtask Generator:** Uses `OpenRouterAIService` and `PromptSystem`.
  * **Status:** _IN PROGRESS_

## 2. Path to New Interactive Mode (JSON-RPC over WebSocket)

The existing architecture, particularly the `DelegateManager`, is well-suited for the new interactive mode.

### Leveraging the Existing Delegate System

* **Control:** The `AILoop` and `ExecutionEngine` already expose control functionalities (start, stop, pause, resume, send messages, provide tool results) via delegate invocations. The WebSocket server will translate incoming JSON-RPC requests into these control delegate calls.
* **Notifications:** Both `AILoop` and `ExecutionEngine` emit a rich set of notifications (session status, AI responses, tool interactions, task progress, errors). These can be captured by a new delegate and forwarded as JSON-RPC notifications over WebSockets to the frontend.
* **Status:** _DONE (foundation present, but new components needed)_

### Required New Components

1. **`JsonRpcInteractiveDelegate`:**
    * This new delegate will be responsible for bridging the Python backend with the WebSocket layer.
    * **Receiving Control:** It will register handlers for specific JSON-RPC methods (e.g., `ui.start_session`, `ui.send_user_message`). When a request comes from the frontend, this delegate will call the appropriate `delegate_manager.invoke_control(...)` method.
    * **Sending Notifications:** It will subscribe to relevant notification events from `AILoop`, `ExecutionEngine`, and potentially other components. Upon receiving a notification, it will format it as a JSON-RPC notification and send it to the connected WebSocket client(s).
    * Ensure all data passed (especially `event_data` in notifications) is JSON serializable.
    * **Status:** _TODO_

2. **WebSocket Server:**
    * A Python WebSocket server (e.g., using the `websockets` library).
    * Manages client connections.
    * Passes incoming JSON-RPC messages to the `JsonRpcInteractiveDelegate`.
    * Receives formatted notifications from the `JsonRpcInteractiveDelegate` and sends them to the appropriate client(s).
    * **Status:** _TODO_

## 3. Recommended Development Roadmap

The primary goal is to get back to a stable development status while progressively implementing the new interactive mode.

**Phase 1: Stabilize Core & Non-Interactive Tests (Critical First Step)**

* **Objective:** Ensure the backend logic is sound before building the new UI.
* **Actions:**
    1. **Review & Fix Core Tests:**
        * Prioritize fixing failing tests in:
            * `test_ai_loop.py`
            * `test_ai_loop_delegates.py`
            * `test_refactored_ai_loop.py` (seems to be the latest for AILoop)
            * `test_execution_engine.py`
            * `test_execution_engine_delegates.py`
        * Focus on tests that *do not* depend on the old interactive UI.
    2. **Address `test_cli_interactive.py`:**
        * Mark most tests as `pytest.mark.skip(reason="Old interactive mode removed, new JSON-RPC mode pending")` or `pytest.mark.xfail(...)`.
        * Salvage any tests related to CLI argument parsing for starting the application in a "server" mode if applicable.
    3. **Verify Other Unit Tests:** Ensure tests for `AIService`, `StateManager`, `ContextManager`, `ToolRegistry`, `PromptSystem`, `PlanParser`, `Postprocessing` steps, and agent handlers are passing for their non-interactive functionalities.
* **Outcome:** A stable backend with reliable core logic.
* **Status:** _IN PROGRESS / PARTIALLY DONE_

**Phase 2: Design and Implement `JsonRpcInteractiveDelegate`**

* **Objective:** Create the bridge between the application's delegate system and the future WebSocket layer.
* **Actions:**
    1. **Define JSON-RPC API:** _TODO_
    2. **Implement `JsonRpcInteractiveDelegate`:** _TODO_
    3. **Unit Test `JsonRpcInteractiveDelegate`:** _TODO_
* **Outcome:** A testable delegate ready for integration with a WebSocket server.
* **Status:** _TODO_

**Phase 3: Implement WebSocket Server**

* **Objective:** Establish the communication channel.
* **Actions:**
    1. Choose a WebSocket library (e.g., `websockets`). _TODO_
    2. Implement the server to:
        * Accept client connections.
        * Parse incoming JSON-RPC messages.
        * Route requests to the `JsonRpcInteractiveDelegate`.
        * Receive messages from `JsonRpcInteractiveDelegate` to send to clients.
    3. Add a CLI command to start the application in this server mode (e.g., `ai-whisperer serve`). _TODO_
* **Outcome:** A running WebSocket server capable of basic JSON-RPC message exchange.
* **Status:** _TODO_

**Phase 4: Develop TypeScript Frontend Client**

* **Objective:** Build the new user interface.
* **Actions:**
    1. Set up the TypeScript project. _TODO_
    2. Implement WebSocket connection logic. _TODO_
    3. Create UI components to send JSON-RPC requests defined in Phase 2. _TODO_
    4. Implement handlers for JSON-RPC notifications from the server to update the UI dynamically (e.g., display streaming AI responses, show tool calls, update task statuses). _TODO_
* **Outcome:** A functional frontend that can interact with the backend.
* **Status:** _TODO_

**Phase 5: Integration Testing and Refinement**

* **Objective:** Ensure the entire system works end-to-end.
* **Actions:**
    1. Thoroughly test all interactive features. _TODO_
    2. Refine the JSON-RPC API and UI based on testing. _TODO_
    3. Address any remaining bugs or performance issues. _TODO_
* **Outcome:** A stable, working interactive mode.
* **Status:** _TODO_

## 4. Test Strategy

* **Unit Tests:** Continue maintaining and expanding unit tests for all backend components. Focus on testing individual modules in isolation.
  * The `test_refactored_ai_loop.py` provides a good model for testing async components with `AsyncMock`.
  * Ensure proper cleanup of asyncio tasks in tests to prevent warnings (as seen in some existing tests).
  * **Status:** _PARTIALLY DONE_
* **Integration Tests:**
  * Once the `JsonRpcInteractiveDelegate` and WebSocket server are in place, write integration tests that simulate a WebSocket client interacting with the server, verifying the JSON-RPC communication and delegate interactions.
  * Later, end-to-end tests involving the actual TypeScript frontend can be considered (e.g., using tools like Playwright or Cypress if the UI becomes complex).
  * **Status:** _TODO_
* **Obsolete Tests:** Tests in `test_cli_interactive.py` related to the old Textual UI should be removed or heavily refactored if any part is still relevant to a non-UI interactive startup.
  * **Status:** _PARTIALLY DONE_

## 5. Conclusion

The refactor is progressing, and the delegate system is a strong asset for the new interactive mode. Prioritizing the stabilization of core backend components and their tests (Phase 1) is crucial. After that, a phased approach to building the JSON-RPC delegate, WebSocket server, and finally the frontend client will provide a structured path to restoring and enhancing interactive capabilities. This approach allows for incremental progress and testing at each stage.
