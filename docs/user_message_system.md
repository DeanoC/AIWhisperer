# User Message System

## 1. Introduction & Purpose

The User Message Delegate system is designed to provide a clear, colored, user-facing message system that is separate from internal application logs. This separation improves the user experience by presenting important information in a clear and easily digestible format, while also providing cleaner logs for developers by directing internal debugging and informational messages to log files only.

## 2. Core Components

### UserMessageLevel Enum

The `UserMessageLevel` enum defines the different levels or types of user messages. These levels are used to categorize messages and can influence how they are displayed (e.g., by using different colors in the console).

```python
from enum import Enum

class UserMessageLevel(Enum):
    INFO = "INFO"
    DETAIL = "DETAIL"
```

* `INFO`: General informational messages.
* `DETAIL`: Provides more verbose or detailed information to the user.

### UserMessageDelegate Protocol

The `UserMessageDelegate` protocol defines the contract for any class that can handle and display user messages. Any class implementing this protocol can be registered with the `DelegateManager` to receive and process user messages.

```python
from typing import Protocol
from src.user_message_delegate import UserMessageLevel

class UserMessageDelegate(Protocol):
    def display_message(self, message: str, level: UserMessageLevel) -> None:
        ...
```

The `display_message` method is the core of the protocol. Implementations of this method are responsible for taking the message string and its corresponding `UserMessageLevel` and presenting it to the user in an appropriate way (e.g., printing to the console, displaying in a GUI, sending a notification).

### ANSIConsoleUserMessageHandler (Example Implementation)

The `ANSIConsoleUserMessageHandler` is a reference implementation of the `UserMessageDelegate` protocol. It is designed to display user messages directly to the console using ANSI escape codes to add color based on the `UserMessageLevel`. This handler serves as the default fallback for displaying user messages in a terminal environment.

This handler can be found in [`src/basic_output_test.py`](src/basic_output_test.py:1).

## 3. How to Use the System

User messages are displayed by leveraging the `DelegateManager`. The designated event type for user message display is `"user_message_display"`.

To display a user message, you need to invoke a notification on the `DelegateManager` with this event type and provide the message content and level in the `event_data`.

```python
from src.ai_whisperer.delegate_manager import DelegateManager
from src.user_message_delegate import UserMessageLevel

# Assuming you have an instance of DelegateManager available
delegate_manager = DelegateManager() # Or obtain the existing instance

message_content = "This is an informational message for the user."
message_level = UserMessageLevel.INFO

delegate_manager.invoke_notification(
    sender=None, # The object sending the message (can be None)
    event_type="user_message_display",
    event_data={"message": message_content, "level": message_level}
)

# Example with an error message
error_message = "An error occurred during the process."
error_level = UserMessageLevel.ERROR

delegate_manager.invoke_notification(
    sender=None,
    event_type="user_message_display",
    event_data={"message": error_message, "level": error_level}
)
```

When `invoke_notification` is called with `"user_message_display"`, the `DelegateManager` will iterate through all registered delegates for this event type and call their `display_message` method with the provided message and level.

## 4. Logging System Modifications

To ensure a clear separation between user messages and internal application logs, modifications were made to the logging system, primarily within [`src/ai_whisperer/logging_custom.py`](src/ai_whisperer/logging_custom.py:1).

The key changes include:

* **Removal of Console Handler for General Logs**: The default console handler that would typically display general application logs (DEBUG, INFO, WARNING, ERROR) to the console has been removed from the basic logging configuration (`setup_basic_logging()`). This ensures that standard `logging` calls only write to configured file handlers (e.g., `logs/aiwhisperer_debug.log`).
* **Removal of Legacy Monitor Handler**: The legacy `set_active_monitor_handler()` function and its associated global variables were removed. The new User Message Delegate system replaces the functionality previously handled by this legacy code, providing a more flexible and extensible approach to displaying user-facing information.

This setup ensures that developers can use the standard Python `logging` module for internal application state and debugging information, while user-facing communication is handled separately through the `DelegateManager` and `UserMessageDelegate` implementations.

## 5. System Flow Diagram

The following diagram illustrates the flow of user messages and internal logs within the system:

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
