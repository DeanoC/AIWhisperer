"""
Channel type definitions for the Response Channels system.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class ChannelType(Enum):
    """Types of response channels."""
    
    ANALYSIS = "analysis"      # Private AI reasoning, never shown to users
    COMMENTARY = "commentary"  # Tool calls and structured data only
    FINAL = "final"           # Clean user-facing responses
    
    @classmethod
    def from_string(cls, value: str) -> Optional['ChannelType']:
        """Convert string to ChannelType, returns None if invalid."""
        try:
            return cls(value.lower())
        except ValueError:
            return None
    
    def is_user_visible(self) -> bool:
        """Check if this channel should be visible to users by default."""
        return self in (ChannelType.FINAL, ChannelType.COMMENTARY)
    
    def requires_formatting(self) -> bool:
        """Check if this channel requires special formatting."""
        return self == ChannelType.COMMENTARY


@dataclass
class ChannelMetadata:
    """Metadata associated with a channel message."""
    
    sequence: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_calls: Optional[list] = None
    continuation_depth: Optional[int] = None
    is_partial: bool = False
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        result = {
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "is_partial": self.is_partial
        }
        
        if self.agent_id:
            result["agent_id"] = self.agent_id
        if self.session_id:
            result["session_id"] = self.session_id
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.continuation_depth is not None:
            result["continuation_depth"] = self.continuation_depth
        if self.custom:
            result.update(self.custom)
            
        return result


@dataclass
class ChannelMessage:
    """A message routed to a specific channel."""
    
    channel: ChannelType
    content: str
    metadata: ChannelMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "channel": self.channel.value,
            "content": self.content,
            "metadata": self.metadata.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChannelMessage':
        """Create ChannelMessage from dictionary."""
        channel = ChannelType(data["channel"])
        content = data["content"]
        
        # Reconstruct metadata
        meta_dict = data["metadata"]
        metadata = ChannelMetadata(
            sequence=meta_dict["sequence"],
            timestamp=datetime.fromisoformat(meta_dict["timestamp"]),
            agent_id=meta_dict.get("agent_id"),
            session_id=meta_dict.get("session_id"),
            tool_calls=meta_dict.get("tool_calls"),
            continuation_depth=meta_dict.get("continuation_depth"),
            is_partial=meta_dict.get("is_partial", False),
            custom={k: v for k, v in meta_dict.items() 
                   if k not in ["sequence", "timestamp", "agent_id", 
                               "session_id", "tool_calls", "continuation_depth", 
                               "is_partial"]}
        )
        
        return cls(channel=channel, content=content, metadata=metadata)