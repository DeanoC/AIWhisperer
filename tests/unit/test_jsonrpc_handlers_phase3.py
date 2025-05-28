"""
Phase 3.3 Tests: JSON-RPC Handler Tests for Agent Architecture
Tests for updated RPC message handlers with agent support
"""
import asyncio
import json
import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

import inspect
from interactive_server.main import (
    agent_list_handler,
    session_switch_agent_handler,
    session_current_agent_handler,
    session_handoff_handler,
    start_session_handler,
    send_user_message_handler,
    provide_tool_result_handler,
    stop_session_handler,
    echo_handler,
    dispatch_command_handler,
    process_json_rpc_request,
    handle_websocket_message
)
from interactive_server.session_manager import InteractiveSession, InteractiveSessionManager
from interactive_server.message_models import (
    SessionStatus,
    MessageStatus,
    ToolResultStatus
)
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.agents.registry import AgentRegistry, Agent as AgentInfo


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages = []
        self.closed = False
        
    async def send_json(self, data):
        self.messages.append(data)
        
    async def send_text(self, text):
        self.messages.append(json.loads(text))
        
    async def close(self):
        self.closed = True


@pytest.fixture
def mock_websocket():
    return MockWebSocket()


@pytest.fixture
def mock_session_manager(monkeypatch):
    """Mock session manager with agent support"""
    manager = MagicMock(spec=InteractiveSessionManager)
    
    # Create mock session with agent support
    mock_session = MagicMock(spec=InteractiveSession)
    mock_session.session_id = "test-session-123"
    mock_session.is_started = True
    mock_session.agents = {}
    mock_session.active_agent = None
    mock_session.delegate_bridge = MagicMock()
    
    # Mock methods
    mock_session.create_agent = AsyncMock()
    mock_session.switch_agent = AsyncMock()
    mock_session.send_user_message = AsyncMock()
    mock_session.send_notification = AsyncMock()
    mock_session.cleanup = AsyncMock()
    
    # Mock manager methods
    manager.create_session = AsyncMock(return_value="test-session-123")
    manager.start_session = AsyncMock()
    manager.stop_session = AsyncMock()
    manager.send_message = AsyncMock()
    manager.cleanup_session = AsyncMock()
    manager.get_session = MagicMock(return_value=mock_session)
    manager.get_session_by_websocket = MagicMock(return_value=mock_session)
    
    # Patch the global session_manager
    monkeypatch.setattr("interactive_server.main.session_manager", manager)
    
    return manager


@pytest.fixture
def mock_agent_registry(monkeypatch):
    """Mock agent registry"""
    registry = MagicMock(spec=AgentRegistry)
    
    # Mock agent info
    agents = [
        AgentInfo(
            agent_id="P",
            name="Planning Agent",
            role="planner",
            description="Plans and organizes tasks",
            tool_tags=["planning"],
            prompt_file="agent_planner.md",
            context_sources=["workspace"],
            color="#4A90E2"
        ),
        AgentInfo(
            agent_id="C",
            name="Coding Agent",
            role="coder",
            description="Writes and modifies code",
            tool_tags=["coding"],
            prompt_file="agent_coder.md",
            context_sources=["code"],
            color="#7ED321"
        ),
        AgentInfo(
            agent_id="R",
            name="Review Agent",
            role="reviewer",
            description="Reviews code and plans",
            tool_tags=["review"],
            prompt_file="agent_reviewer.md",
            context_sources=["code", "tests"],
            color="#F5A623"
        )
    ]
    
    registry.list_agents = MagicMock(return_value=agents)
    registry.get_agent = MagicMock(side_effect=lambda aid: next((a for a in agents if a.agent_id == aid), None))
    
    # Patch the global agent_registry
    monkeypatch.setattr("interactive_server.main.agent_registry", registry)
    
    return registry


