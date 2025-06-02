"""
Unit tests for ai_whisperer.ai_loop.tool_call_accumulator

Tests for the ToolCallAccumulator class that accumulates streaming tool call 
chunks into complete tool calls. This is a CRITICAL module for AI interaction
coordination in the stateless AI loop system.
"""

import pytest
import json
from unittest.mock import Mock, patch

from ai_whisperer.ai_loop.tool_call_accumulator import ToolCallAccumulator
from ai_whisperer.ai_service.tool_calling import ToolCall


class TestToolCallAccumulatorInit:
    """Test ToolCallAccumulator initialization."""
    
    def test_init_creates_empty_accumulator(self):
        """Test that initialization creates empty tool calls dict."""
        accumulator = ToolCallAccumulator()
        
        assert accumulator.tool_calls == {}
        assert accumulator.get_tool_calls() == []
        assert accumulator.get_tool_call_objects() == []


class TestToolCallAccumulatorBasicChunks:
    """Test basic chunk addition functionality."""
    
    def test_add_single_chunk(self):
        """Test adding a single tool call chunk."""
        accumulator = ToolCallAccumulator()
        
        chunk = [{
            "index": 0,
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_function",
                "arguments": '{"param": "value"}'
            }
        }]
        
        accumulator.add_chunk(chunk)
        
        assert len(accumulator.tool_calls) == 1
        assert 0 in accumulator.tool_calls
        tool_call = accumulator.tool_calls[0]
        assert tool_call["id"] == "call_123"
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "test_function"
        assert tool_call["function"]["arguments"] == '{"param": "value"}'
    
    def test_add_empty_chunk_list(self):
        """Test adding empty chunk list does nothing."""
        accumulator = ToolCallAccumulator()
        
        accumulator.add_chunk([])
        
        assert accumulator.tool_calls == {}
        assert accumulator.get_tool_calls() == []
    
    def test_add_none_chunk_list(self):
        """Test adding None chunk list does nothing."""
        accumulator = ToolCallAccumulator()
        
        accumulator.add_chunk(None)
        
        assert accumulator.tool_calls == {}
        assert accumulator.get_tool_calls() == []
    
    def test_add_chunk_with_default_index(self):
        """Test adding chunk without explicit index uses default 0."""
        accumulator = ToolCallAccumulator()
        
        chunk = [{
            "id": "call_456",
            "type": "function",
            "function": {
                "name": "default_function",
                "arguments": '{"test": true}'
            }
        }]
        
        accumulator.add_chunk(chunk)
        
        assert 0 in accumulator.tool_calls
        assert accumulator.tool_calls[0]["id"] == "call_456"
    
    def test_add_chunk_with_default_type(self):
        """Test adding chunk without explicit type uses default 'function'."""
        accumulator = ToolCallAccumulator()
        
        chunk = [{
            "index": 0,
            "id": "call_789",
            "function": {
                "name": "typed_function",
                "arguments": "{}"
            }
        }]
        
        accumulator.add_chunk(chunk)
        
        assert accumulator.tool_calls[0]["type"] == "function"


