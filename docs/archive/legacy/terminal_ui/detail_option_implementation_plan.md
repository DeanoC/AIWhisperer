# Plan: Add Detail Level Option to ANSIConsoleUserMessageHandler and CLI

## 1. Introduction

This document outlines the plan to implement a detail level option for the `ANSIConsoleUserMessageHandler` and expose it as a command-line interface (CLI) argument. This will allow users to control the verbosity of messages displayed by the application.

## 2. Requirements

Based on the RFC ([`project_dev/rfc/add_detail_cli_option.md`](project_dev/rfc/add_detail_cli_option.md:1)):

- Add a detail level setting to `ANSIConsoleUserMessageHandler`.
- Allow this setting to be changed at runtime.
- Add a CLI option to control this detail level.
- The default detail level should be `INFO`.
- Messages with level `DETAIL` should provide more granular information than `INFO`.
- The primary logic for filtering messages based on the detail level should reside in `ANSIConsoleUserMessageHandler.display_message()`.
- `ANSIConsoleUserMessageHandler` will require a new member variable to store the current detail level and methods to get/set it.

## 3. Affected Files and Modules

- **[`src/user_message_delegate.py`](src/user_message_delegate.py:1):** Contains the `UserMessageLevel` enum. (Likely no changes needed as `INFO` and `DETAIL` already exist).
- **[`src/basic_output_display_message.py`](src/basic_output_display_message.py:1):** Contains the `ANSIConsoleUserMessageHandler` class. This will require the most significant changes.
- **[`src/ai_whisperer/cli.py`](src/ai_whisperer/cli.py:1):** Handles CLI argument parsing. A new global argument will be added here.
- **[`src/ai_whisperer/main.py`](src/ai_whisperer/main.py:1):** Where `ANSIConsoleUserMessageHandler` is instantiated and the CLI arguments are processed to set the initial detail level.

## 4. Implementation Plan

### 4.1. `UserMessageLevel` Enum (Review)

File: [`src/user_message_delegate.py`](src/user_message_delegate.py:1)

- **Action:** Review the existing `UserMessageLevel` enum.

    ```python
    class UserMessageLevel(Enum):
        INFO = "INFO"
        DETAIL = "DETAIL"
        # ...
    ```

- **Confirmation:** The enum already supports `INFO` and `DETAIL`. No changes are anticipated here. The convention will be that setting the level to `DETAIL` means both `INFO` and `DETAIL` messages are shown. Setting to `INFO` means only `INFO` messages are shown.

### 4.2. Modify `ANSIConsoleUserMessageHandler`

File: [`src/basic_output_display_message.py`](src/basic_output_display_message.py:1)

