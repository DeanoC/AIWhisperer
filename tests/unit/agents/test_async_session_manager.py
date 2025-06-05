"""
Unit tests for async agent session manager.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.services.agents.async_session_manager import (
    AsyncAgentSessionManager,
    AgentState,
    AgentSession
)
from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority


class TestAsyncAgentSessionManager:
    """Test the async agent session manager."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "openrouter": {
                "api_key": "test-key",
                "model": "test-model"
            }
        }
    
    @pytest.fixture
    async def manager(self, config):
        """Create manager instance."""
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        yield manager
        await manager.stop()
        
    @pytest.mark.asyncio
    async def test_create_agent_session(self, manager):
        """Test creating an agent session."""
        with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
            # Mock agent config
            mock_config = Mock()
            mock_config.system_prompt = "Test agent"
            mock_factory.return_value.get_agent_config.return_value = mock_config
            
            # Create session
            session = await manager.create_agent_session("test_agent", auto_start=False)
            
            # Verify
            assert session.agent_id == "test_agent"
            assert session.state == AgentState.IDLE
            assert session.task_queue.empty()
            assert "test_agent" in manager.sessions
            
    @pytest.mark.asyncio
    async def test_agent_sleep_wake(self, manager):
        """Test agent sleep and wake functionality."""
        with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
            mock_config = Mock()
            mock_config.system_prompt = "Test agent"
            mock_factory.return_value.get_agent_config.return_value = mock_config
            
            # Create session
            session = await manager.create_agent_session("sleepy", auto_start=False)
            
            # Put to sleep
            await manager.sleep_agent("sleepy", duration_seconds=2)
            assert session.state == AgentState.SLEEPING
            assert session.sleep_until is not None
            
            # Wake up
            await manager.wake_agent("sleepy", "test wake")
            assert session.state == AgentState.IDLE
            assert session.sleep_until is None
            
    @pytest.mark.asyncio
    async def test_mailbox_processing(self, manager):
        """Test processing mailbox messages."""
        with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
            mock_config = Mock()
            mock_config.system_prompt = "Test agent"
            mock_factory.return_value.get_agent_config.return_value = mock_config
            
            # Create session
            session = await manager.create_agent_session("mail_test", auto_start=False)
            
            # Mock AI loop
            session.ai_loop = Mock()
            session.ai_loop.process_message = AsyncMock(return_value={
                "response": "Test response"
            })
            
            # Send mail
            mail = Mail(
                from_agent="sender",
                to_agent="mail_test",
                subject="Test",
                body="Test message"
            )
            manager.mailbox.send_mail(mail)
            
            # Check mailbox
            await manager._check_agent_mailbox(session)
            
            # Verify task queued
            assert not session.task_queue.empty()
            task = await session.task_queue.get()
            assert task["type"] == "mailbox_message"
            assert task["from_agent"] == "sender"
            
    @pytest.mark.asyncio
    async def test_direct_task_execution(self, manager):
        """Test sending direct task to agent."""
        with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
            mock_config = Mock()
            mock_config.system_prompt = "Test agent"
            mock_factory.return_value.get_agent_config.return_value = mock_config
            
            # Create session
            session = await manager.create_agent_session("task_test", auto_start=False)
            
            # Mock AI loop
            session.ai_loop = Mock()
            session.ai_loop.process_message = AsyncMock(return_value={
                "response": "Task completed"
            })
            
            # Send task
            result = None
            async def callback(response):
                nonlocal result
                result = response
                
            await manager.send_task_to_agent(
                "task_test",
                "Do something",
                callback
            )
            
            # Process task
            task = await session.task_queue.get()
            await manager._process_agent_task(session, task)
            
            # Verify
            assert result == {"response": "Task completed"}
            
    @pytest.mark.asyncio
    async def test_broadcast_event(self, manager):
        """Test broadcasting events to agents."""
        with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
            mock_config = Mock()
            mock_config.system_prompt = "Test agent"
            mock_factory.return_value.get_agent_config.return_value = mock_config
            
            # Create sessions
            session1 = await manager.create_agent_session("agent1", auto_start=False)
            session2 = await manager.create_agent_session("agent2", auto_start=False)
            
            # Set wake events
            session1.wake_events = {"data_ready", "shutdown"}
            session2.wake_events = {"data_ready"}
            
            # Put agents to sleep
            await manager.sleep_agent("agent1")
            await manager.sleep_agent("agent2")
            
            # Broadcast event
            await manager.broadcast_event("data_ready", {"source": "test"})
            
            # Both should wake
            assert session1.state == AgentState.IDLE
            assert session2.state == AgentState.IDLE
            
            # Put back to sleep
            await manager.sleep_agent("agent1")
            await manager.sleep_agent("agent2")
            
            # Broadcast different event
            await manager.broadcast_event("shutdown", {})
            
            # Only agent1 should wake
            assert session1.state == AgentState.IDLE
            assert session2.state == AgentState.SLEEPING
            
    @pytest.mark.asyncio
    async def test_agent_states_report(self, manager):
        """Test getting agent states."""
        with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
            mock_config = Mock()
            mock_config.system_prompt = "Test agent"
            mock_factory.return_value.get_agent_config.return_value = mock_config
            
            # Create sessions
            await manager.create_agent_session("agent1", auto_start=False)
            await manager.create_agent_session("agent2", auto_start=False)
            
            # Set different states
            manager.sessions["agent1"].state = AgentState.ACTIVE
            manager.sessions["agent2"].state = AgentState.SLEEPING
            
            # Get states
            states = manager.get_agent_states()
            
            assert states["agent1"]["state"] == "active"
            assert states["agent2"]["state"] == "sleeping"
            assert "queue_size" in states["agent1"]
            assert "current_task" in states["agent1"]