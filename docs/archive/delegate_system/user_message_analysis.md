# Analysis and Design: User Message Delegate System

## 1. Introduction

The goal is to implement a User Message Delegate system within the AIWhisperer application. This system will be responsible for displaying user-facing messages with ANSI colored output in the console. A key requirement is to separate these user messages from internal application logs, with the latter being directed exclusively to log files. This will improve the clarity of information presented to the user and streamline debugging by isolating application logs.

This document outlines the necessary components, their interactions, and key design considerations based on the RFC ([`project_dev/rfc/add_user_message_delegate.md`](project_dev/rfc/add_user_message_delegate.md:1)) and an analysis of the existing codebase.

## 2. Core Requirements

* **User-Facing Messages:** Provide a dedicated mechanism for displaying messages intended for the end-user.
* **ANSI Colored Output:** Messages should be color-coded in the console based on their severity or type (e.g., INFO, WARNING, ERROR, SUCCESS).
* **Delegate System Integration:** Leverage the existing `DelegateManager` ([`src/ai_whisperer/delegate_manager.py`](src/ai_whisperer/delegate_manager.py:1)) for extensibility.
* **Separation from Logs:** Application logs (debug, internal info, etc.) must be written to files only and not appear on the console alongside user messages.
* **Fallback Mechanism:** A basic ANSI colored console output handler will serve as the default implementation.
* **Extensibility:** The system should allow for future enhancements, such as GUI-based message display.

## 3. Proposed Components

### 3.1. `UserMessageLevel` Enum

A new enumeration to define the types/levels of user messages, influencing their display (e.g., color).

```python
from enum import Enum

class UserMessageLevel(Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DETAIL = "DETAIL" # For more verbose user-facing information
```

### 3.2. `UserMessageDelegate` Protocol/Interface

A protocol defining the contract for any class that can handle user messages.

```python
from typing import Protocol

class UserMessageDelegate(Protocol):
    def display_message(self, message: str, level: UserMessageLevel) -> None:
        ...
```

### 3.3. `ANSIConsoleUserMessageHandler`

The default/fallback implementation of the `UserMessageDelegate`. This class will:

* Implement the `display_message` method.
* Format the message string with appropriate ANSI escape codes based on the `UserMessageLevel`.
* Print the formatted message to `sys.stdout` or `sys.stderr`.

Example (conceptual):

```python
import sys

class ANSIConsoleUserMessageHandler: # Implements UserMessageDelegate
    COLOR_MAP = {
        UserMessageLevel.INFO: "\033[94m",  # Blue
        UserMessageLevel.DETAIL: "\033[90m", # Bright Black (Gray)
        "RESET": "\033[0m"
    }

    def display_message(self, message: str, level: UserMessageLevel) -> None:
        color_code = self.COLOR_MAP.get(level, "")
        reset_code = self.COLOR_MAP["RESET"]
        print(f"{color_code}{level.value}: {message}{reset_code}")

```

### 3.4. `DelegateManager` Integration

* The `ANSIConsoleUserMessageHandler` (or any other user message handler) will be registered with the global `DelegateManager` instance.
* A specific event type string, e.g., `"user_message_display"`, will be used for registration and invocation.
* Application code wishing to display a user message will call `delegate_manager.invoke_notification(sender=self, event_type="user_message_display", event_data={"message": "...", "level": UserMessageLevel.INFO})`.

## 4. Logging System Changes ([`src/ai_whisperer/logging_custom.py`](src/ai_whisperer/logging_custom.py:1))

To ensure application logs are directed to files *only* and do not interfere with user messages on the console:

* **Modify `setup_basic_logging()` ([`src/ai_whisperer/logging_custom.py:92`](src/ai_whisperer/logging_custom.py:92)):**
  * The `console_handler` ([`src/ai_whisperer/logging_custom.py:106`](src/ai_whisperer/logging_custom.py:106)) should be removed from the list of handlers passed to `logging.basicConfig` ([`src/ai_whisperer/logging_custom.py:121`](src/ai_whisperer/logging_custom.py:121)).
  * Alternatively, if `setup_logging` with a YAML configuration is the primary method, ensure the default console handler for general logs is disabled or removed in that configuration as well.
  * The `FileHandler` ([`src/ai_whisperer/logging_custom.py:115`](src/ai_whisperer/logging_custom.py:115)) setup for writing logs to `logs/aiwhisperer_debug.log` should remain, ensuring logs are captured in files.

