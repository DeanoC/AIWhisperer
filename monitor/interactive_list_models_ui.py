from textual.events import MouseMove, Key
from textual.message import Message  # <-- Ensure Message is imported before use
from textual.widgets import Input
from typing import Any, Optional
from textual.widgets import ListView, ListItem, Label, Static, Header, Footer, Tooltip # Added Header, Footer, Tooltip
from textual.containers import Container # Import Container
from textual.message import Message # Import Message
from textual.reactive import var # Import var
from textual import on # Import on
import logging
from rich.text import Text  # <-- Add this import
import asyncio

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.context_management import ContextManager
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.model_info_provider import ModelInfoProvider
from ai_whisperer.interactive_ai import InteractiveAI
from monitor.interactive_ui_base import InteractiveUIBase
from monitor.multiline_input import MultiLineInput

# Floating tooltip message
class ShowTooltipMessage(Message):
    def __init__(self, tooltip_text: str, x: int, y: int) -> None:
        super().__init__()
        self.tooltip_text = tooltip_text
        self.x = x
        self.y = y
class HideTooltipMessage(Message):
    pass

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
        # Store tooltip text for use in compose (pricing and context length on same line, only prompt/completion price)
        pricing = model_data.get('pricing', {})
        def format_per_million(val):
            try:
                # If already a string, try to convert to float
                if isinstance(val, str):
                    val = float(val)
                return f"${val * 1_000_000:,.2f}/M"
            except Exception:
                return str(val)

        if isinstance(pricing, dict):
            prompt_price = pricing.get('prompt', 'N/A')
            completion_price = pricing.get('completion', 'N/A')
            prompt_str = format_per_million(prompt_price) if prompt_price != 'N/A' else 'N/A'
            completion_str = format_per_million(completion_price) if completion_price != 'N/A' else 'N/A'
            pricing_str = f"Prompt: {prompt_str}, Completion: {completion_str}"
        else:
            pricing_str = str(pricing)
        self._tooltip_text = f"""
[bold]{model_data.get('name', model_data.get('id', 'N/A'))}[/bold] ([dim]{model_data.get('id', 'N/A')}[/dim])\n[yellow]Context:[/yellow] {model_data.get('context_length', 'N/A')} tokens  [yellow]Pricing:[/yellow] {pricing_str}
        """

    def compose(self):
        label = Label(self.model_data.get('id', 'N/A'))
        yield label

    def on_mouse_move(self, event: MouseMove) -> None:
        # Send a message to parent to show tooltip at mouse position
        self.post_message(ShowTooltipMessage(self._tooltip_text, event.screen_x, event.screen_y))

    def on_leave(self, event) -> None:
        # Send a message to parent to hide tooltip
        self.post_message(HideTooltipMessage())


logger = logging.getLogger(__name__)

class InteractiveListModelsUI(InteractiveUIBase):
    CSS_PATH = "interactive_list_models_ui.tcss"
    THEME_LIGHT = "textual-light"
    THEME_DARK = "textual-dark"
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
        self.dark = False
        self.theme = self.THEME_LIGHT

        # Register the receiver within the worker
        self._delegate_manager.register_notification(
            "ai_loop.message.ai_chunk_received", self.ai_chunk_receiver
        )
        # Ensure the event loop is running
        loop = asyncio.get_event_loop()
        self.interactive_ai_task = loop.create_task(self.initialize())  # Start async initialization

    async def initialize(self):
        """Asynchronous initialization logic."""
        self.interactive_ai = InteractiveAI(
            model=self.selected_model,
            ai_config=self._ai_config,
            delegate_manager=self._delegate_manager,
            context_manager=self._context_manager
        )
        await self.interactive_ai.start_interactive_ai_session(
            "You are an AI assistant that provides information about AI models that OpenRouter supports."
        )
        logger.info("Interactive AI session started")

    def on_mount(self) -> None:
        super().on_mount()
        self.set_theme(self.theme)
        # tooltip = self.query_one("#floating_tooltip", Static)
        # tooltip.visible = False
        # tooltip.display = "none"
        model_provider = ModelInfoProvider(self._config)
        models = model_provider.list_models()
        self.display_model_list(models)

    def on_mount(self) -> None:
        super().on_mount()
        # tooltip = self.query_one("#floating_tooltip", Static)
        # tooltip.visible = False
        # tooltip.display = "none"
        model_provider = ModelInfoProvider(self._config)
        models = model_provider.list_models()
        self.display_model_list(models)
        # Focus the input widget
