"""
Unit tests for /clear command functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from interactive_server.stateless_session_manager import StatelessInteractiveSession
from ai_whisperer.context.context_manager import AgentContextManager
from ai_whisperer.context.context_item import ContextItem


class TestClearCommand:
    """Test /clear command functionality"""
    
    @pytest.fixture
    def session(self):
        """Create a test session with mocked dependencies"""
        session = StatelessInteractiveSession("test-session", {}, None, None)
        
        # Mock WebSocket
        session.websocket = AsyncMock()
        
        # Mock context manager
        session.context_manager = Mock(spec=AgentContextManager)
        session.context_manager.get_agent_context = Mock(return_value=[
            Mock(spec=ContextItem),
            Mock(spec=ContextItem),
            Mock(spec=ContextItem)
        ])
        session.context_manager.clear_agent_context = Mock(return_value=3)
        
        # Create test agents
        session.agents = {
            "alice": Mock(context=Mock(clear=Mock())),
            "patricia": Mock(context=Mock(clear=Mock())),
            "e": Mock(context=Mock(clear=Mock()))
        }
        session.active_agent = "alice"
        session.is_started = True
        
        return session
    
    @pytest.mark.asyncio
    async def test_clear_current_agent(self, session):
        """Test /clear without arguments clears current agent"""
        result = await session._handle_command("/clear")
        
        assert result is True
        # The implementation passes the active agent name, not None
        session.context_manager.clear_agent_context.assert_called_once_with("alice")
        session.websocket.send_json.assert_called()
        
        # Check notification content
        notifications = [call[0][0] for call in session.websocket.send_json.call_args_list]
        # Should have context.cleared and system message notifications
        assert any("context.cleared" in str(n) for n in notifications)
        assert any("agent.message" in str(n) for n in notifications)
    
    @pytest.mark.asyncio
    async def test_clear_specific_agent(self, session):
        """Test /clear with agent name"""
        result = await session._handle_command("/clear patricia")
        
        assert result is True
        session.context_manager.clear_agent_context.assert_called_once_with("patricia")
        
        # Check system message
        call_args = session.websocket.send_json.call_args_list[-1][0][0]
        assert "patricia" in str(call_args).lower()
        assert "cleared" in str(call_args).lower()
    
    @pytest.mark.asyncio
    async def test_clear_all_agents(self, session):
        """Test /clear all clears all agents"""
        result = await session._handle_command("/clear all")
        
        assert result is True
        # Should be called once for each agent
        assert session.context_manager.clear_agent_context.call_count == 3
        
        # Check system message mentions total
        call_args = session.websocket.send_json.call_args_list[-1][0][0]
        assert "all agents" in str(call_args).lower()
    
    @pytest.mark.asyncio
    async def test_clear_unknown_agent(self, session):
        """Test /clear with unknown agent name"""
        result = await session._handle_command("/clear unknown_agent")
        
        assert result is True
        # Should not call clear
        session.context_manager.clear_agent_context.assert_not_called()
        
        # Check error message
        call_args = session.websocket.send_json.call_args_list[-1][0][0]
        assert "unknown agent" in str(call_args).lower()
        assert "alice" in str(call_args)  # Should list available agents
    
    @pytest.mark.asyncio
    async def test_clear_method_integration(self, session):
        """Test clear_agent_context method"""
        result = await session.clear_agent_context("alice")
        
        assert result["cleared"] is True
        assert result["items_cleared"] == 3
        assert result["agent_id"] == "alice"
        
        # Check both context manager and agent's context were cleared
        session.context_manager.clear_agent_context.assert_called_once_with("alice")
        session.agents["alice"].context.clear.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_help_command(self, session):
        """Test /help command shows clear command info"""
        result = await session._handle_command("/help")
        
        assert result is True
        
        # Check help message content
        call_args = session.websocket.send_json.call_args_list[-1][0][0]
        help_text = str(call_args).lower()
        assert "/clear" in help_text
        assert "context" in help_text
        assert "agent" in help_text
    
    @pytest.mark.asyncio
    async def test_command_in_message_flow(self, session):
        """Test that commands are intercepted in send_user_message"""
        # Mock the command handler
        session._handle_command = AsyncMock(return_value=True)
        
        await session.send_user_message("/clear")
        
        # Command should be handled and message processing stopped
        session._handle_command.assert_called_once_with("/clear")
        # Context processing should not happen
        session.context_manager.process_message_references.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_system_message_format(self, session):
        """Test system message formatting"""
        await session._send_system_message("Test system message")
        
        # Check notification format
        session.websocket.send_json.assert_called_once()
        notification = session.websocket.send_json.call_args[0][0]
        
        assert notification["method"] == "agent.message"
        assert notification["params"]["agent_id"] == "system"
        assert notification["params"]["message"] == "Test system message"
        assert notification["params"]["type"] == "system"
        assert "timestamp" in notification["params"]


@pytest.mark.asyncio
async def test_context_manager_clear_method():
    """Test the context manager's clear_agent_context method"""
    from ai_whisperer.utils.path import PathManager
    
    # Mock PathManager
    with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_pm:
        mock_pm.return_value = Mock()
        
        manager = AgentContextManager("test-session", mock_pm.return_value)
        
        # Add some context items
        manager.contexts["test_agent"] = [
            Mock(spec=ContextItem),
            Mock(spec=ContextItem)
        ]
        
        # Clear context
        items_cleared = manager.clear_agent_context("test_agent")
        
        assert items_cleared == 2
        assert len(manager.contexts["test_agent"]) == 0
        
        # Clear non-existent agent
        items_cleared = manager.clear_agent_context("non_existent")
        assert items_cleared == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])