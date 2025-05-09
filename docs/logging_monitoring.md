# Logging and Monitoring in AIWhisperer

## Overview
AIWhisperer incorporates a comprehensive logging system and a real-time terminal monitoring interface. These features are designed to provide clear visibility into the execution of plans, aid in debugging, and allow for user interaction with running tasks. Key aspects include detailed action logging, status tracking of plan steps, and interactive commands like pause, resume, and cancel.

## Logging System
### How Logging Works
The logging mechanism within the AIWhisperer runner is designed to capture detailed information about all actions performed during plan execution. This includes events from the execution engine, AI service interactions, file operations, terminal commands, state management, and user interactions. The system uses a structured `LogMessage` format to ensure logs are easy to parse and analyze.

### Log Levels
The AIWhisperer logging system utilizes standard log levels to categorize messages based on their severity:
- **DEBUG**: Detailed information, typically of interest only when diagnosing problems.
- **INFO**: Confirmation that things are working as expected.
- **WARNING**: An indication that something unexpected happened, or indicative of some problem in the near future.
- **ERROR**: Due to a more serious problem, the software has not been able to perform some function.
- **CRITICAL**: A serious error, indicating that the program itself may be unable to continue running.

### Log Storage
Logs are outputted to the following destinations:
- **Console**: Real-time log messages are displayed in the terminal using the Rich library for enhanced formatting.
- **Log Files**: Logs are also written to files for persistent storage and later analysis. By default, two files are created:
    - `aiwhisperer_runner.log`: Contains human-readable text logs.
    - `aiwhisperer_runner.json.log`: Contains structured logs in JSON format, suitable for programmatic parsing.
Log file paths, rotation policies, and formats can be customized via the `logging_config.yaml` file.

### Log Message Format
Log messages in AIWhisperer follow a structured format defined by the `LogMessage` dataclass. Key fields include:
- `timestamp`: The time the log event occurred (in ISO 8601 format).
- `level`: The severity level of the log message (e.g., INFO, ERROR).
- `component`: The part of the system that generated the log (e.g., `execution_engine`, `ai_service`).
- `action`: A verb describing the specific event (e.g., `step_execution_started`, `api_request_sent`).
- `message`: A human-readable summary of the event.
- `step_id`: The ID of the plan step related to the log, if applicable.
- `event_id`: A unique ID for the specific log event, useful for tracing.
- `state_before`: The state of the relevant entity before the action.
- `state_after`: The state of the relevant entity after the action.
- `duration_ms`: The duration of the action in milliseconds, if applicable.
- `details`: A dictionary containing component-specific structured data providing additional context.

## Terminal Monitoring View
The AIWhisperer runner provides a real-time, terminal-based monitoring interface built using the Rich library. This interface offers a dynamic view of the plan execution progress and allows for user interaction.

### Activating the Monitor
The terminal monitor is typically active by default when the AIWhisperer runner executes a plan.

### Information Displayed
The Rich-based terminal UI is divided into several panels to provide a comprehensive overview:
- **Header**: Displays the overall plan name and its current status.
- **Plan Overview Panel**: A table listing all steps defined in the plan, showing their unique IDs, descriptions, and current execution statuses (e.g., Pending, Running, Completed, Failed, Paused, Skipped).
- **Current Step Logs Panel**: This panel displays log messages specifically related to the currently executing or the most recently active step. This provides a running commentary of the actions and interactions occurring within that step, including details of AI service calls, file operations, and command executions.
- **Status Bar/Footer**: Provides general status information about the runner and includes a prompt for user input.

### Interactive Features
Users can interact with the running plan through the terminal monitor by typing commands:
- `pause`: To temporarily halt the execution of the current plan.
- `resume`: To continue the execution of a plan that has been paused.
- `cancel`: To terminate the current plan execution immediately.
- `context <your additional context text>`: To provide supplementary information or instructions to the AI for the current or next step. This context can influence subsequent AI interactions.
- `details <step_id>`: (If implemented) To switch the focus of the "Current Step Logs Panel" to display logs for a specific step, even if it's already completed or failed.
- `help`: To display a list of available commands and their descriptions.

## Log Configuration
For advanced customization of logging behavior, such as modifying log levels per component, changing log file paths, or adjusting output formats, refer to the `logging_config.yaml` file. This file allows fine-grained control over how logs are generated and handled.