import asyncio
from datetime import datetime, timezone
import time
import json
import threading
import queue
from typing import Optional, List, Dict, Any
import sys
import os
import logging

# Removed PromptSession import
from prompt_toolkit.application import Application # Removed run_in_terminal import
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, BufferControl, FormattedTextControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style as PromptToolkitStyle
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.widgets import TextArea, Frame, Label

# Import necessary input/output classes
from prompt_toolkit.input import create_input
from prompt_toolkit.output import create_output

from src.ai_whisperer.terminal_monitor.command_parser import CommandParser, CommandParsingError, UnknownCommandError
# Import command classes and pass monitor instance to them if needed for interaction
from src.ai_whisperer.terminal_monitor.commands import DebuggerCommand, AskCommand, ExitCommand # Import ExitCommand
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, set_active_monitor_handler
from src.ai_whisperer.state_management import StateManager

logger = logging.getLogger(__name__)

class TerminalMonitor(logging.Handler):
    """
    Provides a terminal-based monitoring view for the AIWhisperer runner
    using prompt_toolkit for the UI. Also acts as a logging handler.
    """

    def __init__(self, state_manager: StateManager, config_path: str, monitor_enabled: bool = True, ai_runner_shutdown_event: Optional[threading.Event] = None):
        super().__init__()
        return
        self.level = logging.DEBUG
        self.state_manager = state_manager
        self.config_path = config_path # Store config_path
        self.monitor_enabled = monitor_enabled
        self._ai_runner_shutdown_event = ai_runner_shutdown_event # Store the AI runner's shutdown event
        self._application: Optional[Application] = None
        self._running = False
        self._update_queue = queue.Queue() # Still use queue for thread safety in emit
        self._shutdown_event = threading.Event() # This is for the UI thread's own shutdown
        # Removed _app_ready_event and _input_thread

        # Create input and output instances
        logger.debug("Creating prompt_toolkit input and output instances.")
        self._input = create_input() # This should handle disabling terminal echoing
        self._output = create_output()
        logger.debug("prompt_toolkit input and output instances created.")

        # prompt_toolkit UI components
        # Make the log buffer writable so it can be updated
        self._log_buffer = Buffer()
        self._log_window = Window(BufferControl(buffer=self._log_buffer), wrap_lines=True)

        self._input_buffer = Buffer()
        self._input_window = Window(BufferControl(buffer=self._input_buffer), height=1)

        self._status_label = Label(text="Initializing...")
        self._plan_label = Label(text="Loading Plan...")

        self._layout = self._create_layout()

        # Command handler mapping
        # Instantiate commands that the monitor will handle, passing necessary dependencies
        self.command_handlers = {
            DebuggerCommand.name: DebuggerCommand(config_path=self.config_path, state_manager=self.state_manager), # Pass config_path and state_manager
            AskCommand.name: AskCommand(config_path=self.config_path, state_manager=self.state_manager), # Pass config_path and state_manager
            ExitCommand.name: ExitCommand(config_path=self.config_path, monitor_instance=self), # Pass config_path and monitor_instance
        }
        self.command_parser = CommandParser(self.command_handlers)

        self._current_step_logs: List[LogMessage] = []
        self._general_logs: List[LogMessage] = []
        self._active_subtask_id: Optional[str] = None
        self._runner_status_info: str = "Initializing..."
        self._plan_name: str = "Loading Plan..."

        self._key_bindings = KeyBindings()

        @self._key_bindings.add('c-c')
        def _(event):
            """Handle Ctrl+C."""
            logger.info("Ctrl+C received. Signaling shutdown.")
            self._shutdown_event.set() # Signal UI loop to stop
            if self._ai_runner_shutdown_event:
                logger.debug("Ctrl+C: Signaling AI runner thread to stop.")
                self._ai_runner_shutdown_event.set() # Signal AI thread to stop
            # Signal the prompt_toolkit application to exit gracefully
            # Use call_soon_threadsafe to schedule the exit on the UI thread's event loop
            if self._application and self._application.loop:
                self._application.loop.call_soon_threadsafe(self._application.exit)
            else:
                logger.warning("Ctrl+C received, but prompt_toolkit application or loop not available to schedule exit.")

        @self._key_bindings.add('enter')
        def _(event):
            """Handle Enter key."""
            # Get command input from the current buffer (should be the input buffer)
            command_input = event.current_buffer.text
            logger.debug(f"Enter key pressed. Raw command input: '{command_input}'")
            event.current_buffer.reset() # Clear the input buffer
            # Process command input directly in the UI thread's event loop
            self._process_command_input(command_input)

    def _create_layout(self) -> Layout:
        """Creates the prompt_toolkit layout for the terminal UI."""
        root_layout = HSplit([
            VSplit([
                Frame(self._plan_label, title="Plan", height=1),
                Frame(self._status_label, title="Status", height=1),
            ], height=1),
            Frame(self._log_window, title="Logs", height=None, style="class:logs"),
            Frame(self._input_window, title="Input", height=3, style="class:input"),
        ])
        return Layout(root_layout)

    def _get_log_text(self) -> str:
        logs_to_display = self._current_step_logs if self._active_subtask_id else self._general_logs
        log_lines = []
        for log_entry in logs_to_display:
            level_style = "ansigreen"
            if log_entry.level == LogLevel.WARNING:
                level_style = "ansiyellow"
            elif log_entry.level == LogLevel.ERROR or log_entry.level == LogLevel.CRITICAL:
                level_style = "ansired"
            elif log_entry.level == LogLevel.DEBUG:
                level_style = "ansiblue"
            elif log_entry.level == LogLevel.INFO:
                level_style = "ansicyan"
            log_prefix = (
                f"<style fg='ansidim'>[{log_entry.timestamp}]</style> "
                f"<style fg='{level_style}'>[{log_entry.level.value.lower()}]</style>"
                f" {log_entry.component.value}: "
            )
            try:
                json_data = json.loads(log_entry.event_summary)
                json_string = json.dumps(json_data, indent=2)
                log_lines.append(f"{log_prefix}{json_string}")
            except json.JSONDecodeError:
                log_lines.append(f"{log_prefix}{log_entry.event_summary}")
        if not log_lines:
            return "<style fg='ansidim'>No monitor output yet...</style>"
        return "\n".join(log_lines)

    def update_display(self):
        return
        if self._application:
            self._log_buffer.text = self._get_log_text()
            overall_status = self.state_manager.get_global_state("plan_status") or "Unknown"
            self._plan_label.text = f"Plan: {self._plan_name}"
            self._status_label.text = f"Status: {self._runner_status_info} | Overall: {overall_status}"
            self._application.invalidate()

    def set_plan_name(self, plan_name: str):
        self._plan_name = plan_name
        self.update_display()

    def set_runner_status(self, status: str):
        self._runner_status_info = status
        self.update_display()

    def set_active_subtask_id(self, subtask_id: Optional[str]):
        self._active_subtask_id = subtask_id
        self._current_step_logs = []
        self.update_display()

    def emit(self, record: logging.LogRecord):
        if not self.monitor_enabled:
            return
        if hasattr(record, 'component') and record.component in [ComponentType.MONITOR.value, ComponentType.EXECUTION_ENGINE.value, ComponentType.RUNNER.value]:
            try:
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
                    event_summary=getattr(record, 'event_summary', getattr(record, 'message', 'N/A')),
                    timestamp=getattr(record, 'timestamp', datetime.now(timezone.utc).isoformat(timespec="milliseconds") + "Z"),
                    subtask_id=getattr(record, 'subtask_id', None),
                    event_id=getattr(record, 'event_id', None),
                    state_before=getattr(record, 'state_before', None),
                    state_after=getattr(record, 'state_after', None),
                    duration_ms=getattr(record, 'duration_ms', None),
                    details=getattr(record, 'details', {}),
                )
                self._update_queue.put({"type": "log", "data": log_message})
                if self._application and self._application.loop and not self._application.future.done():
                    try:
                        self._application.loop.call_soon_threadsafe(lambda: self._process_update(self._update_queue.get_nowait()))
                    except Exception as schedule_e:
                        logger.error(f"Error scheduling UI update from logging thread: {schedule_e}", exc_info=True)
                elif self._shutdown_event.is_set():
                    pass
                else:
                    pass
            except Exception as e:
                print(f"Error in TerminalMonitor processing log record: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)

    def _ui_thread_loop(self):
        logger.debug("_ui_thread_loop started.")
        logging.getLogger().propagate = False
        logger.debug("_ui_thread_loop: Initializing prompt_toolkit application.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.debug("_ui_thread_loop: New asyncio event loop created and set.")
        try:
            style = PromptToolkitStyle.from_dict({
                'frame.border': '#888888',
                'frame.label': '#ffffff',
                'logs': '#00aa00',
                'input': '#0000aa',
            })
            self._application = Application(
                layout=self._layout,
                key_bindings=self._key_bindings,
                style=style,
                full_screen=True,
                input=self._input,
                output=self._output,
            )
            self._application.layout.focus(self._input_buffer)
            logger.debug("_ui_thread_loop: Calling self._application.run().")
            loop.run_until_complete(self._application.run_async())
            logger.debug("_ui_thread_loop: self._application.run_async() finished.")
            logger.debug("_ui_thread_loop: prompt_toolkit application run finished.")
        except Exception as e:
            logger.error(f"_ui_thread_loop caught exception: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
        finally:
            logger.debug("_ui_thread_loop finished.")
            self._running = False
            set_active_monitor_handler(None)
            if self._input and hasattr(self._input, 'close'):
                try:
                    self._input.close()
                    logger.debug("_ui_thread_loop: Input stream closed.")
                except Exception as e:
                    logger.error(f"_ui_thread_loop: Error closing input stream: {e}")
            if self._output and hasattr(self._output, 'leave_raw_mode'):
                try:
                    self._output.leave_raw_mode()
                    logger.debug("_ui_thread_loop: Output stream left raw mode.")
                except Exception as e:
                    logger.error(f"_ui_thread_loop: Error leaving raw mode for output stream: {e}")
            if loop and not loop.is_closed():
                logger.debug("_ui_thread_loop: Closing asyncio event loop.")
                loop.close()
                logger.debug("_ui_thread_loop: Asyncio event loop closed.")

    def _process_update(self, update: Dict[str, Any]):
        update_type = update.get("type")
        data = update.get("data")
        if update_type == "log":
            log_message = data
            if log_message.subtask_id and log_message.subtask_id == self._active_subtask_id:
                self._current_step_logs.append(log_message)
            elif not log_message.subtask_id:
                self._general_logs.append(log_message)
            self.update_display()

    def _process_command_input(self, command_input: str):
        if self._shutdown_event.is_set():
            logger.debug("_process_command_input: Shutdown event is set, ignoring further command input.")
            return
        logger.debug(f"_process_command_input: Received command input: '{command_input}'")
        try:
            if not command_input or command_input.isspace():
                logger.debug("_process_command_input: Command input is empty or whitespace, skipping parsing.")
                return
            parsed_command = self.command_parser.parse(command_input)
            command_name = parsed_command.name
            command_args = parsed_command.args
            logger.debug(f"Parsed command name: {command_name}, args: {command_args}")
            if command_name in self.command_handlers:
                command_instance = self.command_handlers[command_name]
                command_instance.execute(command_args)
            else:
                error_message = LogMessage(
                    level=LogLevel.ERROR,
                    component=ComponentType.MONITOR,
                    action="command_error",
                    event_summary=f"Unknown command '{command_name}'"
                )
                self._update_queue.put({"type": "log", "data": error_message})
                if self._application and self._application.loop:
                    self._application.loop.call_soon_threadsafe(lambda: self._process_update(self._update_queue.get_nowait()))
        except (CommandParsingError, UnknownCommandError) as e:
            error_message = LogMessage(
                level=LogLevel.ERROR,
                component=ComponentType.MONITOR,
                action="command_parsing_error",
                event_summary=f"Error parsing command: {e}"
            )
            self._update_queue.put({"type": "log", "data": error_message})
            if self._application and self._application.loop:
                self._application.loop.call_soon_threadsafe(lambda: self._process_update(self._update_queue.get_nowait()))
        except Exception as e:
            error_message = LogMessage(
                level=LogLevel.CRITICAL,
                component=ComponentType.MONITOR,
                action="command_execution_error",
                event_summary=f"An unexpected error occurred during command execution: {e}"
            )
            self._update_queue.put({"type": "log", "data": error_message})
            if self._application and self._application.loop:
                self._application.loop.call_soon_threadsafe(lambda: self._process_update(self._update_queue.get_nowait()))

    def run(self):
        if self.monitor_enabled:
            set_active_monitor_handler(self)
            self._running = True
            logger.debug("TerminalMonitor.run: Starting prompt_toolkit UI thread.")
            ui_thread = threading.Thread(target=self._ui_thread_loop, name="UITerminalMonitorThread", daemon=True)
            ui_thread.start()
            logger.debug("TerminalMonitor.run: prompt_toolkit UI thread started.")
            logger.debug("TerminalMonitor.run: UI thread started. Main thread will not wait for UI thread to join here.")
        else:
            print("Terminal monitoring is disabled.")

    def stop(self):
        logger.debug(f"TerminalMonitor.stop called. Current state: _running={self._running}, _shutdown_event.is_set()={self._shutdown_event.is_set()}, _ai_runner_shutdown_event={self._ai_runner_shutdown_event})")
        if self.monitor_enabled:
            if self._ai_runner_shutdown_event and not self._ai_runner_shutdown_event.is_set():
                logger.debug("TerminalMonitor.stop: Signaling AI runner thread to stop.")
                self._ai_runner_shutdown_event.set()
            elif self._ai_runner_shutdown_event:
                logger.debug("TerminalMonitor.stop: AI runner shutdown event was already set.")
            else:
                logger.debug("TerminalMonitor.stop: _ai_runner_shutdown_event is None.")
            if self._application and self._application.loop and not self._application.future.done():
                logger.debug("TerminalMonitor.stop: Scheduling prompt_toolkit application exit.")
                self._application.loop.call_soon_threadsafe(self._application.exit)
            elif self._application and self._application.future.done():
                logger.debug("TerminalMonitor.stop: prompt_toolkit application is already done.")
            else:
                logger.debug("TerminalMonitor.stop: prompt_toolkit application or loop not available.")
            if not self._shutdown_event.is_set():
                logger.debug("TerminalMonitor.stop: Setting UI _shutdown_event.")
                self._shutdown_event.set()
            else:
                logger.debug("TerminalMonitor.stop: UI _shutdown_event was already set.")
        logger.debug("TerminalMonitor.stop finished.")
