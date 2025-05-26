import pytest

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from interactive_server.message_models import (
    StartSessionRequest, StartSessionResponse, SendUserMessageRequest, SendUserMessageResponse,
    AIMessageChunkNotification, SessionStatusNotification, StopSessionRequest, StopSessionResponse,
    ProvideToolResultRequest, ProvideToolResultResponse, SessionParams,
    SessionStatus, MessageStatus, ToolResultStatus
)

def test_start_session_request():
    req = StartSessionRequest(userId="user1", sessionParams=SessionParams(language="en"))
    assert req.userId == "user1"
    assert req.sessionParams.language == "en"

def test_start_session_response():
    resp = StartSessionResponse(sessionId="sess1", status=SessionStatus.Active)
    assert resp.status == SessionStatus.Active

def test_send_user_message_request():
    req = SendUserMessageRequest(sessionId="sess1", message="hello")
    assert req.message == "hello"

def test_send_user_message_response():
    resp = SendUserMessageResponse(messageId="msg1", status=MessageStatus.OK)
    assert resp.status == MessageStatus.OK

def test_ai_message_chunk_notification():
    note = AIMessageChunkNotification(sessionId="sess1", chunk="hi", isFinal=False)
    assert note.chunk == "hi"
    assert note.isFinal is False

def test_session_status_notification():
    note = SessionStatusNotification(sessionId="sess1", status=SessionStatus.Stopped, reason="done")
    assert note.status == SessionStatus.Stopped
    assert note.reason == "done"

def test_stop_session_request():
    req = StopSessionRequest(sessionId="sess1")
    assert req.sessionId == "sess1"

def test_stop_session_response():
    resp = StopSessionResponse(status=SessionStatus.Stopped)
    assert resp.status == SessionStatus.Stopped

def test_provide_tool_result_request():
    req = ProvideToolResultRequest(sessionId="sess1", toolCallId="tool1", result="42")
    assert req.result == "42"

def test_provide_tool_result_response():
    resp = ProvideToolResultResponse(status=ToolResultStatus.OK)
    assert resp.status == ToolResultStatus.OK
