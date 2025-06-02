"""
Module: ai_whisperer/agents/base_handler.py
Purpose: Handler implementation for base

This module implements an AI agent that processes user messages
and executes specialized tasks. It integrates with the tool system
and manages conversation context.

Key Components:
- BaseAgentHandler: Base class for all agent handlers

Usage:
    baseagenthandler = BaseAgentHandler()
    result = baseagenthandler.handle_message()

Dependencies:
- abc

Related:
- See UNTESTED_MODULES_REPORT.md
- See TEST_CONSOLIDATED_SUMMARY.md

"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ai_whisperer.services.agents.registry import Agent

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
