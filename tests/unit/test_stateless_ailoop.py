"""
Tests for the new stateless AILoop interface.
This tests the process_with_context() method that will allow AILoop
to be used without delegates and with direct return values.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.context.provider import ContextProvider


class TestStatelessAILoop:
    """Test the new stateless AILoop interface."""
    
    @pytest.fixture
    def mock_context_provider(self):
        """Create a mock context provider."""
        provider = Mock(spec=ContextProvider)
        provider.retrieve_messages.return_value = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]
        provider.store_message = Mock()
        provider.set_metadata = Mock()
        provider.get_metadata = Mock(return_value=None)
        return provider
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        service = Mock()
        
        # Create a mock stream response
        async def mock_stream():
            # Mock streaming chunks
            from types import SimpleNamespace
            
            yield SimpleNamespace(
                delta_content="Hello ",
                delta_tool_call_part=None,
                finish_reason=None
            )
            yield SimpleNamespace(
                delta_content="there!",
                delta_tool_call_part=None,
                finish_reason=None
            )
            yield SimpleNamespace(
                delta_content="",
                delta_tool_call_part=None,
                finish_reason="stop"
            )
        
        service.stream_chat_completion = AsyncMock(return_value=mock_stream())
        return service
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock AI config."""
        return AIConfig(
            api_key="test-key",
            model_id="gpt-4",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
    
    @pytest.mark.asyncio
    async def test_process_with_context_simple_response(self, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context returns AI response directly."""
        # Import will fail since we haven't created the new interface yet
        # This is TDD - we write the test first
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process a message with context
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=mock_context_provider
        )
        
        # Verify the result structure
        assert result['response'] == "Hello there!"
        assert result['finish_reason'] == "stop"
        assert result['tool_calls'] is None
        
        # Verify context was updated
        mock_context_provider.store_message.assert_called()
        stored_calls = mock_context_provider.store_message.call_args_list
        assert len(stored_calls) == 2  # User message + AI response
        
        # Check user message was stored
        assert stored_calls[0][0][0]['role'] == 'user'
        assert stored_calls[0][0][0]['content'] == 'Hello'
        
        # Check AI response was stored
        assert stored_calls[1][0][0]['role'] == 'assistant'
        assert stored_calls[1][0][0]['content'] == 'Hello there!'
    
    @pytest.mark.asyncio
    async def test_process_with_context_streaming(self, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context with streaming callback."""
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Track streaming chunks
        chunks = []
        async def on_chunk(chunk):
            chunks.append(chunk)
        
        # Process with streaming callback
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=mock_context_provider,
            on_stream_chunk=on_chunk
        )
        
        # Verify chunks were received
        assert len(chunks) == 3  # Including final empty chunk
        assert chunks[0] == "Hello "
        assert chunks[1] == "there!"
        assert chunks[2] == ""  # Final chunk
        
        # Verify final result
        assert result['response'] == "Hello there!"
    
    @pytest.mark.asyncio
    async def test_process_with_context_tool_calls(self, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context with tool calls."""
        # Setup AI service to return tool calls
        async def mock_stream_with_tools():
            from types import SimpleNamespace
            import json
            
            yield SimpleNamespace(
                delta_content="I'll help you with that.",
                delta_tool_call_part=None,
                finish_reason=None
            )
            
            tool_calls = [{
                "id": "call_123",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "London"}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="",
                delta_tool_call_part=json.dumps({"tool_calls": tool_calls}),
                finish_reason="tool_calls"
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_tools())
        
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message
        result = await ai_loop.process_with_context(
            message="What's the weather in London?",
            context_provider=mock_context_provider
        )
        
        # Verify tool calls in result
        assert result['finish_reason'] == "tool_calls"
        assert result['tool_calls'] is not None
        assert len(result['tool_calls']) == 1
        assert result['tool_calls'][0]['function']['name'] == "get_weather"
        
        # Verify message with tool calls was stored
        stored_calls = mock_context_provider.store_message.call_args_list
        assert len(stored_calls) == 2
        
        # Check AI message has tool_calls
        ai_message = stored_calls[1][0][0]
        assert ai_message['role'] == 'assistant'
        assert 'tool_calls' in ai_message
    
    @pytest.mark.asyncio
    async def test_process_with_context_no_delegates(self, mock_config, mock_ai_service, mock_context_provider):
        """Test that process_with_context works without any delegate manager."""
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        # Create AILoop without delegate manager
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Should not have delegate_manager attribute
        assert not hasattr(ai_loop, 'delegate_manager')
        
        # Process should work fine
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=mock_context_provider
        )
        
        assert result['response'] == "Hello there!"
    
    @pytest.mark.asyncio
    async def test_process_with_context_error_handling(self, mock_config, mock_ai_service, mock_context_provider):
        """Test error handling in process_with_context."""
        # Make AI service raise an error
        mock_ai_service.stream_chat_completion = AsyncMock(
            side_effect=Exception("AI Service Error")
        )
        
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process should handle error gracefully
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=mock_context_provider
        )
        
        # Should return error in result
        assert result['error'] is not None
        assert "AI Service Error" in str(result['error'])
        assert result['response'] is None
        
        # Error message should be stored in context
        stored_calls = mock_context_provider.store_message.call_args_list
        assert len(stored_calls) >= 2
        
        # Check error message was stored
        error_message = stored_calls[-1][0][0]
        assert error_message['role'] == 'assistant'
        assert 'error' in error_message['content'].lower()
    
    @pytest.mark.asyncio 
    async def test_process_with_context_timeout(self, mock_config, mock_ai_service, mock_context_provider):
        """Test timeout handling in process_with_context."""
        import asyncio
        
        # Make AI service hang
        async def mock_hanging_stream():
            await asyncio.sleep(10)  # Hang for 10 seconds
            yield None  # Never reached
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_hanging_stream())
        
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process with timeout
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=mock_context_provider,
            timeout=0.1  # 100ms timeout
        )
        
        # Should return timeout error
        assert result['error'] is not None
        assert 'timeout' in str(result['error']).lower()
        
        # Timeout message should be stored
        stored_calls = mock_context_provider.store_message.call_args_list
        error_message = stored_calls[-1][0][0]
        assert 'timeout' in error_message['content'].lower()
    
    @pytest.mark.asyncio
    async def test_process_with_context_custom_tools(self, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context with custom tool definitions."""
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Define custom tools
        custom_tools = [
            {
                "type": "function",
                "function": {
                    "name": "custom_tool",
                    "description": "A custom tool",
                    "parameters": {}
                }
            }
        ]
        
        # Process with custom tools
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=mock_context_provider,
            tools=custom_tools
        )
        
        # Verify custom tools were passed to AI service
        mock_ai_service.stream_chat_completion.assert_called_once()
        call_args = mock_ai_service.stream_chat_completion.call_args
        assert call_args[1]['tools'] == custom_tools
    
    @pytest.mark.asyncio
    async def test_process_with_context_without_storing(self, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context can skip storing messages."""
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process without storing
        result = await ai_loop.process_with_context(
            message="Hello",
            context_provider=mock_context_provider,
            store_messages=False
        )
        
        # Should still get result
        assert result['response'] == "Hello there!"
        
        # But messages should not be stored
        mock_context_provider.store_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_direct_process_without_context(self, mock_config, mock_ai_service):
        """Test direct processing without context provider."""
        from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process with explicit messages instead of context provider
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        
        result = await ai_loop.process_messages(messages)
        
        # Should get result
        assert result['response'] == "Hello there!"
        
        # Verify correct messages were sent to AI
        mock_ai_service.stream_chat_completion.assert_called_once()
        call_args = mock_ai_service.stream_chat_completion.call_args
        assert call_args[1]['messages'] == messages