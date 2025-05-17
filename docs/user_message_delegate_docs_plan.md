# Documentation Update Plan: User Message Delegate System

**Phase 1: Information Gathering & Analysis (Completed)**

* Reviewed [`docs/user_message_analysis.md`](docs/user_message_analysis.md:1) for an in-depth understanding of the system's design, purpose, and components.
* Examined [`src/user_message_delegate.py`](src/user_message_delegate.py:1) to understand the `UserMessageDelegate` protocol and the `UserMessageLevel` enum.
* Checked [`src/basic_output_test.py`](src/basic_output_test.py:1) for the reference implementation of `ANSIConsoleUserMessageHandler`.
* Listed files in the [`docs/`](docs/:1) directory to identify existing documentation.
* Read [`docs/delegate_manager_analysis.md`](docs/delegate_manager_analysis.md:1) to understand the role and usage of the `DelegateManager`, which is central to the new system.

**Phase 2: Documentation Strategy**

1. **Create a New Core Document**:
    * A new file, [`docs/user_message_system.md`](docs/user_message_system.md:1), will be created. This document will serve as the primary source of information for the User Message Delegate system.
2. **Update Existing Key Documents**:
    * **[`docs/index.md`](docs/index.md:1)**: This file will be updated to include a link to the new [`docs/user_message_system.md`](docs/user_message_system.md:1), ensuring discoverability.
    * **[`docs/delegate_manager_analysis.md`](docs/delegate_manager_analysis.md:1)**: This document will be updated to briefly mention the `"user_message_display"` event type as a practical example of a notification delegate, linking to [`docs/user_message_system.md`](docs/user_message_system.md:1) for detailed information.
    * **Logging Documentation**: The changes to the logging system (directing internal logs to files only) will be primarily detailed within the new [`docs/user_message_system.md`](docs/user_message_system.md:1). If a dedicated, more general logging document is identified or deemed necessary later, cross-references can be added.

**Phase 3: Content Generation for [`docs/user_message_system.md`](docs/user_message_system.md:1)**

This new document will cover:

* **1. Introduction & Purpose**:
  * Explain the goal: to provide a clear, colored, user-facing message system separate from internal application logs.
  * Briefly mention its benefits (improved user experience, cleaner logs for developers).
* **2. Core Components**:
  * **`UserMessageLevel` Enum**:
    * Definition and purpose.
    * List and describe each level: `INFO`, `DETAIL`.
    * Code example from [`src/user_message_delegate.py`](src/user_message_delegate.py:1).
  * **`UserMessageDelegate` Protocol**:
    * Definition and purpose as a contract for message handlers.
    * Explain the `display_message(self, message: str, level: UserMessageLevel) -> None` method.
    * Code example from [`src/user_message_delegate.py`](src/user_message_delegate.py:1).
  * **`ANSIConsoleUserMessageHandler` (Example Implementation)**:
    * Role as the default handler for console output.
    * Brief overview of its operation (using ANSI escape codes for colors).
    * Reference to its location in [`src/basic_output_test.py`](src/basic_output_test.py:1).
* **3. How to Use the System**:
  * **Displaying User Messages via `DelegateManager`**:
    * The designated event type: `"user_message_display"`.
    * How to invoke: `delegate_manager.invoke_notification(sender: Any, event_type="user_message_display", event_data: Dict[str, Any])`.
    * Structure of `event_data`: `{"message": str, "level": UserMessageLevel}`.
    * Provide a clear code example of invoking a user message.
* **4. Logging System Modifications**:
  * Clarify the separation: User messages go to the console (via delegates), internal logs go to files.
  * Explain changes made to [`src/ai_whisperer/logging_custom.py`](src/ai_whisperer/logging_custom.py:1):
    * Removal of the console handler from `setup_basic_logging()` for general logs.
    * Removal of the legacy `set_active_monitor_handler()` function and related globals.
* **5. System Flow Diagram**:
  * Include the Mermaid diagram from [`docs/user_message_analysis.md#L98`](docs/user_message_analysis.md:98) to visually represent the user message and logging flows.

    ```mermaid
    graph TD
        subgraph User Message Flow
            A[Application Code] -- Generates user message --> B{DelegateManager};
            B -- Invokes "user_message_display" notification --> C[UserMessageDelegate Implementations (e.g., ANSIConsoleUserMessageHandler)];
            C -- Formats with ANSI (message, level) --> D[Console Output (stdout/stderr)];
        end

        subgraph Logging Flow
            F[Application Code] -- Generates log event (LogMessage) --> G{logging_custom.py};
            G -- Writes to file (via FileHandler) --> H[Log File (e.g., logs/aiwhisperer_debug.log)];
            G -.x Does NOT write to console;
        end
    ```

**Phase 4: Content Updates for Existing Files**

* **[`docs/index.md`](docs/index.md:1)**:
  * Add an entry: `- [User Message System](user_message_system.md)` under a relevant section (e.g., "Core Systems" or "Developer Guides").
* **[`docs/delegate_manager_analysis.md`](docs/delegate_manager_analysis.md:1)**:
  * In section `3.1. In ExecutionEngine` or `4.1 Strengths` or as a new example, add:
        > "A key example of a notification event is `"user_message_display"`, used by the User Message System to output formatted messages to the user. For more details, see the [User Message System documentation](user_message_system.md)."

**Phase 5: Review**

* Ensure all information is accurate, clear, and addresses the requirements of the original task.
* Verify that the documentation accurately reflects the implementation details found in [`docs/user_message_analysis.md`](docs/user_message_analysis.md:1), [`src/user_message_delegate.py`](src/user_message_delegate.py:1), and [`src/basic_output_test.py`](src/basic_output_test.py:1).
