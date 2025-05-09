import time
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from rich.style import Style

# Assuming LogMessage, LogLevel, ComponentType are defined in logging.py
# and StateManager is defined in state_management.py
# We will need to import them or define local mocks for standalone testing if necessary.
# For the actual implementation, we will import from the respective modules.

import time
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from rich.style import Style

# Import real classes from the respective modules
from src.ai_whisperer.logging import LogMessage, LogLevel, ComponentType
from src.ai_whisperer.state_management import StateManager


class TerminalMonitor:
    """
    Provides a terminal-based monitoring view for the AIWhisperer runner.
    """
    def __init__(self, state_manager: StateManager):
        self.console = Console()
        self.state_manager = state_manager
        self._live: Optional[Live] = None
        self._layout = self._create_layout()
        self._current_step_logs: List[LogMessage] = [] # Logs for the currently displayed step
        self._general_logs: List[LogMessage] = [] # Logs not associated with a specific step
        self._active_step_id: Optional[str] = None
        self._runner_status_info: str = "Initializing..."
        self._plan_name: str = "Loading Plan..."

    def _create_layout(self) -> Layout:
        """Creates the Rich layout for the terminal UI."""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main_content", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main_content"].split_row(
            Layout(name="plan_overview_panel", ratio=1, minimum_size=40),
            Layout(name="current_step_logs_panel", ratio=2),
        )
        layout["footer"].split_row(
            Layout(name="status_bar_panel", ratio=3),
            Layout(name="user_input_panel", ratio=1)
        )
        return layout

    def _get_header_panel_content(self) -> Panel:
        """Generates the content for the header panel."""
        overall_status = self.state_manager.get_global_state("plan_status") or "Unknown"
        return Panel(Text(f"Plan: {self._plan_name} | Status: {overall_status}", justify="center"), title="[b]AIWhisperer Runner[/b]")

    def _get_plan_overview_panel_content(self) -> Panel:
        """Generates the content for the plan overview panel."""
        # Get plan steps data from the state manager's state
        plan_steps_data = self.state_manager.state.get("plan", [])
        table = Table(title="Plan Execution")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Description", style="magenta")
        table.add_column("Status", justify="right")

        for step in plan_steps_data:
            step_id = step.get("step_id", "N/A")
            description = step.get("description", "No description")
            status = self.state_manager.get_task_status(step_id) or "Pending"

            status_style = "green"
            if status.lower() == "failed":
                status_style = "red"
            elif status.lower() == "running":
                status_style = "yellow"
            elif status.lower() == "paused":
                status_style = "orange"
            elif status.lower() == "cancelled":
                status_style = "grey50"
            elif status.lower() == "pending":
                 status_style = "blue"


            table.add_row(step_id, description, Text(status.capitalize(), style=status_style))
        return Panel(table, title="[b]Plan Overview[/b]", border_style="blue")

    def _get_current_step_logs_panel_content(self) -> Panel:
        """Generates the content for the current step logs panel."""
        logs_to_display = self._current_step_logs if self._active_step_id else self._general_logs
        log_display_texts = []
        for log_entry in logs_to_display:
            level_style = Style(color="green")
            if log_entry.level == LogLevel.WARNING:
                level_style = Style(color="yellow")
            elif log_entry.level == LogLevel.ERROR or log_entry.level == LogLevel.CRITICAL:
                level_style = Style(color="red")
            elif log_entry.level == LogLevel.DEBUG:
                 level_style = Style(color="blue")

            log_display_texts.append(Text(f"[{log_entry.timestamp}] ", style="dim") +
                                     Text(f"[{log_entry.level.value.lower()}]", style=level_style) +
                                      Text(f" {log_entry.component.value}: {log_entry.event_summary}"))

        title = f"[b]Logs for Step: {self._active_step_id}[/b]" if self._active_step_id else "[b]General Logs[/b]"
        return Panel(Text("\n").join(log_display_texts), title=title, border_style="green")

    def _get_status_bar_panel_content(self) -> Panel:
        """Generates the content for the status bar panel."""
        return Panel(Text(self._runner_status_info), title="[b]Status[/b]")

    def _get_user_input_panel_content(self) -> Panel:
        """Generates the content for the user input panel."""
        # This panel is more of a placeholder for where input would be taken.
        # Actual input handling is done via console.input or similar.
        return Panel(Text("Type command (e.g., pause, cancel):"), title="[b]Input[/b]")

    def update_display(self):
        """Updates the Rich Live display with the current state."""
        if self._live:
            self._layout["header"].update(self._get_header_panel_content())
            self._layout["plan_overview_panel"].update(self._get_plan_overview_panel_content())
            self._layout["current_step_logs_panel"].update(self._get_current_step_logs_panel_content())
            self._layout["status_bar_panel"].update(self._get_status_bar_panel_content())
            self._layout["user_input_panel"].update(self._get_user_input_panel_content()) # Update input panel content
            self._live.update(self._layout)

    def add_log_message(self, log_message: LogMessage):
        """Adds a log message to the appropriate log list and updates the display."""
        if log_message.step_id and log_message.step_id == self._active_step_id:
            self._current_step_logs.append(log_message)
        elif not log_message.step_id:
             self._general_logs.append(log_message)
        # Note: Logs for steps other than the active one are not stored in this simple monitor.
        # A more advanced monitor would store all logs and allow switching views.
        self.update_display()

    def set_active_step(self, step_id: Optional[str]):
        """Sets the step whose logs should be displayed."""
        self._active_step_id = step_id
        self._current_step_logs = [] # Clear previous step logs when switching
        # In a real implementation, you would load logs for this step from a log store.
        self.update_display()

    def set_runner_status_info(self, info: str):
        """Sets the information displayed in the status bar."""
        self._runner_status_info = info
        self.update_display()

    def set_plan_name(self, plan_name: str):
        """Sets the name of the plan being executed."""
        self._plan_name = plan_name
        self.update_display()

    def run(self):
        """Starts the terminal monitoring interface."""
        with Live(self._layout, console=self.console, screen=True, refresh_per_second=4) as live:
            self._live = live
            self.update_display() # Initial display
            # The main runner loop would drive updates to the state manager and call update_display
            # This run method would likely be called in a separate thread or async task
            # to allow the main runner logic to proceed.
            # For a simple example, we can keep it running until interrupted.
            try:
                while True:
                    # In a real application, user input would be handled here asynchronously
                    # or via a separate input thread/task.
                    # For this basic monitor, we'll just keep the display alive.
                    time.sleep(0.1)
            except KeyboardInterrupt:
                pass # Allow exiting with Ctrl+C

    # Placeholder for user input handling (would need to be integrated with the runner loop)
    def handle_user_input(self, command: str):
        """Processes user input commands."""
        command = command.strip().lower()
        if command == "pause":
            print("Pause requested (not implemented)") # Placeholder
            # Signal runner to pause
        elif command == "resume":
            print("Resume requested (not implemented)") # Placeholder
            # Signal runner to resume
        elif command == "cancel":
            print("Cancel requested (not implemented)") # Placeholder
            # Signal runner to cancel
        elif command.startswith("context "):
            context_text = command[8:].strip()
            print(f"Context added: {context_text} (not implemented)") # Placeholder
            # Pass context to runner
        elif command.startswith("details "):
            step_id = command[8:].strip()
            self.set_active_step(step_id)
        elif command == "help":
            print("Available commands: pause, resume, cancel, context <text>, details <step_id>, help")
        else:
            print(f"Unknown command: {command}")