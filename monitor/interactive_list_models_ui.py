from typing import Any, Optional
from textual.widgets import ListView, ListItem, Label, Static, Header, Footer # Added Header, Footer
from textual.containers import Container # Import Container
from textual.message import Message # Import Message
from textual.reactive import var # Import var
from textual import on # Import on

# Define a custom message for AI chunks
class AIChunkMessage(Message):
    """Message to carry AI response chunks."""
    def __init__(self, lines_in_chunk: list[str]) -> None:
        super().__init__()
        self.lines_in_chunk = lines_in_chunk

class ModelListItem(ListItem):
    """A custom ListItem for displaying model information with tooltips."""
    def __init__(self, model_data):
        super().__init__()
        self.model_data = model_data
        # Create tooltip content with detailed model information
        tooltip_text = f"""
[bold]{model_data.get('name', model_data.get('id', 'N/A'))}[/bold] ([dim]{model_data.get('id', 'N/A')}[/dim])\n[yellow]Description:[/yellow] {model_data.get('description', 'No description').replace('&', '&').replace('<', '<').replace('>', '>').replace('[', '&#91;').replace(']', '&#93;')}\n[yellow]Context Length:[/yellow] {model_data.get('context_length', 'N/A')} tokens\n[yellow]Pricing:[/yellow] {model_data.get('pricing', 'N/A')}
        """
        self.tooltip = tooltip_text
    def compose(self):
        yield Label(self.model_data.get('id', 'N/A'))
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.context_management import ContextManager
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.model_info_provider import ModelInfoProvider
from ai_whisperer.interactive_ai import ask_ai_about_model_interactive
import logging
from .interactive_ui_base import InteractiveUIBase
from rich.text import Text  # <-- Add this import

logger = logging.getLogger(__name__)

class InteractiveListModelsUI(InteractiveUIBase):
    CSS_PATH = "interactive_list_models_ui.tcss"
    """A Textual app for listing models and interacting with them, inheriting from InteractiveUIBase."""

    BINDINGS = [
    ]

    models: list = []
    selected_model: dict | None = None
    _current_ai_message_widget: Optional[Static] = None  # Added for streaming AI messages
    
    def __init__(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        super().__init__(config=config,
                          ai_config=ai_config,
                          delegate_manager=delegate_manager,
                          context_manager=context_manager,
                          **kwargs)
        logger.info("InteractiveListModelsUI initialized")
        self.models = []
        self.selected_model = None
        self._current_ai_message_widget = None # Initialize here as well

    def on_mount(self) -> None:
        super().on_mount()
        model_provider = ModelInfoProvider(self._config)
        models = model_provider.list_models()
        self.display_model_list(models)

    def compose(self):
        yield Header()  # Yield Header first
        with Container(id="main_content"): # Container for model list and chat window
            yield ListView(id="model_list")
            yield Static(id="chat_window") # Chat window to the right
        yield Footer()  # Yield Footer last

    def display_model_list(self, models: list) -> None:
        # Only update the list if the models have actually changed
        if self.models == models:
            return  # No change, don't clear/repopulate (prevents tooltip flicker)
        self.models = models
        model_list_view = self.query_one("#model_list", ListView)
        model_list_view.clear()
        for model in models:
            model_list_view.append(ModelListItem(model))

    def _write_user_message(self, log_widget, message: str):
        # Add a user message as a Static widget with user-message class
        log_widget.mount(Static(message, classes="user-message"))

    def _write_ai_message(self, log_widget, message: str):
        # Add an AI message as a Static widget with ai-message class
        log_widget.mount(Static(message, classes="ai-message"))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        logger.debug(f"on_list_view_selected called. event.list_view.id: {event.list_view.id}")
        if event.list_view.id == "model_list":
            selected_model_id = str(event.item.query_one(Label).renderable)
            self.selected_model = next((model for model in self.models if model.get('id') == selected_model_id), None)
            if self.selected_model:
                self.call_later(self.ask_ai_about_model)

    async def _run_ask_ai_worker(self) -> None:
        """Runs the ask_ai_about_model_interactive in a worker thread."""
        # log_container = self.query_one("#chat_window", Static) # No longer needed in worker

        def ai_chunk_receiver(sender: Any, event_data: dict) -> None:
            content_chunk = event_data.get("delta_content") if isinstance(event_data, dict) and "delta_content" in event_data else str(event_data)
            
            if not content_chunk: # Skip empty or None chunks
                return

            # Determine lines in chunk, keeping terminators for accurate newline detection
            lines_in_chunk = content_chunk.splitlines(keepends=True)
            if not lines_in_chunk and content_chunk: # Handles case where content_chunk is not empty but has no newlines
                lines_in_chunk = [content_chunk]

            # Post a message to the main thread
            self.post_message(AIChunkMessage(lines_in_chunk))

        # Register the receiver within the worker
        self._delegate_manager.register_notification(
            "ai_loop.message.ai_chunk_received", ai_chunk_receiver
        )

        try:
            await ask_ai_about_model_interactive(
                model=self.selected_model,
                prompt=f"Tell me about the model: {self.selected_model.get('id')}",
                ai_config=self._ai_config,
                delegate_manager=self._delegate_manager,
                context_manager=self._context_manager
            )
        finally:
            # Unregister the receiver when the worker finishes
            self._delegate_manager.unregister_notification(
                "ai_loop.message.ai_chunk_received", ai_chunk_receiver
            )

    async def ask_ai_about_model(self) -> None:
        log_container = self.query_one("#chat_window", Static) # Renamed for clarity
        # User prompt
        self._write_user_message(log_container, f"Asking AI about {self.selected_model.get('id')}...")

        self._current_ai_message_widget = None # Reset before new AI response stream

        # Run the AI interaction in a worker thread
        self.run_worker(self._run_ask_ai_worker)

    @property
    def current_ai_message_widget(self) -> Optional[Static]:
        """Property to access the current AI message widget."""
        return self._current_ai_message_widget

    @current_ai_message_widget.setter
    def current_ai_message_widget(self, widget: Optional[Static]) -> None:
        """Setter for the current AI message widget."""
        self._current_ai_message_widget = widget

    @on(AIChunkMessage)
    def on_ai_chunk_message(self, message: AIChunkMessage) -> None:
        """Handles AI chunk messages received from the worker."""
        log_container = self.query_one("#chat_window", Static)
        lines_in_chunk = message.lines_in_chunk

        for line_part in lines_in_chunk:
            if not line_part: # Skip empty strings that might result from splitlines
                continue

            has_newline = '\\n' in line_part

            if self.current_ai_message_widget is None:
                self.current_ai_message_widget = Static(line_part, classes="ai-message")
                log_container.mount(self.current_ai_message_widget)
            else:
                # Append to existing Static widget
                # Static.renderable can be Text or str. Text + str works.
                self.current_ai_message_widget.update(self.current_ai_message_widget.renderable + line_part)

            if has_newline:
                self.current_ai_message_widget = None # This line is complete, next part/chunk starts new Static
