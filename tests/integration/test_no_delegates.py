"""
Integration tests to verify the system works without delegates.
This ensures that all functionality is preserved when delegates are removed.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.agents.stateless_agent import StatelessAgent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext
from interactive_server.streaming_session import StreamingSession


class TestNoDelegates:
    """Test that the system works without any delegate dependencies."""
    
    @pytest.fixture
    def ai_config(self):
        """Create AI configuration."""
        return AIConfig(
            api_key="test-key",
            model_id="gpt-4",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        service = Mock(spec=OpenRouterAIService)
        
        async def mock_stream():
            from types import SimpleNamespace
            yield SimpleNamespace(delta_content="Test ", delta_tool_call_part=None, finish_reason=None)
            yield SimpleNamespace(delta_content="response", delta_tool_call_part=None, finish_reason=None)
            yield SimpleNamespace(delta_content="", delta_tool_call_part=None, finish_reason="stop")
        
        service.stream_chat_completion = AsyncMock(return_value=mock_stream())
        return service
    
    @pytest.mark.asyncio
    async def test_stateless_ailoop_no_delegates(self, ai_config, mock_ai_service):
        """Test StatelessAILoop works without delegates."""
        # Create stateless AI loop
        ai_loop = StatelessAILoop(config=ai_config, ai_service=mock_ai_service)
        
        # Should not have delegate_manager
        assert not hasattr(ai_loop, 'delegate_manager')
        
        # Create context
        context = AgentContext(agent_id="test")
        context.store_message({"role": "system", "content": "You are helpful"})
        
        # Process message
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=context
        )
        
        # Should work without delegates
        assert result['response'] == "Test response"
        assert result['finish_reason'] == "stop"
    
    @pytest.mark.asyncio
    async def test_stateless_agent_no_delegates(self, ai_config, mock_ai_service):
        """Test StatelessAgent works without delegates."""
        # Create components
        ai_loop = StatelessAILoop(config=ai_config, ai_service=mock_ai_service)
        context = AgentContext(agent_id="test-agent")
        config = AgentConfig(
            name="test-agent",
            description="Test agent",
            system_prompt="You are helpful",
            model_name="gpt-4",
            provider="openai",
            api_settings={"api_key": "test"},
            generation_params={"temperature": 0.7, "max_tokens": 1000}
        )
        
        # Create agent
        agent = StatelessAgent(config=config, context=context, ai_loop=ai_loop)
        
        # Should not have delegate references
        assert not hasattr(agent, 'delegate_manager')
        
        # Process message
        result = await agent.process_message("Hello")
        assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_streaming_session_no_delegates(self):
        """Test StreamingSession works without delegates."""
        # Mock WebSocket
        mock_ws = Mock()
        mock_ws.send_json = AsyncMock()
        
        # Create session
        session = StreamingSession(
            session_id="test-123",
            websocket=mock_ws,
            config={
                "openrouter": {
                    "api_key": "test-key",
                    "model": "gpt-4",
                    "params": {"temperature": 0.7, "max_tokens": 1000}
                }
            }
        )
        
        # Should not have delegate_bridge
        assert not hasattr(session, 'delegate_bridge')
        assert not hasattr(session, 'delegate_manager')
        
        # Create agent
        agent = await session.create_agent("test", "You are helpful")
        assert isinstance(agent, StatelessAgent)
    
    @pytest.mark.asyncio
    async def test_end_to_end_no_delegates(self):
        """Test complete flow without delegates."""
        # Mock WebSocket
        mock_ws = Mock()
        notifications = []
        
        async def capture_notification(data):
            notifications.append(data)
        
        mock_ws.send_json = AsyncMock(side_effect=capture_notification)
        
        # Create session
        session = StreamingSession(
            session_id="test-e2e",
            websocket=mock_ws,
            config={
                "openrouter": {
                    "api_key": "test-key",
                    "model": "gpt-4",
                    "params": {"temperature": 0.7, "max_tokens": 1000}
                }
            }
        )
        
        # Create agent
        await session.create_agent("assistant", "You are a helpful assistant")
        
        # Mock the AI loop response
        with patch.object(session._ai_loop, 'process_with_context', new_callable=AsyncMock) as mock_process:
            # Set up streaming response
            async def mock_stream_response(**kwargs):
                if kwargs.get('on_stream_chunk'):
                    await kwargs['on_stream_chunk']("Hello ")
                    await kwargs['on_stream_chunk']("there!")
                return {
                    'response': 'Hello there!',
                    'finish_reason': 'stop',
                    'tool_calls': None,
                    'error': None
                }
            
            mock_process.side_effect = mock_stream_response
            
            # Send message
            result = await session.send_message("Hi", agent_id="assistant")
        
        # Verify response
        assert result['success'] is True
        assert result['response'] == "Hello there!"
        
        # Verify notifications were sent
        assert len(notifications) >= 3  # At least 2 chunks + final
        
        # Check chunk notifications
        chunk_notifs = [n for n in notifications if n.get('method') == 'AIMessageChunkNotification']
        assert len(chunk_notifs) >= 3
        assert any(n['params']['chunk'] == 'Hello ' for n in chunk_notifs)
        assert any(n['params']['chunk'] == 'there!' for n in chunk_notifs)
        assert any(n['params']['isFinal'] is True for n in chunk_notifs)
    
    @pytest.mark.asyncio
    async def test_tool_calls_no_delegates(self):
        """Test tool call handling without delegates."""
        mock_ws = Mock()
        notifications = []
        mock_ws.send_json = AsyncMock(side_effect=lambda d: notifications.append(d))
        
        session = StreamingSession(
            session_id="test-tools",
            websocket=mock_ws,
            config={
                "openrouter": {
                    "api_key": "test-key",
                    "model": "gpt-4",
                    "params": {"temperature": 0.7, "max_tokens": 1000}
                }
            }
        )
        
        await session.create_agent("assistant", "You are helpful")
        
        # Mock tool call response
        with patch.object(session._ai_loop, 'process_with_context', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                'response': 'Let me check that.',
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
            
            result = await session.send_message("What's the weather?")
        
        # Verify tool calls handled
        assert result['tool_calls'] is not None
        assert len(result['tool_calls']) == 1
        
        # Check tool notifications
        tool_notifs = [n for n in notifications if n.get('method') == 'ToolCallNotification']
        assert len(tool_notifs) == 1
        assert tool_notifs[0]['params']['toolName'] == 'get_weather'
    
    @pytest.mark.asyncio
    async def test_error_handling_no_delegates(self):
        """Test error handling without delegates."""
        mock_ws = Mock()
        notifications = []
        mock_ws.send_json = AsyncMock(side_effect=lambda d: notifications.append(d))
        
        session = StreamingSession(
            session_id="test-error",
            websocket=mock_ws,
            config={
                "openrouter": {
                    "api_key": "test-key",
                    "model": "gpt-4",
                    "params": {"temperature": 0.7, "max_tokens": 1000}
                }
            }
        )
        
        await session.create_agent("assistant", "You are helpful")
        
        # Mock error response
        with patch.object(session._ai_loop, 'process_with_context', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                'response': None,
                'finish_reason': 'error',
                'tool_calls': None,
                'error': Exception("Test error")
            }
            
            result = await session.send_message("Hello")
        
        # Should handle error
        assert result['success'] is True  # Session continues
        assert result['response'] is None
        
        # Check error notification
        error_notifs = [n for n in notifications if n.get('method') == 'SessionStatusNotification' 
                       and n.get('params', {}).get('status') == 3]  # SessionStatus.Error = 3
        assert len(error_notifs) > 0
    
    def test_no_delegate_imports_in_stateless_modules(self):
        """Verify stateless modules don't import delegates."""
        # Check StatelessAILoop
        import ai_whisperer.ai_loop.stateless_ai_loop as sal
        module_dict = sal.__dict__
        assert 'DelegateManager' not in module_dict
        assert 'delegate_manager' not in str(module_dict)
        
        # Check StatelessAgent  
        import ai_whisperer.agents.stateless_agent as sa
        module_dict = sa.__dict__
        assert 'DelegateManager' not in module_dict
        assert 'delegate_manager' not in str(module_dict)
        
        # Check StreamingSession
        import interactive_server.streaming_session as ss
        module_dict = ss.__dict__
        assert 'DelegateBridge' not in module_dict
        assert 'delegate_bridge' not in str(module_dict)