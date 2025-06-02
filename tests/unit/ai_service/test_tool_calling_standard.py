"""
Test suite for OpenAI/OpenRouter standard tool calling implementation.
Uses TDD approach to define expected behavior before implementation.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from ai_whisperer.services.ai.tool_calling import (
    ToolCall,
    ToolCallResult,
    ToolCallHandler,
    ToolCallMessage,
    AssistantMessage,
    UserMessage,
)
from ai_whisperer.tools.base_tool import AITool


class MockWeatherTool(AITool):
    """Mock tool for testing"""
    @property
    def name(self) -> str:
        return "get_weather"
    
    @property
    def description(self) -> str:
        return "Get current weather for a location"
    
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature units"
                }
            },
            "required": ["location"],
            "additionalProperties": False
        }
    
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for AI on how to use this tool"""
        return "Use this tool to get weather information for any location."
    
    async def execute(self, location: str, units: str = "celsius") -> str:
        return f"Temperature in {location}: 20°{units[0].upper()}"


class MockEmailTool(AITool):
    """Mock email tool for testing parallel calls"""
    @property
    def name(self) -> str:
        return "send_email"
    
    @property
    def description(self) -> str:
        return "Send an email"
    
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["to", "subject", "body"],
            "additionalProperties": False
        }
    
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for AI on how to use this tool"""
        return "Use this tool to send emails."
    
    async def execute(self, to: str, subject: str, body: str) -> str:
        return f"Email sent to {to}"


class TestToolCallingStandard:
    """Test OpenAI/OpenRouter standard tool calling implementation"""
    
    def test_tool_call_parsing(self):
        """Test parsing tool calls from API response"""
        # API response with tool calls
        api_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Paris, France", "units": "celsius"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        handler = ToolCallHandler()
        tool_calls = handler.parse_tool_calls(api_response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0].id == "call_abc123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {"location": "Paris, France", "units": "celsius"}
    
    def test_multiple_tool_calls(self):
        """Test parsing multiple parallel tool calls"""
        api_response = {
            "choices": [{
                "message": {
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "Paris"}'
                            }
                        },
                        {
                            "id": "call_456",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "London"}'
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        handler = ToolCallHandler()
        tool_calls = handler.parse_tool_calls(api_response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0].id == "call_123"
        assert tool_calls[1].id == "call_456"
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test executing tool calls"""
        tool = MockWeatherTool()
        tool_call = ToolCall(
            id="call_123",
            name="get_weather",
            arguments={"location": "Paris", "units": "fahrenheit"}
        )
        
        handler = ToolCallHandler()
        handler.register_tool(tool)
        
        result = await handler.execute_tool_call(tool_call)
        
        assert result.tool_call_id == "call_123"
        assert result.name == "get_weather"
        assert result.content == "Temperature in Paris: 20°F"
    
    def test_tool_result_message_format(self):
        """Test tool result message follows OpenAI format"""
        result = ToolCallResult(
            tool_call_id="call_123",
            name="get_weather",
            content="Temperature: 20°C"
        )
        
        message = result.to_message()
        
        assert message["role"] == "tool"
        assert message["tool_call_id"] == "call_123"
        assert message["name"] == "get_weather"
        assert message["content"] == "Temperature: 20°C"
    
    def test_message_history_with_tools(self):
        """Test building message history with tool calls"""
        messages = [
            UserMessage("What's the weather in Paris?"),
            AssistantMessage(
                content=None,
                tool_calls=[{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Paris"}'
                    }
                }]
            ),
            ToolCallMessage(
                tool_call_id="call_123",
                name="get_weather",
                content="Temperature: 20°C"
            ),
            AssistantMessage("The temperature in Paris is 20°C.")
        ]
        
        handler = ToolCallHandler()
        formatted = handler.format_messages(messages)
        
        assert len(formatted) == 4
        assert formatted[0]["role"] == "user"
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["tool_calls"] is not None
        assert formatted[2]["role"] == "tool"
        assert formatted[3]["role"] == "assistant"
        assert formatted[3]["content"] == "The temperature in Paris is 20°C."
    
    def test_tool_choice_parameter(self):
        """Test tool_choice parameter support"""
        handler = ToolCallHandler()
        
        # Test auto (default)
        params = handler.build_api_params(tool_choice="auto")
        assert params["tool_choice"] == "auto"
        
        # Test required
        params = handler.build_api_params(tool_choice="required")
        assert params["tool_choice"] == "required"
        
        # Test specific function
        params = handler.build_api_params(
            tool_choice={"type": "function", "function": {"name": "get_weather"}}
        )
        assert params["tool_choice"]["function"]["name"] == "get_weather"
        
        # Test none
        params = handler.build_api_params(tool_choice="none")
        assert params["tool_choice"] == "none"
    
    def test_strict_mode_schema_validation(self):
        """Test strict mode schema requirements"""
        tool = MockWeatherTool()
        
        # Should have additionalProperties: false
        schema = tool.get_openrouter_tool_definition()
        assert schema["function"]["parameters"]["additionalProperties"] is False
        
        # All required fields should be listed
        assert "required" in schema["function"]["parameters"]
        assert "location" in schema["function"]["parameters"]["required"]
    
    def test_parallel_tool_calls_parameter(self):
        """Test parallel_tool_calls parameter"""
        handler = ToolCallHandler()
        
        # Default should allow parallel
        params = handler.build_api_params()
        assert params.get("parallel_tool_calls", True) is True
        
        # Disable parallel calls
        params = handler.build_api_params(parallel_tool_calls=False)
        assert params["parallel_tool_calls"] is False
    
    @pytest.mark.asyncio
    async def test_error_handling_in_tool_execution(self):
        """Test error handling when tool execution fails"""
        class FailingTool(AITool):
            @property
            def name(self) -> str:
                return "failing_tool"
            
            @property
            def description(self) -> str:
                return "A tool that fails"
            
            @property
            def parameters_schema(self) -> dict:
                return {"type": "object", "properties": {}}
            
            def get_ai_prompt_instructions(self) -> str:
                return "A test tool."
            
            async def execute(self, **kwargs) -> str:
                raise ValueError("Tool execution failed")
        
        tool = FailingTool()
        tool_call = ToolCall(id="call_123", name="failing_tool", arguments={})
        
        handler = ToolCallHandler()
        handler.register_tool(tool)
        
        result = await handler.execute_tool_call(tool_call)
        
        assert result.tool_call_id == "call_123"
        assert "error" in result.content.lower()
        assert "Tool execution failed" in result.content


