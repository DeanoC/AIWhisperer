"""
Module: ai_whisperer/agents/session_manager.py
Purpose: AI agent implementation for specialized task handling

This module implements an AI agent that processes user messages
and executes specialized tasks. It integrates with the tool system
and manages conversation context.

Key Components:
- AgentSession: Manages a chat session with agent switching capabilities

Usage:
    agentsession = AgentSession()
    result = agentsession.switch_agent()

Dependencies:
- base_handler

"""

from typing import Dict, List, Optional, Any
from ai_whisperer.services.agents.registry import Agent, AgentRegistry
from ai_whisperer.services.agents.base import BaseAgentHandler

class AgentSession:
    """Manages a chat session with agent switching capabilities"""
    def __init__(self, registry: AgentRegistry, engine: Any):
        self.registry = registry
        self.engine = engine
        self.current_agent: Optional[Agent] = None
        self.agent_handlers: Dict[str, BaseAgentHandler] = {}
        self.conversation_history: List[Dict] = []
        self.agent_contexts: Dict[str, List[Dict]] = {}  # Per-agent conversation history

    def switch_agent(self, agent_id: str) -> bool:
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return False
        if self.current_agent:
            self.agent_contexts[self.current_agent.agent_id] = self.conversation_history.copy()
        self.current_agent = agent
        if agent_id in self.agent_contexts:
            self.conversation_history = self.agent_contexts[agent_id]
        else:
            self.conversation_history = []
        if agent_id not in self.agent_handlers:
            self.agent_handlers[agent_id] = self._create_handler(agent)
        return True

    def _create_handler(self, agent: Agent) -> BaseAgentHandler:
        # Dummy handler for now
        class DummyHandler(BaseAgentHandler):
            async def handle_message(self, message, conversation_history):
                return {"response": "ok"}
            def can_handoff(self, conversation_history):
                return None
        return DummyHandler(agent, self.engine)
