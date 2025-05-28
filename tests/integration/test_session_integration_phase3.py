"""
Phase 3.4: Session Integration Testing
End-to-end tests for complete session workflows with the new Agent architecture
"""
import asyncio
import json
import pytest
import websockets
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import tempfile
import os

from interactive_server.session_manager import InteractiveSession, InteractiveSessionManager
from interactive_server.main import app, session_manager as global_session_manager
from interactive_server.message_models import SessionStatus, MessageStatus
from interactive_server.delegate_bridge import DelegateBridge
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.ai_loop.ai_loopy import AILoop
from ai_whisperer.delegate_manager import DelegateManager


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


def create_mock_websocket():
    """Create a mock WebSocket that tracks messages"""
    ws = MagicMock()
    ws.messages = []
    ws.closed = False
    
    async def send_json(data):
        ws.messages.append(data)
    
    async def send_text(text):
        ws.messages.append(json.loads(text))
    
    async def close():
        ws.closed = True
    
    ws.send_json = AsyncMock(side_effect=send_json)
    ws.send_text = AsyncMock(side_effect=send_text)
    ws.close = AsyncMock(side_effect=close)
    ws.accept = AsyncMock()
    
    return ws


@pytest.fixture
def mock_websocket():
    """Fixture that returns a mock WebSocket"""
    return create_mock_websocket()


class TestEndToEndSessionWorkflows:
    """Test complete session workflows from start to finish"""
    
    @pytest.mark.asyncio
    async def test_complete_session_lifecycle(self, mock_config, mock_websocket):
        """Test a complete session from creation to cleanup"""
        manager = InteractiveSessionManager(mock_config)
        
        # 1. Create session
        session_id = await manager.create_session(mock_websocket)
        assert session_id is not None
        assert manager.get_session(session_id) is not None
        
        # 2. Start session (creates default agent)
        await manager.start_session(session_id, "You are a helpful assistant")
        session = manager.get_session(session_id)
        assert session.is_started
        assert len(session.agents) == 1
        assert "default" in session.agents
        
        # 3. Send messages
        # Mock the agent's process_message
        default_agent = session.agents["default"]
        default_agent.process_message = AsyncMock()
        
        await manager.send_message(session_id, "Hello, AI!")
        default_agent.process_message.assert_called_once_with("Hello, AI!")
        
        # 4. Stop session
        await manager.stop_session(session_id)
        assert not session.is_started
        
        # 5. Cleanup
        await manager.cleanup_session(session_id)
        assert manager.get_session(session_id) is None
    
    @pytest.mark.asyncio
    async def test_websocket_message_flow(self, mock_config, mock_websocket):
        """Test the complete flow through WebSocket messages"""
        from interactive_server.main import handle_websocket_message
        
        # Patch the global session manager
        with patch("interactive_server.main.session_manager", InteractiveSessionManager(mock_config)) as manager:
            # 1. Start session request
            start_msg = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "startSession",
                "params": {
                    "userId": "test-user",
                    "sessionParams": {"context": "Test context"}
                }
            })
            
            response = await handle_websocket_message(mock_websocket, start_msg)
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response
            session_id = response["result"]["sessionId"]
            
            # 2. Send message
            send_msg = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "sendUserMessage",
                "params": {
                    "sessionId": session_id,
                    "message": "Hello from WebSocket"
                }
            })
            
            # Mock the session's send_user_message
            session = manager.get_session(session_id)
            session.send_user_message = AsyncMock()
            
            response = await handle_websocket_message(mock_websocket, send_msg)
            assert response["id"] == 2
            assert "result" in response
            session.send_user_message.assert_called_once_with("Hello from WebSocket")
            
            # 3. Stop session
            stop_msg = json.dumps({
                "jsonrpc": "2.0",
                "id": 3,
                "method": "stopSession",
                "params": {"sessionId": session_id}
            })
            
            response = await handle_websocket_message(mock_websocket, stop_msg)
            assert response["id"] == 3
            assert response["result"]["status"] == SessionStatus.Stopped
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, mock_config, mock_websocket):
        """Test that sessions can recover from errors"""
        manager = InteractiveSessionManager(mock_config)
        
        session_id = await manager.create_session(mock_websocket)
        await manager.start_session(session_id)
        
        session = manager.get_session(session_id)
        
        # Simulate an error during message processing
        session.agents["default"].process_message = AsyncMock(
            side_effect=Exception("Processing failed")
        )
        
        # Should handle error gracefully
        with pytest.raises(Exception):
            await manager.send_message(session_id, "This will fail")
        
        # Session should still be functional
        assert session.is_started
        
        # Should be able to send another message
        session.agents["default"].process_message = AsyncMock()
        await manager.send_message(session_id, "This should work")
        session.agents["default"].process_message.assert_called_once()


