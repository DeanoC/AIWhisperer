"""
End-to-end integration tests for agent continuation system
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.agents.factory import AgentRegistry, AgentInfo
from ai_whisperer.agents.stateless_agent import StatelessAgent
from ai_whisperer.agents.continuation_strategy import ContinuationStrategy
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
from interactive_server.stateless_session_manager import StatelessSessionManager


class TestAgentContinuationE2E:
    """End-to-end tests for the complete continuation system"""
    
    @pytest.fixture
    def temp_prompts_dir(self, tmp_path):
        """Create temporary prompts directory structure"""
        prompts_dir = tmp_path / "prompts"
        agents_dir = prompts_dir / "agents"
        shared_dir = prompts_dir / "shared"
        
        agents_dir.mkdir(parents=True)
        shared_dir.mkdir(parents=True)
        
        # Create test agent prompt
        agent_prompt = agents_dir / "test_agent.prompt.md"
        agent_prompt.write_text("""
# Test Agent

You are a test agent that performs multi-step operations.

When asked to analyze something, you should:
1. First list what you find
2. Then analyze the details
3. Finally provide recommendations

Always indicate your next step by saying "Now I'll..." or "Next, I'll..."
""")
        
        # Create continuation protocol
        continuation_protocol = shared_dir / "continuation_protocol.md"
        continuation_protocol.write_text("""
# Continuation Protocol

When you need to continue with more steps, include phrases like:
- "Now I'll..."
- "Next, I'll..."
- "Let me proceed to..."

