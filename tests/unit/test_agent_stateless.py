"""
Tests for Agent class using the new stateless AILoop interface.
This tests the refactored Agent that works without delegates.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop


class TestAgentWithStatelessAILoop:
    """Test Agent class with stateless AILoop."""
    
    @pytest.fixture
    def mock_agent_config(self):
        """Create a mock agent configuration."""
        return AgentConfig(
            name="test-agent",
            description="Test agent",
            system_prompt="You are a test assistant",
            model_name="gpt-4",
            provider="openai",
            api_settings={"api_key": "test-key"},
            generation_params={
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )
    
    @pytest.fixture
    def mock_agent_context(self):
        """Create a mock agent context."""
        context = Mock(spec=AgentContext)
        context.agent_id = "test-agent"
        context.retrieve_messages.return_value = [
            {"role": "system", "content": "You are a test assistant"}
        ]
        context.store_message = Mock()
        return context
    
    @pytest.fixture
    def mock_stateless_ai_loop(self):
        """Create a mock stateless AI loop."""
        ai_loop = Mock(spec=StatelessAILoop)
        ai_loop.process_with_context = AsyncMock(return_value={
            'response': 'Hello from AI!',
            'finish_reason': 'stop',
            'tool_calls': None,
            'error': None
        })
        return ai_loop
    
    def test_agent_creation_with_stateless_loop(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test creating an agent with stateless AI loop."""
        agent = Agent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        assert agent.config == mock_agent_config
        assert agent.context == mock_agent_context
        assert agent.ai_loop == mock_stateless_ai_loop
        
        # Should not have any delegate references
        assert not hasattr(agent, 'delegate_manager')
    
    @pytest.mark.asyncio
    async def test_agent_process_message_stateless(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test agent processing a message with stateless AILoop."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        agent = StatelessAgent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        # Process a message
        result = await agent.process_message("Hello")
        
        # Should use process_with_context
        mock_stateless_ai_loop.process_with_context.assert_called_once()
        call_args = mock_stateless_ai_loop.process_with_context.call_args
        assert call_args[1]['message'] == "Hello"
        assert call_args[1]['context_provider'] == mock_agent_context
        
        # Should return the AI response
        assert result == "Hello from AI!"
    
    @pytest.mark.asyncio
    async def test_agent_streaming_support(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test agent with streaming callback support."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        agent = StatelessAgent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        # Track streamed chunks
        chunks = []
        async def on_chunk(chunk):
            chunks.append(chunk)
        
        # Mock streaming response
        async def mock_process_stream(**kwargs):
            # Simulate streaming
            if kwargs.get('on_stream_chunk'):
                await kwargs['on_stream_chunk']("Hello ")
                await kwargs['on_stream_chunk']("from ")
                await kwargs['on_stream_chunk']("AI!")
            return {
                'response': 'Hello from AI!',
                'finish_reason': 'stop',
                'tool_calls': None,
                'error': None
            }
        
        mock_stateless_ai_loop.process_with_context.side_effect = mock_process_stream
        
        # Process with streaming
        result = await agent.process_message("Hello", on_stream_chunk=on_chunk)
        
        # Should have received chunks
        assert chunks == ["Hello ", "from ", "AI!"]
        assert result == "Hello from AI!"
    
    @pytest.mark.asyncio
    async def test_agent_tool_execution(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test agent handling tool calls."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        # Mock response with tool calls
        mock_stateless_ai_loop.process_with_context.return_value = {
            'response': 'Let me check that for you.',
            'finish_reason': 'tool_calls',
            'tool_calls': [{
                'id': 'call_123',
                'function': {
                    'name': 'get_weather',
                    'arguments': '{"location": "London"}'
                }
            }],
            'error': None
        }
        
        agent = StatelessAgent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        # Process message that triggers tool call
        result = await agent.process_message("What's the weather in London?")
        
        # Should return response and tool calls
        assert isinstance(result, dict)
        assert result['response'] == 'Let me check that for you.'
        assert result['tool_calls'] is not None
        assert len(result['tool_calls']) == 1
        assert result['tool_calls'][0]['function']['name'] == 'get_weather'
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test agent error handling."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        # Mock error response
        mock_stateless_ai_loop.process_with_context.return_value = {
            'response': None,
            'finish_reason': 'error',
            'tool_calls': None,
            'error': Exception("AI Service Error")
        }
        
        agent = StatelessAgent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        # Process message that causes error
        result = await agent.process_message("Hello")
        
        # Should handle error gracefully
        assert isinstance(result, dict)
        assert result['error'] is not None
        assert 'AI Service Error' in str(result['error'])
    
    @pytest.mark.asyncio
    async def test_agent_context_persistence(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test that agent properly stores messages in context."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        agent = StatelessAgent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        # Process multiple messages
        await agent.process_message("Hello")
        await agent.process_message("How are you?")
        
        # Should have called process_with_context twice
        assert mock_stateless_ai_loop.process_with_context.call_count == 2
        
        # Context should be passed each time
        for call in mock_stateless_ai_loop.process_with_context.call_args_list:
            assert call[1]['context_provider'] == mock_agent_context
    
    @pytest.mark.asyncio
    async def test_agent_custom_generation_params(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test agent using custom generation parameters."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        # Update config with custom params
        mock_agent_config.generation_params['temperature'] = 0.9
        mock_agent_config.generation_params['max_tokens'] = 2000
        
        agent = StatelessAgent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        # Process message with custom params
        await agent.process_message("Hello", temperature=0.5, max_tokens=500)
        
        # Should pass custom params to AI loop
        call_args = mock_stateless_ai_loop.process_with_context.call_args
        # Verify custom params override config defaults
        assert call_args[1].get('temperature') == 0.5
        assert call_args[1].get('max_tokens') == 500
    
    @pytest.mark.asyncio
    async def test_agent_no_session_management(self, mock_agent_config, mock_agent_context, mock_stateless_ai_loop):
        """Test that stateless agent doesn't manage sessions."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        agent = StatelessAgent(
            config=mock_agent_config,
            context=mock_agent_context,
            ai_loop=mock_stateless_ai_loop
        )
        
        # Should not have session-related methods
        assert not hasattr(agent, 'start_session')
        assert not hasattr(agent, 'stop_session')
        assert not hasattr(agent, '_session_task')
        
        # Process message should work without session
        result = await agent.process_message("Hello")
        assert result == "Hello from AI!"
    
    def test_agent_config_validation(self, mock_agent_context, mock_stateless_ai_loop):
        """Test agent validates configuration."""
        from ai_whisperer.agents.stateless_agent import StatelessAgent
        
        # Should raise error with None config
        with pytest.raises(ValueError, match="AgentConfig must not be None"):
            StatelessAgent(
                config=None,
                context=mock_agent_context,
                ai_loop=mock_stateless_ai_loop
            )
        
        # Should raise error with None context
        mock_config = Mock(spec=AgentConfig)
        with pytest.raises(ValueError, match="AgentContext must not be None"):
            StatelessAgent(
                config=mock_config,
                context=None,
                ai_loop=mock_stateless_ai_loop
            )
        
        # Should raise error with None AI loop
        with pytest.raises(ValueError, match="AILoop instance must not be None"):
            StatelessAgent(
                config=mock_config,
                context=mock_agent_context,
                ai_loop=None
            )