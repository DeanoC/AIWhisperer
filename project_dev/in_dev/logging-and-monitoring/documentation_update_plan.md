# Plan to Update Project Documentation for Logging and Monitoring

**Overall Goal:** Create new documentation for the logging and monitoring features and update existing documentation to reflect these additions, based on the instructions in `project_dev/in_dev/logging-and-monitoring/subtask_update_documentation.json` and the content of `project_dev/in_dev/logging-and-monitoring/logging_monitoring_design.md`.

**Detailed Steps:**

1.  **Create New Documentation File: `docs/logging_monitoring.md`**
    *   This file will be the central place for all information regarding logging and monitoring.
    *   **Content Source:** Primarily from `project_dev/in_dev/logging-and-monitoring/logging_monitoring_design.md`.
    *   **Key Sections to Include:**
        *   **Overview:** A brief introduction to the purpose and benefits of logging and monitoring within the AIWhisperer system.
        *   **Logging System Details:**
            *   Explanation of how logging is implemented in the AIWhisperer runner.
            *   Description of standard log levels used (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL), referencing the `LogLevel` enum from the design.
            *   Information on log storage, including console output and file-based logs (e.g., `aiwhisperer_runner.log`, `aiwhisperer_runner.json.log`), and a mention of `logging_config.yaml`.
            *   Details on the `LogMessage` data structure, outlining key fields and their purpose.
        *   **Terminal Monitoring View:**
            *   How the terminal-based monitoring interface is activated and presented to the user (based on Rich library implementation).
            *   Description of the information displayed in the monitor (e.g., overall plan status, individual step progress, current step logs, status bar).
            *   Explanation of interactive features available to the user (e.g., commands like `pause`, `resume`, `cancel`, `context <text>`, `details <step_id>`, `help`).
        *   **Log Configuration (Briefly):** A note for advanced users about the `logging_config.yaml` file for customizing logging behavior.
    *   **Proposed Structure for `docs/logging_monitoring.md`:**
        ```markdown
        # Logging and Monitoring in AIWhisperer

        ## Overview
        [Brief explanation of logging and monitoring purpose and benefits in AIWhisperer.]

        ## Logging System
        ### How Logging Works
        [Detailed explanation of the logging mechanism within the AIWhisperer runner, drawing from the design document's description of the core logging system.]
        ### Log Levels
        [Description of standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) and their intended use.]
        ### Log Storage
        [Information on where logs are outputted:
        - Console (via RichHandler)
        - Log files (e.g., `aiwhisperer_runner.log` for text, `aiwhisperer_runner.json.log` for structured JSON). Mention that paths and rotation can be configured.]
        ### Log Message Format
        [Detailed breakdown of the `LogMessage` structure, explaining key fields like `timestamp`, `level`, `component`, `action`, `message`, `step_id`, `details`, etc., based on the design document.]

        ## Terminal Monitoring View
        The AIWhisperer runner provides a real-time, terminal-based monitoring interface built using the Rich library.
        ### Activating the Monitor
        [Explain that the monitor is typically active by default when the runner executes a plan.]
        ### Information Displayed
        [Describe the layout and components of the Rich-based UI, such as:
        - Header: Overall plan name and status.
        - Plan Overview Panel: A table listing all plan steps with their IDs, descriptions, and current statuses (e.g., Pending, Running, Completed, Failed, Paused).
        - Current Step Logs Panel: A view of log messages relevant to the currently executing or most recently active step.
        - Status Bar/Footer: General status information and prompts for user input.]
        ### Interactive Features
        [List and explain the commands users can input into the monitor:
        - `pause`: To temporarily halt execution.
        - `resume`: To continue a paused execution.
        - `cancel`: To terminate the current plan execution.
        - `context <your additional context text>`: To provide supplementary information to the AI for the current or next step.
        - `details <step_id>`: (If implemented as per design) To view logs for a specific step.
        - `help`: To display available commands.]

        ## Log Configuration
        For advanced customization of logging behavior, such as modifying log levels per component, changing log file paths, or adjusting output formats, refer to the `logging_config.yaml` file.
        ```