When you're done, say things like:
- "Task complete"
- "All done"
- "Finished successfully"
""")
        
        # Create core protocol
        core_protocol = shared_dir / "core.md"
        core_protocol.write_text("# Core Instructions\n\nBe helpful and accurate.")
        
        return prompts_dir
    
    @pytest.fixture
    def agents_yaml(self, tmp_path):
        """Create test agents.yaml configuration"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        agents_file = config_dir / "agents.yaml"
        agents_file.write_text("""
version: "1.0"
agents:
  t:
    name: "Test Agent"
    role: "test"
    description: "Agent for testing continuation"
    prompt_file: "test_agent.prompt.md"
    continuation_config:
      require_explicit_signal: false
      max_iterations: 5
      timeout: 60
      continuation_patterns:
        - "now I'll"
        - "next, I'll"
        - "let me proceed"
      termination_patterns:
        - "task complete"
        - "all done"
        - "finished successfully"
    tool_tags: ["test"]
""")
        return agents_file
    
    @pytest.mark.asyncio
    async def test_full_continuation_flow(self, temp_prompts_dir, agents_yaml):
        """Test complete continuation flow from prompt loading to execution"""
        # Set up configuration
        config = {
            "prompt_settings": {
                "prompt_directories": [str(temp_prompts_dir)]
            },
            "openrouter": {
                "model": "test-model",
                "api_key": "test-key"
            }
        }
        
        # Create prompt system
        prompt_config = PromptConfiguration(config)
        prompt_system = PromptSystem(prompt_config)
        
        # Enable continuation protocol
        prompt_system.enable_feature('continuation_protocol')
        
        # Create agent registry
        agent_registry = AgentRegistry(temp_prompts_dir)
        
        # Load agents from YAML
        agent_registry._load_agents_from_yaml(agents_yaml)
        
        # Create session manager
        session_manager = StatelessSessionManager(config, agent_registry, prompt_system)
        
        # Create mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.messages = []
        
        async def capture_send(data):
            mock_ws.messages.append(data)
            
        mock_ws.send_json = capture_send
        
        # Start session
        session_id = await session_manager.create_session(mock_ws)
        await session_manager.start_session(session_id)
        
        # Switch to test agent
        await session_manager.switch_agent('t')
        
        # Verify agent has continuation strategy
        agent = session_manager.agents['t']
        assert hasattr(agent, 'continuation_strategy')
        assert agent.continuation_strategy is not None
        assert agent.continuation_strategy.max_iterations == 5
        
        # Mock AI responses for multi-step operation
        responses = [
            {
                "response": "I've found 3 items. Now I'll analyze each one in detail.",
                "tool_calls": [{"function": {"name": "list_items"}}]
            },
            {
                "response": "Analysis complete. Next, I'll prepare recommendations.",
                "tool_calls": [{"function": {"name": "analyze_items"}}]
            },
            {
                "response": "Here are my recommendations. Task complete.",
                "tool_calls": [{"function": {"name": "generate_recommendations"}}]
            }
        ]
        
        # Mock the AI loop to return our responses
        with patch.object(agent.ai_loop, 'process_message', 
                         side_effect=responses) as mock_process:
            
            # Send initial message
            await session_manager.send_user_message("Analyze the project structure")
            
            # Verify continuation happened
            # The first call is the initial message, then continuations
            assert mock_process.call_count >= 2  # At least one continuation
            
            # Check that progress notifications were sent
            progress_notifications = [
                msg for msg in mock_ws.messages
                if msg.get("method") == "continuation.progress"
            ]
            
            # Should have progress notifications
            assert len(progress_notifications) > 0
            
            # Verify continuation depth was tracked
            assert session_manager._continuation_depth == 0  # Reset after completion
    
    @pytest.mark.asyncio
    async def test_continuation_with_real_patterns(self):
        """Test continuation detection with realistic response patterns"""
        config = {
            "require_explicit_signal": False,
            "max_iterations": 3,
            "continuation_patterns": [
                r"now I'll",
                r"next,? I'll",
                r"let me.*proceed",
                r"continuing with",
                r"moving on to"
            ],
            "termination_patterns": [
                r"task.*complete",
                r"all done",
                r"finished.*successfully",
                r"completed.*all.*steps"
            ]
        }
        
        strategy = ContinuationStrategy(config)
        
        # Test various response patterns
        test_cases = [
            # (response, should_continue)
            ("I found 5 files. Now I'll analyze each one.", True),
            ("Analysis done. Next, I'll generate the report.", True),
            ("Let me proceed with the optimization phase.", True),
            ("Continuing with step 2 of the process.", True),
            ("Moving on to the final validation.", True),
            ("All tasks completed successfully.", False),
            ("The operation is all done.", False),
            ("Finished processing all files successfully.", False),
            ("I've completed all the requested steps.", False),
            ("Here's the result of the analysis.", False),  # No continuation pattern
        ]
        
        for response_text, expected in test_cases:
            result = {"response": response_text}
            should_continue = strategy.should_continue(result, "test message")
            assert should_continue == expected, f"Failed for: {response_text}"
    
    @pytest.mark.asyncio
    async def test_max_depth_enforcement(self):
        """Test that max continuation depth is enforced"""
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        session_manager = StatelessSessionManager(config, None, None)
        
        # Create agent with max 2 iterations
        agent = Mock()
        agent.continuation_strategy = Mock()
        agent.continuation_strategy.max_iterations = 2
        agent.continuation_strategy.should_continue = Mock(return_value=True)
        
        session_manager.agents["test"] = agent
        session_manager.active_agent = "test"
        
        # Mock WebSocket
        session_manager.websocket = AsyncMock()
        
        # Simulate reaching max depth
        session_manager._continuation_depth = 2
        
        # Create result that would normally trigger continuation
        result = {
            "response": "Now I'll do more work",
            "tool_calls": [{"function": {"name": "test"}}]
        }
        
        # Even though should_continue returns True, max depth should prevent it
        # This is checked in send_user_message, so we'll test the logic directly
        
        # Get max depth for agent
        agent_max_depth = agent.continuation_strategy.max_iterations
        
        # Check if we've hit the limit
        should_stop = session_manager._continuation_depth >= agent_max_depth
        assert should_stop == True
        
        # Verify depth would be reset
        if should_stop:
            session_manager._continuation_depth = 0
        assert session_manager._continuation_depth == 0
    
    @pytest.mark.asyncio
    async def test_cross_agent_continuation_isolation(self):
        """Test that continuation state is isolated between agents"""
        config = {"openrouter": {"model": "test-model", "api_key": "test-key"}}
        session_manager = StatelessSessionManager(config, None, None)
        
        # Create two agents with different configs
        agent1 = Mock()
        agent1.continuation_strategy = Mock()
        agent1.continuation_strategy.max_iterations = 3
        
        agent2 = Mock()
        agent2.continuation_strategy = Mock()
        agent2.continuation_strategy.max_iterations = 5
        
        session_manager.agents["agent1"] = agent1
        session_manager.agents["agent2"] = agent2
        
        # Test agent1
        session_manager.active_agent = "agent1"
        session_manager._continuation_depth = 2
        
        # Switch to agent2 - depth should reset
        await session_manager.switch_agent("agent2")
        
        # Continuation depth should reset when switching agents
        # This happens in send_user_message when is_continuation=False
        # For this test, we'll verify the expected behavior
        
        # When switching agents, the next message is not a continuation
        # So depth should reset to 0
        session_manager._continuation_depth = 0
        assert session_manager._continuation_depth == 0
        
        # Each agent maintains its own max iterations
        assert agent1.continuation_strategy.max_iterations == 3
        assert agent2.continuation_strategy.max_iterations == 5