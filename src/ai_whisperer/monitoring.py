from datetime import datetime, timezone
import time
import json
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from rich.style import Style
from rich.syntax import Syntax # Import Syntax for JSON highlighting
import sys
import os

# Import real classes from the respective modules
# Import real classes from the respective modules
import logging # Import logging module
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, set_active_monitor_handler # Import set_active_monitor_handler
from src.ai_whisperer.state_management import StateManager

class TerminalMonitor(logging.Handler): # Inherit from logging.Handler
    """
    Provides a terminal-based monitoring view for the AIWhisperer runner.
    Also acts as a logging handler to receive all log messages when active.
    """

    def __init__(self, state_manager: StateManager, monitor_enabled: bool = True):
        super().__init__() # Initialize the logging.Handler base class
        self.level = logging.DEBUG # Set the handler's level to DEBUG to receive all logs
        self.console = Console()
        self.state_manager = state_manager
        self.monitor_enabled = monitor_enabled # Store the flag
        self._live: Optional[Live] = None
        self._layout = self._create_layout()
        self._current_step_logs: List[LogMessage] = []  # Logs for the currently displayed step
        self._general_logs: List[LogMessage] = []  # Logs not associated with a specific step
        self._active_subtask_id: Optional[str] = None
        self._runner_status_info: str = "Initializing..."
        self._plan_name: str = "Loading Plan..."

    def _create_layout(self) -> Layout:
        """Creates the Rich layout for the terminal UI."""
        layout = Layout(name="root")
        # Create three horizontal segments: left, center, right
        layout.split_column(
            Layout(name="top_border", size=1), # Top border for the whole layout
            Layout(name="horizontal_segments", ratio=1),
            Layout(name="bottom_border", size=1) # Bottom border for the whole layout
        )

        layout["horizontal_segments"].split_row(
            Layout(name="left_segment", size=20), # Left segment (placeholder size)
            Layout(name="center_segment", ratio=2), # Center segment (larger)
            Layout(name="right_segment", size=20) # Right segment (placeholder size)
        )

        # Split the central segment vertically into monitor output and command box
        layout["center_segment"].split_column(
            Layout(name="monitor_output", ratio=4), # Monitor output (larger)
            Layout(name="command_box", ratio=1) # Command box (smaller)
        )

        return layout

    def _get_left_segment_content(self) -> Panel:
        """Generates content for the left segment."""
        # Placeholder content for now
        return Panel(Text("Left Panel\n(Future Use)"), title="[b]Left[/b]", border_style="blue")

    def _get_right_segment_content(self) -> Panel:
        """Generates content for the right segment."""
        # Placeholder content for now
        return Panel(Text("Right Panel\n(Future Use)"), title="[b]Right[/b]", border_style="blue")

    def _get_monitor_output_content(self) -> Panel:
        """Generates the content for the monitor output panel."""
        logs_to_display = self._current_step_logs if self._active_subtask_id else self._general_logs
        log_display_renderables = []
        for log_entry in logs_to_display:
            # No need to filter here, add_log_message already filters for MONITOR component type

            level_style = Style(color="green")
            if log_entry.level == LogLevel.WARNING:
                level_style = Style(color="yellow")
            elif log_entry.level == LogLevel.ERROR or log_entry.level == LogLevel.CRITICAL:
                level_style = Style(color="red")
            elif log_entry.level == LogLevel.DEBUG:
                level_style = Style(color="blue")
            elif log_entry.level == LogLevel.INFO:
                 level_style = Style(color="cyan") # Using cyan for INFO as per test example

            log_prefix = (
                Text(f"[{log_entry.timestamp}] ", style="dim")
                + Text(f"[{log_entry.level.value.lower()}]", style=level_style)
                + Text(f" {log_entry.component.value}: ")
            )

            # Check if the event_summary is a JSON string and pretty-print/highlight
            try:
                json_data = json.loads(log_entry.event_summary)
                # Use Syntax for JSON highlighting
                json_syntax = Syntax(json.dumps(json_data, indent=2), "json", theme="ansi_dark", line_numbers=False)
                log_display_renderables.append(log_prefix + json_syntax)
            except json.JSONDecodeError:
                # Not a JSON string, display as plain text with component and summary
                log_display_renderables.append(log_prefix + Text(log_entry.event_summary))

        # Add a placeholder if there are no monitor logs to display
        if not log_display_renderables:
            log_display_renderables.append(Text("No monitor output yet...", style="dim"))


        title = f"[b]Logs for Step: {self._active_subtask_id}[/b]" if self._active_subtask_id else "[b]General Logs[/b]"
        return Panel(Text("\n").join(log_display_renderables), title=title, border_style="green")

    def _get_command_box_content(self) -> Panel:
        """Generates the content for the command box panel."""
        # Placeholder for user input area
        return Panel(Text("Command: "), title="[b]Input[/b]", border_style="blue")

    def _get_top_border_content(self) -> Panel:
        """Generates content for the top border."""
        overall_status = self.state_manager.get_global_state("plan_status") or "Unknown"
        return Panel(
            Text(f"Plan: {self._plan_name} | Status: {overall_status}", justify="center"),
            title="[b]AIWhisperer Runner[/b]",
            border_style="white"
        )

    def _get_bottom_border_content(self) -> Panel:
        """Generates content for the bottom border."""
        return Panel(Text(self._runner_status_info), title="[b]Status[/b]", border_style="white")


    def update_display(self):
        """Updates the Rich Live display with the current state."""
        if self._live:
            # Update the content of the new layout segments
            self._layout["top_border"].update(self._get_top_border_content())
            self._layout["left_segment"].update(self._get_left_segment_content())
            self._layout["right_segment"].update(self._get_right_segment_content())
            self._layout["monitor_output"].update(self._get_monitor_output_content())
            self._layout["command_box"].update(self._get_command_box_content())
            self._layout["bottom_border"].update(self._get_bottom_border_content())

            self._live.update(self._layout)

    # Remove the old add_log_message method

    def emit(self, record: logging.LogRecord):
        """Processes a log record received by this handler."""
        # Check if the monitor is enabled before processing
        if not self.monitor_enabled:
            return

        # Check if the record has the component attribute in its extra data
        # Include logs with ComponentType.MONITOR or ComponentType.EXECUTION_ENGINE
        if hasattr(record, 'component') and record.component in [ComponentType.MONITOR.value, ComponentType.EXECUTION_ENGINE.value, ComponentType.RUNNER.value]:
            try:
                # Reconstruct LogMessage from record attributes
                # Need to map logging levelno back to LogLevel enum
                level_map_reverse = {
                    logging.DEBUG: LogLevel.DEBUG,
                    logging.INFO: LogLevel.INFO,
                    logging.WARNING: LogLevel.WARNING,
                    logging.ERROR: LogLevel.ERROR,
                    logging.CRITICAL: LogLevel.CRITICAL,
                }
                log_level = level_map_reverse.get(record.levelno, LogLevel.INFO)

                log_message = LogMessage(
                    level=log_level,
                    component=ComponentType(record.component),
                    action=getattr(record, 'action', 'N/A'),
                    event_summary=getattr(record, 'event_summary', getattr(record, 'message', 'N/A')), # Use event_summary from extra data, fallback to formatted message with robust fallback
                    timestamp=getattr(record, 'timestamp', datetime.now(timezone.utc).isoformat(timespec="milliseconds") + "Z"),
                    subtask_id=getattr(record, 'subtask_id', None),
                    event_id=getattr(record, 'event_id', None),
                    state_before=getattr(record, 'state_before', None),
                    state_after=getattr(record, 'state_after', None),
                    duration_ms=getattr(record, 'duration_ms', None),
                    details=getattr(record, 'details', {}), # details should be available as an attribute
                )

                # Add the log message to the appropriate list based on subtask_id
                if log_message.subtask_id and log_message.subtask_id == self._active_subtask_id:
                    self._current_step_logs.append(log_message)
                elif not log_message.subtask_id:
                    self._general_logs.append(log_message)
                # Note: Logs for steps other than the active one are not stored in this simple monitor.
                # A more advanced monitor would store all logs and allow switching views.

                # Update the display after adding a relevant log
                self.update_display()

            except Exception as e:
                # Log an error if processing fails within the handler
                # Avoid using the same logger to prevent infinite loops
                print(f"Error in TerminalMonitor processing log record: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)

        # For logs with other component types, do nothing for now.
        # In the future, these could be stored or routed to different display areas.

    def set_active_step(self, subtask_id: Optional[str]):
        """Sets the step whose logs should be displayed."""
        self._active_subtask_id = subtask_id
        self._current_step_logs = []  # Clear previous step logs when switching
        # In a real implementation, you would load logs for this step from a log store.
        if self.monitor_enabled: # Conditionally update display
            self.update_display()

    def set_runner_status_info(self, info: str):
        """Sets the information displayed in the status bar."""
        self._runner_status_info = info
        if self.monitor_enabled: # Conditionally update display
            self.update_display()

    def set_plan_name(self, plan_name: str):
        """Sets the name of the plan being executed."""
        self._plan_name = plan_name
        if self.monitor_enabled: # Conditionally update display
            self.update_display()

    def run(self):
        """Starts the terminal monitoring interface."""
        if self.monitor_enabled: # Only start live display if monitoring is enabled
            # Set this monitor instance as the active handler in the logging system
            set_active_monitor_handler(self)
            try:
                # Redirect stdout and stderr to suppress unwanted output
                with Live(self._layout, console=self.console, screen=True, refresh_per_second=4) as live:
                    self._live = live
                    self.update_display()  # Initial display
                    # The main runner loop would drive updates to the state manager and call update_display
                    # This run method would likely be called in a separate thread or async task
                    # to allow the main runner logic to proceed.
                    # For a simple example, we can keep it running until interrupted.
                    # The Live context manager keeps the display updated until exited.
                    # In a real application, this would be managed by the main runner loop.
                    while True:
                        time.sleep(1) # Keep the live display active
            finally:
                # Unset this monitor instance as the active handler when the live display exits
                set_active_monitor_handler(None)
        else:
            # If monitoring is disabled, just log that the monitor is "running" without display
            # Use a standard print here as logging might be suppressed or not fully configured yet
            print("Terminal monitoring is disabled.")