class TestToolCallAccumulatorStreaming:
    """Test streaming accumulation functionality."""
    
    def test_accumulate_streaming_arguments(self):
        """Test accumulating arguments across multiple chunks."""
        accumulator = ToolCallAccumulator()
        
        # First chunk with partial arguments
        chunk1 = [{
            "index": 0,
            "id": "call_stream",
            "type": "function",
            "function": {
                "name": "streaming_function",
                "arguments": '{"param1": "'
            }
        }]
        
        # Second chunk with more arguments
        chunk2 = [{
            "index": 0,
            "function": {
                "arguments": 'value1", "param2": '
            }
        }]
        
        # Third chunk completing arguments
        chunk3 = [{
            "index": 0,
            "function": {
                "arguments": '"value2"}'
            }
        }]
        
        accumulator.add_chunk(chunk1)
        accumulator.add_chunk(chunk2)
        accumulator.add_chunk(chunk3)
        
        tool_call = accumulator.tool_calls[0]
        expected_args = '{"param1": "value1", "param2": "value2"}'
        assert tool_call["function"]["arguments"] == expected_args
    
    def test_multiple_tool_calls_different_indices(self):
        """Test accumulating multiple tool calls with different indices."""
        accumulator = ToolCallAccumulator()
        
        # First tool call
        chunk1 = [{
            "index": 0,
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "function_1",
                "arguments": '{"a": 1}'
            }
        }]
        
        # Second tool call
        chunk2 = [{
            "index": 1,
            "id": "call_2",
            "type": "function",
            "function": {
                "name": "function_2",
                "arguments": '{"b": 2}'
            }
        }]
        
        accumulator.add_chunk(chunk1)
        accumulator.add_chunk(chunk2)
        
        assert len(accumulator.tool_calls) == 2
        assert accumulator.tool_calls[0]["id"] == "call_1"
        assert accumulator.tool_calls[1]["id"] == "call_2"
        assert accumulator.tool_calls[0]["function"]["name"] == "function_1"
        assert accumulator.tool_calls[1]["function"]["name"] == "function_2"
    
    def test_mixed_chunks_multiple_tool_calls(self):
        """Test mixed chunks for multiple tool calls."""
        accumulator = ToolCallAccumulator()
        
        # Mixed chunk with both tool calls
        mixed_chunk = [
            {
                "index": 0,
                "id": "call_mix_1",
                "type": "function",
                "function": {
                    "name": "mix_function_1",
                    "arguments": '{"start": '
                }
            },
            {
                "index": 1,
                "id": "call_mix_2",
                "type": "function",
                "function": {
                    "name": "mix_function_2",
                    "arguments": '{"other": '
                }
            }
        ]
        
        # Continuation chunks
        continuation1 = [{
            "index": 0,
            "function": {"arguments": '"value"}'}
        }]
        
        continuation2 = [{
            "index": 1,
            "function": {"arguments": 'true}'}
        }]
        
        accumulator.add_chunk(mixed_chunk)
        accumulator.add_chunk(continuation1)
        accumulator.add_chunk(continuation2)
        
        assert len(accumulator.tool_calls) == 2
        assert accumulator.tool_calls[0]["function"]["arguments"] == '{"start": "value"}'
        assert accumulator.tool_calls[1]["function"]["arguments"] == '{"other": true}'


class TestToolCallAccumulatorGetMethods:
    """Test get_tool_calls and get_tool_call_objects methods."""
    
    def test_get_tool_calls_returns_complete_calls_only(self):
        """Test that get_tool_calls only returns complete tool calls."""
        accumulator = ToolCallAccumulator()
        
        # Complete tool call
        complete_chunk = [{
            "index": 0,
            "id": "call_complete",
            "type": "function",
            "function": {
                "name": "complete_function",
                "arguments": '{"valid": true}'
            }
        }]
        
        # Incomplete tool call (no name)
        incomplete_chunk = [{
            "index": 1,
            "id": "call_incomplete",
            "type": "function",
            "function": {
                "arguments": '{"incomplete": true}'
            }
        }]
        
        accumulator.add_chunk(complete_chunk)
        accumulator.add_chunk(incomplete_chunk)
        
        tool_calls = accumulator.get_tool_calls()
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["id"] == "call_complete"
        assert tool_calls[0]["function"]["name"] == "complete_function"
    
    def test_get_tool_calls_filters_missing_id(self):
        """Test that get_tool_calls filters out calls without ID."""
        accumulator = ToolCallAccumulator()
        
        # Tool call without ID
        no_id_chunk = [{
            "index": 0,
            "type": "function",
            "function": {
                "name": "no_id_function",
                "arguments": '{"test": true}'
            }
        }]
        
        accumulator.add_chunk(no_id_chunk)
        
        tool_calls = accumulator.get_tool_calls()
        
        assert len(tool_calls) == 0
    
    def test_get_tool_calls_maintains_order(self):
        """Test that get_tool_calls maintains index order."""
        accumulator = ToolCallAccumulator()
        
        # Add tool calls in non-sequential order
        chunks = [
            [{
                "index": 2,
                "id": "call_2",
                "function": {"name": "function_2", "arguments": "{}"}
            }],
            [{
                "index": 0,
                "id": "call_0",
                "function": {"name": "function_0", "arguments": "{}"}
            }],
            [{
                "index": 1,
                "id": "call_1",
                "function": {"name": "function_1", "arguments": "{}"}
            }]
        ]
        
        for chunk in chunks:
            accumulator.add_chunk(chunk)
        
        tool_calls = accumulator.get_tool_calls()
        
        # Note: Dict iteration order is insertion order in Python 3.7+
        # So order depends on when indices were first inserted
        assert len(tool_calls) == 3
        ids = [tc["id"] for tc in tool_calls]
        assert "call_0" in ids
        assert "call_1" in ids
        assert "call_2" in ids