class TestMultiAgentConversations:
    """Test multi-agent conversation scenarios"""
    
    @pytest.mark.asyncio
    async def test_agent_switching_workflow(self, mock_config, mock_websocket):
        """Test switching between agents in a conversation"""
        manager = InteractiveSessionManager(mock_config)
        
        session_id = await manager.create_session(mock_websocket)
        session = manager.get_session(session_id)
        
        # Create multiple agents
        await session.create_agent("planner", "You are a planning agent")
        await session.create_agent("coder", "You are a coding agent")
        await session.create_agent("reviewer", "You are a review agent")
        
        # Mock agent processing
        for agent_id in ["planner", "coder", "reviewer"]:
            session.agents[agent_id].process_message = AsyncMock()
        
        # Switch to planner
        await session.switch_agent("planner")
        assert session.active_agent == "planner"
        
        # Send message to planner
        await session.send_user_message("Create a plan")
        session.agents["planner"].process_message.assert_called_once_with("Create a plan")
        
        # Switch to coder
        await session.switch_agent("coder")
        assert session.active_agent == "coder"
        
        # Send message to coder
        await session.send_user_message("Implement the plan")
        session.agents["coder"].process_message.assert_called_once_with("Implement the plan")
        
        # Switch to reviewer
        await session.switch_agent("reviewer")
        assert session.active_agent == "reviewer"
        
        # Send message to reviewer
        await session.send_user_message("Review the code")
        session.agents["reviewer"].process_message.assert_called_once_with("Review the code")
    
    @pytest.mark.asyncio
    async def test_agent_context_isolation(self, mock_config, mock_websocket):
        """Test that agent contexts are properly isolated"""
        manager = InteractiveSessionManager(mock_config)
        
        session_id = await manager.create_session(mock_websocket)
        session = manager.get_session(session_id)
        
        # Create two agents
        await session.create_agent("agent1", "Agent 1 prompt")
        await session.create_agent("agent2", "Agent 2 prompt")
        
        # Add messages to agent1's context
        agent1 = session.agents["agent1"]
        agent1.context.store_message({"role": "user", "content": "Message for agent1"})
        agent1.context.store_message({"role": "assistant", "content": "Response from agent1"})
        
        # Add messages to agent2's context
        agent2 = session.agents["agent2"]
        agent2.context.store_message({"role": "user", "content": "Message for agent2"})
        agent2.context.store_message({"role": "assistant", "content": "Response from agent2"})
        
        # Verify contexts are isolated
        agent1_messages = agent1.context.retrieve_messages()
        agent2_messages = agent2.context.retrieve_messages()
        
        assert len(agent1_messages) == 2
        assert len(agent2_messages) == 2
        assert agent1_messages[0]["content"] == "Message for agent1"
        assert agent2_messages[0]["content"] == "Message for agent2"
    
    @pytest.mark.asyncio
    async def test_agent_handoff_workflow(self, mock_config, mock_websocket):
        """Test agent handoff scenario"""
        from interactive_server.main import session_handoff_handler
        
        manager = InteractiveSessionManager(mock_config)
        
        # Patch global session manager
        with patch("interactive_server.main.session_manager", manager):
            session_id = await manager.create_session(mock_websocket)
            session = manager.get_session(session_id)
            
            # Create agents
            await session.create_agent("planner", "Planning agent")
            await session.create_agent("implementer", "Implementation agent")
            
            # Start with planner
            await session.switch_agent("planner")
            
            # Handoff to implementer
            result = await session_handoff_handler(
                {"to_agent": "implementer"},
                websocket=mock_websocket
            )
            
            assert result["success"] is True
            assert result["from_agent"] == "planner"
            assert result["to_agent"] == "implementer"
            assert session.active_agent == "implementer"


