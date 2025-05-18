# Terminal Monitor Command Mode Design

## 1. Introduction

* **Purpose:** This document outlines the design for the AIWhisperer terminal monitor's interactive command mode.
* **Scope:** The design covers command input and processing, core features (history, editing, help, coloring, shortcuts, aliases), the specification for initial built-in commands, and the approach for ensuring modularity and extensibility.
* **References:**
  * [`docs/monitor_terminal_analysis.md`](docs/monitor_terminal_analysis.md:1) (Provides context for the command box within the overall terminal layout).
  * Subtask Definition: `project_dev/in_dev/terminal_monitor_command_parser/subtask_95b619a1-2b3e-4e1c-af08-51b109683c77.json` (Details the specific requirements for this design task).

## 2. Python Library Evaluation for Interactive CLI

Several Python libraries can be used for building interactive command-line interfaces. The following were considered:

* **`cmd` (Python Standard Library):**
  * *Pros:* Built-in, no external dependencies. Simple to get started for basic Read-Eval-Print Loops (REPLs).
  * *Cons:* Limited features. Lacks advanced line editing, sophisticated autocompletion, syntax highlighting, and good asynchronous support. Customization can be cumbersome.

* **`readline` (Python Standard Library, primarily Unix-focused):**
  * *Pros:* Provides command history and basic line editing capabilities (often leveraging GNU Readline).
  * *Cons:* Low-level. Functionality can be OS-dependent and less rich compared to dedicated libraries. Not ideal for complex UI elements or cross-platform consistency in advanced features.

* **`prompt_toolkit`:**
  * *Pros:* A powerful and comprehensive library for building interactive command-line applications. Cross-platform. Offers rich features including:
    * Advanced line editing (Emacs and Vi keybindings).
    * Autocompletion (context-aware).
    * Syntax highlighting.
    * Persistent command history.
    * Support for asynchronous operations.
    * Flexible layout capabilities for more complex UIs.
  * *Cons:* It's an external dependency. May have a slightly steeper learning curve initially compared to `cmd`.

* **Recommendation:**
    **`prompt_toolkit`** is highly recommended for implementing the terminal command mode. Its extensive feature set directly addresses the requirements for command history, advanced line editing, coloring, and keyboard shortcuts. Its modularity and support for asynchronous operations make it a robust choice for AIWhisperer, allowing for future enhancements and integrations.

## 3. Core Architecture Design

The command mode will be built around a modular architecture to facilitate clarity, maintenance, and extensibility.

```mermaid
graph TD
    A[User Input] --> B{Command Input Handler (prompt_toolkit)};
    B -- Raw Input --> C[Command Parser];
    C -- Parsed Command + Args --> D[Command Registry];
    D -- Matched Command --> E[Command Executor];
    E -- Executes --> F[Specific Command Logic];
    F -- Output/Result --> G[Output Formatter];
    G --> H{Display (prompt_toolkit/Terminal)};
    D -- Command Info --> I[Help System];
    I -- Help Text --> H;
    B -- History/Editing Features --> B;
```

* **Components:**
  * **Command Input Handler (`prompt_toolkit`):**
    * Manages the user input prompt.
    * Provides built-in line editing (e.g., arrow keys, Emacs/Vi modes), command history navigation (up/down arrows), and basic input validation.
    * Handles keyboard interrupts (`Ctrl+C`).
  * **Command Parser:**
    * Receives the raw input string from the Input Handler.
    * Tokenizes the input into a command name and its arguments. Initially, a simple space-based separation will be used. For commands with more complex argument structures, `argparse` or a similar library could be integrated on a per-command basis.
  * **Command Registry:**
    * A central mapping (e.g., a dictionary) of command names and their aliases to corresponding command handler objects or functions.
    * Commands will ideally be defined as classes inheriting from a `BaseCliCommand` abstract class, or via a decorator pattern.
    * Example Structure:

            ```python
            # Conceptual example
            class BaseCliCommand:
                name: str = ""  # Canonical command name
                aliases: list[str] = []
                help_text: str = "No help available for this command."
                
                def __init__(self):
                    pass # Initialize if needed
                    
                def execute(self, args: list[str]):
                    raise NotImplementedError("Execute method not implemented.")

            command_registry = {} # e.g., {"command_name": CommandClassInstance}

            def register_command(command_class):
                instance = command_class()
                command_registry[instance.name] = instance
                for alias in instance.aliases:
                    command_registry[alias] = instance
                return command_class
            ```

  * **Command Executor:**
    * Receives the parsed command name and arguments.
    * Looks up the command in the `CommandRegistry`.
    * If found, invokes the `execute` method of the command object, passing the arguments.
    * Handles common exceptions during command execution (e.g., `CommandNotFound`, `ArgumentError`) and formats user-friendly error messages.
  * **Help System:**
    * Implemented as a special `help` command.
    * `help`: Lists all available commands with their brief descriptions (first line of `help_text`).
    * `help <command_name>`: Displays detailed help for the specified command (full `help_text`).
    * Help text is sourced directly from the command definitions (e.g., `help_text` attribute or formatted docstrings).
  * **Output Formatter:**
    * Responsible for formatting command output before it's displayed to the user.
    * This includes applying colors, pretty-printing (especially for JSON, as per [`docs/monitor_terminal_analysis.md`](docs/monitor_terminal_analysis.md:34)), and ensuring consistent presentation.

