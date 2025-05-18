from typing import Optional
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log
from textual.widgets import ListView, ListItem, Label

from ai_whisperer.delegate_manager import DelegateManager # Import DelegateManager
from ai_whisperer.execution_engine import ExecutionEngine # Import ExecutionEngine
from ai_whisperer.context_management import ContextManager # Import ContextManager
from ai_whisperer.model_info_provider import ModelInfoProvider
from ai_whisperer.config import load_config
import logging # Import logging
import signal # Import signal
import time # Import time
import threading # Import threading

logger = logging.getLogger(__name__)

from ai_whisperer.interactive_ai import ask_ai_about_model_interactive # Import the new function

class InteractiveDelegate(App):
    """A Textual app to act as an interactive delegate."""

    CTRL_C_TIMEOUT = 0.5 # Seconds

    def __init__(self, delegate_manager: DelegateManager, engine: ExecutionEngine, context_manager: ContextManager, config: dict, **kwargs):
        """Initialize the InteractiveDelegate with dependencies."""
        super().__init__(**kwargs)
        self.delegate_manager = delegate_manager
        self.engine = engine
        self.context_manager = context_manager
        self.config = config  # Store the passed config
        self._ai_runner_shutdown_event: Optional[threading.Event] = None # Instance variable for shutdown event
        self._ctrl_c_pressed_time: float = 0 # Instance variable for Ctrl-C timestamp
        logger.debug("InteractiveDelegate initialized with delegate_manager, engine, context_manager, and config.")


    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Retrieve the shutdown event from shared state
        self._ai_runner_shutdown_event = self.delegate_manager.get_shared_state("ai_runner_shutdown_event")
        if not isinstance(self._ai_runner_shutdown_event, threading.Event):
            logger.warning("AI Runner shutdown event not found in shared state or is not a threading.Event.")
            self._ai_runner_shutdown_event = None # Ensure it's None if not found or incorrect type

        # Register the signal handler for SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, self.handle_ctrl_c)
        logger.debug("SIGINT signal handler registered.")

        # Use the config passed to the constructor
        model_provider = ModelInfoProvider(self.config)
        models = model_provider.list_models()
        self.display_model_list(models)


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
            self.delegate_manager.restore_original_delegate("user_message_display")
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

    models: list = [] # Placeholder for model data
    selected_model: dict | None = None # Store the selected model

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        yield Footer()
        yield ListView(id="model_list") # Add ListView for models with an ID
        yield ListView(id="model_options", classes="hidden") # Add a second ListView for options, initially hidden
        yield Log()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def display_model_list(self, models: list) -> None:
        """Displays the list of models in the ListView."""
        self.models = models
        model_list_view = self.query_one("#model_list", ListView)
        model_list_view.clear() # Clear existing items
        for model in models:
            model_id = model.get('id', 'N/A')
            model_list_view.append(ListItem(Label(model_id)))

    async def on_list_view_selected(self, event: ListView.Selected) -> None: # Make the method async
        """Handles a model selection from the list."""
        logger.debug(f"on_list_view_selected called. event.list_view.id: {event.list_view.id}")
        print(f"[DEBUG] on_list_view_selected: event.list_view.id={event.list_view.id}")
        if event.list_view.id == "model_list":
            # Try accessing the Label's value through children
            selected_model_id = str(event.item.query_one(Label).renderable) # Access renderable and convert to string
            self.selected_model = next((model for model in self.models if model.get('id') == selected_model_id), None)
            if self.selected_model:
                self.show_model_options()
        elif event.list_view.id == "model_options":
            selected_option = str(event.item.query_one(Label).renderable) # Access renderable and convert to string
            if selected_option.startswith("Ask AI about"):
                logger.debug(f"Selected option: {selected_option}. Calling ask_ai_about_model().")
                await self.ask_ai_about_model() # Await the async call
            elif selected_option == "Back to model list":
                self.back_to_model_list()

    def show_model_options(self) -> None:
        """Displays options after a model is selected."""
        model_list_view = self.query_one("#model_list", ListView)
        model_options_view = self.query_one("#model_options", ListView)
        text_log = self.query_one(Log)

        model_list_view.add_class("hidden")
        model_options_view.remove_class("hidden")
        text_log.add_class("hidden") # Hide text log for now

        model_options_view.clear()
        model_options_view.append(ListItem(Label(f"Ask AI about {self.selected_model.get('id')}")))
        model_options_view.append(ListItem(Label("Back to model list")))

    async def ask_ai_about_model(self) -> None: # Make the method async
        """Initiates an AI interaction about the selected model."""
        print(f"[DEBUG] ask_ai_about_model called for model: {self.selected_model.get('id')}")
        self.query_one(Log).write(f"Asking AI about {self.selected_model.get('id')}...")
        try:
            # Call the new function to initiate the AI loop
            await ask_ai_about_model_interactive( # Await the async call
                model=self.selected_model,
                prompt=f"Tell me about the model: {self.selected_model.get('id')}",
                engine=self.engine,
                delegate_manager=self.delegate_manager,
                context_manager=self.context_manager # Pass the context_manager
            )
        finally:
            # After the AI interaction, return to the model list (even if error)
            await self.back_to_model_list()


    async def back_to_model_list(self) -> None:
        """Returns to the model list view and refreshes UI. Handles missing widgets gracefully."""
        try:
            model_list_view = self.query_one("#model_list", ListView)
            model_list_view.remove_class("hidden")
        except Exception:
            pass
        try:
            model_options_view = self.query_one("#model_options", ListView)
            model_options_view.add_class("hidden")
        except Exception:
            pass
        try:
            text_log = self.query_one(Log)
            text_log.remove_class("hidden") # Show text log again
        except Exception:
            pass
        self.refresh()

    def handle_message(self, sender, event_data) -> None:
        """Handle incoming messages as a delegate (sender, event_data)."""
        # For compatibility, extract message if present
        message = event_data["message"] if isinstance(event_data, dict) and "message" in event_data else str(event_data)
        # Existing logic (if any) can go here
