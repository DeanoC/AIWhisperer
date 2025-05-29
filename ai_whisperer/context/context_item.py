"""Context item model for tracking files and content in agent context."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal, Dict, Any, Tuple
import hashlib
import uuid


@dataclass
class ContextItem:
    """Represents a single item in agent context.
    
    This tracks files, file sections, or other content that an agent
    is aware of during a conversation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    agent_id: str = ""
    type: Literal["file", "file_section", "directory_summary", "reference"] = "file"
    path: str = ""
    content: str = ""
    line_range: Optional[Tuple[int, int]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    file_modified_time: Optional[datetime] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_hash(self) -> str:
        """Calculate content hash for change detection."""
        if not self.content:
            return ""
        return hashlib.sha256(self.content.encode()).hexdigest()
    
    def is_stale(self, current_modified_time: Optional[datetime] = None) -> bool:
        """Check if context item is stale based on file modification time.
        
        Args:
            current_modified_time: Current modification time of the file
            
        Returns:
            True if the item is stale, False otherwise
        """
        if not current_modified_time or not self.file_modified_time:
            return False
        return current_modified_time > self.file_modified_time
    
    def get_age_seconds(self) -> float:
        """Get age of context item in seconds."""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "type": self.type,
            "path": self.path,
            "content": self.content,
            "line_range": self.line_range,
            "timestamp": self.timestamp.isoformat(),
            "file_modified_time": self.file_modified_time.isoformat() if self.file_modified_time else None,
            "content_hash": self.content_hash,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextItem":
        """Create from dictionary."""
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            session_id=data.get("session_id", ""),
            agent_id=data.get("agent_id", ""),
            type=data.get("type", "file"),
            path=data.get("path", ""),
            content=data.get("content", ""),
            line_range=data.get("line_range"),
            metadata=data.get("metadata", {})
        )
        
        # Parse timestamps
        if data.get("timestamp"):
            item.timestamp = datetime.fromisoformat(data["timestamp"])
        if data.get("file_modified_time"):
            item.file_modified_time = datetime.fromisoformat(data["file_modified_time"])
            
        item.content_hash = data.get("content_hash")
        
        return item