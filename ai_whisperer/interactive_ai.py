import logging
import uuid # Import uuid for task_id
import asyncio # Import asyncio

from ai_whisperer.ai_loop import run_ai_loop
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.context_management import ContextManager # Import ContextManager

logger = logging.getLogger(__name__)

async def ask_ai_about_model_interactive( # Make the function async
    model: dict,
    prompt: str,
    engine: ExecutionEngine,
    delegate_manager: DelegateManager,
    context_manager: ContextManager # Add context_manager parameter
):
    """
    Initiates an interactive AI conversation about a specific model.

    Args:
        model: The dictionary containing the selected model's information.
        prompt: The initial prompt for the AI.
        engine: The ExecutionEngine instance.
        delegate_manager: The DelegateManager instance.
        context_manager: The ContextManager instance for managing conversation history.
    """
    logger.debug(f"Initiating interactive AI conversation about model: {model.get('id')}")

    # Create a dummy task definition and task ID for the ai_loop
    task_id = str(uuid.uuid4())
    task_definition = {
        "task_id": task_id,
        "task_description": f"Ask AI about model: {model.get('id')}",
        "steps": [] # No specific steps for this interactive task
    }

    # Set the model in the engine's config for this interaction
    original_model = engine.config.get('model')
    original_openrouter_model = engine.config.get('openrouter', {}).get('model')

    # Temporarily override the model in the engine's config
    if 'openrouter' not in engine.config:
        engine.config['openrouter'] = {}
    engine.config['openrouter']['model'] = model.get('id')
    engine.config['model'] = model.get('id') # Also set the general 'model' key for compatibility

    try:
        # Run the AI loop with the specific model and prompt
        await asyncio.to_thread( # Run in a separate thread
            run_ai_loop,
            engine=engine,
            task_definition=task_definition,
            task_id=task_id,
            initial_prompt=prompt,
            logger=logger,
            context_manager=context_manager, # Pass the context_manager
            delegate_manager=delegate_manager
        )
    finally:
        # Restore the original model in the engine's config
        if original_openrouter_model is not None:
            engine.config['openrouter']['model'] = original_openrouter_model
        elif 'openrouter' in engine.config:
             del engine.config['openrouter']['model']

        if original_model is not None:
             engine.config['model'] = original_model
        elif 'model' in engine.config:
             del engine.config['model']

        # Clear the context manager history after the interactive session
        context_manager.clear_history()

    logger.debug(f"Interactive AI conversation about model {model.get('id')} finished.")