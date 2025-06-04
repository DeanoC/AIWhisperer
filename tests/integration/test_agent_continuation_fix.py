"""Test to verify agent continuation works with the new AI-driven approach."""

import pytest
from unittest.mock import Mock, AsyncMock

from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.extensions.agents.continuation_strategy import ContinuationStrategy
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.services.execution.ai_loop import StatelessAILoop


class TestAgentContinuationFix:
    """Test the new AI-driven continuation logic."""
    
    @pytest.fixture
    def agent_config(self):
        """Create a config for an agent."""
        return AgentConfig(
            name="test_agent",
            description="Test agent",
            system_prompt="You are a test agent.",
            model_name="openai/gpt-4",
            provider="openrouter",
            api_settings={"api_key": "test_key"},
            generation_params={},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
    
    def test_continuation_strategy_processes_ai_response(self):
        """Test that continuation strategy processes AI responses correctly."""
        strategy = ContinuationStrategy({'require_explicit_signal': True})
        
        # AI response with explicit continuation signal (structured output)
        ai_response = {
            'response': 'I need to analyze more files to complete this task.',
            'continuation': {
                'status': 'CONTINUE',
                'reason': 'Need to analyze additional files'
            }
        }
        
        # Strategy should detect the continuation signal from AI
        should_continue = strategy.should_continue(ai_response)
        assert should_continue is True
        
        # Extract continuation state
        state = strategy.extract_continuation_state(ai_response)
        assert state is not None
        assert state.status == 'CONTINUE'
        assert state.reason == 'Need to analyze additional files'
    
    def test_no_continuation_without_ai_signal(self):
        """Test that continuation doesn't happen without AI signal."""
        strategy = ContinuationStrategy({'require_explicit_signal': True})
        
        # AI response without continuation signal
        ai_response = {
            'response': 'I found the information you requested.',
            'tool_calls': [{'function': {'name': 'read_file', 'arguments': {'path': 'test.py'}}}]
        }
        
        # Should not continue without explicit signal
        should_continue = strategy.should_continue(ai_response)
        assert should_continue is False
    
    def test_terminate_signal_from_ai(self):
        """Test that AI TERMINATE signal stops continuation."""
        strategy = ContinuationStrategy({'require_explicit_signal': True})
        
        # AI response with explicit TERMINATE signal
        ai_response = {
            'response': 'I have completed the analysis.',
            'continuation': {
                'status': 'TERMINATE',
                'reason': 'Task completed successfully'
            }
        }
        
        # Should not continue with TERMINATE signal
        should_continue = strategy.should_continue(ai_response)
        assert should_continue is False
        
        # Extract continuation state
        state = strategy.extract_continuation_state(ai_response)
        assert state is not None
        assert state.status == 'TERMINATE'
        assert state.reason == 'Task completed successfully'
    
    def test_tools_return_data_not_continuation(self):
        """Test that tools return structured data without continuation logic."""
        # Mock a tool response - just data, no continuation
        tool_response = {
            "content": "File content here",
            "path": "test.py",
            "exists": True,
            "size": 1234
        }
        
        # Tool responses should not contain continuation signals
        assert 'continuation' not in tool_response
        assert 'CONTINUE' not in str(tool_response)
        assert 'TERMINATE' not in str(tool_response)
    
    def test_agent_continuation_strategy_initialization(self, agent_config):
        """Test that agents can be initialized with continuation strategy."""
        context = AgentContext(agent_id="test", system_prompt="Test")
        ai_loop = Mock(spec=StatelessAILoop)
        
        # Create registry info with continuation config
        agent_registry_info = Mock()
        agent_registry_info.continuation_config = {
            'require_explicit_signal': True,
            'max_iterations': 5,
            'timeout': 300
        }
        
        # Create agent
        agent = StatelessAgent(agent_config, context, ai_loop, agent_registry_info)
        
        # Verify continuation strategy was created with correct config
        assert agent.continuation_strategy is not None
        assert isinstance(agent.continuation_strategy, ContinuationStrategy)
        assert agent.continuation_strategy.require_explicit_signal is True
        assert agent.continuation_strategy.max_iterations == 5
        assert agent.continuation_strategy.timeout == 300