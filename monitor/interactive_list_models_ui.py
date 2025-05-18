from typing import Optional
from textual.widgets import ListView, ListItem, Label, Log
from ai_whisperer.context_management import ContextManager
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.model_info_provider import ModelInfoProvider
from ai_whisperer.interactive_ai import ask_ai_about_model_interactive
import logging
from .interactive_ui_base import InteractiveUIBase

logger = logging.getLogger(__name__)

class InteractiveListModelsUI(InteractiveUIBase):
    """A Textual app for listing models and interacting with them, inheriting from InteractiveUIBase."""

    models: list = []
    selected_model: dict | None = None
    
    def __init__(self, delegate_manager: DelegateManager, engine: ExecutionEngine, context_manager: ContextManager, config: dict, **kwargs):
        super().__init__(config=config,
                          engine=engine,
                          delegate_manager=delegate_manager,
                          context_manager=context_manager,
                          **kwargs)
        logger.info("InteractiveListModelsUI initialized")
        self.models = []
        self.selected_model = None

    def on_mount(self) -> None:
        super().on_mount()
        model_provider = ModelInfoProvider(self._config)
        models = model_provider.list_models()
        self.display_model_list(models)

    def compose(self):
        yield from super().compose()
        yield ListView(id="model_list")
        yield ListView(id="model_options", classes="hidden")
        yield Log()

    def display_model_list(self, models: list) -> None:
        self.models = models
        model_list_view = self.query_one("#model_list", ListView)
        model_list_view.clear()
        for model in models:
            model_id = model.get('id', 'N/A')
            model_list_view.append(ListItem(Label(model_id)))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        logger.debug(f"on_list_view_selected called. event.list_view.id: {event.list_view.id}")
        if event.list_view.id == "model_list":
            selected_model_id = str(event.item.query_one(Label).renderable)
            self.selected_model = next((model for model in self.models if model.get('id') == selected_model_id), None)
            if self.selected_model:
                self.show_model_options()
        elif event.list_view.id == "model_options":
            selected_option = str(event.item.query_one(Label).renderable)
            if selected_option.startswith("Ask AI about"):
                logger.debug(f"Selected option: {selected_option}. Calling ask_ai_about_model().")
                await self.ask_ai_about_model()
            elif selected_option == "Back to model list":
                await self.back_to_model_list()

    def show_model_options(self) -> None:
        model_list_view = self.query_one("#model_list", ListView)
        model_options_view = self.query_one("#model_options", ListView)
        text_log = self.query_one(Log)
        model_list_view.add_class("hidden")
        model_options_view.remove_class("hidden")
        text_log.add_class("hidden")
        model_options_view.clear()
        model_options_view.append(ListItem(Label(f"Ask AI about {self.selected_model.get('id')}")))
        model_options_view.append(ListItem(Label("Back to model list")))

    async def ask_ai_about_model(self) -> None:
        self.query_one(Log).write(f"Asking AI about {self.selected_model.get('id')}...")
        try:
            await ask_ai_about_model_interactive(
                model=self.selected_model,
                prompt=f"Tell me about the model: {self.selected_model.get('id')}",
                engine=self._engine,
                delegate_manager=self._delegate_manager,
                context_manager=self._context_manager
            )
        finally:
            await self.back_to_model_list()

    async def back_to_model_list(self) -> None:
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
            text_log.remove_class("hidden")
        except Exception:
            pass
        self.refresh()