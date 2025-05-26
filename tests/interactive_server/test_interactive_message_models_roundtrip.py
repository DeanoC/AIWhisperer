import sys
import os
import json
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from interactive_server.message_models import (
    StartSessionRequest, StartSessionResponse, SendUserMessageRequest, SendUserMessageResponse,
    AIMessageChunkNotification, SessionStatusNotification, StopSessionRequest, StopSessionResponse,
    ProvideToolResultRequest, ProvideToolResultResponse, SessionParams,
    SessionStatus, MessageStatus, ToolResultStatus
)

def test_start_session_request_roundtrip():
    data = {"userId": "user1", "sessionParams": {"language": "en"}}
    model = StartSessionRequest(**data)
    json_str = model.model_dump_json()
    model2 = StartSessionRequest.model_validate_json(json_str)
    assert model2.userId == "user1"
    assert model2.sessionParams.language == "en"

def test_start_session_response_roundtrip():
    data = {"sessionId": "sess1", "status": SessionStatus.Active}
    model = StartSessionResponse(**data)
    json_str = model.model_dump_json()
    model2 = StartSessionResponse.model_validate_json(json_str)
    assert model2.status == SessionStatus.Active

def test_send_user_message_request_roundtrip():
    data = {"sessionId": "sess1", "message": "hello"}
    model = SendUserMessageRequest(**data)
    json_str = model.model_dump_json()
    model2 = SendUserMessageRequest.model_validate_json(json_str)
    assert model2.message == "hello"

def test_send_user_message_response_roundtrip():
    data = {"messageId": "msg1", "status": MessageStatus.OK}
    model = SendUserMessageResponse(**data)
    json_str = model.model_dump_json()
    model2 = SendUserMessageResponse.model_validate_json(json_str)
    assert model2.status == MessageStatus.OK

def test_ai_message_chunk_notification_roundtrip():
    data = {"sessionId": "sess1", "chunk": "hi", "isFinal": False}
    model = AIMessageChunkNotification(**data)
    json_str = model.model_dump_json()
    model2 = AIMessageChunkNotification.model_validate_json(json_str)
    assert model2.chunk == "hi"
    assert model2.isFinal is False

def test_session_status_notification_roundtrip():
    data = {"sessionId": "sess1", "status": SessionStatus.Stopped, "reason": "done"}
    model = SessionStatusNotification(**data)
    json_str = model.model_dump_json()
    model2 = SessionStatusNotification.model_validate_json(json_str)
    assert model2.status == SessionStatus.Stopped
    assert model2.reason == "done"

def test_stop_session_request_roundtrip():
    data = {"sessionId": "sess1"}
    model = StopSessionRequest(**data)
    json_str = model.model_dump_json()
    model2 = StopSessionRequest.model_validate_json(json_str)
    assert model2.sessionId == "sess1"

def test_stop_session_response_roundtrip():
    data = {"status": SessionStatus.Stopped}
    model = StopSessionResponse(**data)
    json_str = model.model_dump_json()
    model2 = StopSessionResponse.model_validate_json(json_str)
    assert model2.status == SessionStatus.Stopped

def test_provide_tool_result_request_roundtrip():
    data = {"sessionId": "sess1", "toolCallId": "tool1", "result": "42"}
    model = ProvideToolResultRequest(**data)
    json_str = model.model_dump_json()
    model2 = ProvideToolResultRequest.model_validate_json(json_str)
    assert model2.result == "42"

def test_provide_tool_result_response_roundtrip():
    data = {"status": ToolResultStatus.OK}
    model = ProvideToolResultResponse(**data)
    json_str = model.model_dump_json()
    model2 = ProvideToolResultResponse.model_validate_json(json_str)
    assert model2.status == ToolResultStatus.OK
