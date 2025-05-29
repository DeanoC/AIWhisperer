from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .registry import Agent

class BaseAgentHandler(ABC):
    """Base class for all agent handlers"""
    def __init__(self, agent: Agent, engine: Any):
        self.agent = agent
        self.engine = engine
        self.context_manager = None  # Not used in dummy

    @abstractmethod
    async def handle_message(self, message: str, conversation_history: list[Dict]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def can_handoff(self, conversation_history: list[Dict]) -> Optional[str]:
        pass