class TestAgentHandlers:
    """Tests for agent-related JSON-RPC handlers"""
    
    @pytest.mark.asyncio
    async def test_agent_list_handler(self, mock_agent_registry):
        """Test listing available agents"""
        result = await agent_list_handler({})
        
        assert "agents" in result
        assert len(result["agents"]) == 3
        
        # Check agent structure
        agent = result["agents"][0]
        assert agent["agent_id"] == "P"
        assert agent["name"] == "Planning Agent"
        assert agent["role"] == "planner"
        assert agent["description"] == "Plans and organizes tasks"
        assert agent["color"] == "#4A90E2"
        assert agent["shortcut"] == "[P]"
    
    @pytest.mark.asyncio
    async def test_session_switch_agent_with_websocket(self, mock_websocket, mock_session_manager):
        """Test switching agent via WebSocket"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Mock the switch_agent method to work properly
        session.switch_agent = AsyncMock()
        
        result = await session_switch_agent_handler(
            {"agent_id": "coder"}, 
            websocket=mock_websocket
        )
        
        assert result["success"] is True
        assert result["current_agent"] == "coder"
        session.switch_agent.assert_called_once_with("coder")
    
    @pytest.mark.asyncio
    async def test_session_switch_agent_with_session_id(self, mock_session_manager):
        """Test switching agent with session ID"""
        session = mock_session_manager.get_session("test-session-123")
        session.switch_agent = AsyncMock()
        
        result = await session_switch_agent_handler(
            {"agent_id": "reviewer", "sessionId": "test-session-123"}
        )
        
        assert result["success"] is True
        assert result["current_agent"] == "reviewer"
        session.switch_agent.assert_called_once_with("reviewer")
    
    @pytest.mark.asyncio
    async def test_session_switch_agent_error_handling(self, mock_websocket, mock_session_manager):
        """Test error handling when switching to invalid agent"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        session.switch_agent = AsyncMock(side_effect=ValueError("Agent not found"))
        
        result = await session_switch_agent_handler(
            {"agent_id": "invalid-agent"}, 
            websocket=mock_websocket
        )
        
        assert "error" in result
        assert result["error"]["code"] == -32001
        assert "Agent not found" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_session_current_agent_handler(self, mock_websocket, mock_session_manager):
        """Test getting current active agent"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Mock agent
        session.active_agent = "planner"
        
        result = await session_current_agent_handler({}, websocket=mock_websocket)
        
        assert result["current_agent"] == "planner"
    
    @pytest.mark.asyncio
    async def test_session_current_agent_none(self, mock_websocket, mock_session_manager):
        """Test getting current agent when none is active"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        session.active_agent = None
        
        result = await session_current_agent_handler({}, websocket=mock_websocket)
        
        assert result["current_agent"] is None
    
    @pytest.mark.asyncio
    async def test_session_handoff_handler(self, mock_websocket, mock_session_manager):
        """Test agent handoff functionality"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Mock current agent
        session.active_agent = "planner"
        session.switch_agent = AsyncMock()
        
        result = await session_handoff_handler(
            {"to_agent": "coder"}, 
            websocket=mock_websocket
        )
        
        assert result["success"] is True
        assert result["from_agent"] == "planner"
        assert result["to_agent"] == "coder"
        session.switch_agent.assert_called_once_with("coder")
    
    @pytest.mark.asyncio
    async def test_session_handoff_error_handling(self, mock_websocket, mock_session_manager):
        """Test handoff error when agent not found"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        session.switch_agent = AsyncMock(side_effect=ValueError("Agent not found"))
        
        result = await session_handoff_handler(
            {"to_agent": "invalid-agent"}, 
            websocket=mock_websocket
        )
        
        assert "error" in result
        assert result["error"]["code"] == -32001
        assert "Agent not found" in result["error"]["message"]


