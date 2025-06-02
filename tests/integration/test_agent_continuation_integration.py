"""Integration tests for agent continuation system."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.extensions.agents.continuation_strategy import ContinuationStrategy
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
from ai_whisperer.utils.path import PathManager
from interactive_server.stateless_session_manager import StatelessInteractiveSession


class TestAgentContinuationIntegration:
    """Test agent continuation system integration."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        websocket = AsyncMock()
        websocket.send_json = AsyncMock()
        return websocket
    
    @pytest.fixture
    def mock_path_manager(self):
        """Mock PathManager for testing."""
        with patch('ai_whisperer.utils.path.PathManager.get_instance') as mock_get_instance:
            mock_instance = Mock()
            mock_instance.prompt_path = Path(__file__).parent.parent.parent
            mock_instance.app_path = Path(__file__).parent.parent.parent
            mock_instance.workspace_path = Path(__file__).parent.parent.parent
            mock_instance.output_path = Path(__file__).parent.parent.parent / "output"
            mock_instance.resolve_path = lambda path: path
            mock_get_instance.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def prompt_system(self, mock_path_manager):
        """Create a PromptSystem instance."""
        config = PromptConfiguration({})
        return PromptSystem(config)
    
    @pytest.fixture
    def agent_config(self):
        """Create a test agent configuration."""
        return AgentConfig(
            name="test_agent",
            description="Test agent with continuation",
            system_prompt="You are a test agent.",
            model_name="openai/gpt-3.5-turbo",
            provider="openrouter",
            api_settings={"api_key": "test_key"},
            generation_params={},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
    
    @pytest.fixture
    def continuation_config(self):
        """Create continuation configuration."""
        return {
            'max_iterations': 3,
            'timeout': 60,
            'require_explicit_signal': True
        }
    
    @pytest.fixture
    def mock_ai_loop(self):
        """Create a mock AI loop."""
        ai_loop = Mock(spec=StatelessAILoop)
        # Don't use AsyncMock directly to avoid unawaited coroutine warnings
        return ai_loop
    
    @pytest.fixture
    def agent_with_continuation(self, agent_config, continuation_config, mock_ai_loop):
        """Create an agent with continuation strategy."""
        context = AgentContext(agent_id="test_agent", system_prompt="Test agent")
        
        # Create agent with continuation config in registry info
        agent_registry_info = Mock()
        agent_registry_info.continuation_config = continuation_config
        
        agent = StatelessAgent(agent_config, context, mock_ai_loop, agent_registry_info)
        
        # Verify continuation strategy was initialized
        assert agent.continuation_strategy is not None
        assert isinstance(agent.continuation_strategy, ContinuationStrategy)
        
        return agent
    
    @pytest.mark.asyncio
    async def test_continuation_strategy_initialization(self, agent_with_continuation):
        """Test that continuation strategy is properly initialized."""
        agent = agent_with_continuation
        
        # Check strategy configuration
        assert agent.continuation_strategy.max_iterations == 3
        assert agent.continuation_strategy.timeout == 60
        assert agent.continuation_strategy.require_explicit_signal is True
    
    def test_explicit_continuation_signal(self, agent_with_continuation):
        """Test that continuation strategy recognizes explicit signals."""
        agent = agent_with_continuation
        strategy = agent.continuation_strategy
        
        # Reset strategy
        strategy.reset()
        
        # Test response with explicit continuation signal
        response_with_continue = {
            'response': 'I need to continue with more steps.',
            'continuation': {
                'status': 'CONTINUE',
                'reason': 'More tools needed',
                'progress': {
                    'current_step': 1,
                    'total_steps': 3
                }
            },
            'tool_calls': [
                {'function': {'name': 'test_tool', 'arguments': {}}}
            ]
        }
        
        # Should continue
        assert strategy.should_continue(response_with_continue) is True
        
        # Test response with terminate signal
        response_with_terminate = {
            'response': 'Task completed.',
            'continuation': {
                'status': 'TERMINATE',
                'reason': 'All done'
            }
        }
        
        # Should not continue
        assert strategy.should_continue(response_with_terminate) is False
    
    @pytest.mark.asyncio
    async def test_session_manager_continuation_detection(self, mock_websocket, prompt_system):
        """Test session manager detects and handles continuation."""
        # Create session with mock dependencies
        config = {
            'openrouter': {
                'api_key': 'test_key',
                'model': 'openai/gpt-3.5-turbo'
            }
        }
        
        session = StatelessInteractiveSession(
            session_id="test_session",
            websocket=mock_websocket,
            config=config,
            prompt_system=prompt_system
        )
        
        # Create a mock agent with continuation strategy
        mock_agent = Mock()
        mock_agent.config = Mock(model_name='openai/gpt-3.5-turbo')
        mock_agent.continuation_strategy = ContinuationStrategy({'require_explicit_signal': True})
        mock_agent.continuation_strategy.reset()
        mock_agent.context = Mock(_context={})
        
        # Mock process_message to return continuation signal
        async def mock_process_message(msg, **kwargs):
            return {
                'response': 'Processing...',
                'continuation': {'status': 'CONTINUE', 'reason': 'Need more steps'},
                'tool_calls': [{'function': {'name': 'test_tool'}}]
            }
        
        mock_agent.process_message = mock_process_message
        
        # Add agent to session
        session.agents['test'] = mock_agent
        session.active_agent = 'test'
        session.is_started = True
        
        # Test continuation detection
        result = {
            'response': 'Step 1 complete',
            'continuation': {'status': 'CONTINUE'},
            'tool_calls': [{'function': {'name': 'tool1'}}]
        }
        
        should_continue = await session._should_continue_after_tools(result, "test message")
        assert should_continue is True
    
    @pytest.mark.asyncio
    async def test_continuation_progress_notification(self, mock_websocket):
        """Test that progress notifications are sent during continuation."""
        config = {'openrouter': {'api_key': 'test', 'model': 'test'}}
        
        session = StatelessInteractiveSession(
            session_id="test_session",
            websocket=mock_websocket,
            config=config
        )
        
        # Create mock agent with continuation strategy
        mock_agent = Mock()
        continuation_strategy = ContinuationStrategy()
        continuation_strategy.reset()
        continuation_strategy._iteration_count = 2
        
        mock_agent.continuation_strategy = continuation_strategy
        mock_agent.context = Mock(_context={'continuation_history': []})
        
        session.agents['test'] = mock_agent
        session.active_agent = 'test'
        
        # Mock the send_user_message to prevent actual execution
        with patch.object(session, 'send_user_message', new_callable=AsyncMock):
            # Simulate continuation flow
            session._continuation_depth = 1
            
            # Check that notification would be sent
            # (In actual flow, this happens inside the continuation logic)
            progress = continuation_strategy.get_progress(mock_agent.context._context)
            
            await session.send_notification("continuation.progress", {
                "agent_id": "test",
                "iteration": 1,
                "progress": progress
            })
            
            # Verify notification was sent
            mock_websocket.send_json.assert_called()
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args['method'] == 'continuation.progress'
            assert call_args['params']['agent_id'] == 'test'
    
    def test_continuation_safety_limits(self, agent_with_continuation):
        """Test that safety limits prevent infinite continuation."""
        agent = agent_with_continuation
        strategy = agent.continuation_strategy
        
        # Reset and set up for testing
        strategy.reset()
        
        # Test iteration limit
        # The limit check happens BEFORE incrementing, so we need to be past the limit
        strategy._iteration_count = 10  # Past max of 3
        result = {'continuation': {'status': 'CONTINUE'}}
        
        assert strategy.should_continue(result) is False
        
        # Test timeout
        strategy.reset()  # Reset to get a valid start time
        # Set start time to a value that will trigger timeout
        import time
        strategy._start_time = time.time() - 3600  # 1 hour ago (timeout is 60 seconds)
        
        assert strategy.should_continue(result) is False
    
    def test_continuation_context_update(self, agent_with_continuation):
        """Test that context is properly updated during continuation."""
        agent = agent_with_continuation
        strategy = agent.continuation_strategy
        
        # Reset strategy
        strategy.reset()
        
        # Create test response with continuation
        response = {
            'response': 'Step 1 complete',
            'continuation': {
                'status': 'CONTINUE',
                'reason': 'More steps needed',
                'progress': {
                    'current_step': 1,
                    'total_steps': 3,
                    'steps_completed': ['Initialize'],
                    'steps_remaining': ['Process', 'Finalize']
                }
            },
            'tool_calls': [{'function': {'name': 'test_tool'}}]
        }
        
        # Update context
        context = {}
        updated_context = strategy.update_context(context, response)
        
        # Verify context was updated
        assert 'continuation_history' in updated_context
        assert len(updated_context['continuation_history']) == 1
        assert 'progress' in updated_context
        assert updated_context['progress']['current_step'] == 1
        assert updated_context['progress']['total_steps'] == 3
    
    @pytest.mark.asyncio
    async def test_prompt_system_continuation_injection(self, prompt_system):
        """Test that continuation protocol is injected into agent prompts."""
        # Enable continuation feature
        prompt_system.enable_feature('continuation_protocol')
        
        # Mock a simple agent prompt
        with patch.object(prompt_system, 'get_prompt') as mock_get_prompt:
            mock_prompt = Mock()
            mock_prompt.content = "You are a test agent."
            mock_get_prompt.return_value = mock_prompt
            
            # Get formatted prompt with shared components
            formatted = prompt_system.get_formatted_prompt(
                category='agents',
                name='test_agent',
                include_shared=True
            )
            
            # Verify continuation protocol was included
            # The actual format includes "CONTINUATION_PROTOCOL INSTRUCTIONS"
            assert 'CONTINUATION_PROTOCOL INSTRUCTIONS' in formatted
            # Check for actual content from the continuation protocol
            assert 'When responding, you MUST include a "continuation" field' in formatted