from typing import Optional
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log
from textual.widgets import ListView, ListItem, Label

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.delegate_manager import DelegateManager # Import DelegateManager
from ai_whisperer.context_management import ContextManager # Import ContextManager
from ai_whisperer.config import load_config
import logging # Import logging
import signal # Import signal
import time # Import time
import threading # Import threading

logger = logging.getLogger(__name__)

class InteractiveUIBase(App):
    """A Textual app to act as an interactive delegate."""

    CTRL_C_TIMEOUT = 0.5 # Seconds

    def __init__(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        """Initialize the InteractiveUIBase with dependencies."""
        super().__init__(**kwargs)
        self._delegate_manager = delegate_manager
        self._ai_config = ai_config
        self._context_manager = context_manager
        self._config = config  # Store the passed config
        self._ai_runner_shutdown_event: Optional[threading.Event] = None # Instance variable for shutdown event
        self._ctrl_c_pressed_time: float = 0 # Instance variable for Ctrl-C timestamp
        logger.debug("InteractiveUIBase initialized with delegate_manager, ai_config, context_manager, and config.")
 

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Retrieve the shutdown event from shared state
        self._ai_runner_shutdown_event = self._delegate_manager.get_shared_state("ai_runner_shutdown_event")
        if not isinstance(self._ai_runner_shutdown_event, threading.Event):
            logger.warning("AI Runner shutdown event not found in shared state or is not a threading.Event.")
            self._ai_runner_shutdown_event = None # Ensure it's None if not found or incorrect type

        # Register the signal handler for SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, self.handle_ctrl_c)
        logger.debug("SIGINT signal handler registered.")


    def handle_ctrl_c(self, signum, frame) -> None:
        """Handles the Ctrl+C signal for graceful exit."""
        current_time = time.time()

        if self._ctrl_c_pressed_time and (current_time - self._ctrl_c_pressed_time) < self.CTRL_C_TIMEOUT:
            logger.info("Double Ctrl+C detected. Initiating graceful exit.")
            # Set the shutdown event if available
            if self._ai_runner_shutdown_event:
                self._ai_runner_shutdown_event.set()
                logger.debug("AI Runner shutdown event set.")
            # Restore the original delegate
            self._delegate_manager.restore_original_delegate("user_message_display")
            logger.debug("Original delegate restored.")
            # This will stop the Textual app and allow the main program to continue
            self.exit()
        else:
            self._ctrl_c_pressed_time = current_time
            logger.warning(f"Press Ctrl+C again within {self.CTRL_C_TIMEOUT} seconds to exit gracefully.")
            # Reset the timestamp after the timeout (optional, but good practice)
            # This would require a timer, which is more complex in signal handlers.
            # For now, relying on the time check on the next signal is sufficient.


    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        yield Footer()


    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def handle_message(self, sender, event_data) -> None:
        """Handle incoming messages as a delegate (sender, event_data)."""
        # For compatibility, extract message if present
        message = event_data["message"] if isinstance(event_data, dict) and "message" in event_data else str(event_data)