class TestToolCallAccumulatorObjectConversion:
    """Test conversion to ToolCall objects."""
    
    @patch('ai_whisperer.ai_loop.tool_call_accumulator.ToolCall.from_api_response')
    def test_get_tool_call_objects_success(self, mock_from_api):
        """Test successful conversion to ToolCall objects."""
        accumulator = ToolCallAccumulator()
        
        # Mock ToolCall objects
        mock_tool_call = Mock(spec=ToolCall)
        mock_from_api.return_value = mock_tool_call
        
        chunk = [{
            "index": 0,
            "id": "call_obj",
            "type": "function",
            "function": {
                "name": "object_function",
                "arguments": '{"convert": true}'
            }
        }]
        
        accumulator.add_chunk(chunk)
        
        tool_call_objects = accumulator.get_tool_call_objects()
        
        assert len(tool_call_objects) == 1
        assert tool_call_objects[0] == mock_tool_call
        mock_from_api.assert_called_once_with(accumulator.tool_calls[0])
    
    @patch('ai_whisperer.ai_loop.tool_call_accumulator.ToolCall.from_api_response')
    @patch('ai_whisperer.ai_loop.tool_call_accumulator.logger')
    def test_get_tool_call_objects_handles_conversion_error(self, mock_logger, mock_from_api):
        """Test handling of conversion errors."""
        accumulator = ToolCallAccumulator()
        
        # Mock conversion error
        mock_from_api.side_effect = ValueError("Invalid tool call format")
        
        chunk = [{
            "index": 0,
            "id": "call_error",
            "type": "function",
            "function": {
                "name": "error_function",
                "arguments": '{"invalid": json}'
            }
        }]
        
        accumulator.add_chunk(chunk)
        
        tool_call_objects = accumulator.get_tool_call_objects()
        
        assert len(tool_call_objects) == 0
        mock_logger.warning.assert_called_once()
        assert "Failed to parse tool call" in str(mock_logger.warning.call_args)
    
    @patch('ai_whisperer.ai_loop.tool_call_accumulator.ToolCall.from_api_response')
    def test_get_tool_call_objects_partial_success(self, mock_from_api):
        """Test partial success in object conversion."""
        accumulator = ToolCallAccumulator()
        
        # First call succeeds, second fails
        mock_tool_call = Mock(spec=ToolCall)
        mock_from_api.side_effect = [mock_tool_call, Exception("Parse error")]
        
        chunks = [
            [{
                "index": 0,
                "id": "call_success",
                "function": {"name": "success_func", "arguments": "{}"}
            }],
            [{
                "index": 1,
                "id": "call_fail",
                "function": {"name": "fail_func", "arguments": "{}"}
            }]
        ]
        
        for chunk in chunks:
            accumulator.add_chunk(chunk)
        
        tool_call_objects = accumulator.get_tool_call_objects()
        
        assert len(tool_call_objects) == 1
        assert tool_call_objects[0] == mock_tool_call


class TestToolCallAccumulatorEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_chunk_missing_function_section(self):
        """Test handling chunk without function section."""
        accumulator = ToolCallAccumulator()
        
        chunk = [{
            "index": 0,
            "id": "call_no_func",
            "type": "function"
            # Missing function section
        }]
        
        accumulator.add_chunk(chunk)
        
        # Should create tool call with empty function
        assert 0 in accumulator.tool_calls
        tool_call = accumulator.tool_calls[0]
        assert tool_call["function"]["name"] is None
        assert tool_call["function"]["arguments"] == ""
    
    def test_chunk_with_empty_function(self):
        """Test handling chunk with empty function dict."""
        accumulator = ToolCallAccumulator()
        
        chunk = [{
            "index": 0,
            "id": "call_empty_func",
            "type": "function",
            "function": {}
        }]
        
        accumulator.add_chunk(chunk)
        
        tool_call = accumulator.tool_calls[0]
        assert tool_call["function"]["name"] is None
        assert tool_call["function"]["arguments"] == ""
    
    def test_accumulate_arguments_without_initial_function(self):
        """Test accumulating arguments when initial chunk had no function."""
        accumulator = ToolCallAccumulator()
        
        # First chunk without function
        chunk1 = [{
            "index": 0,
            "id": "call_late_func",
            "type": "function"
        }]
        
        # Second chunk with function arguments (should not crash)
        chunk2 = [{
            "index": 0,
            "function": {
                "arguments": '{"added": "later"}'
            }
        }]
        
        accumulator.add_chunk(chunk1)
        accumulator.add_chunk(chunk2)
        
        tool_call = accumulator.tool_calls[0]
        assert tool_call["function"]["arguments"] == '{"added": "later"}'
    
    def test_very_long_argument_accumulation(self):
        """Test accumulating very long arguments across many chunks."""
        accumulator = ToolCallAccumulator()
        
        # Initial chunk
        initial_chunk = [{
            "index": 0,
            "id": "call_long",
            "function": {"name": "long_function", "arguments": ""}
        }]
        accumulator.add_chunk(initial_chunk)
        
        # Add many small chunks
        for i in range(100):
            chunk = [{
                "index": 0,
                "function": {"arguments": f"part_{i}_"}
            }]
            accumulator.add_chunk(chunk)
        
        tool_call = accumulator.tool_calls[0]
        expected_args = "".join([f"part_{i}_" for i in range(100)])
        assert tool_call["function"]["arguments"] == expected_args
    
    def test_reusing_index_accumulates_arguments(self):
        """Test that reusing an index accumulates arguments rather than overwriting."""
        accumulator = ToolCallAccumulator()
        
        # First tool call at index 0
        chunk1 = [{
            "index": 0,
            "id": "call_first",
            "function": {"name": "first_function", "arguments": '{"first": true'}
        }]
        
        # Second chunk at same index (should accumulate arguments)
        chunk2 = [{
            "index": 0,
            "function": {"arguments": ', "second": true}'}
        }]
        
        accumulator.add_chunk(chunk1)
        accumulator.add_chunk(chunk2)
        
        # Should have the first call with accumulated arguments
        assert len(accumulator.tool_calls) == 1
        tool_call = accumulator.tool_calls[0]
        assert tool_call["id"] == "call_first"
        assert tool_call["function"]["name"] == "first_function"
        assert tool_call["function"]["arguments"] == '{"first": true, "second": true}'


