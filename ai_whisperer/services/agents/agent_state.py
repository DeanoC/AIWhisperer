"""Agent state management for async multi-agent system."""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


class AgentState(Enum):
    """Possible states for an async agent."""
    
    IDLE = "idle"           # Agent created but not started
    ACTIVE = "active"       # Agent running and processing
    PAUSED = "paused"       # Agent temporarily suspended
    SLEEPING = "sleeping"   # Agent waiting for wake event
    STOPPED = "stopped"     # Agent terminated
    ERROR = "error"         # Agent in error state


@dataclass
class AgentStateInfo:
    """Detailed information about an agent's state."""
    
    agent_id: str
    state: AgentState
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class AgentStateMachine:
    """Manages valid state transitions for agents."""
    
    # Valid state transitions
    TRANSITIONS = {
        AgentState.IDLE: [AgentState.ACTIVE, AgentState.STOPPED],
        AgentState.ACTIVE: [AgentState.PAUSED, AgentState.SLEEPING, AgentState.STOPPED, AgentState.ERROR],
        AgentState.PAUSED: [AgentState.ACTIVE, AgentState.STOPPED],
        AgentState.SLEEPING: [AgentState.ACTIVE, AgentState.STOPPED],
        AgentState.ERROR: [AgentState.STOPPED],
        AgentState.STOPPED: []  # Terminal state
    }
    
    @classmethod
    def can_transition(cls, from_state: AgentState, to_state: AgentState) -> bool:
        """Check if a state transition is valid."""
        return to_state in cls.TRANSITIONS.get(from_state, [])
    
    @classmethod
    def transition(cls, state_info: AgentStateInfo, to_state: AgentState) -> AgentStateInfo:
        """Perform a state transition if valid."""
        if not cls.can_transition(state_info.state, to_state):
            raise ValueError(
                f"Invalid transition from {state_info.state.value} to {to_state.value} "
                f"for agent {state_info.agent_id}"
            )
        
        # Update timestamps based on transition
        now = datetime.now()
        state_info.last_activity = now
        
        if to_state == AgentState.ACTIVE and state_info.state == AgentState.IDLE:
            state_info.started_at = now
        elif to_state == AgentState.PAUSED:
            state_info.paused_at = now
        elif to_state == AgentState.STOPPED:
            state_info.stopped_at = now
        elif to_state == AgentState.ACTIVE and state_info.state == AgentState.PAUSED:
            state_info.paused_at = None
        
        state_info.state = to_state
        return state_info