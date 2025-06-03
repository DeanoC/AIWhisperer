"""
Module: ai_whisperer/extensions/agents/agent_e_exceptions.py
Purpose: Exception definitions for Agent E (Eamonn) functionality

This module contains all custom exceptions used by Agent E for
plan decomposition and task execution.

Exception Hierarchy:
- AgentEError (base)
  - InvalidPlanError
  - TaskDecompositionError
  - DependencyCycleError
"""

class AgentEError(Exception):
    """Base exception for Agent E operations."""
    pass


class InvalidPlanError(AgentEError):
    """Raised when a plan structure is invalid or missing required fields."""
    pass


class TaskDecompositionError(AgentEError):
    """Raised when task decomposition fails."""
    pass


class DependencyCycleError(AgentEError):
    """Raised when circular dependencies are detected in tasks."""
    pass


class ExternalAgentError(AgentEError):
    """Raised when external agent operations fail."""
    pass