"""
Agent Communication Protocol for inter-agent messaging.
Defines message types and data structures for Agent E <-> Agent P communication.
"""
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class MessageType(Enum):
    """Types of messages agents can exchange."""
    CLARIFICATION_REQUEST = "clarification_request"
    CLARIFICATION_RESPONSE = "clarification_response"
    PLAN_REFINEMENT_REQUEST = "plan_refinement_request"
    PLAN_REFINEMENT_RESPONSE = "plan_refinement_response"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"


@dataclass
class AgentMessage:
    """Base message structure for agent communication."""
    from_agent: str
    to_agent: str
    message_type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'message_id': self.message_id,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'message_type': self.message_type.value,
            'timestamp': self.timestamp.isoformat(),
            'payload': self.payload,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(
            message_id=data.get('message_id', str(uuid.uuid4())),
            from_agent=data['from_agent'],
            to_agent=data['to_agent'],
            message_type=MessageType(data['message_type']),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(timezone.utc),
            payload=data.get('payload', {}),
            context=data.get('context', {})
        )


@dataclass
class ClarificationRequest:
    """Request for clarification on a specific aspect of a task."""
    task_id: str
    task_name: str
    question: str
    context: Dict[str, Any]
    options: List[str] = field(default_factory=list)
    
    def to_message(self, from_agent: str, to_agent: str, message_id: str) -> AgentMessage:
        """Convert to agent message."""
        return AgentMessage(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.CLARIFICATION_REQUEST,
            payload={
                'task_id': self.task_id,
                'task_name': self.task_name,
                'question': self.question,
                'context': self.context,
                'options': self.options
            }
        )


@dataclass
class ClarificationResponse:
    """Response to a clarification request."""
    request_id: str
    answer: str
    additional_context: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_message(self, sender: str, recipient: str, message_id: str) -> AgentMessage:
        """Convert to agent message."""
        return AgentMessage(
            message_id=message_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.CLARIFICATION_RESPONSE,
            content={
                'request_id': self.request_id,
                'answer': self.answer,
                'additional_context': self.additional_context,
                'confidence': self.confidence
            }
        )


@dataclass
class PlanRefinementRequest:
    """Request to refine part of a plan based on decomposition insights."""
    task_id: str
    task_name: str
    issue_description: str
    suggested_refinements: List[Dict[str, Any]]
    decomposition_insights: Dict[str, Any]
    
    def to_message(self, from_agent: str, to_agent: str, message_id: str) -> AgentMessage:
        """Convert to agent message."""
        return AgentMessage(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.PLAN_REFINEMENT_REQUEST,
            payload={
                'task_id': self.task_id,
                'task_name': self.task_name,
                'issue_description': self.issue_description,
                'suggested_refinements': self.suggested_refinements,
                'decomposition_insights': self.decomposition_insights
            }
        )


@dataclass
class PlanRefinementResponse:
    """Response to plan refinement request."""
    request_id: str
    approved: bool
    refined_plan: Optional[Dict[str, Any]] = None
    reasoning: str = ""
    
    def to_message(self, sender: str, recipient: str, message_id: str) -> AgentMessage:
        """Convert to agent message."""
        return AgentMessage(
            message_id=message_id,
            sender=sender,
            recipient=recipient,
            message_type=MessageType.PLAN_REFINEMENT_RESPONSE,
            content={
                'request_id': self.request_id,
                'approved': self.approved,
                'refined_plan': self.refined_plan,
                'reasoning': self.reasoning
            }
        )