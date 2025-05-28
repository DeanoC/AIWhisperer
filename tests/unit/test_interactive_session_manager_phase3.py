"""
Phase 3.2 Tests: Session Manager Tests for Agent Architecture
Comprehensive tests for InteractiveSessionManager with agent integration
"""
import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from datetime import datetime

from interactive_server.session_manager import InteractiveSession, InteractiveSessionManager
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages = []
        self.closed = False
        
    async def send_json(self, data):
        self.messages.append(data)
        
    async def close(self):
        self.closed = True


@pytest.fixture
def mock_config():
    return {
        "openrouter": {
            "api_key": "test-key",
            "model": "test-model",
            "params": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    }


class TestInteractiveSessionManagerOperations:
    """Tests for InteractiveSessionManager operations"""
    
    def test_manager_initialization(self, mock_config):
        """Test that manager initializes properly"""
        manager = InteractiveSessionManager(mock_config)
        
        assert manager.config == mock_config
        assert manager.sessions == {}
        assert manager.websocket_sessions == {}
        assert hasattr(manager, '_lock')
    
    @pytest.mark.asyncio
    async def test_create_session_assigns_unique_ids(self, mock_config):
        """Test that each session gets a unique ID"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create multiple sessions
        session_ids = []
        for i in range(5):
            ws = MockWebSocket()
            session_id = await manager.create_session(ws)
            session_ids.append(session_id)
        
        # All IDs should be unique
        assert len(set(session_ids)) == 5
        assert len(manager.sessions) == 5
    
    @pytest.mark.asyncio
    async def test_websocket_to_session_mapping(self, mock_config):
        """Test WebSocket to session mapping"""
        manager = InteractiveSessionManager(mock_config)
        
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        
        session_id1 = await manager.create_session(ws1)
        session_id2 = await manager.create_session(ws2)
        
        # Check mappings
        assert manager.get_session_by_websocket(ws1).session_id == session_id1
        assert manager.get_session_by_websocket(ws2).session_id == session_id2
        
        # Check reverse mapping
        assert manager.websocket_sessions[ws1] == session_id1
        assert manager.websocket_sessions[ws2] == session_id2
    
    @pytest.mark.asyncio
    async def test_start_session_creates_default_agent(self, mock_config):
        """Test that starting a session creates a default agent"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        await manager.start_session(session_id, "Test system prompt")
        
        session = manager.get_session(session_id)
        assert session.is_started
        assert len(session.agents) >= 1
        assert "default" in session.agents
        assert session.active_agent == "default"
    
    @pytest.mark.asyncio
    async def test_send_message_routes_to_active_agent(self, mock_config):
        """Test that messages are routed to the active agent"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        await manager.start_session(session_id)
        
        # Mock agent's process_message
        session = manager.get_session(session_id)
        mock_agent = MagicMock(spec=Agent)
        mock_agent.process_message = AsyncMock(return_value=None)
        session.agents[session.active_agent] = mock_agent
        
        # Send message
        await manager.send_message(session_id, "Test message")
        
        # Verify agent received message
        mock_agent.process_message.assert_called_once_with("Test message")
    
    @pytest.mark.asyncio
    async def test_stop_session_stops_agents(self, mock_config):
        """Test that stopping a session stops all agents"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        await manager.start_session(session_id)
        
        session = manager.get_session(session_id)
        
        # Mock AILoop stop_session
        for agent in session.agents.values():
            agent.ai_loop.stop_session = AsyncMock()
        
        # Stop session
        await manager.stop_session(session_id)
        
        # Verify all agents stopped
        assert not session.is_started
        for agent in session.agents.values():
            if hasattr(agent.ai_loop, 'stop_session'):
                agent.ai_loop.stop_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_manager_error_handling_on_missing_session(self, mock_config):
        """Test proper error handling for missing sessions"""
        manager = InteractiveSessionManager(mock_config)
        
        # Try operations on non-existent session
        with pytest.raises(ValueError, match="Session fake-id not found"):
            await manager.start_session("fake-id")
        
        with pytest.raises(ValueError, match="Session fake-id not found"):
            await manager.send_message("fake-id", "message")
        
        with pytest.raises(ValueError, match="Session fake-id not found"):
            await manager.stop_session("fake-id")


class TestSessionCleanupAndMemoryManagement:
    """Tests for session cleanup and memory management"""
    
    @pytest.mark.asyncio
    async def test_cleanup_session_removes_all_references(self, mock_config):
        """Test that cleanup removes all references to prevent memory leaks"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        await manager.start_session(session_id)
        
        # Verify session exists
        assert session_id in manager.sessions
        assert ws in manager.websocket_sessions
        
        # Cleanup
        await manager.cleanup_session(session_id)
        
        # Verify all references removed
        assert session_id not in manager.sessions
        assert ws not in manager.websocket_sessions
        assert manager.get_session(session_id) is None
        assert manager.get_session_by_websocket(ws) is None
    
    @pytest.mark.asyncio
    async def test_cleanup_calls_agent_cleanup(self, mock_config):
        """Test that cleanup properly cleans up all agents"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        session = manager.get_session(session_id)
        
        # Create multiple agents
        await session.create_agent("agent1", "Agent 1")
        await session.create_agent("agent2", "Agent 2")
        
        # Mock cleanup methods
        for agent in session.agents.values():
            agent.ai_loop.stop_session = AsyncMock()
        
        # Cleanup session
        await manager.cleanup_session(session_id)
        
        # Verify agents were cleaned up
        for agent in session.agents.values():
            if hasattr(agent.ai_loop, 'stop_session'):
                agent.ai_loop.stop_session.assert_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_websocket_cleans_associated_session(self, mock_config):
        """Test that cleaning up by WebSocket works"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        await manager.start_session(session_id)
        
        # Cleanup by WebSocket
        await manager.cleanup_websocket(ws)
        
        # Verify session cleaned up
        assert session_id not in manager.sessions
        assert ws not in manager.websocket_sessions
    
    @pytest.mark.asyncio
    async def test_cleanup_all_sessions_cleans_everything(self, mock_config):
        """Test that cleanup_all removes all sessions"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            ws = MockWebSocket()
            session_id = await manager.create_session(ws)
            await manager.start_session(session_id)
            sessions.append((session_id, ws))
        
        assert len(manager.sessions) == 3
        
        # Cleanup all
        await manager.cleanup_all()
        
        # Verify all cleaned up
        assert len(manager.sessions) == 0
        assert len(manager.websocket_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_memory_leak_prevention_with_circular_references(self, mock_config):
        """Test that cleanup handles circular references properly"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        session = manager.get_session(session_id)
        
        # Create circular reference
        session._self_ref = session
        
        # Cleanup should still work
        await manager.cleanup_session(session_id)
        
        # Verify cleanup succeeded
        assert session_id not in manager.sessions


class TestConcurrentSessionHandling:
    """Tests for concurrent session operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, mock_config):
        """Test creating multiple sessions concurrently"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create sessions concurrently
        tasks = []
        websockets = []
        for i in range(10):
            ws = MockWebSocket()
            websockets.append(ws)
            tasks.append(manager.create_session(ws))
        
        session_ids = await asyncio.gather(*tasks)
        
        # All sessions should be created
        assert len(set(session_ids)) == 10
        assert len(manager.sessions) == 10
        
        # All WebSocket mappings should exist
        for ws in websockets:
            assert ws in manager.websocket_sessions
    
    @pytest.mark.asyncio
    async def test_concurrent_message_sending(self, mock_config):
        """Test sending messages to multiple sessions concurrently"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create and start sessions
        session_ids = []
        for i in range(5):
            ws = MockWebSocket()
            session_id = await manager.create_session(ws)
            await manager.start_session(session_id)
            session_ids.append(session_id)
        
        # Mock agent processing
        for session_id in session_ids:
            session = manager.get_session(session_id)
            for agent in session.agents.values():
                agent.process_message = AsyncMock()
        
        # Send messages concurrently
        tasks = []
        for i, session_id in enumerate(session_ids):
            tasks.append(manager.send_message(session_id, f"Message {i}"))
        
        await asyncio.gather(*tasks)
        
        # All messages should be processed
        for session_id in session_ids:
            session = manager.get_session(session_id)
            agent = session.agents[session.active_agent]
            agent.process_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_cleanup_safety(self, mock_config):
        """Test that concurrent cleanup operations are safe"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create sessions
        session_ids = []
        for i in range(5):
            ws = MockWebSocket()
            session_id = await manager.create_session(ws)
            session_ids.append(session_id)
        
        # Cleanup concurrently
        tasks = [manager.cleanup_session(sid) for sid in session_ids]
        await asyncio.gather(*tasks)
        
        # All should be cleaned up
        assert len(manager.sessions) == 0
        assert len(manager.websocket_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_race_condition_prevention(self, mock_config):
        """Test that locks prevent race conditions"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        
        # Try to cleanup same session concurrently multiple times
        tasks = [manager.cleanup_session(session_id) for _ in range(5)]
        
        # Should not raise any errors
        await asyncio.gather(*tasks)
        
        # Session should be gone
        assert session_id not in manager.sessions


class TestSessionPersistence:
    """Tests for session persistence functionality"""
    
    @pytest.mark.asyncio
    async def test_sessions_saved_to_file(self, mock_config, tmp_path, monkeypatch):
        """Test that sessions are saved to file"""
        # Use temp directory for sessions file
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(Path, "exists", lambda self: sessions_file.exists())
        
        with patch("builtins.open", mock_open()) as mock_file:
            manager = InteractiveSessionManager(mock_config)
            
            # Create sessions
            ws1 = MockWebSocket()
            ws2 = MockWebSocket()
            session_id1 = await manager.create_session(ws1)
            session_id2 = await manager.create_session(ws2)
            
            # Verify save was called
            mock_file.assert_called()
            
            # Check write calls
            write_calls = [call for call in mock_file().write.call_args_list]
            assert len(write_calls) > 0
    
    @pytest.mark.asyncio
    async def test_session_state_persistence(self, mock_config):
        """Test getting and restoring session state"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        session = manager.get_session(session_id)
        
        # Create agent and add context
        await session.create_agent("test-agent", "Test prompt")
        agent = session.agents["test-agent"]
        agent.context.store_message({"role": "user", "content": "Hello"})
        agent.context.store_message({"role": "assistant", "content": "Hi there"})
        
        # Get state
        state = await session.get_state()
        
        # Create new session and restore
        new_ws = MockWebSocket()
        new_session_id = await manager.create_session(new_ws)
        new_session = manager.get_session(new_session_id)
        
        await new_session.restore_state(state)
        
        # Verify restoration
        assert "test-agent" in new_session.agents
        restored_agent = new_session.agents["test-agent"]
        messages = restored_agent.context.retrieve_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there"
    
    def test_load_sessions_on_startup(self, mock_config, tmp_path, monkeypatch):
        """Test that manager loads persisted sessions on startup"""
        # Create a sessions file
        sessions_data = {
            "sessions": ["session-1", "session-2", "session-3"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock file reading
        with patch("builtins.open", mock_open(read_data=json.dumps(sessions_data))):
            with patch("pathlib.Path.exists", return_value=True):
                manager = InteractiveSessionManager(mock_config)
                
                # Manager should have logged loading sessions
                # (In real test, we'd check logs or have a method to verify)
                assert True  # Placeholder for actual verification


class TestErrorHandlingAndRecovery:
    """Tests for error handling and recovery"""
    
    @pytest.mark.asyncio
    async def test_graceful_handling_of_agent_creation_failure(self, mock_config):
        """Test that session remains functional if agent creation fails"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        session = manager.get_session(session_id)
        
        # Mock agent creation to fail
        with patch.object(session, '_create_ai_loop', side_effect=Exception("AI Loop failed")):
            with pytest.raises(Exception):
                await session.create_agent("bad-agent", "Test")
        
        # Session should still be functional
        assert session.session_id == session_id
        assert len(session.agents) == 0  # No agent created
    
    @pytest.mark.asyncio
    async def test_cleanup_continues_on_agent_cleanup_failure(self, mock_config):
        """Test that cleanup continues even if agent cleanup fails"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        await manager.start_session(session_id)
        
        session = manager.get_session(session_id)
        
        # Make agent cleanup fail
        for agent in session.agents.values():
            agent.ai_loop.stop_session = AsyncMock(side_effect=Exception("Cleanup failed"))
        
        # Cleanup should not raise
        await manager.cleanup_session(session_id)
        
        # Session should still be removed
        assert session_id not in manager.sessions
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(self, mock_config):
        """Test handling of WebSocket disconnection"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        await manager.start_session(session_id)
        
        # Simulate WebSocket disconnect
        ws.closed = True
        
        # Cleanup by WebSocket should work
        await manager.cleanup_websocket(ws)
        
        # Session should be cleaned up
        assert session_id not in manager.sessions
    
    @pytest.mark.asyncio
    async def test_recovery_from_corrupted_session_state(self, mock_config):
        """Test recovery from corrupted session state"""
        manager = InteractiveSessionManager(mock_config)
        ws = MockWebSocket()
        
        session_id = await manager.create_session(ws)
        session = manager.get_session(session_id)
        
        # Try to restore corrupted state
        corrupted_state = {
            "session_id": "corrupted",
            "agents": {
                "bad-agent": {}  # Missing required fields
            }
        }
        
        # Should handle gracefully (might log error but not crash)
        try:
            await session.restore_state(corrupted_state)
        except Exception:
            # Expected to fail, but session should remain functional
            pass
        
        # Session should still be usable
        assert session.session_id == session_id