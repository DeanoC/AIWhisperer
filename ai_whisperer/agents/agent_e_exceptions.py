"""
Exception classes for Agent E functionality.
"""


class AgentEException(Exception):
    """Base exception for Agent E errors."""
    pass


class InvalidPlanError(AgentEException):
    """Raised when a plan is invalid or missing required fields."""
    pass


class TaskDecompositionError(AgentEException):
    """Raised when task decomposition fails."""
    pass


class DependencyCycleError(TaskDecompositionError):
    """Raised when circular dependencies are detected in tasks."""
    pass


class ExternalAgentError(AgentEException):
    """Raised when external agent integration fails."""
    pass


class CommunicationError(AgentEException):
    """Raised when agent communication fails."""
    pass