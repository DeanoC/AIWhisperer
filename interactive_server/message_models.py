

from pydantic import BaseModel, Field
from typing import Optional, Dict

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