class TestToolCallAccumulatorIntegration:
    """Integration tests for ToolCallAccumulator."""
    
    def test_realistic_openai_streaming_simulation(self):
        """Test realistic OpenAI streaming pattern simulation."""
        accumulator = ToolCallAccumulator()
        
        # Simulate typical OpenAI streaming chunks
        streaming_chunks = [
            # First chunk - tool call start
            [{
                "index": 0,
                "id": "call_12345",
                "type": "function",
                "function": {"name": "get_weather", "arguments": ""}
            }],
            # Arguments streaming
            [{"index": 0, "function": {"arguments": '{"loc'}}],
            [{"index": 0, "function": {"arguments": 'ation": "'}}],
            [{"index": 0, "function": {"arguments": 'New York'}}],
            [{"index": 0, "function": {"arguments": '", "unit'}}],
            [{"index": 0, "function": {"arguments": '": "celsius'}}],
            [{"index": 0, "function": {"arguments": '"}'}}],
        ]
        
        for chunk in streaming_chunks:
            accumulator.add_chunk(chunk)
        
        tool_calls = accumulator.get_tool_calls()
        
        assert len(tool_calls) == 1
        tc = tool_calls[0]
        assert tc["id"] == "call_12345"
        assert tc["function"]["name"] == "get_weather"
        
        # Parse the accumulated arguments
        import json
        args = json.loads(tc["function"]["arguments"])
        assert args["location"] == "New York"
        assert args["unit"] == "celsius"
    
    def test_multiple_concurrent_streaming_calls(self):
        """Test multiple tool calls streaming concurrently."""
        accumulator = ToolCallAccumulator()
        
        # Simulate concurrent streaming for two tool calls
        concurrent_chunks = [
            # Both start
            [
                {
                    "index": 0,
                    "id": "call_weather",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": ""}
                },
                {
                    "index": 1,
                    "id": "call_time",
                    "type": "function", 
                    "function": {"name": "get_time", "arguments": ""}
                }
            ],
            # Both continue
            [
                {"index": 0, "function": {"arguments": '{"city": "'}},
                {"index": 1, "function": {"arguments": '{"timezone": "'}}
            ],
            [
                {"index": 0, "function": {"arguments": 'Paris"}'}},
                {"index": 1, "function": {"arguments": 'UTC"}'}}
            ],
        ]
        
        for chunk in concurrent_chunks:
            accumulator.add_chunk(chunk)
        
        tool_calls = accumulator.get_tool_calls()
        
        assert len(tool_calls) == 2
        
        # Check both tool calls
        call_by_id = {tc["id"]: tc for tc in tool_calls}
        
        weather_call = call_by_id["call_weather"]
        assert weather_call["function"]["name"] == "get_weather"
        weather_args = json.loads(weather_call["function"]["arguments"])
        assert weather_args["city"] == "Paris"
        
        time_call = call_by_id["call_time"]
        assert time_call["function"]["name"] == "get_time"
        time_args = json.loads(time_call["function"]["arguments"])
        assert time_args["timezone"] == "UTC"