

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal, Any
from datetime import datetime

# ToolCallNotification model for tool call events
class ToolCallNotification(BaseModel):
    sessionId: str
    toolCallId: str
    toolName: str
    arguments: Dict[str, str] = Field(default_factory=dict)

class SessionParams(BaseModel):
    language: Optional[str] = None
    model: Optional[str] = None
    context: Optional[str] = None

class StartSessionRequest(BaseModel):
    userId: str
    sessionParams: Optional[SessionParams] = None

class StartSessionResponse(BaseModel):
    sessionId: str
    status: int  # Should be SessionStatus enum

class SendUserMessageRequest(BaseModel):
    sessionId: str
    message: str

class SendUserMessageResponse(BaseModel):
    messageId: str
    status: int  # Should be MessageStatus enum

class AIMessageChunkNotification(BaseModel):
    sessionId: str
    chunk: str
    isFinal: bool

class SessionStatusNotification(BaseModel):
    sessionId: str
    status: int  # Should be SessionStatus enum
    reason: Optional[str] = None

class StopSessionRequest(BaseModel):
    sessionId: str

class StopSessionResponse(BaseModel):
    status: int  # Should be SessionStatus enum

class ProvideToolResultRequest(BaseModel):
    sessionId: str
    toolCallId: str
    result: str

class ProvideToolResultResponse(BaseModel):
    status: int  # Should be ToolResultStatus enum

class ContinuationProgressNotification(BaseModel):
    sessionId: str
    agent_id: str
    iteration: int
    max_iterations: int
    progress: Optional[Dict] = None
    current_tools: Optional[list] = None
    timestamp: Optional[str] = None

# Enums as Python Enums for type safety
from enum import IntEnum
class SessionStatus(IntEnum):
    Starting = 0
    Active = 1
    Stopped = 2
    Error = 3

class MessageStatus(IntEnum):
    OK = 0
    Error = 1

class ToolResultStatus(IntEnum):
    OK = 0
    Error = 1

# Old test/demo models
class EchoParams(BaseModel):
    message: str

class AddParams(BaseModel):
    a: int
    b: int

# Channel Message Models
class ChannelMetadata(BaseModel):
    """Metadata for channel messages."""
    sequence: int
    timestamp: str  # ISO format
    agentId: Optional[str] = None
    sessionId: Optional[str] = None
    toolCalls: Optional[List[str]] = None
    continuationDepth: Optional[int] = None
    isPartial: bool = False
    custom: Dict[str, Any] = Field(default_factory=dict)

class ChannelMessageNotification(BaseModel):
    """Notification for channel-routed messages."""
    type: Literal["channel_message"] = "channel_message"
    channel: Literal["analysis", "commentary", "final"]
    content: str
    metadata: ChannelMetadata
    
class ChannelVisibilityUpdate(BaseModel):
    """Update channel visibility preferences."""
    sessionId: str
    showCommentary: bool
    showAnalysis: bool = False  # Default to hidden
    
class ChannelHistoryRequest(BaseModel):
    """Request channel message history."""
    sessionId: str
    channels: Optional[List[Literal["analysis", "commentary", "final"]]] = None
    limit: Optional[int] = None
    sinceSequence: Optional[int] = None
    
class ChannelHistoryResponse(BaseModel):
    """Response with channel message history."""
    messages: List[ChannelMessageNotification]
    totalCount: int