2.  **Update Existing Documentation File: `docs/index.md`**
    *   **Action:** Add a new section or an entry under an existing "Features" or "Advanced Usage" section to introduce Logging and Monitoring.
    *   **Content:** Provide a brief overview of the logging and monitoring features and include a direct link to the newly created `docs/logging_monitoring.md` page.
    *   **Proposed Addition (to be placed appropriately, e.g., after the "State Management" section):**
        ```markdown
        ## Logging and Monitoring

        AIWhisperer incorporates a comprehensive logging system and a real-time terminal monitoring interface. These features are designed to provide clear visibility into the execution of plans, aid in debugging, and allow for user interaction with running tasks. Key aspects include detailed action logging, status tracking of plan steps, and interactive commands like pause, resume, and cancel.

        For an in-depth understanding, please see the [Logging and Monitoring Documentation](logging_monitoring.md).
        ```

3.  **Update Existing Documentation File: `docs/execution_engine.md`**
    *   **Action:** Integrate a brief mention of how logging and monitoring relate to the Execution Engine's operations.
    *   **Content:** Explain that the engine's activities are logged and monitored, and link to `docs/logging_monitoring.md` for more details.
    *   **Proposed Addition (e.g., as a new subsection or integrated into the "Overview"):**
        ```markdown
        ## Integration with Logging and Monitoring

        The Execution Engine's operations are thoroughly logged and can be observed via the AIWhisperer's monitoring interface. This includes the initiation of tasks, state transitions (e.g., from "pending" to "running", "completed", or "failed"), dependency evaluations, and any errors encountered during execution. This detailed logging is crucial for understanding the engine's behavior and for debugging purposes.

        For comprehensive information on the logging and monitoring capabilities, refer to the [Logging and Monitoring Documentation](./logging_monitoring.md).
        ```

4.  **Update Existing Documentation File: `docs/internal_process.md`**
    *   **Action:** Add a section or paragraph explaining how logging and monitoring support the understanding and debugging of the system's internal processes.
    *   **Content:** Highlight the role of logging/monitoring in providing insights into the runner's workings and link to `docs/logging_monitoring.md`.
    *   **Proposed Addition (e.g., as a new top-level section):**
        ```markdown
        ## Role of Logging and Monitoring in Internal Processes

        Logging and monitoring are integral to understanding and debugging the internal processes of the AIWhisperer system. As the Orchestrator, Subtask Generator, Execution Engine, and other components perform their functions, detailed logs are generated. These logs capture:

        *   Interactions with AI services.
        *   File system operations.
        *   Execution of terminal commands.
        *   State changes within the system.
        *   User interactions with the runner.

        This comprehensive audit trail, coupled with the real-time terminal monitoring view, provides developers with the necessary insights to trace execution flows, diagnose issues, and verify that internal processes are operating as expected.

        For a complete guide to these features, please consult the [Logging and Monitoring Documentation](./logging_monitoring.md).
        ```

**Mermaid Diagram of the Plan:**

```mermaid
graph TD
    A[Start: Update Documentation Task] --> B{Read `subtask_update_documentation.json`};
    B --> C{Read `logging_monitoring_design.md` (Source for new content)};
    C --> D[Create new file: `docs/logging_monitoring.md` with detailed content];
    A --> E{Read `docs/index.md` (Existing)};
    D --> F[Update `docs/index.md`: Add section & link to `docs/logging_monitoring.md`];
    A --> G{Read `docs/execution_engine.md` (Existing)};
    D --> H[Update `docs/execution_engine.md`: Add reference & link to `docs/logging_monitoring.md`];
    A --> I{Read `docs/internal_process.md` (Existing)};
    D --> J[Update `docs/internal_process.md`: Add reference & link to `docs/logging_monitoring.md`];
    F --> K{Verify all files created/updated};
    H --> K;
    J --> K;
    K -- All Good --> L[End: Documentation Updated];