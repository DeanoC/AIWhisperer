"""
Module: ai_whisperer/agents/__init__.py
Purpose: Package initialization for agents

This module implements an AI agent that processes user messages
and executes specialized tasks. It integrates with the tool system
and manages conversation context.

Dependencies:
- config
- stateless_agent
- factory

Related:
- See UNTESTED_MODULES_REPORT.md

"""

# Agent system initialization
from .registry import Agent, AgentRegistry
from .stateless_agent import StatelessAgent
from .config import AgentConfig
from .factory import AgentFactory

__all__ = ['Agent', 'AgentRegistry', 'StatelessAgent', 'AgentConfig', 'AgentFactory']