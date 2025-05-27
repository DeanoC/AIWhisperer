import logging
import uuid
import asyncio
import threading

from ai_whisperer.ai_loop.ai_loopy import AILoop
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.context_management import ContextManager

logger = logging.getLogger(__name__)

class InteractiveAI:
    def __init__(self, model: dict, ai_config: AIConfig, delegate_manager: DelegateManager, context_manager: ContextManager):
        """
        Initializes the InteractiveAI class with the required parameters.

        Args:
            model: The dictionary containing the selected model's information.
            ai_config: The AIConfig instance.
            delegate_manager: The DelegateManager instance.
            context_manager: The ContextManager instance for managing conversation history.
        """
        self.model = model
        self.ai_config = ai_config
        self.delegate_manager = delegate_manager
        self.context_manager = context_manager
        # Use threading.Event for compatibility with OpenRouterAIService
        # but ensure it doesn't block the async event loop
        self.shutdown_event = threading.Event()

    async def start_interactive_ai_session(self, system_prompt: str = "You are an AI assistant that provides information about AI models and OpenRouter services.") -> None:
        """
        Initiates an interactive AI conversation using the new AILoop.
        """

        # Create OpenRouterAIService instance
        ai_service = OpenRouterAIService(config=self.ai_config, shutdown_event=self.shutdown_event)

        # Instantiate the new AILoop
        self.ai_loop = AILoop(
            config=self.ai_config,
            ai_service=ai_service,
            context_manager=self.context_manager,
            delegate_manager=self.delegate_manager        )

        await self.ai_loop.start_session(system_prompt=system_prompt)

    async def send_message(self, message: str) -> None:
        """
        Sends a message to the AI loop and waits for a response.

        Args:
            message: The message to send to the AI loop.
        """
        logger.error(f"[send_message] ENTRY: message={message}")
        if not self.ai_loop:
            raise RuntimeError("AI loop is not initialized. Call start_interactive_ai_session first.")

        # Send the message to the AI loop
        logger.error(f"[send_message] Calling ai_loop.send_user_message")
        await self.ai_loop.send_user_message(message)
        logger.error(f"[send_message] ai_loop.send_user_message completed")

    async def wait_for_idle(self):
        """
        Waits for the AI loop to become idle.
        """
        await self.ai_loop.wait_for_idle()
