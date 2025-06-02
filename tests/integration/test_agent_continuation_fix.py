"""Test to verify agent continuation works after fixing the order of checks."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from ai_whisperer.agents.stateless_agent import StatelessAgent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.agents.continuation_strategy import ContinuationStrategy
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
from interactive_server.stateless_session_manager import StatelessInteractiveSession


class TestAgentContinuationFix:
    """Test the fixed continuation logic."""
    
    @pytest.fixture
    def single_tool_agent_config(self):
        """Create a config for a single-tool model agent."""
        return AgentConfig(
            name="test_single_tool_agent",
            description="Test agent using single-tool model",
            system_prompt="You are a test agent.",
            model_name="google/gemini-2.5-flash-preview-05-20:thinking",  # Single-tool model
            provider="openrouter",
            api_settings={"api_key": "test_key"},
            generation_params={},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        websocket = AsyncMock()
        websocket.send_json = AsyncMock()
        return websocket
    
    @pytest.fixture
    def session_with_continuation(self, mock_websocket):
        """Create a session with continuation enabled."""
        config = {'openrouter': {'api_key': 'test', 'model': 'google/gemini-2.5-flash-preview-05-20:thinking'}}
        
        session = StatelessInteractiveSession(
            session_id="test_session",
            websocket=mock_websocket,
            config=config
        )
        
        # Create mock agent with continuation strategy
        mock_agent = Mock()
        mock_agent.config = Mock(model_name='google/gemini-2.5-flash-preview-05-20:thinking')
        
        # Initialize continuation strategy
        continuation_strategy = ContinuationStrategy({'require_explicit_signal': True})
        continuation_strategy.reset()
        mock_agent.continuation_strategy = continuation_strategy
        
        # Add to session
        session.agents['test'] = mock_agent
        session.active_agent = 'test'
        
        return session
    
    @pytest.mark.asyncio
    async def test_continuation_strategy_checked_before_model_capability(self, session_with_continuation):
        """Test that continuation strategy is checked BEFORE model capability check."""
        session = session_with_continuation
        
        # Create a response with explicit CONTINUE signal
        result = {
            'response': 'I need to continue with more analysis.',
            'continuation': {
                'status': 'CONTINUE',
                'reason': 'Need to analyze more files'
            },
            'tool_calls': [{'function': {'name': 'read_file', 'arguments': {'path': 'test.py'}}}]
        }
        
        # Test continuation detection
        should_continue = await session._should_continue_after_tools(result, "analyze the project")
        
        # Should return True because continuation strategy detects the CONTINUE signal
        # even though it's a single-tool model
        assert should_continue is True
    
    @pytest.mark.asyncio
    async def test_no_continuation_without_explicit_signal(self, session_with_continuation):
        """Test that single-tool models don't continue without explicit signal."""
        session = session_with_continuation
        
        # Response WITHOUT continuation signal
        result = {
            'response': 'I found the file content.',
            'tool_calls': [{'function': {'name': 'read_file', 'arguments': {'path': 'test.py'}}}]
        }
        
        # Test continuation detection
        should_continue = await session._should_continue_after_tools(result, "read test.py")
        
        # Should return False because there's no explicit continuation signal
        assert should_continue is False
    
    @pytest.mark.asyncio
    async def test_terminate_signal_stops_continuation(self, session_with_continuation):
        """Test that TERMINATE signal prevents continuation."""
        session = session_with_continuation
        
        # Response with explicit TERMINATE signal
        result = {
            'response': 'I have completed the analysis.',
            'continuation': {
                'status': 'TERMINATE',
                'reason': 'Analysis complete'
            },
            'tool_calls': [{'function': {'name': 'read_file', 'arguments': {'path': 'test.py'}}}]
        }
        
        # Test continuation detection
        should_continue = await session._should_continue_after_tools(result, "analyze test.py")
        
        # Should return False because of TERMINATE signal
        assert should_continue is False
    
    def test_agent_gets_continuation_strategy_from_config(self, single_tool_agent_config):
        """Test that agents initialize continuation strategy from registry config."""
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
        agent = StatelessAgent(single_tool_agent_config, context, ai_loop, agent_registry_info)
        
        # Verify continuation strategy was created
        assert agent.continuation_strategy is not None
        assert isinstance(agent.continuation_strategy, ContinuationStrategy)
        assert agent.continuation_strategy.require_explicit_signal is True
        assert agent.continuation_strategy.max_iterations == 5
        assert agent.continuation_strategy.timeout == 300