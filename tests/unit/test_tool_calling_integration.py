"""
Integration tests for the new tool calling system with AI service.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from ai_whisperer.ai_service.tool_calling import (
    ToolCallHandler,
    ToolCall,
    ToolCallResult,
    UserMessage,
    AssistantMessage,
    ToolCallMessage,
)
from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
from ai_whisperer.tools.session_health_tool import SessionHealthTool
from ai_whisperer.tools.session_analysis_tool import SessionAnalysisTool
from ai_whisperer.tools.monitoring_control_tool import MonitoringControlTool


class TestToolCallingIntegration:
    """Test integration of new tool calling system"""
    
    @pytest.mark.asyncio
    async def test_stateless_ai_loop_with_new_tool_handler(self):
        """Test StatelessAILoop using new ToolCallHandler"""
        # Create mock AI service
        mock_ai_service = AsyncMock()
        
        # Create tool handler with session tools
        tool_handler = ToolCallHandler()
        tool_handler.register_tools([
            SessionHealthTool(),
            SessionAnalysisTool(),
            MonitoringControlTool()
        ])
        
        # Create AI loop with tool handler
        ai_loop = StatelessAILoop(
            ai_service=mock_ai_service,
            tool_handler=tool_handler  # New parameter
        )
        
        # Mock AI response with tool calls
        mock_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "session_health",
                            "arguments": '{"session_id": "current"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        # Mock streaming response
        async def mock_stream():
            yield json.dumps(mock_response)
        
        mock_ai_service.stream_chat_completion.return_value = mock_stream()
        
        # Process message
        result = await ai_loop.process_message("Check session health", {})
        
        # Verify tool was executed
        assert "Session Health Report" in result["response"]
        assert result["finish_reason"] == "tool_calls"
        assert len(result["tool_calls"]) == 1
    
    @pytest.mark.asyncio
    async def test_message_history_with_tool_results(self):
        """Test proper message history formatting with tool results"""
        tool_handler = ToolCallHandler()
        tool_handler.register_tool(SessionHealthTool())
        
        # Build conversation with tool calls
        messages = [
            UserMessage("Check the health of my session"),
            AssistantMessage(
                content=None,
                tool_calls=[{
                    "id": "call_456",
                    "type": "function",
                    "function": {
                        "name": "session_health",
                        "arguments": '{"session_id": "current"}'
                    }
                }]
            )
        ]
        
        # Execute tool call
        tool_call = ToolCall(
            id="call_456",
            name="session_health",
            arguments={"session_id": "current"}
        )
        result = await tool_handler.execute_tool_call(tool_call)
        
        # Add tool result to messages
        messages.append(ToolCallMessage(
            tool_call_id=result.tool_call_id,
            name=result.name,
            content=result.content
        ))
        
        # Add final assistant response
        messages.append(AssistantMessage(
            "Based on the health check, your session is running smoothly with a health score of 80/100."
        ))
        
        # Format messages
        formatted = tool_handler.format_messages(messages)
        
        # Verify message structure
        assert len(formatted) == 4
        assert formatted[0]["role"] == "user"
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["tool_calls"] is not None
        assert formatted[2]["role"] == "tool"
        assert formatted[2]["tool_call_id"] == "call_456"
        assert formatted[3]["role"] == "assistant"
        assert "health score of 80/100" in formatted[3]["content"]
    
    @pytest.mark.asyncio
    async def test_continuation_for_single_tool_models(self):
        """Test automatic continuation for models that can only call one tool at a time"""
        # Create handler for Gemini (single-tool model)
        tool_handler = ToolCallHandler(model_capabilities={"multi_tool": False})
        tool_handler.register_tools([
            SessionHealthTool(),
            SessionAnalysisTool()
        ])
        
        # First response - list sessions
        response1 = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "session_health",
                            "arguments": '{"session_id": "current"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        # Should need continuation
        assert tool_handler.needs_continuation(response1) is True
        
        # Get continuation message
        cont_msg = tool_handler.get_continuation_message()
        assert cont_msg["role"] == "user"
        assert "continue" in cont_msg["content"].lower()
        
        # Second response - analyze session
        response2 = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_2",
                        "function": {
                            "name": "session_analysis",
                            "arguments": '{"session_id": "current", "focus_area": "errors"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        # Should still need continuation (depth = 2)
        assert tool_handler.needs_continuation(response2) is True
        
        # After 3 continuations, should stop
        tool_handler.get_continuation_message()  # depth = 3
        response3 = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_3",
                        "function": {
                            "name": "monitoring_control",
                            "arguments": '{"action": "status"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        # Should NOT need continuation (max depth reached)
        assert tool_handler.needs_continuation(response3) is False
    
    @pytest.mark.asyncio
    async def test_parallel_tool_calls_execution(self):
        """Test executing multiple tool calls in parallel"""
        tool_handler = ToolCallHandler()
        tool_handler.register_tools([
            SessionHealthTool(),
            MonitoringControlTool()
        ])
        
        # Create multiple tool calls
        tool_calls = [
            ToolCall(
                id="call_1",
                name="session_health",
                arguments={"session_id": "session-123"}
            ),
            ToolCall(
                id="call_2",
                name="session_health",
                arguments={"session_id": "session-456"}
            ),
            ToolCall(
                id="call_3",
                name="monitoring_control",
                arguments={"action": "status"}
            )
        ]
        
        # Execute all calls
        results = await tool_handler.execute_tool_calls(tool_calls)
        
        # Verify results
        assert len(results) == 3
        assert all(isinstance(r, ToolCallResult) for r in results)
        assert results[0].tool_call_id == "call_1"
        assert results[1].tool_call_id == "call_2"
        assert results[2].tool_call_id == "call_3"
        assert "Session Health Report" in results[0].content
        assert "Session Health Report" in results[1].content
        assert "Monitoring Status" in results[2].content
    
    @pytest.mark.asyncio
    async def test_streaming_tool_calls_with_debbie(self):
        """Test streaming tool calls specifically for Debbie's tools"""
        tool_handler = ToolCallHandler()
        accumulator = tool_handler.create_stream_accumulator()
        
        # Simulate streaming chunks for Debbie checking session health
        chunks = [
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "id": "call_debbie_1",
                            "function": {
                                "name": "session_health",
                                "arguments": ""
                            }
                        }]
                    }
                }]
            },
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {
                                "arguments": '{"sess'
                            }
                        }]
                    }
                }]
            },
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {
                                "arguments": 'ion_id": "curr'
                            }
                        }]
                    }
                }]
            },
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {
                                "arguments": 'ent"}'
                            }
                        }]
                    }
                }]
            }
        ]
        
        # Accumulate chunks
        for chunk in chunks:
            accumulator.add_chunk(chunk)
        
        # Get final tool calls
        tool_calls = accumulator.get_tool_calls()
        
        # Verify
        assert len(tool_calls) == 1
        assert tool_calls[0].id == "call_debbie_1"
        assert tool_calls[0].name == "session_health"
        assert tool_calls[0].arguments == {"session_id": "current"}
    
    @pytest.mark.asyncio
    async def test_tool_choice_with_debbie_tools(self):
        """Test tool_choice parameter with Debbie's debugging tools"""
        tool_handler = ToolCallHandler()
        tool_handler.register_tools([
            SessionHealthTool(),
            SessionAnalysisTool(),
            MonitoringControlTool()
        ])
        
        # Test forcing specific tool
        params = tool_handler.build_api_params(
            tool_choice={
                "type": "function",
                "function": {"name": "session_analysis"}
            }
        )
        
        assert params["tool_choice"]["type"] == "function"
        assert params["tool_choice"]["function"]["name"] == "session_analysis"
        
        # Test requiring any tool
        params = tool_handler.build_api_params(tool_choice="required")
        assert params["tool_choice"] == "required"
        
        # Verify tools are included with strict mode
        assert "tools" in params
        assert len(params["tools"]) == 3
        assert all(t["function"]["strict"] for t in params["tools"])