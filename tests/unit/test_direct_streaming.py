"""
Tests for direct JSON-RPC streaming without delegates.
This tests the new streaming approach that bypasses the delegate system
and sends notifications directly from the session layer.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.context.agent_context import AgentContext


class TestDirectStreaming:
    """Test direct JSON-RPC streaming functionality."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = Mock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        return ws
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for StreamingSession."""
        return {
            "openrouter": {
                "api_key": "test-key",
                "model": "openai/gpt-3.5-turbo",
                "params": {
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }
        }
    
    @pytest.fixture
    def mock_agent_context(self):
        """Create a mock agent context."""
        context = Mock(spec=AgentContext)
        context.retrieve_messages.return_value = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        context.store_message = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_direct_streaming_session(self, mock_websocket, mock_agent_context, mock_config):
        """Test session with direct streaming (no delegates)."""
        from interactive_server.streaming_session import StreamingSession
        
        session = StreamingSession(
            session_id="test-123",
            websocket=mock_websocket,
            config=mock_config
        )
        
        # Create a default agent first
        await session.create_agent("default", "You are a helpful assistant")
        
        # Mock the AI loop's process_with_context method
        with patch.object(session._ai_loop, 'process_with_context', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                'response': 'Hello there!',
                'finish_reason': 'stop',
                'tool_calls': None,
                'error': None
            }
            
            # Send a message
            response = await session.send_message(
                message="Hello",
                agent_id="default"
            )
        
        # Verify streaming happened
        assert response['success'] is True
        
        # Check that WebSocket received notifications
        calls = mock_websocket.send_json.call_args_list
        assert len(calls) > 0
        
        # Should have AI chunk notifications
        chunk_notifications = [
            call for call in calls 
            if call[0][0].get('method') == 'AIMessageChunkNotification'
        ]
        assert len(chunk_notifications) > 0
    
    @pytest.mark.asyncio
    async def test_streaming_wrapper(self):
        """Test the streaming wrapper for AILoop responses."""
        from interactive_server.streaming_wrapper import StreamingWrapper
        
        # Mock chunks to simulate AI response
        async def mock_chunks():
            yield {"content": "Hello ", "is_final": False}
            yield {"content": "there!", "is_final": False}
            yield {"content": "", "is_final": True}
        
        wrapper = StreamingWrapper()
        chunks_received = []
        
        async def on_chunk(chunk):
            chunks_received.append(chunk)
        
        # Process the stream
        result = await wrapper.process_stream(
            stream=mock_chunks(),
            on_chunk=on_chunk
        )
        
        # Verify result
        assert result['response'] == "Hello there!"
        assert result['finish_reason'] == 'stop'
        assert len(chunks_received) == 3
    
    @pytest.mark.asyncio
    async def test_token_by_token_updates(self, mock_websocket, mock_config):
        """Test token-by-token streaming updates."""
        from interactive_server.streaming_session import StreamingSession
        
        session = StreamingSession(
            session_id="test-456",
            websocket=mock_websocket,
            config=mock_config
        )
        
        # Simulate token streaming
        tokens = ["The", " ", "quick", " ", "brown", " ", "fox"]
        
        for token in tokens:
            await session._send_token_notification(token)
        
        # Send final notification
        await session._send_token_notification("", is_final=True)
        
        # Verify all tokens were sent
        calls = mock_websocket.send_json.call_args_list
        assert len(calls) == len(tokens) + 1  # tokens + final
        
        # Check token content
        for i, token in enumerate(tokens):
            notification = calls[i][0][0]
            assert notification['method'] == 'AIMessageChunkNotification'
            assert notification['params']['chunk'] == token
            assert notification['params']['isFinal'] is False
        
        # Check final notification
        final = calls[-1][0][0]
        assert final['params']['isFinal'] is True
    
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, mock_websocket, mock_config):
        """Test error handling during streaming."""
        from interactive_server.streaming_session import StreamingSession
        
        session = StreamingSession(
            session_id="test-789",
            websocket=mock_websocket,
            config=mock_config
        )
        
        # Mock AI service that raises error during streaming
        async def error_stream():
            yield {"content": "Starting...", "is_final": False}
            raise Exception("Stream interrupted")
        
        # Process with error
        result = await session._process_ai_stream(error_stream())
        
        # Should handle error gracefully
        assert result['error'] is not None
        assert "Stream interrupted" in str(result['error'])
        
        # Should send error notification
        error_calls = [
            call for call in mock_websocket.send_json.call_args_list
            if call[0][0].get('method') == 'SessionStatusNotification'
            and call[0][0].get('params', {}).get('status') == 3  # SessionStatus.Error value
        ]
        assert len(error_calls) > 0
    
    @pytest.mark.asyncio
    async def test_no_delegate_dependencies(self):
        """Test that streaming works without any delegates."""
        from interactive_server.streaming_session import StreamingSession
        
        # Create session without delegate manager
        session = StreamingSession(
            session_id="test-nodelegates",
            websocket=Mock()
        )
        
        # Should not have delegate_manager
        assert not hasattr(session, 'delegate_manager')
        
        # Should still be able to stream
        assert hasattr(session, '_process_ai_stream')
        assert hasattr(session, '_send_notification')
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_sessions(self, mock_websocket, mock_config):
        """Test multiple concurrent streaming sessions."""
        from interactive_server.streaming_session import StreamingSession
        
        # Create multiple sessions
        sessions = [
            StreamingSession(f"session-{i}", Mock(), config=mock_config) 
            for i in range(3)
        ]
        
        # Stream to all sessions concurrently
        async def stream_to_session(session, message):
            chunks = []
            
            async def on_chunk(chunk):
                chunks.append(chunk)
            
            await session._stream_response(
                message=message,
                on_chunk=on_chunk
            )
            
            return chunks
        
        # Run concurrently
        results = await asyncio.gather(
            stream_to_session(sessions[0], "Hello 1"),
            stream_to_session(sessions[1], "Hello 2"),
            stream_to_session(sessions[2], "Hello 3")
        )
        
        # Each session should have received chunks
        for chunks in results:
            assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_tool_call_streaming(self, mock_websocket, mock_config):
        """Test streaming with tool calls."""
        from interactive_server.streaming_session import StreamingSession
        
        session = StreamingSession(
            session_id="test-tools",
            websocket=mock_websocket,
            config=mock_config
        )
        
        # Mock stream with tool calls
        async def tool_stream():
            yield {"content": "Let me help with that.", "is_final": False}
            yield {
                "tool_calls": [{
                    "id": "call_123",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "London"}'
                    }
                }],
                "is_final": True,
                "finish_reason": "tool_calls"
            }
        
        result = await session._process_ai_stream(tool_stream())
        
        # Should have tool calls in result
        assert result['tool_calls'] is not None
        assert len(result['tool_calls']) == 1
        assert result['tool_calls'][0]['function']['name'] == 'get_weather'
        
        # Should send tool call notification
        tool_calls = [
            call for call in mock_websocket.send_json.call_args_list
            if call[0][0].get('method') == 'ToolCallNotification'
        ]
        assert len(tool_calls) > 0
    
    @pytest.mark.asyncio
    async def test_streaming_performance_metrics(self):
        """Test streaming performance tracking."""
        from interactive_server.streaming_session import StreamingSession
        import time
        
        session = StreamingSession(
            session_id="test-perf",
            websocket=Mock()
        )
        
        # Track timing
        start_time = time.time()
        chunks_count = 0
        
        async def mock_stream():
            nonlocal chunks_count
            for i in range(100):  # Simulate 100 chunks
                chunks_count += 1
                yield {"content": f"chunk{i}", "is_final": False}
                await asyncio.sleep(0.001)  # Small delay
            yield {"content": "", "is_final": True}
        
        result = await session._process_ai_stream(mock_stream())
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should process all chunks
        assert chunks_count == 100
        
        # Should complete reasonably quickly (under 1 second for 100 chunks)
        assert duration < 1.0
        
        # Calculate throughput
        throughput = chunks_count / duration
        print(f"Streaming throughput: {throughput:.2f} chunks/second")
        
        # Should maintain good throughput (>100 chunks/second)
        assert throughput > 100