class TestSessionPersistenceAndRecovery:
    """Test session persistence and recovery scenarios"""
    
    @pytest.mark.asyncio
    async def test_session_state_persistence(self, mock_config, mock_websocket):
        """Test saving and restoring session state"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create session with agents and messages
        session_id = await manager.create_session(mock_websocket)
        session = manager.get_session(session_id)
        
        await session.create_agent("test-agent", "Test agent prompt")
        agent = session.agents["test-agent"]
        
        # Add some conversation history
        agent.context.store_message({"role": "user", "content": "Hello"})
        agent.context.store_message({"role": "assistant", "content": "Hi there"})
        agent.context.store_message({"role": "user", "content": "How are you?"})
        agent.context.store_message({"role": "assistant", "content": "I'm doing well"})
        
        # Get state
        state = await session.get_state()
        
        # Create new session and restore
        new_websocket = create_mock_websocket()
        new_session_id = await manager.create_session(new_websocket)
        new_session = manager.get_session(new_session_id)
        
        # Restore state
        await new_session.restore_state(state)
        
        # Verify restoration
        assert "test-agent" in new_session.agents
        restored_agent = new_session.agents["test-agent"]
        restored_messages = restored_agent.context.retrieve_messages()
        
        assert len(restored_messages) == 4
        assert restored_messages[0]["content"] == "Hello"
        assert restored_messages[1]["content"] == "Hi there"
        assert restored_messages[2]["content"] == "How are you?"
        assert restored_messages[3]["content"] == "I'm doing well"
    
    @pytest.mark.asyncio
    async def test_session_recovery_after_disconnect(self, mock_config):
        """Test session recovery after WebSocket disconnect"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create initial WebSocket and session
        ws1 = create_mock_websocket()
        session_id = await manager.create_session(ws1)
        await manager.start_session(session_id)
        
        session = manager.get_session(session_id)
        session.agents["default"].process_message = AsyncMock()
        
        # Send some messages
        await session.send_user_message("Message 1")
        
        # Simulate disconnect (don't cleanup)
        ws1.closed = True
        
        # Session should still exist
        assert manager.get_session(session_id) is not None
        
        # Reconnect with new WebSocket
        ws2 = create_mock_websocket()
        # Update WebSocket mapping
        manager.websocket_sessions[ws2] = session_id
        session.websocket = ws2
        
        # Should be able to continue conversation
        await session.send_user_message("Message 2")
        assert session.agents["default"].process_message.call_count == 2
    
    @pytest.mark.asyncio
    async def test_session_file_persistence(self, mock_config, tmp_path):
        """Test that sessions are saved to and loaded from file"""
        # Use temporary directory for sessions file
        sessions_file = tmp_path / "sessions.json"
        
        # Patch the actual file operations in session manager
        import builtins
        original_open = builtins.open
        
        def mock_open(file, mode='r', *args, **kwargs):
            if 'sessions.json' in str(file):
                return original_open(str(sessions_file), mode, *args, **kwargs)
            return original_open(file, mode, *args, **kwargs)
        
        with patch("builtins.open", mock_open):
            with patch("os.path.exists", lambda p: sessions_file.exists() if 'sessions.json' in p else os.path.exists(p)):
                manager = InteractiveSessionManager(mock_config)
                
                # Create sessions
                ws1 = create_mock_websocket()
                ws2 = create_mock_websocket()
                
                session_id1 = await manager.create_session(ws1)
                session_id2 = await manager.create_session(ws2)
                
                # Sessions should be saved
                assert sessions_file.exists()
                
                with open(sessions_file, 'r') as f:
                    data = json.load(f)
                    assert len(data["sessions"]) >= 2  # May have more from initialization
                    assert session_id1 in data["sessions"]
                    assert session_id2 in data["sessions"]


class TestConcurrentSessionOperations:
    """Test concurrent session operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, mock_config):
        """Test creating multiple sessions concurrently"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create 10 sessions concurrently
        tasks = []
        for i in range(10):
            ws = create_mock_websocket()
            tasks.append(manager.create_session(ws))
        
        session_ids = await asyncio.gather(*tasks)
        
        # All should be unique
        assert len(set(session_ids)) == 10
        assert manager.get_active_sessions_count() == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self, mock_config):
        """Test handling messages concurrently across sessions"""
        manager = InteractiveSessionManager(mock_config)
        
        # Create multiple sessions
        sessions = []
        for i in range(5):
            ws = create_mock_websocket()
            session_id = await manager.create_session(ws)
            await manager.start_session(session_id)
            
            # Mock agent processing
            session = manager.get_session(session_id)
            session.agents["default"].process_message = AsyncMock()
            
            sessions.append((session_id, session))
        
        # Send messages concurrently
        tasks = []
        for i, (session_id, session) in enumerate(sessions):
            for j in range(3):
                tasks.append(manager.send_message(session_id, f"Session {i} Message {j}"))
        
        await asyncio.gather(*tasks)
        
        # Each session should have received 3 messages
        for session_id, session in sessions:
            assert session.agents["default"].process_message.call_count == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self, mock_config):
        """Test concurrent agent operations within a session"""
        manager = InteractiveSessionManager(mock_config)
        
        ws = create_mock_websocket()
        session_id = await manager.create_session(ws)
        session = manager.get_session(session_id)
        
        # Create agents concurrently
        agent_tasks = []
        for i in range(5):
            agent_tasks.append(
                session.create_agent(f"agent{i}", f"Agent {i} prompt")
            )
        
        await asyncio.gather(*agent_tasks)
        
        assert len(session.agents) == 5
        
        # Switch agents concurrently (should be serialized by lock)
        switch_tasks = []
        for i in range(5):
            switch_tasks.append(session.switch_agent(f"agent{i}"))
        
        await asyncio.gather(*switch_tasks)
        
        # Last switch should win
        assert session.active_agent == "agent4"