## 4. Feature Integration Plan

* **Command History:**
  * `prompt_toolkit` provides `History` objects (e.g., `FileHistory` for persistence across sessions).
  * Users can navigate history using up and down arrow keys.
* **Line Editing:**
  * `prompt_toolkit` offers rich line editing capabilities out-of-the-box, including Emacs and Vi keybindings. This covers requirements for efficient command input and correction.
* **Text Coloring:**
  * Leverage `prompt_toolkit`'s styling system (which can use ANSI escape codes or its own `Style` objects).
  * A consistent color scheme will be defined for:
    * Input prompt
    * Command output (standard)
    * Error messages
    * Help text
    * Syntax highlighting for specific outputs like JSON (as per [`docs/monitor_terminal_analysis.md`](docs/monitor_terminal_analysis.md:31)).
* **Keyboard Shortcuts:**
  * `prompt_toolkit` allows defining custom keybindings via its `KeyBindings` object.
  * Initial essential shortcuts:
    * `Ctrl+C`: Interrupt the current foreground command or, if the input line is empty, offer to exit the prompt (or exit directly).
    * `Ctrl+D`: Exit the monitor (if the input line is empty). This is a common convention.
    * `Ctrl+L`: Clear the terminal screen (if feasible and integrates cleanly with the segmented layout).
* **Command Aliases:**
  * The `CommandRegistry` will support mapping multiple alias strings to a single canonical command object.
  * Aliases will be defined within the command's class definition (e.g., `aliases = ["q", "quit"]` for an `exit` command).
  * Future enhancement: A dedicated `alias` command could allow users to define custom, persistent aliases.

## 5. Initial Built-in Commands

The following commands will be available initially:

* **`exit`**
  * **Aliases:** `quit`, `q`
  * **Description:** Exits the AIWhisperer monitor application.
  * **Parameters:** None.
  * **Behavior:**
        1. Optionally, prompt for confirmation if there's unsaved state or running tasks (future consideration).
        2. Cleanly terminate the command loop.
        3. Signal the main AIWhisperer application to shut down gracefully.

* **`debugger`**
  * **Aliases:** `dbg`
  * **Description:** Activates debug mode, allowing an external debugger (e.g., VSCode) to attach to the AIWhisperer process.
  * **Parameters:** None.
  * **Behavior:**
        1. Print a message to the console indicating that AIWhisperer is now paused and waiting for a debugger to attach (e.g., "Debugger active. Waiting for connection on port X...").
        2. This command will trigger the same mechanism used by the `--debug` CLI flag, which typically involves `debugpy.listen()` and `debugpy.wait_for_client()` or similar, effectively pausing execution until a debugger connects.
        3. The user will then need to attach their debugger from their IDE.

* **`ask <query_string>`**
  * **Aliases:** None initially.
  * **Description:** Sends the provided query string to the configured AI model for a response.
  * **Parameters:**
    * `query_string` (required, string): The full text of the query to be sent to the AI.
  * **Behavior:**
        1. The entire string following the `ask` command is treated as the `query_string`.
        2. The command will interface with the appropriate AI service module within AIWhisperer to send the query.
        3. The AI's response will be displayed in the main monitor output area.
        4. JSON responses should be pretty-printed and syntax-highlighted as per [`docs/monitor_terminal_analysis.md`](docs/monitor_terminal_analysis.md:34).
        5. Errors from the AI service (e.g., API errors, timeouts) should be caught and displayed gracefully to the user.

## 6. Modularity and Extensibility

The design prioritizes making it easy to add new commands:

1. **Create a Command Class:** Define a new Python class that inherits from `BaseCliCommand` (or conforms to a similar defined interface).

    ```python
    # Example for a new 'status' command
    # @register_command # If using a decorator
    class StatusCommand(BaseCliCommand):
        name = "status"
        aliases = ["st"]
        help_text = "Displays the current status of AIWhisperer.\n\nUsage: status"
        
        def execute(self, args: list[str]):
            if args:
                return "Error: 'status' command takes no arguments."
            # Logic to fetch and display status
            current_status = "System is All Good!" # Placeholder
            return f"AIWhisperer Status: {current_status}"
    ```

2. **Implement Logic:** Implement the `execute(self, args)` method to perform the command's action. Define `name`, `aliases`, and `help_text`.
3. **Register Command:** Ensure the command class is imported and registered with the `CommandRegistry` when the application starts (e.g., via decorator or explicit registration call).

This component-based approach with a clear interface for commands ensures that new functionality can be added with minimal impact on existing code.

## 7. Dependencies

* **`prompt_toolkit`** (Recommended version: >= 3.0.0)
  * *License:* BSD-3-Clause (Confirm from library's official documentation).
  * *Compatibility:* Cross-platform (Windows, macOS, Linux). This is crucial for AIWhisperer's user base.
