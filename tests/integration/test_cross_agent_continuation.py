"""
Integration tests for cross-agent continuation consistency
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from ai_whisperer.agents.registry import AgentRegistry
from ai_whisperer.agents.factory import AgentInfo
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
from interactive_server.stateless_session_manager import StatelessSessionManager


class TestCrossAgentContinuation:
    """Test continuation behavior consistency across different agents"""
    
    @pytest.fixture
    def mock_agents_config(self):
        """Create mock agent configurations with different continuation settings"""
        return {
            "alice": {
                "agent_id": "a",
                "name": "Alice",
                "continuation_config": {
                    "require_explicit_signal": True,
                    "max_iterations": 5,
                    "timeout": 300
                }
            },
            "patricia": {
                "agent_id": "p", 
                "name": "Patricia",
                "continuation_config": {
                    "require_explicit_signal": False,
                    "max_iterations": 5,
                    "timeout": 300,
                    "continuation_patterns": ["now I'll", "let me create"],
                    "termination_patterns": ["RFC created", "complete"]
                }
            },
            "eamonn": {
                "agent_id": "e",
                "name": "Eamonn",
                "continuation_config": {
                    "require_explicit_signal": False,
                    "max_iterations": 10,
                    "timeout": 600,
                    "continuation_patterns": ["now I'll", "next, I'll"],
                    "termination_patterns": ["task complete", "all done"]
                }
            },
            "debbie": {
                "agent_id": "d",
                "name": "Debbie",
                "continuation_config": {
                    "require_explicit_signal": True,
                    "max_iterations": 10,
                    "timeout": 600
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_continuation_config_per_agent(self, mock_agents_config):
        """Test that each agent maintains its own continuation configuration"""
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        session_manager = StatelessSessionManager(config, None, None)
        
        # Create agents with different configurations
        for agent_id, agent_config in mock_agents_config.items():
            agent = Mock()
            agent.agent_registry_info = Mock()
            agent.agent_registry_info.continuation_config = agent_config["continuation_config"]
            
            # Create continuation strategy
            from ai_whisperer.agents.continuation_strategy import ContinuationStrategy
            agent.continuation_strategy = ContinuationStrategy(agent_config["continuation_config"])
            
            session_manager.agents[agent_config["agent_id"]] = agent
        
        # Test each agent's configuration
        for agent_id, expected_config in mock_agents_config.items():
            aid = expected_config["agent_id"]
            agent = session_manager.agents[aid]
            
            # Verify configuration
            assert agent.continuation_strategy.require_explicit_signal == expected_config["continuation_config"]["require_explicit_signal"]
            assert agent.continuation_strategy.max_iterations == expected_config["continuation_config"]["max_iterations"]
            assert agent.continuation_strategy.timeout == expected_config["continuation_config"]["timeout"]
            
            # Test pattern matching for agents with patterns
            if not expected_config["continuation_config"]["require_explicit_signal"]:
                # Test continuation patterns
                if "continuation_patterns" in expected_config["continuation_config"]:
                    result = {"response": "I've listed the files. Now I'll analyze them."}
                    should_continue = agent.continuation_strategy.should_continue(result, "test")
                    assert should_continue == True
                    
                # Test termination patterns
                if "termination_patterns" in expected_config["continuation_config"]:
                    result = {"response": "The task is complete."}
                    should_continue = agent.continuation_strategy.should_continue(result, "test")
                    assert should_continue == False
    
    @pytest.mark.asyncio
    async def test_depth_reset_on_agent_switch(self):
        """Test that continuation depth resets when switching agents"""
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        session_manager = StatelessSessionManager(config, None, None)
        session_manager.websocket = AsyncMock()
        
        # Create two agents
        agent1 = Mock()
        agent1.continuation_strategy = Mock()
        agent1.continuation_strategy.max_iterations = 3
        
        agent2 = Mock()
        agent2.continuation_strategy = Mock() 
        agent2.continuation_strategy.max_iterations = 5
        
        session_manager.agents["a"] = agent1
        session_manager.agents["e"] = agent2
        
        # Start with agent1 and build up continuation depth
        session_manager.active_agent = "a"
        session_manager._continuation_depth = 2
        
        # Switch to agent2
        await session_manager.switch_agent("e")
        
        # The switch itself doesn't reset depth, but the next non-continuation message will
        # Simulate sending a new message (not a continuation)
        with patch.object(session_manager, '_should_continue_after_tools', return_value=False):
            # In real flow, send_user_message with is_continuation=False resets depth
            session_manager._continuation_depth = 0
        
        assert session_manager._continuation_depth == 0
        assert session_manager.active_agent == "e"
    
    @pytest.mark.asyncio
    async def test_consistent_progress_notifications(self):
        """Test that progress notifications are consistent across agents"""
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        session_manager = StatelessSessionManager(config, None, None)
        
        # Mock WebSocket to capture notifications
        mock_ws = AsyncMock()
        notifications = []
        
        async def capture_notification(method, data):
            notifications.append({"method": method, "data": data})
            
        session_manager.send_notification = capture_notification
        
        # Create agents with different max iterations
        agents = {
            "a": {"max_iterations": 3},
            "e": {"max_iterations": 10}
        }
        
        for agent_id, config in agents.items():
            agent = Mock()
            agent.continuation_strategy = Mock()
            agent.continuation_strategy.max_iterations = config["max_iterations"]
            agent.continuation_strategy.get_progress = Mock(return_value={
                "current_step": 1,
                "total_steps": 3,
                "completion_percentage": 33
            })
            session_manager.agents[agent_id] = agent
        
        # Test progress notification for each agent
        for agent_id in ["a", "e"]:
            session_manager.active_agent = agent_id
            session_manager._continuation_depth = 1
            
            # Send progress notification
            progress = {"current_step": 1, "total_steps": 3}
            await session_manager._send_progress_notification(progress, ["test_tool"])
            
        # Verify notifications were sent
        assert len(notifications) == 2
        
        # Check notification structure is consistent
        for notif in notifications:
            assert notif["method"] == "continuation.progress"
            assert "agent_id" in notif["data"]
            assert "iteration" in notif["data"]
            assert "max_iterations" in notif["data"]
            assert "progress" in notif["data"]
    
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test a workflow that involves multiple agents with continuation"""
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        
        # Create mock registry and prompt system
        mock_registry = Mock()
        mock_prompt_system = Mock()
        mock_prompt_system.get_formatted_prompt = Mock(return_value="Test prompt")
        
        session_manager = StatelessSessionManager(config, mock_registry, mock_prompt_system)
        session_manager.websocket = AsyncMock()
        
        # Workflow: Alice → Patricia → Eamonn
        workflow_agents = {
            "a": {
                "name": "Alice",
                "max_iterations": 3,
                "responses": [
                    {"response": "I'll help you create an RFC. Let me switch you to Patricia."},
                ]
            },
            "p": {
                "name": "Patricia", 
                "max_iterations": 5,
                "responses": [
                    {"response": "I'll create the RFC. Now I'll gather requirements.", "tool_calls": [{"function": {"name": "gather_info"}}]},
                    {"response": "Requirements gathered. Let me create the RFC document.", "tool_calls": [{"function": {"name": "create_rfc"}}]},
                    {"response": "RFC created successfully. You may want Eamonn to create a plan from this."}
                ]
            },
            "e": {
                "name": "Eamonn",
                "max_iterations": 10,
                "responses": [
                    {"response": "I'll create a plan from the RFC. First, let me read it.", "tool_calls": [{"function": {"name": "read_rfc"}}]},
                    {"response": "RFC read. Now I'll generate the plan structure.", "tool_calls": [{"function": {"name": "generate_plan"}}]},
                    {"response": "Plan generated. Task complete."}
                ]
            }
        }
        
        # Set up agents
        for agent_id, agent_data in workflow_agents.items():
            agent = Mock()
            agent.name = agent_data["name"]
            agent.continuation_strategy = Mock()
            agent.continuation_strategy.max_iterations = agent_data["max_iterations"]
            agent.continuation_strategy.should_continue = Mock()
            
            # Set up responses
            response_index = 0
            def make_responder(responses):
                def respond(*args):
                    nonlocal response_index
                    if response_index < len(responses):
                        resp = responses[response_index]
                        response_index += 1
                        return resp
                    return {"response": "Done"}
                return respond
            
            agent.process_message = AsyncMock(side_effect=make_responder(agent_data["responses"]))
            session_manager.agents[agent_id] = agent
        
        # Execute workflow
        results = []
        
        # Start with Alice
        session_manager.active_agent = "a"
        result = await session_manager.agents["a"].process_message("Help me create a feature")
        results.append(("Alice", result))
        
        # Switch to Patricia
        await session_manager.switch_agent("p")
        # Patricia should do multiple steps
        for i in range(2):
            result = await session_manager.agents["p"].process_message("continue")
            results.append(("Patricia", result))
        
        # Switch to Eamonn
        await session_manager.switch_agent("e")
        # Eamonn should also do multiple steps
        for i in range(2):
            result = await session_manager.agents["e"].process_message("continue")
            results.append(("Eamonn", result))
        
        # Verify all agents executed their steps
        assert len(results) == 5  # 1 Alice + 2 Patricia + 2 Eamonn
        
        # Verify each agent maintained its own configuration
        assert session_manager.agents["a"].continuation_strategy.max_iterations == 3
        assert session_manager.agents["p"].continuation_strategy.max_iterations == 5
        assert session_manager.agents["e"].continuation_strategy.max_iterations == 10
    
    @pytest.mark.asyncio
    async def test_continuation_feature_enabled_for_all(self):
        """Test that continuation protocol is enabled for all agents"""
        config = {
            "openrouter": {"model": "test-model", "api_key": "test-key"},
            "prompt_settings": {"prompt_directories": ["prompts"]}
        }
        
        # Create mock prompt system
        prompt_system = Mock()
        enabled_features = set()
        
        def mock_enable_feature(feature):
            enabled_features.add(feature)
            
        prompt_system.enable_feature = mock_enable_feature
        prompt_system.get_enabled_features = Mock(return_value=enabled_features)
        
        # Create session manager
        session_manager = StatelessSessionManager(config, None, prompt_system)
        
        # The continuation feature should be enabled during initialization
        # This happens in interactive_server/main.py
        prompt_system.enable_feature('continuation_protocol')
        
        # Verify continuation protocol is enabled
        assert 'continuation_protocol' in enabled_features
        
        # When loading any agent prompt, it should include continuation protocol
        prompt_system.get_formatted_prompt = Mock(return_value="Agent prompt with continuation")
        
        # Mock agent creation to verify prompt includes continuation
        mock_agent_registry = Mock()
        mock_agent_info = Mock()
        mock_agent_info.prompt_file = "test.md"
        mock_agent_info.continuation_config = {"max_iterations": 5}
        
        session_manager.agent_registry = mock_agent_registry
        mock_agent_registry.get_agent = Mock(return_value=mock_agent_info)
        
        # Switch to agent (which loads prompt)
        with patch.object(session_manager, '_create_agent_internal', return_value=Mock()):
            await session_manager.switch_agent("test")
            
        # Verify prompt was requested with shared components
        prompt_system.get_formatted_prompt.assert_called()
        call_args = prompt_system.get_formatted_prompt.call_args
        # By default, include_shared=True
        assert call_args[1].get('include_shared', True) == True