class TestWebSocketStreaming:
    """Test WebSocket streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_ai_response_streaming(self, mock_config, mock_websocket):
        """Test that AI responses are streamed properly via notifications"""
        manager = InteractiveSessionManager(mock_config)
        
        session_id = await manager.create_session(mock_websocket)
        session = manager.get_session(session_id)
        
        # Create agent
        await session.create_agent("streamer", "Streaming agent")
        
        # Simulate streaming chunks via session notifications
        chunks = ["Hello", " from", " the", " AI", "!"]
        for i, chunk in enumerate(chunks):
            await session.send_notification("AIMessageChunkNotification", {
                "sessionId": session_id,
                "chunk": chunk,
                "isFinal": i == len(chunks) - 1
            })
        
        # Check that chunks were sent via WebSocket
        chunk_messages = [
            msg for msg in mock_websocket.messages 
            if msg.get("method") == "AIMessageChunkNotification"
        ]
        
        assert len(chunk_messages) == 5
        assert chunk_messages[0]["params"]["chunk"] == "Hello"
        assert chunk_messages[4]["params"]["chunk"] == "!"
        assert chunk_messages[4]["params"]["isFinal"] is True
    
    @pytest.mark.asyncio
    async def test_tool_call_notifications(self, mock_config, mock_websocket):
        """Test that tool calls generate proper notifications"""
        manager = InteractiveSessionManager(mock_config)
        
        session_id = await manager.create_session(mock_websocket)
        session = manager.get_session(session_id)
        
        # Simulate tool call notification
        await session.send_notification("ToolCallNotification", {
            "sessionId": session_id,
            "toolCallId": "tool-123",
            "toolName": "write_file",
            "arguments": {"path": "test.py", "content": "print('hello')"}
        })
        
        # Check notification
        tool_notifications = [
            msg for msg in mock_websocket.messages
            if msg.get("method") == "ToolCallNotification"
        ]
        
        assert len(tool_notifications) == 1
        notification = tool_notifications[0]["params"]
        assert notification["sessionId"] == session_id
        assert notification["toolCallId"] == "tool-123"
        assert notification["toolName"] == "write_file"
        assert notification["arguments"]["path"] == "test.py"


class TestRegressionTests:
    """Run regression tests to ensure nothing is broken"""
    
    @pytest.mark.asyncio
    async def test_existing_api_compatibility(self, mock_config, mock_websocket):
        """Test that existing API calls still work"""
        from interactive_server.main import (
            start_session_handler,
            send_user_message_handler,
            stop_session_handler
        )
        
        with patch("interactive_server.main.session_manager", InteractiveSessionManager(mock_config)):
            # Old-style start session
            result = await start_session_handler(
                {"userId": "test-user"},
                websocket=mock_websocket
            )
            
            assert "sessionId" in result
            assert result["status"] == SessionStatus.Active
            
            session_id = result["sessionId"]
            
            # Old-style send message
            result = await send_user_message_handler(
                {"sessionId": session_id, "message": "Test message"},
                websocket=mock_websocket
            )
            
            assert "messageId" in result
            assert result["status"] == MessageStatus.OK
            
            # Old-style stop session
            result = await stop_session_handler(
                {"sessionId": session_id},
                websocket=mock_websocket
            )
            
            assert result["status"] == SessionStatus.Stopped
    
    @pytest.mark.skip(reason="DelegateBridge needs refactoring for new Agent architecture")
    @pytest.mark.asyncio
    async def test_delegate_bridge_compatibility(self, mock_config, mock_websocket):
        """Test that delegate bridge still works with new architecture"""
        # TODO: DelegateBridge expects session.delegate_manager which doesn't exist
        # in the new architecture. This will be addressed in Phase 4 when we
        # simplify the AILoop and remove delegates.
        pass
    
    @pytest.mark.asyncio  
    async def test_backwards_compatibility_with_interactive_ai(self, mock_config):
        """Test backwards compatibility when interactive_ai is expected"""
        manager = InteractiveSessionManager(mock_config)
        
        ws = create_mock_websocket()
        session_id = await manager.create_session(ws)
        session = manager.get_session(session_id)
        
        # Some handlers might expect interactive_ai attribute
        # Ensure it exists or is handled gracefully
        assert not hasattr(session, 'interactive_ai') or session.interactive_ai is None