#        self.query_one("#chat-input").focus()
        # Ensure the Input widget captures key events
        # command_input = self.query_one("#command_input", Input)
        # command_input.capture_key_events = True
        # command_input.on_key = self.on_key  # Bind the key event handler
        # command_input.focus()  # Focus the command input area on mount
        
    def compose(self):
        yield Header()  # Yield Header first
        with Container(id="main_content"):
            yield ListView(id="model_list")
            # Chat area with chat window and command editor stacked vertically
            with Container(id="chat_area", classes="chat-area"):
                yield Static(id="chat_window")  # Chat window (messages)
                yield Label("Enter your message (Ctrl+Enter to send):", id="command-label")
                yield MultiLineInput(id="chat-input")
#                yield Static("Commands", id="command_label", classes="command-label")
#                yield Input(id="command_input", classes="command-input")
        # Floating tooltip (initially hidden)
        # yield Static("", id="floating_tooltip", classes="floating-tooltip")
        yield Footer()  # Yield Footer last

    # @on(ShowTooltipMessage)
    # def show_floating_tooltip(self, message: ShowTooltipMessage) -> None:
    #     tooltip = self.query_one("#floating_tooltip", Static)
    #     tooltip.update(message.tooltip_text)
    #     # Get screen size if possible (fallback to 800x600)
    #     try:
    #         screen_width = self.size.width
    #         screen_height = self.size.height
    #     except Exception:
    #         screen_width = 800
    #         screen_height = 600
    #     # Tooltip size estimate (max width 50 chars, height 8 lines)
    #     tooltip_width = 50 * 8  # 8px per char
    #     tooltip_height = 8 * 20 # 20px per line
    #     # Default offset
    #     left = message.x + 32
    #     # If mouse is in lower half, show above; else below
    #     if message.y > screen_height // 2:
    #         top = max(0, message.y - tooltip_height - 32)
    #     else:
    #         top = message.y + 32
    #     # Flip left if near right edge
    #     if left + tooltip_width > screen_width:
    #         left = max(0, message.x - tooltip_width - 32)
    #     tooltip.styles.left = left
    #     tooltip.styles.top = top
    #     tooltip.styles.max_width = 400
    #     tooltip.styles.max_height = 200
    #     tooltip.styles.overflow_y = "auto"
    #     tooltip.styles.word_break = "break-word"
    #     tooltip.display = "block"
    #     tooltip.visible = True

    # @on(HideTooltipMessage)
    # def hide_floating_tooltip(self, message: HideTooltipMessage) -> None:
    #     tooltip = self.query_one("#floating_tooltip", Static)
    #     tooltip.visible = False
    #     tooltip.display = "none"

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
        log_widget.scroll_end(animate=False)

    def _write_ai_message(self, log_widget, message: str):
        # Add an AI message as a Static widget with ai-message class
        log_widget.mount(Static(message, classes="ai-message"))
        log_widget.scroll_end(animate=False)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        logger.debug(f"on_list_view_selected called. event.list_view.id: {event.list_view.id}")
        if event.list_view.id == "model_list":
            selected_model_id = str(event.item.query_one(Label).renderable)
            self.selected_model = next((model for model in self.models if model.get('id') == selected_model_id), None)
            if self.selected_model:
                self.call_later(self.ask_ai_about_model)

    def ai_chunk_receiver(self, sender: Any, event_data: dict) -> None:
        content_chunk = event_data.get("delta_content") if isinstance(event_data, dict) and "delta_content" in event_data else str(event_data)

        if not content_chunk: # Skip empty or None chunks
            return

        # Determine lines in chunk, keeping terminators for accurate newline detection
        lines_in_chunk = content_chunk.splitlines(keepends=True)
        if not lines_in_chunk and content_chunk: # Handles case where content_chunk is not empty but has no newlines
            lines_in_chunk = [content_chunk]

        # Post a message to the main thread
        self.post_message(AIChunkMessage(lines_in_chunk))

    async def _run_ask_ai_worker(self) -> None:
        """Runs the ask_ai_about_model_interactive"""
        await self.interactive_ai.wait_for_idle()  # Ensure AI loop is idle before starting

        log_container = self.query_one("#chat_window", Static) # Renamed for clarity

        # Show the model's full description before asking the AI
        if self.selected_model:
            model_id = self.selected_model.get('id', 'N/A')
            model_name = self.selected_model.get('name', model_id)
            model_desc = self.selected_model.get('description', None)
            if model_desc:
                desc_message = f"[b]{model_name}[/b] ([dim]{model_id}[/dim])\n{model_desc}"
            else:
                desc_message = f"[b]{model_name}[/b] ([dim]{model_id}[/dim])\n(No description available)"
            self._write_user_message(log_container, desc_message)

        # User prompt for AI
        self._write_user_message(log_container, f"Asking AI about {self.selected_model.get('id')}...")

        self._current_ai_message_widget = None # Reset before new AI response stream

        await self.interactive_ai.send_message(
            message=f"Tell me about the model: {self.selected_model.get('id')}"
        )

    async def ask_ai_about_model(self) -> None:
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

            has_newline = '\n' in line_part

            if self.current_ai_message_widget is None:
                self.current_ai_message_widget = Static(line_part, classes="ai-message")
                log_container.mount(self.current_ai_message_widget)
            else:
                # Append to existing Static widget
                # Static.renderable can be Text or str. Text + str works.
                self.current_ai_message_widget.update(self.current_ai_message_widget.renderable + line_part)

            # Auto-scroll to bottom after each update
            log_container.scroll_end(animate=False)

            if has_newline:
                self.current_ai_message_widget = None # This line is complete, next part/chunk starts new Static

    # def on_key(self, event: Key) -> None:
    #     """Handle key press events in the command input."""
    #     command_input = self.query_one("#command_input", Input)
    #     if event.key == "enter":
    #         user_input = command_input.value.strip()
    #         if user_input:
    #             self._write_user_message(self.query_one("#chat_window", Static), user_input)
    #             command_input.value = ""  # Clear the input field
    #             asyncio.create_task(self.interactive_ai.send_message(message=user_input))
#     def on_multiline_input_submitted(self, message: MultiLineInput.Submitted) -> None:
#         """Handle submission of the input widget."""
#         if not message.value.strip():
#             return
            
#         # Add user message to chat
# #        chat_container = self.query_one("#chat-container")
# #        chat_container.mount(ChatMessage(message.value))
        
#         # Process command (in a real app, this would send to an AI)
#         command_parts = message.value.strip().split(maxsplit=1)
#         command = command_parts[0].lower() if command_parts else ""
        
#         # Simple command handling
#         if command == "quit":
#             self.exit()
#         elif command == "clear":
#             # Clear all messages except the first one
#             chat_container = self.query_one("#chat-container")
#             messages = chat_container.query("ChatMessage")
#             for i, msg in enumerate(messages):
#                 if i > 0:  # Keep the first welcome message
#                     msg.remove()
#         else:
#             # Simulate AI response
#             response = f"You said: {message.value}\n\nThis is a demo response. In a real application, this would be processed by an AI."
# #            chat_container.mount(ChatMessage(response, is_user=False))
        
#         # Scroll to the bottom
#         chat_container.scroll_end(animate=False)
