"""
Integration tests for conversation persistence (save/load/clear).
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from interactive_server.stateless_session_manager import StatelessSessionManager
from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext


class TestConversationPersistence:
    """Test conversation persistence functionality"""
    
    @pytest.fixture
    def session_with_agents(self):
        """Create a session with multiple agents and some conversation history"""
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        session = StatelessSessionManager(config, None, None)
        session.session_id = "test-persist-session"
        session.websocket = AsyncMock()
        session.is_started = True
        
        # Create Alice with some context
        alice_config = AgentConfig(
            name="alice",
            description="Test Alice",
            system_prompt="I am Alice",
            model_name="test-model",
            provider="test",
            api_settings={},
            generation_params={"temperature": 0.7, "max_tokens": 1000}
        )
        alice = Mock(spec=StatelessAgent)
        alice.config = alice_config
        alice.context = Mock(spec=AgentContext)
        alice.context.retrieve_messages = Mock(return_value=[
            {"role": "user", "content": "List files"},
            {"role": "assistant", "content": "Here are the files: README.md, setup.py"},
            {"role": "user", "content": "Read README.md"},
            {"role": "assistant", "content": "# AIWhisperer\nAI-powered coding assistant"}
        ])
        alice.context._metadata = {"files_discussed": ["README.md", "setup.py"]}
        alice.context.clear = Mock()
        
        # Create Patricia with RFC context
        patricia_config = AgentConfig(
            name="patricia",
            description="Test Patricia",
            system_prompt="I am Patricia",
            model_name="test-model",
            provider="test",
            api_settings={},
            generation_params={"temperature": 0.7, "max_tokens": 1000}
        )
        patricia = Mock(spec=StatelessAgent)
        patricia.config = patricia_config
        patricia.context = Mock(spec=AgentContext)
        patricia.context.retrieve_messages = Mock(return_value=[
            {"role": "user", "content": "Create RFC for persistence"},
            {"role": "assistant", "content": "I'll create an RFC for conversation persistence"}
        ])
        patricia.context._metadata = {"rfc_created": "conversation_persistence.md"}
        patricia.context.clear = Mock()
        
        # Add agents to session
        session.agents = {
            "alice": alice,
            "patricia": patricia
        }
        session.active_agent = "alice"
        session.introduced_agents = {"alice", "patricia"}
        
        # Mock context manager
        session.context_manager = Mock()
        session.context_manager.clear_agent_context = Mock(return_value=5)
        session.context_manager.get_agent_context = Mock(return_value=[Mock(), Mock(), Mock(), Mock(), Mock()])
        
        # Mock command handling helpers
        session._send_system_message = AsyncMock()
        session.send_notification = AsyncMock()
        
        return session
    
    @pytest.mark.asyncio
    async def test_save_session_default_path(self, session_with_agents):
        """Test saving session to default path"""
        filepath = await session_with_agents.save_session()
        
        assert filepath is not None
        assert ".WHISPER/sessions" in filepath
        assert session_with_agents.session_id in filepath
        assert filepath.endswith(".json")
        
        # Verify file was created
        assert Path(filepath).exists()
        
        # Verify content
        with open(filepath, 'r') as f:
            saved_state = json.load(f)
        
        assert saved_state["session_id"] == "test-persist-session"
        assert saved_state["version"] == "1.0"
        assert "saved_at" in saved_state
        assert saved_state["active_agent"] == "alice"
        assert len(saved_state["agents"]) == 2
        assert "alice" in saved_state["agents"]
        assert "patricia" in saved_state["agents"]
        
        # Check Alice's saved state
        alice_state = saved_state["agents"]["alice"]
        assert alice_state["config"]["name"] == "alice"
        assert len(alice_state["context"]["messages"]) == 4
        assert alice_state["context"]["metadata"]["files_discussed"] == ["README.md", "setup.py"]
        
        # Check notification was sent
        session_with_agents.send_notification.assert_called()
        # Find the session.saved notification
        for call in session_with_agents.send_notification.call_args_list:
            if call[0][0] == "session.saved":
                assert call[0][1]["session_id"] == "test-persist-session"
                assert "filepath" in call[0][1]
                break
        else:
            pytest.fail("session.saved notification not found")
        
        # Cleanup
        os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_save_session_custom_path(self, session_with_agents):
        """Test saving session to custom path"""
        custom_path = "test_output/custom_session.json"
        filepath = await session_with_agents.save_session(custom_path)
        
        assert filepath == custom_path
        assert Path(filepath).exists()
        
        # Cleanup
        os.remove(filepath)
        os.rmdir("test_output")
    
    @pytest.mark.asyncio
    async def test_load_session(self, session_with_agents):
        """Test loading a saved session"""
        # First save the session
        filepath = await session_with_agents.save_session()
        
        # Create a new empty session
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        new_session = StatelessSessionManager(config, None, None)
        new_session.session_id = "new-session"
        new_session.websocket = AsyncMock()
        new_session.send_notification = AsyncMock()
        
        # Mock agent creation
        with patch.object(new_session, '_create_agent_internal', AsyncMock()) as mock_create:
            # Load the saved session
            await new_session.load_session(filepath)
        
        # Verify session was restored
        assert new_session.is_started == True
        assert new_session.active_agent == "alice"
        assert "alice" in new_session.introduced_agents
        assert "patricia" in new_session.introduced_agents
        
        # Verify agents were created
        assert mock_create.call_count == 2
        
        # Check notification was sent  
        new_session.send_notification.assert_called()
        # Find the session.loaded notification
        for call in new_session.send_notification.call_args_list:
            if call[0][0] == "session.loaded":
                assert call[0][1]["active_agent"] == "alice"
                assert call[0][1]["agent_count"] == 2
                break
        else:
            pytest.fail("session.loaded notification not found")
        
        # Cleanup
        os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, session_with_agents):
        """Test loading from non-existent file"""
        with pytest.raises(FileNotFoundError):
            await session_with_agents.load_session("nonexistent.json")
    
    @pytest.mark.asyncio
    async def test_clear_all_then_save(self, session_with_agents):
        """Test clearing all agents then saving shows empty contexts"""
        # Clear all agents
        await session_with_agents._handle_command("/clear all")
        
        # Save session
        filepath = await session_with_agents.save_session()
        
        # Load and verify
        with open(filepath, 'r') as f:
            saved_state = json.load(f)
        
        # Agents should still exist but context should be cleared
        assert len(saved_state["agents"]) == 2
        
        # Context manager should have been called for each agent
        assert session_with_agents.context_manager.clear_agent_context.call_count == 2
        
        # Cleanup
        os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_persistence_commands(self, session_with_agents):
        """Test /save and /load commands"""
        # Test /save command
        result = await session_with_agents._handle_command("/save")
        assert result is True
        
        # Get the saved filepath from system message
        system_msg_call = session_with_agents._send_system_message.call_args_list[-1]
        msg_content = system_msg_call[0][0]
        assert "Session saved to:" in msg_content
        
        # Extract filepath (this is a bit hacky but works for testing)
        # In real usage, we'd parse the actual message
        saved_files = list(Path(".WHISPER/sessions").glob("*.json"))
        assert len(saved_files) > 0
        filepath = str(saved_files[0])
        
        # Test /load command
        result = await session_with_agents._handle_command(f"/load {filepath}")
        assert result is True
        
        # Verify system message
        system_msg_call = session_with_agents._send_system_message.call_args_list[-1]
        msg_content = system_msg_call[0][0]
        assert "Session loaded successfully" in msg_content
        
        # Cleanup
        for f in saved_files:
            os.remove(f)
    
    @pytest.mark.asyncio
    async def test_save_load_with_context_manager(self):
        """Test save/load with actual context manager"""
        from ai_whisperer.context.context_manager import AgentContextManager
        from ai_whisperer.utils.path import PathManager
        
        # Mock PathManager
        with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_pm:
            mock_pm.return_value = Mock()
            
            # Create session with real context manager
            config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
            session = StatelessSessionManager(config, None, None)
            session.session_id = "test-session"
            session.websocket = AsyncMock()
            session.context_manager = AgentContextManager("test-session", mock_pm.return_value)
            session.is_started = True
            
            # Add some context items
            session.context_manager.contexts["alice"] = [Mock(), Mock(), Mock()]
            session.context_manager.contexts["patricia"] = [Mock(), Mock()]
            
            # Test clearing specific agent
            items_cleared = session.context_manager.clear_agent_context("alice")
            assert items_cleared == 3
            assert len(session.context_manager.contexts["alice"]) == 0
            assert len(session.context_manager.contexts["patricia"]) == 2  # Unchanged
            
            # Test clearing all
            session.context_manager.contexts["alice"] = [Mock(), Mock()]  # Add some back
            total_before = sum(len(contexts) for contexts in session.context_manager.contexts.values())
            assert total_before == 4
            
            # Clear all manually
            for agent_id in list(session.context_manager.contexts.keys()):
                session.context_manager.clear_agent_context(agent_id)
            
            total_after = sum(len(contexts) for contexts in session.context_manager.contexts.values())
            assert total_after == 0


@pytest.mark.asyncio
async def test_persistence_workflow():
    """Test a complete persistence workflow"""
    config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
    session = StatelessSessionManager(config, None, None)
    session.session_id = "workflow-test"
    session.websocket = AsyncMock()
    session.is_started = True
    session.agents = {}  # Initialize agents dict
    
    # Mock some agents
    for agent_id in ["alice", "patricia", "e"]:
        config = AgentConfig(
            name=agent_id,
            description=f"Test {agent_id}",
            system_prompt=f"I am {agent_id}",
            model_name="test-model",
            provider="test",
            api_settings={},
            generation_params={"temperature": 0.7, "max_tokens": 1000}
        )
        agent = Mock(spec=StatelessAgent)
        agent.config = config
        agent.context = Mock(spec=AgentContext)
        agent.context.retrieve_messages = Mock(return_value=[
            {"role": "user", "content": f"Hello {agent_id}"},
            {"role": "assistant", "content": f"Hello from {agent_id}"}
        ])
        agent.context._metadata = {f"{agent_id}_data": "test"}
        agent.context.clear = Mock()
        session.agents[agent_id] = agent
    
    session.active_agent = "alice"
    session.introduced_agents = {"alice", "patricia", "e"}
    session.context_manager = Mock()
    session.context_manager.clear_agent_context = Mock(return_value=3)
    session.context_manager.get_agent_context = Mock(return_value=[Mock(), Mock(), Mock()])
    session._send_system_message = AsyncMock()
    session.send_notification = AsyncMock()
    
    # 1. Save initial state
    filepath1 = await session.save_session()
    assert Path(filepath1).exists()
    
    # 2. Clear all agents
    await session._handle_command("/clear all")
    assert session.context_manager.clear_agent_context.call_count == 3
    
    # 3. Save cleared state
    filepath2 = await session.save_session()
    assert Path(filepath2).exists()
    
    # 4. Load original state
    with patch.object(session, '_create_agent_internal', AsyncMock()):
        await session.load_session(filepath1)
    
    # 5. Verify state was restored
    assert session.active_agent == "alice"
    assert len(session.agents) == 3
    
    # Cleanup
    os.remove(filepath1)
    os.remove(filepath2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])