- **Add Member Variable:**
  - In the `__init__` method (or add one if it doesn't exist), initialize `self.current_detail_level`:

        ```python
        from user_message_delegate import UserMessageLevel # Ensure import

        class ANSIConsoleUserMessageHandler(UserMessageDelegate):
            def __init__(self):
                super().__init__() # If UserMessageDelegate has an __init__
                self.current_detail_level: UserMessageLevel = UserMessageLevel.INFO # Default
        ```

- **Add Setter Method:**

    ```python
    def set_detail_level(self, level: UserMessageLevel) -> None:
        if not isinstance(level, UserMessageLevel):
            raise ValueError(f"Invalid detail level type: {type(level)}. Must be UserMessageLevel enum.")
        self.current_detail_level = level
    ```

- **Add Getter Method:**

    ```python
    def get_detail_level(self) -> UserMessageLevel:
        return self.current_detail_level
    ```

- **Modify `display_message` Method:**
  - The existing method already parses the `level` from the incoming `data`.
  - Add filtering logic:

        ```python
        def display_message(self, sender: Any, data: dict) -> None:
            message = data.get("message", "")
            message_level_str = data.get("level", UserMessageLevel.INFO.value) # Get as string or enum
            
            # Convert message_level_str to UserMessageLevel enum if it's a string
            try:
                if isinstance(message_level_str, str):
                    message_level = UserMessageLevel(message_level_str.upper())
                elif isinstance(message_level_str, UserMessageLevel):
                    message_level = message_level_str
                else:
                    # Handle unexpected type, perhaps log a warning and default
                    print(f"Warning: Unexpected message level type: {type(message_level_str)}. Defaulting to INFO.")
                    message_level = UserMessageLevel.INFO
            except ValueError:
                # Handle invalid string value, perhaps log a warning and default
                print(f"Warning: Invalid message level string: {message_level_str}. Defaulting to INFO.")
                message_level = UserMessageLevel.INFO

            # Filtering Logic
            if self.current_detail_level == UserMessageLevel.INFO:
                if message_level == UserMessageLevel.INFO:
                    print(f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}")
            elif self.current_detail_level == UserMessageLevel.DETAIL:
                # Show both INFO and DETAIL messages when current_detail_level is DETAIL
                if message_level == UserMessageLevel.INFO or message_level == UserMessageLevel.DETAIL:
                    # Optionally, add a prefix to distinguish DETAIL messages if desired
                    # prefix = "[DETAIL] " if message_level == UserMessageLevel.DETAIL else ""
                    # print(f"{UserMessageColour.RESET}{prefix}{message}{UserMessageColour.RESET}")
                    print(f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}")
            # Else, if other levels were added, they would be handled here.
        ```

### 4.3. Modify CLI Argument Parsing

File: [`src/ai_whisperer/cli.py`](src/ai_whisperer/cli.py:1)

- **Add Global Argument:**
  - In the `cli` function, add an argument to the main `parser`:

        ```python
        # In cli function, after other global arguments
        parser.add_argument(
            "--detail-level",
            type=str.upper, # Convert to uppercase for case-insensitive matching
            choices=[level.value for level in UserMessageLevel], # Use values from enum
            default=UserMessageLevel.INFO.value,
            help=f"Set the detail level for console output. Choices: {[level.value for level in UserMessageLevel]}. Default: {UserMessageLevel.INFO.value}.",
            metavar="LEVEL"
        )
        ```

### 4.4. Integrate CLI Option with `ANSIConsoleUserMessageHandler`

File: [`src/ai_whisperer/main.py`](src/ai_whisperer/main.py:1) (or where `ANSIConsoleUserMessageHandler` is instantiated)

- **Set Detail Level from Parsed Arguments:**
  - After `parsed_args` are available and `ansi_handler` is instantiated:

        ```python
        # Assuming 'parsed_args' contains the parsed command line arguments
        # and 'ansi_handler' is an instance of ANSIConsoleUserMessageHandler
        
        # Example snippet within main() or equivalent startup logic:
        # ...
        # parsed_args = cli_function_that_returns_parsed_args() # Or however parsed_args is obtained
        # delegate_manager = DelegateManager()
        # ansi_handler = ANSIConsoleUserMessageHandler()
        # delegate_manager.register_delegate(ansi_handler, "user_message_display") # Example registration
        # ...

        if hasattr(parsed_args, 'detail_level'):
            try:
                cli_detail_level_str = parsed_args.detail_level
                selected_detail_level = UserMessageLevel(cli_detail_level_str) # Convert string from CLI to enum
                ansi_handler.set_detail_level(selected_detail_level)
                # Optionally, log the chosen detail level
                # logger.info(f"Console detail level set to: {selected_detail_level.value}")
            except ValueError:
                # Handle case where string to enum conversion fails (should be caught by argparse choices, but good for safety)
                # logger.warning(f"Invalid detail level '{parsed_args.detail_level}' from CLI. Defaulting to INFO.")
                ansi_handler.set_detail_level(UserMessageLevel.INFO) # Default to INFO on error
            except AttributeError as e:
                # logger.error(f"Error accessing detail_level or ansi_handler: {e}")
                # Fallback or error handling if ansi_handler or detail_level is not set up correctly
                pass # Or raise
        # ... rest of the main function
        ```

    *Note: The exact placement will depend on how `parsed_args` and `ansi_handler` are managed in `main.py`. The key is to call `ansi_handler.set_detail_level()` after the handler is created and CLI args are parsed.*

## 5. Visual Plan (Mermaid Diagram)

```mermaid
graph TD
    A[Start: Add Detail Level Feature] --> B(Review UserMessageLevel Enum);
    B -- Exists: INFO, DETAIL --> C[Modify ANSIConsoleUserMessageHandler in basic_output_display_message.py];
    C --> C1[Add self.current_detail_level: UserMessageLevel (default INFO)];
    C --> C2[Add set_detail_level(level) method];
    C --> C3[Add get_detail_level() method];
    C --> C4[Modify display_message() to filter based on self.current_detail_level and message_level];
    
    A --> D[Modify CLI Argument Parsing in cli.py];
    D --> D1[Add global --detail-level argument to main ArgumentParser];
    D1 --> D2[Choices: INFO, DETAIL (case-insensitive)];
    D1 --> D3[Default: INFO];
    
    A --> E[Integrate CLI with Handler in main.py];
    E --> E1[After CLI parsing & ANSIConsoleUserMessageHandler instantiation];
    E1 --> E2[Get parsed_args.detail_level string];
    E2 --> E3[Convert string to UserMessageLevel enum];
    E3 --> E4[Call ansi_handler.set_detail_level(enum_level)];
    
    F[Documentation] --> G((End: Feature Planned));
    H[Testing Considerations] --> G;

    C4 --> H;
    E4 --> H;
    A --> F;

    classDef fileStyle fill:#f9f,stroke:#333,stroke-width:2px;
    class C,D,E fileStyle;
```

## 6. Testing Considerations

- **Default Behavior:** Run the CLI without the `--detail-level` option. Verify only `INFO` messages are displayed.
- **Explicit INFO Level:** Run with `--detail-level INFO`. Verify only `INFO` messages are displayed.
- **DETAIL Level:** Run with `--detail-level DETAIL`. Verify both `INFO` and `DETAIL` messages are displayed.
- **Case Insensitivity:** Test `--detail-level info` and `--detail-level detail`.
- **Invalid Level:** Test with an invalid value (e.g., `--detail-level DEBUG`). Argparse should handle this with an error message due to `choices`.
- **Message Emission:** Ensure different parts of the application can emit messages with `UserMessageLevel.INFO` and `UserMessageLevel.DETAIL` and that they are filtered correctly by `ANSIConsoleUserMessageHandler`.
- **Runtime Change (Manual Test):** If a mechanism is exposed (e.g., through a debugger or a future command) to change the detail level at runtime, test this functionality.

## 7. Output Artifact

This plan will be saved as [`docs/detail_option_implementation_plan.md`](docs/detail_option_implementation_plan.md).
