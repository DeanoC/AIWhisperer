"""
Tests for the new stateless AILoop interface.
This tests the process_with_context() method that will allow AILoop
to be used without delegates and with direct return values.
"""
import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.context.provider import ContextProvider
from ai_whisperer.services.execution.ai_loop import StatelessAILoop


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
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_simple_response(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context returns AI response directly."""
        # Mock tool registry to avoid socket warnings
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Import will fail since we haven't created the new interface yet
        # This is TDD - we write the test first
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_streaming(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context with streaming callback."""
        # Mock tool registry to avoid socket warnings
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_tool_calls(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context with tool calls."""
        # Mock tool registry
        mock_tool = Mock()
        mock_tool.execute.return_value = "Current weather in London: 15°C, partly cloudy"
        
        mock_registry = Mock()
        mock_registry.get_tool_by_name.return_value = mock_tool
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls
        async def mock_stream_with_tools():
            from types import SimpleNamespace
            import json
            
            yield SimpleNamespace(
                delta_content="I'll help you with that.",
                delta_tool_call_part=None,
                finish_reason=None
            )
            
            # Tool calls should be provided as a list, not JSON
            tool_call_chunk = [{
                "index": 0,
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "London"}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="",
                delta_tool_call_part=tool_call_chunk,
                finish_reason="tool_calls"
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_tools())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
        
        # Verify messages were stored (user, assistant with tool calls, and tool result)
        stored_calls = mock_context_provider.store_message.call_args_list
        assert len(stored_calls) == 3
        
        # Check user message
        user_message = stored_calls[0][0][0]
        assert user_message['role'] == 'user'
        assert user_message['content'] == "What's the weather in London?"
        
        # Check AI message has tool_calls
        ai_message = stored_calls[1][0][0]
        assert ai_message['role'] == 'assistant'
        assert 'tool_calls' in ai_message
        
        # Check tool result message
        tool_message = stored_calls[2][0][0]
        assert tool_message['role'] == 'tool'
        assert tool_message['name'] == 'get_weather'
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_no_delegates(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test that process_with_context works without any delegate manager."""
        # Mock tool registry to avoid socket warnings
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_error_handling(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test error handling in process_with_context."""
        # Mock tool registry
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Make AI service raise an error
        mock_ai_service.stream_chat_completion = AsyncMock(
            side_effect=Exception("AI Service Error")
        )
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
        
        # When there's an error, messages are NOT stored (atomic handling)
        mock_context_provider.store_message.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Timeout parameter not yet implemented")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_timeout(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test timeout handling in process_with_context."""
        # Mock tool registry to avoid socket warnings
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        import asyncio
        
        # Make AI service hang
        async def mock_hanging_stream():
            await asyncio.sleep(10)  # Hang for 10 seconds
            yield None  # Never reached
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_hanging_stream())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
    @pytest.mark.xfail(reason="Custom tools parameter not yet implemented")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_custom_tools(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context with custom tool definitions."""
        # Mock tool registry to avoid socket warnings
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
    @pytest.mark.xfail(reason="store_messages parameter not yet implemented")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_process_with_context_without_storing(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test process_with_context can skip storing messages."""
        # Mock tool registry to avoid socket warnings
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
    @pytest.mark.xfail(reason="process_messages method not yet implemented")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    async def test_direct_process_without_context(self, mock_get_registry, mock_config, mock_ai_service):
        """Test direct processing without context provider."""
        # Mock tool registry to avoid socket warnings
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
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
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_tool_execution_success(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test successful tool execution in stateless AI loop."""
        # Mock tool registry with a test tool
        mock_tool = Mock()
        mock_tool.execute = Mock(return_value="RFC created successfully!")
        
        mock_registry = Mock()
        mock_registry.get_tool_by_name.return_value = mock_tool
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls
        async def mock_stream_with_tool_execution():
            from types import SimpleNamespace
            
            yield SimpleNamespace(
                delta_content="I'll help you create an RFC.",
                delta_tool_call_part=None,
                finish_reason=None,
                delta_reasoning=None
            )
            
            # Tool calls should be provided as a list, not wrapped in JSON
            tool_calls = [{
                "id": "call_123",
                "function": {
                    "name": "create_rfc",
                    "arguments": '{"title": "Test RFC", "summary": "Test summary", "author": "Test"}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="",
                delta_tool_call_part=tool_calls,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_tool_execution())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message that triggers tool execution
        result = await ai_loop.process_with_context(
            message="Create an RFC for testing",
            context_provider=mock_context_provider
        )
        
        # Verify tool was executed
        mock_tool.execute.assert_called_once_with(arguments={
            "title": "Test RFC",
            "summary": "Test summary", 
            "author": "Test"
        })
        
        # Verify tool execution result is included in response
        assert "🔧 **create_rfc** executed:" in result['response']
        assert "RFC created successfully!" in result['response']
        assert result['finish_reason'] == "tool_calls"
        assert result['tool_calls'] is not None
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_tool_execution_async_tool(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test execution of async tools."""
        # Mock tool registry with an async tool
        mock_tool = Mock()
        mock_tool.execute = AsyncMock(return_value="Async operation completed!")
        
        mock_registry = Mock()
        mock_registry.get_tool_by_name.return_value = mock_tool
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls
        async def mock_stream_with_async_tool():
            from types import SimpleNamespace
            
            # Tool calls should be provided as a list
            tool_calls = [{
                "id": "call_456",
                "function": {
                    "name": "async_tool",
                    "arguments": '{"param": "value"}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="Processing...",
                delta_tool_call_part=tool_calls,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_async_tool())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message
        result = await ai_loop.process_with_context(
            message="Execute async tool",
            context_provider=mock_context_provider
        )
        
        # Verify async tool was executed
        mock_tool.execute.assert_called_once_with(arguments={"param": "value"})
        
        # Verify result includes tool execution output
        assert "🔧 **async_tool** executed:" in result['response']
        assert "Async operation completed!" in result['response']
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_tool_execution_tool_not_found(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test handling when tool is not found in registry."""
        # Mock tool registry that returns None for missing tool
        mock_registry = Mock()
        mock_registry.get_tool_by_name.return_value = None
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls
        async def mock_stream_with_missing_tool():
            from types import SimpleNamespace
            
            tool_calls = [{
                "id": "call_789",
                "function": {
                    "name": "missing_tool",
                    "arguments": '{"param": "value"}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="Calling tool...",
                delta_tool_call_part=tool_calls,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_missing_tool())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message
        result = await ai_loop.process_with_context(
            message="Call missing tool",
            context_provider=mock_context_provider
        )
        
        # Verify error is handled gracefully
        assert "🔧 Tool Error: Tool 'missing_tool' not found" in result['response']
        assert result['finish_reason'] == "tool_calls"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_tool_execution_invalid_arguments(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test handling of invalid tool arguments."""
        # Mock tool registry
        mock_registry = Mock()
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls with invalid JSON
        async def mock_stream_with_invalid_args():
            from types import SimpleNamespace
            
            tool_calls = [{
                "id": "call_invalid",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"invalid": json}'  # Invalid JSON
                }
            }]
            
            yield SimpleNamespace(
                delta_content="Processing...",
                delta_tool_call_part=tool_calls,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_invalid_args())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message
        result = await ai_loop.process_with_context(
            message="Execute tool with invalid args",
            context_provider=mock_context_provider
        )
        
        # Verify invalid arguments error is handled
        assert "🔧 Tool Error: Invalid arguments for test_tool" in result['response']
        assert result['finish_reason'] == "tool_calls"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_tool_execution_tool_raises_exception(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test handling when tool execution raises an exception."""
        # Mock tool registry with a tool that raises an exception
        mock_tool = Mock()
        mock_tool.execute = Mock(side_effect=Exception("Tool execution failed"))
        
        mock_registry = Mock()
        mock_registry.get_tool_by_name.return_value = mock_tool
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls
        async def mock_stream_with_failing_tool():
            from types import SimpleNamespace
            
            tool_calls = [{
                "id": "call_fail",
                "function": {
                    "name": "failing_tool",
                    "arguments": '{"param": "value"}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="Executing tool...",
                delta_tool_call_part=tool_calls,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_failing_tool())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message
        result = await ai_loop.process_with_context(
            message="Execute failing tool",
            context_provider=mock_context_provider
        )
        
        # Verify tool execution was attempted
        mock_tool.execute.assert_called_once_with(arguments={"param": "value"})
        
        # Verify error is handled gracefully
        assert "🔧 Tool Error: Failed to execute failing_tool" in result['response']
        assert "Tool execution failed" in result['response']
        assert result['finish_reason'] == "tool_calls"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_multiple_tool_execution(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test execution of multiple tools in one response."""
        # Mock tool registry with multiple tools
        mock_tool_one = Mock()
        mock_tool_one.execute = Mock(return_value="Tool one result")
        
        mock_tool_two = Mock()
        mock_tool_two.execute = Mock(return_value="Tool two result")
        
        mock_registry = Mock()
        def get_tool_side_effect(name):
            if name == "tool_one":
                return mock_tool_one
            elif name == "tool_two":
                return mock_tool_two
            return None
        
        mock_registry.get_tool_by_name.side_effect = get_tool_side_effect
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return multiple tool calls
        async def mock_stream_with_multiple_tools():
            from types import SimpleNamespace
            
            # First tool call chunk
            tool_calls_1 = [
                {
                    "index": 0,
                    "id": "call_1",
                    "function": {
                        "name": "tool_one",
                        "arguments": '{"arg1": "value1"}'
                    }
                }
            ]
            
            yield SimpleNamespace(
                delta_content="Executing multiple tools...",
                delta_tool_call_part=tool_calls_1,
                finish_reason=None,
                delta_reasoning=None
            )
            
            # Second tool call chunk
            tool_calls_2 = [
                {
                    "index": 1,
                    "id": "call_2", 
                    "function": {
                        "name": "tool_two",
                        "arguments": '{"arg2": "value2"}'
                    }
                }
            ]
            
            yield SimpleNamespace(
                delta_content="",
                delta_tool_call_part=tool_calls_2,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_multiple_tools())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message
        result = await ai_loop.process_with_context(
            message="Execute multiple tools",
            context_provider=mock_context_provider
        )
        
        # Verify both tools were executed
        mock_tool_one.execute.assert_called_once_with(arguments={"arg1": "value1"})
        mock_tool_two.execute.assert_called_once_with(arguments={"arg2": "value2"})
        
        # Verify both tool results are in response
        assert "🔧 **tool_one** executed:" in result['response']
        assert "Tool one result" in result['response']
        assert "🔧 **tool_two** executed:" in result['response']
        assert "Tool two result" in result['response']
        assert result['finish_reason'] == "tool_calls"
        assert len(result['tool_calls']) == 2
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_tool_execution_signature_fallback(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test fallback from arguments= to **kwargs signature."""
        # Mock tool registry with a tool that only accepts **kwargs
        mock_tool = Mock()
        # First call (arguments=) raises TypeError, second call (**kwargs) succeeds
        mock_tool.execute.side_effect = [
            TypeError("unexpected keyword argument 'arguments'"),
            "Command executed successfully"
        ]
        
        mock_registry = Mock()
        mock_registry.get_tool_by_name.return_value = mock_tool
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls
        async def mock_stream_with_kwargs_tool():
            from types import SimpleNamespace
            
            tool_calls = [{
                "id": "call_kwargs",
                "function": {
                    "name": "kwargs_tool",
                    "arguments": '{"command": "ls", "cwd": "."}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="Executing command...",
                delta_tool_call_part=tool_calls,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_kwargs_tool())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Process message
        result = await ai_loop.process_with_context(
            message="Execute command",
            context_provider=mock_context_provider
        )
        
        # Verify both call patterns were tried
        assert mock_tool.execute.call_count == 2
        # First call with arguments=
        mock_tool.execute.assert_any_call(arguments={"command": "ls", "cwd": "."})
        # Second call with **kwargs
        mock_tool.execute.assert_any_call(command="ls", cwd=".")
        
        # Verify result includes tool execution output
        assert "🔧 **kwargs_tool** executed:" in result['response']
        assert "Command executed successfully" in result['response']
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                        reason="Socket resource warning in CI")
    @patch('ai_whisperer.services.execution.ai_loop.get_tool_registry')
    @pytest.mark.skip(reason="Tool results are no longer appended to response - they are returned separately in tool_results field")

    async def test_tool_execution_streaming(self, mock_get_registry, mock_config, mock_ai_service, mock_context_provider):
        """Test that tool execution results are streamed to the client."""
        # Mock tool registry with a test tool
        mock_tool = Mock()
        mock_tool.execute = Mock(return_value="Tool result for streaming")
        
        mock_registry = Mock()
        mock_registry.get_tool_by_name.return_value = mock_tool
        mock_registry.get_all_tool_definitions.return_value = []
        mock_get_registry.return_value = mock_registry
        
        # Setup AI service to return tool calls
        async def mock_stream_with_tool_for_streaming():
            from types import SimpleNamespace
            
            yield SimpleNamespace(
                delta_content="I'll help you with that.",
                delta_tool_call_part=None,
                finish_reason=None,
                delta_reasoning=None
            )
            
            tool_calls = [{
                "id": "call_stream",
                "function": {
                    "name": "streaming_tool",
                    "arguments": '{"param": "test"}'
                }
            }]
            
            yield SimpleNamespace(
                delta_content="",
                delta_tool_call_part=tool_calls,
                finish_reason="tool_calls",
                delta_reasoning=None
            )
        
        mock_ai_service.stream_chat_completion = AsyncMock(return_value=mock_stream_with_tool_for_streaming())
        
        from ai_whisperer.services.execution.ai_loop import StatelessAILoop
        
        ai_loop = StatelessAILoop(
            config=mock_config,
            ai_service=mock_ai_service
        )
        
        # Track streaming chunks
        chunks = []
        async def on_chunk(chunk):
            chunks.append(chunk)
        
        # Process message with streaming
        result = await ai_loop.process_with_context(
            message="Execute streaming tool",
            context_provider=mock_context_provider,
            on_stream_chunk=on_chunk
        )
        
        # Verify tool was executed
        mock_tool.execute.assert_called_once_with(arguments={"param": "test"})
        
        # Verify tool results were streamed
        assert len(chunks) >= 3  # Initial content + final empty + tool results
        
        # Check that tool execution results appear in chunks
        all_chunks = "".join(chunks)
        assert "🔧 **streaming_tool** executed:" in all_chunks
        assert "Tool result for streaming" in all_chunks
        
        # Verify final result also contains tool execution
        assert "🔧 **streaming_tool** executed:" in result['response']
        assert "Tool result for streaming" in result['response']