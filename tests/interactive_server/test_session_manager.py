import pytest
from fastapi import WebSocket
from interactive_server.session_manager import InteractiveSessionManager, InteractiveSession

class DummyWebSocket:
    def __init__(self):
        self.sent = []
    async def send_text(self, text):
        self.sent.append(text)

@pytest.fixture
def dummy_config():
    return {
        'openrouter': {'api_key': 'test-key', 'model': 'openai/gpt-3.5-turbo'},
        'ai_loop': {'temperature': 0.7, 'max_tokens': 1000}
    }

@pytest.mark.asyncio
async def test_create_and_cleanup_session(dummy_config):
    manager = InteractiveSessionManager(dummy_config)
    ws = DummyWebSocket()
    session_id = await manager.create_session(ws)
    assert session_id in manager.sessions
    session = manager.get_session(session_id)
    assert session is not None
    assert session.websocket is ws
    await manager.cleanup_session(session_id)
    assert session_id not in manager.sessions

@pytest.mark.asyncio
async def test_websocket_session_mapping(dummy_config):
    manager = InteractiveSessionManager(dummy_config)
    ws = DummyWebSocket()
    session_id = await manager.create_session(ws)
    assert manager.get_session_by_websocket(ws) is not None
    await manager.cleanup_websocket(ws)
    assert manager.get_session_by_websocket(ws) is None

@pytest.mark.asyncio
async def test_start_and_stop_ai_session(dummy_config):
    manager = InteractiveSessionManager(dummy_config)
    ws = DummyWebSocket()
    session_id = await manager.create_session(ws)
    session = manager.get_session(session_id)
    # Should be able to start and stop session (will raise if fails)
    await session.start_ai_session(system_prompt="Test prompt")
    assert session.is_started
    await session.stop_ai_session()
    assert not session.is_started
    await manager.cleanup_session(session_id)

@pytest.mark.asyncio
async def test_send_user_message_requires_started(dummy_config):
    manager = InteractiveSessionManager(dummy_config)
    ws = DummyWebSocket()
    session_id = await manager.create_session(ws)
    session = manager.get_session(session_id)
    with pytest.raises(RuntimeError):
        await session.send_user_message("hi")
    await manager.cleanup_session(session_id)

@pytest.mark.asyncio
async def test_cleanup_all_sessions(dummy_config):
    manager = InteractiveSessionManager(dummy_config)
    ws1 = DummyWebSocket()
    ws2 = DummyWebSocket()
    id1 = await manager.create_session(ws1)
    id2 = await manager.create_session(ws2)
    assert manager.get_active_sessions_count() == 2
    await manager.cleanup_all_sessions()
    assert manager.get_active_sessions_count() == 0