class TestDebbieSessionTools:
    """Test Debbie's session debugging tools"""
    
    @pytest.mark.asyncio
    async def test_session_health_tool(self):
        """Test session_health tool definition and execution"""
        from ai_whisperer.tools.session_health_tool import SessionHealthTool
        
        tool = SessionHealthTool()
        
        # Test tool definition
        definition = tool.get_openrouter_tool_definition()
        assert definition["function"]["name"] == "session_health"
        assert "session_id" in definition["function"]["parameters"]["properties"]
        
        # Test execution
        result = await tool.execute(session_id="test-session-123")
        assert isinstance(result, str)
        assert "health_score" in result or "Health Score" in result
    
    @pytest.mark.asyncio
    async def test_session_analysis_tool(self):
        """Test session_analysis tool"""
        from ai_whisperer.tools.session_analysis_tool import SessionAnalysisTool
        
        tool = SessionAnalysisTool()
        
        # Test tool definition
        definition = tool.get_openrouter_tool_definition()
        assert definition["function"]["name"] == "session_analysis"
        assert "time_range_minutes" in definition["function"]["parameters"]["properties"]
        assert "focus_area" in definition["function"]["parameters"]["properties"]
        
        # Test execution with different focus areas
        result = await tool.execute(
            session_id="test-session",
            time_range_minutes=30,
            focus_area="errors"
        )
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_monitoring_control_tool(self):
        """Test monitoring_control tool"""
        from ai_whisperer.tools.monitoring_control_tool import MonitoringControlTool
        
        tool = MonitoringControlTool()
        
        # Test tool definition
        definition = tool.get_openrouter_tool_definition()
        assert definition["function"]["name"] == "monitoring_control"
        assert "action" in definition["function"]["parameters"]["properties"]
        assert "enable" in definition["function"]["parameters"]["properties"]["action"]["enum"]
        
        # Test execution
        result = await tool.execute(action="status")
        assert isinstance(result, str)
        assert "monitoring" in result.lower()


class TestModelSpecificBehavior:
    """Test model-specific tool calling behaviors"""
    
    @pytest.mark.asyncio
    async def test_single_tool_model_continuation(self):
        """Test automatic continuation for single-tool models like Gemini"""
        handler = ToolCallHandler(model_capabilities={"multi_tool": False})
        
        # First response with tool call
        response1 = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "list_files",
                            "arguments": "{}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        # Should detect need for continuation
        assert handler.needs_continuation(response1) is True
        
        # After tool execution, should generate continuation message
        continuation_msg = handler.get_continuation_message()
        assert continuation_msg["role"] == "user"
        assert "continue" in continuation_msg["content"].lower()
    
    @pytest.mark.asyncio
    async def test_multi_tool_model_no_continuation(self):
        """Test that multi-tool models don't need continuation"""
        handler = ToolCallHandler(model_capabilities={"multi_tool": True})
        
        # Response with multiple tool calls
        response = {
            "choices": [{
                "message": {
                    "tool_calls": [
                        {"id": "call_1", "function": {"name": "tool1", "arguments": "{}"}},
                        {"id": "call_2", "function": {"name": "tool2", "arguments": "{}"}}
                    ]
                },
                "finish_reason": "tool_calls"
            }]
        }
        
        # Should not need continuation
        assert handler.needs_continuation(response) is False
    
    def test_model_capability_detection(self):
        """Test automatic model capability detection"""
        handler = ToolCallHandler()
        
        # Gemini models
        assert handler.get_model_capabilities("google/gemini-2.0-flash")["multi_tool"] is False
        
        # GPT-4 models
        assert handler.get_model_capabilities("openai/gpt-4")["multi_tool"] is True
        
        # Claude models
        assert handler.get_model_capabilities("anthropic/claude-3.5-sonnet")["multi_tool"] is True


class TestStreamingToolCalls:
    """Test streaming tool call handling"""
    
    def test_streaming_tool_call_accumulation(self):
        """Test accumulating tool call chunks during streaming"""
        handler = ToolCallHandler()
        accumulator = handler.create_stream_accumulator()
        
        # Simulate streaming chunks
        chunks = [
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_123", "function": {"name": "get_weather", "arguments": ""}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"loc'}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": 'ation":'}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '"Paris"}'}}]}}]},
        ]
        
        for chunk in chunks:
            accumulator.add_chunk(chunk)
        
        tool_calls = accumulator.get_tool_calls()
        assert len(tool_calls) == 1
        assert tool_calls[0].id == "call_123"
        assert tool_calls[0].name == "get_weather"
        assert tool_calls[0].arguments == {"location": "Paris"}