class TestSessionHandlers:
    """Tests for session management handlers"""
    
    @pytest.mark.asyncio
    async def test_start_session_handler(self, mock_websocket, mock_session_manager):
        """Test starting a new session"""
        params = {
            "userId": "test-user-123",
            "sessionParams": {
                "context": "You are a helpful assistant"
            }
        }
        
        result = await start_session_handler(params, websocket=mock_websocket)
        
        assert result["sessionId"] == "test-session-123"
        assert result["status"] == SessionStatus.Active
        
        mock_session_manager.create_session.assert_called_once()
        mock_session_manager.start_session.assert_called_once_with("test-session-123")
    
    @pytest.mark.asyncio
    async def test_send_user_message_handler(self, mock_websocket, mock_session_manager):
        """Test sending a user message"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        params = {
            "sessionId": "test-session-123",
            "message": "Hello, AI!"
        }
        
        result = await send_user_message_handler(params, websocket=mock_websocket)
        
        assert "messageId" in result
        assert result["status"] == MessageStatus.OK
        
        session.send_user_message.assert_called_once_with("Hello, AI!")
    
    @pytest.mark.asyncio
    async def test_send_user_message_invalid_session(self, mock_websocket, mock_session_manager):
        """Test sending message to invalid session"""
        mock_session_manager.get_session_by_websocket.return_value = None
        mock_session_manager.get_session.return_value = None
        
        params = {
            "sessionId": "invalid-session",
            "message": "Hello"
        }
        
        with pytest.raises(ValueError, match="Invalid session"):
            await send_user_message_handler(params, websocket=mock_websocket)
    
    @pytest.mark.asyncio
    async def test_provide_tool_result_handler(self, mock_session_manager):
        """Test providing tool results"""
        session = mock_session_manager.get_session("test-session-123")
        
        # Mock interactive_ai and ai_loop
        session.interactive_ai = MagicMock()
        session.interactive_ai.ai_loop = MagicMock()
        session.interactive_ai.ai_loop._handle_provide_tool_result = AsyncMock()
        
        params = {
            "sessionId": "test-session-123",
            "toolCallId": "tool-123",
            "result": '{"output": "Tool execution successful"}'
        }
        
        result = await provide_tool_result_handler(params)
        
        assert result["status"] == ToolResultStatus.OK
        
        session.interactive_ai.ai_loop._handle_provide_tool_result.assert_called_once_with(
            tool_call_id="tool-123",
            result='{"output": "Tool execution successful"}'
        )
    
    @pytest.mark.asyncio
    async def test_stop_session_handler(self, mock_session_manager):
        """Test stopping a session"""
        session = mock_session_manager.get_session("test-session-123")
        
        params = {"sessionId": "test-session-123"}
        
        result = await stop_session_handler(params)
        
        assert result["status"] == SessionStatus.Stopped
        
        mock_session_manager.stop_session.assert_called_once_with("test-session-123")
        mock_session_manager.cleanup_session.assert_called_once_with("test-session-123")
        session.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_session_idempotent(self, mock_session_manager):
        """Test that stop session is idempotent"""
        # Session doesn't exist
        mock_session_manager.get_session.return_value = None
        
        params = {"sessionId": "non-existent-session"}
        
        # Should not raise, returns stopped
        result = await stop_session_handler(params)
        
        assert result["status"] == SessionStatus.Stopped
    
    @pytest.mark.asyncio
    async def test_echo_handler(self):
        """Test echo handler"""
        # Test with message param
        result = await echo_handler({"message": "Hello, echo!"})
        assert result == "Hello, echo!"
        
        # Test with other params
        result = await echo_handler({"data": "test"})
        assert result == {"data": "test"}
        
        # Test with non-dict
        result = await echo_handler("simple string")
        assert result == "simple string"


class TestJSONRPCProtocol:
    """Tests for JSON-RPC protocol handling"""
    
    @pytest.mark.asyncio
    async def test_process_json_rpc_request_success(self, mock_websocket):
        """Test successful JSON-RPC request processing"""
        with patch("interactive_server.main.HANDLERS", {"echo": echo_handler}):
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "echo",
                "params": {"message": "test"}
            }
            
            result = await process_json_rpc_request(message, mock_websocket)
            
            assert result["jsonrpc"] == "2.0"
            assert result["id"] == 1
            assert result["result"] == "test"
    
    @pytest.mark.asyncio
    async def test_process_json_rpc_request_method_not_found(self, mock_websocket):
        """Test JSON-RPC method not found error"""
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "invalid_method",
            "params": {}
        }
        
        result = await process_json_rpc_request(message, mock_websocket)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 2
        assert "error" in result
        assert result["error"]["code"] == -32601
        assert "Method not found" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_process_json_rpc_request_handler_error(self, mock_websocket):
        """Test JSON-RPC handler error"""
        async def failing_handler(params, websocket=None):
            raise ValueError("Handler failed")
        
        with patch("interactive_server.main.HANDLERS", {"failing": failing_handler}):
            with patch("interactive_server.main.inspect", inspect):
                message = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "failing",
                    "params": {}
                }
                
                result = await process_json_rpc_request(message, mock_websocket)
                
                assert result["jsonrpc"] == "2.0"
                assert result["id"] == 3
                assert "error" in result
                assert result["error"]["code"] == -32602  # ValueError is treated as invalid params
                assert "Handler failed" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_handle_websocket_message_valid_json(self, mock_websocket):
        """Test handling valid JSON WebSocket message"""
        with patch("interactive_server.main.process_json_rpc_request", new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {"jsonrpc": "2.0", "id": 1, "result": "ok"}
            
            text_message = '{"jsonrpc": "2.0", "id": 1, "method": "echo", "params": {}}'
            
            result = await handle_websocket_message(mock_websocket, text_message)
            
            mock_process.assert_called_once()
            assert result["jsonrpc"] == "2.0"
            assert result["id"] == 1
            assert result["result"] == "ok"
    
    @pytest.mark.asyncio
    async def test_handle_websocket_message_invalid_json(self, mock_websocket):
        """Test handling invalid JSON"""
        text_message = "not valid json"
        
        result = await handle_websocket_message(mock_websocket, text_message)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] is None
        assert result["error"]["code"] == -32700
        assert "Parse error" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_handle_websocket_message_missing_jsonrpc(self, mock_websocket):
        """Test handling message without jsonrpc field"""
        text_message = '{"id": 1, "method": "echo", "params": {}}'
        
        result = await handle_websocket_message(mock_websocket, text_message)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert result["error"]["code"] == -32600
        assert "Invalid Request" in result["error"]["message"]


class TestErrorScenarios:
    """Tests for various error scenarios"""
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_switching(self, mock_websocket, mock_session_manager):
        """Test concurrent agent switching requests"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Simulate slow switch operation
        async def slow_switch(agent_id):
            await asyncio.sleep(0.1)
        
        session.switch_agent = slow_switch
        
        # Send multiple switch requests concurrently
        tasks = [
            session_switch_agent_handler({"agent_id": f"agent{i}"}, websocket=mock_websocket)
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without errors
        assert all(isinstance(r, dict) for r in results)
    
    @pytest.mark.asyncio
    async def test_session_cleanup_during_message_send(self, mock_websocket, mock_session_manager):
        """Test session cleanup while message is being sent"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Simulate slow message send
        async def slow_send(message):
            await asyncio.sleep(0.1)
            raise RuntimeError("Session was cleaned up")
        
        session.send_user_message = slow_send
        
        # Start sending message
        send_task = asyncio.create_task(
            send_user_message_handler(
                {"sessionId": "test-session-123", "message": "test"}, 
                websocket=mock_websocket
            )
        )
        
        # Cleanup session while message is sending
        await asyncio.sleep(0.05)
        mock_session_manager.get_session_by_websocket.return_value = None
        
        # Should handle gracefully
        with pytest.raises(RuntimeError):
            await send_task
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect_during_operation(self, mock_websocket, mock_session_manager):
        """Test WebSocket disconnect during operation"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Simulate WebSocket disconnect
        mock_websocket.closed = True
        
        # Try to send notification
        await session.send_notification("test", {"data": "test"})
        
        # Should handle gracefully (logged but not raised)
        session.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_malformed_tool_result(self, mock_session_manager):
        """Test handling malformed tool result"""
        params = {
            "sessionId": "test-session-123",
            "toolCallId": None,  # Invalid
            "result": "not a dict"  # Should be dict
        }
        
        with pytest.raises(Exception):  # Validation should fail
            await provide_tool_result_handler(params)


class TestAgentIntegration:
    """Tests for agent integration with RPC handlers"""
    
    @pytest.mark.asyncio
    async def test_agent_creation_on_session_start(self, mock_websocket, mock_session_manager):
        """Test that starting session creates default agent"""
        params = {"userId": "test-user"}
        
        result = await start_session_handler(params, websocket=mock_websocket)
        
        assert result["sessionId"] == "test-session-123"
        assert result["status"] == SessionStatus.Active
        
        # Should have started session (which creates default agent)
        mock_session_manager.start_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agent_context_preservation(self, mock_websocket, mock_session_manager):
        """Test that agent context is preserved across messages"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Send multiple messages
        messages = ["Hello", "How are you?", "Tell me a joke"]
        
        for msg in messages:
            await send_user_message_handler(
                {"sessionId": "test-session-123", "message": msg},
                websocket=mock_websocket
            )
        
        # All messages should be sent to the same session
        assert session.send_user_message.call_count == 3
        
        # Check messages were sent in order
        calls = session.send_user_message.call_args_list
        for i, msg in enumerate(messages):
            assert calls[i][0][0] == msg
    
    @pytest.mark.asyncio
    async def test_multi_agent_session_flow(self, mock_websocket, mock_session_manager, mock_agent_registry):
        """Test complete multi-agent session flow"""
        session = mock_session_manager.get_session_by_websocket(mock_websocket)
        
        # Start session
        await start_session_handler({"userId": "test-user"}, websocket=mock_websocket)
        
        # List agents
        agents_result = await agent_list_handler({})
        assert len(agents_result["agents"]) == 3
        
        # Switch to planner agent
        session.switch_agent = AsyncMock()
        switch_result = await session_switch_agent_handler(
            {"agent_id": "P"}, 
            websocket=mock_websocket
        )
        assert switch_result["success"] is True
        
        # Send message to planner
        await send_user_message_handler(
            {"sessionId": "test-session-123", "message": "Create a plan for building a web app"},
            websocket=mock_websocket
        )
        
        # Switch to coder agent
        switch_result = await session_switch_agent_handler(
            {"agent_id": "C"}, 
            websocket=mock_websocket
        )
        assert switch_result["success"] is True
        
        # Send message to coder
        await send_user_message_handler(
            {"sessionId": "test-session-123", "message": "Implement the first feature"},
            websocket=mock_websocket
        )
        
        # Check agent was switched twice
        assert session.switch_agent.call_count == 2
        
        # Stop session
        await stop_session_handler({"sessionId": "test-session-123"})
        mock_session_manager.cleanup_session.assert_called_once()