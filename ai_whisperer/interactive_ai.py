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
    engine: ExecutionEngine,
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

    # Create AIConfig from the main config
    # Map relevant config values to AIConfig arguments
    ai_loop_config = AIConfig(
        api_key=engine.config.get('openrouter', {}).get('api_key', ''), # Assuming API key is here
        model_id=model.get('id'), # Use the selected model's ID
        temperature=engine.config.get('openrouter', {}).get('params', {}).get('temperature', 0.7), # Assuming temperature is here
        max_tokens=engine.config.get('openrouter', {}).get('params', {}).get('max_tokens', None), # Assuming max_tokens is here
        # Pass other relevant config as kwargs if needed by AIConfig
        **engine.config.get('ai_loop_params', {}) # Assuming other AI loop params might be here
    )

    # Create a dummy shutdown event for now, as it's not readily available here
    # In a real application, this should be managed properly.
    shutdown_event = threading.Event()

    # Create OpenRouterAIService instance
    ai_service = OpenRouterAIService(config=ai_loop_config, shutdown_event=shutdown_event)

    # Instantiate the new AILoop
    ai_loop = AILoop(
        config=ai_loop_config,
        ai_service=ai_service,
        context_manager=context_manager,
        delegate_manager=delegate_manager
    )

    await ai_loop.start_session("You are an AI assistant that provides information about AI models and OpenRouter services.")
    await ai_loop.send_user_message(f"Tell me about this model {model.get('id')}")

    await ai_loop.wait_for_idle()

    logger.debug(f"Interactive AI conversation about model {model.get('id')} finished.")