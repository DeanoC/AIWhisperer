import pytest
import asyncio
from types import SimpleNamespace
from interactive_server.delegate_bridge import DelegateBridge
from interactive_server.message_models import (
    AIMessageChunkNotification,
    SessionStatusNotification,
    ToolCallNotification,
    SessionStatus
)

class DummySession:
    def __init__(self):
        self.sent = []
        self.session_id = "test-session"
        self.delegate_manager = SimpleNamespace()
        self.delegate_manager._handlers = {}
        def register_notification(event, handler):
            self.delegate_manager._handlers[event] = handler
        def unregister_notification(event, handler):
            self.delegate_manager._handlers.pop(event, None)
        self.delegate_manager.register_notification = register_notification
        self.delegate_manager.unregister_notification = unregister_notification
    async def send_notification(self, method, notification_data):
        self.sent.append((method, notification_data))

@pytest.mark.asyncio
async def test_session_started_notification():
    session = DummySession()
    bridge = DelegateBridge(session)
    await bridge._handle_session_started(sender=None, event_data=None)
    assert session.sent
    method, notif = session.sent[-1]
    assert method == "SessionStatusNotification"
    assert notif.status == SessionStatus.Active
    assert "started" in notif.reason

@pytest.mark.asyncio
async def test_session_ended_notification():
    session = DummySession()
    bridge = DelegateBridge(session)
    await bridge._handle_session_ended(sender=None, event_data="stopped")
    method, notif = session.sent[-1]
    assert method == "SessionStatusNotification"
    assert notif.status == SessionStatus.Stopped
    assert "ended" in notif.reason

@pytest.mark.asyncio
async def test_ai_chunk_notification():
    session = DummySession()
    bridge = DelegateBridge(session)
    await bridge._handle_ai_chunk_received(sender=None, event_data="chunky")
    method, notif = session.sent[-1]
    assert method == "AIMessageChunkNotification"
    assert notif.chunk == "chunky"
    assert not notif.isFinal

@pytest.mark.asyncio
async def test_tool_call_notification():
    session = DummySession()
    bridge = DelegateBridge(session)
    await bridge._handle_tool_call_identified(sender=None, event_data=["tool1"])
    method, notif = session.sent[-1]
    assert method == "ToolCallNotification"
    assert notif.toolName == "tool1"

@pytest.mark.asyncio
async def test_error_notification():
    session = DummySession()
    bridge = DelegateBridge(session)
    await bridge._handle_error(sender=None, event_data="fail")
    method, notif = session.sent[-1]
    assert method == "SessionStatusNotification"
    assert notif.status == SessionStatus.Error
    assert "fail" in notif.reason

@pytest.mark.asyncio
async def test_cleanup_unregisters_handlers():
    session = DummySession()
    bridge = DelegateBridge(session)
    await bridge.cleanup()
    # All handlers should be unregistered
    assert not session.delegate_manager._handlers
