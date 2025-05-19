import logging
import uuid
import asyncio
import threading

from ai_whisperer.ai_loop.ai_loopy import AILoop
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService # Import OpenRouterAIService
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.context_management import ContextManager

logger = logging.getLogger(__name__)

async def ask_ai_about_model_interactive(
    model: dict,
    prompt: str,
    ai_config: AIConfig,
    delegate_manager: DelegateManager,
    context_manager: ContextManager
):
    """
    Initiates an interactive AI conversation about a specific model using the new AILoop.

    Args:
        model: The dictionary containing the selected model's information.
        prompt: The initial prompt for the AI.
        engine: The ExecutionEngine instance (contains the main config).
        delegate_manager: The DelegateManager instance.
        context_manager: The ContextManager instance for managing conversation history.
    """
    logger.debug(f"Initiating interactive AI conversation about model: {model.get('id')} using new AILoop")

    # Create a dummy shutdown event for now, as it's not readily available here
    # In a real application, this should be managed properly.
    shutdown_event = threading.Event()

    # Create OpenRouterAIService instance
    ai_service = OpenRouterAIService(config=ai_config, shutdown_event=shutdown_event)

    # Instantiate the new AILoop
    ai_loop = AILoop(
        config=ai_config,
        ai_service=ai_service,
        context_manager=context_manager,
        delegate_manager=delegate_manager
    )

    await ai_loop.start_session("You are an AI assistant that provides information about AI models and OpenRouter services.")
    await ai_loop.send_user_message(prompt)

    await ai_loop.wait_for_idle()

    logger.debug(f"Interactive AI conversation about model {model.get('id')} finished.")