* **Remove Legacy Monitor Handler Code:**
  * The function `set_active_monitor_handler()` ([`src/ai_whisperer/logging_custom.py:177`](src/ai_whisperer/logging_custom.py:177)) and its associated global variables (`active_monitor_handler` ([`src/ai_whisperer/logging_custom.py:172`](src/ai_whisperer/logging_custom.py:172)), `_suppressed_handlers_state` ([`src/ai_whisperer/logging_custom.py:175`](src/ai_whisperer/logging_custom.py:175))) are legacy and will be removed from [`src/ai_whisperer/logging_custom.py`](src/ai_whisperer/logging_custom.py:1). The new User Message Delegate system supersedes this functionality.
  * The `ANSIConsoleUserMessageHandler` will write directly to `stdout/stderr`, not as a `logging.Handler`, to avoid conflicts with the logging system's handler management.

## 5. Interactions

```mermaid
graph TD
    subgraph User Message Flow
        A[Application Code] -- Generates user message --> B{DelegateManager};
        B -- Invokes "user_message_display" notification --> C[ANSIConsoleUserMessageHandler];
        C -- Formats with ANSI (message, level) --> D[Console Output (stdout/stderr)];
        B -- Future: Invokes other delegates --> E[e.g., GUIOutputMessageHandler];
    end

    subgraph Logging Flow
        F[Application Code] -- Generates log event (LogMessage) --> G{logging_custom.py};
        G -- Writes to file (via FileHandler) --> H[Log File (e.g., logs/aiwhisperer_debug.log)];
        G -.x Does NOT write to console;
    end
```

## 6. Design Considerations

* **ANSI Color Mapping:** The `COLOR_MAP` in `ANSIConsoleUserMessageHandler` should provide a clear and accessible set of default colors. Consider making this configurable in the future.
* **Thread Safety:** The `DelegateManager` already uses `threading.Lock` ([`src/ai_whisperer/delegate_manager.py:11`](src/ai_whisperer/delegate_manager.py:11)). The `ANSIConsoleUserMessageHandler` writing to `stdout/stderr` via `print()` is generally thread-safe for distinct lines.
* **Testability:**
  * The "basic output test class" mentioned in the RFC ([`project_dev/rfc/add_user_message_delegate.md:13`](project_dev/rfc/add_user_message_delegate.md:13)) refers to the `ANSIConsoleUserMessageHandler` itself or a test utility.
  * A mock `UserMessageDelegate` implementation can be registered during tests to capture and assert displayed messages and their levels.
* **Error Handling:** The `ANSIConsoleUserMessageHandler` should gracefully handle unknown message levels, perhaps defaulting to a standard color or no color.
* **Windows ANSI Support:** Ensure ANSI escape codes work as expected on Windows (modern Windows Terminal supports them, but older `cmd.exe` might require `colorama` or similar libraries if compatibility is a concern, though this might be out of scope for the initial implementation).
* **Clarity of `UserMessageLevel` vs. `LogLevel`:** The `UserMessageLevel` is for user-facing communication. The existing `LogLevel` ([`src/ai_whisperer/logging_custom.py:12`](src/ai_whisperer/logging_custom.py:12)) in `logging_custom.py` is for internal application logging. These should remain distinct.

## 7. Impact on Existing Code

* Instances throughout the codebase that currently use `print()` for user-facing messages or `logging.info()` (etc.) directed to the console for user feedback will need to be refactored.
* These points will be updated to use `delegate_manager.invoke_notification(...)` with the new `"user_message_display"` event type.
* The `set_active_monitor_handler` function and related globals will be removed from [`src/ai_whisperer/logging_custom.py`](src/ai_whisperer/logging_custom.py:1).

## 8. Conclusion

The proposed User Message Delegate system, centered around a new delegate type, a dedicated `UserMessageLevel` enum, and an `ANSIConsoleUserMessageHandler`, will effectively separate user-facing communication from internal logging. By modifying the logging system to output only to files and removing legacy console handling code, and routing user messages through this new delegate, the application will provide clearer, colored console output for users while maintaining robust logging for developers. This design aligns with the RFC and provides a foundation for future enhancements to user message display.
