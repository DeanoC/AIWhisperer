"""
OpenAI/OpenRouter standard tool calling implementation.
Provides proper tool call handling with message formatting following API standards.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)


class ToolChoice(Enum):
    """Tool choice options"""
    AUTO = "auto"
    REQUIRED = "required"
    NONE = "none"


@dataclass
class ToolCall:
    """Represents a tool call request from the model"""
    id: str
    name: str
    arguments: Dict[str, Any]
    
    @classmethod
    def from_api_response(cls, tool_call_data: dict) -> "ToolCall":
        """Create from API response format"""
        return cls(
            id=tool_call_data["id"],
            name=tool_call_data["function"]["name"],
            arguments=json.loads(tool_call_data["function"]["arguments"])
        )
    
    def to_dict(self) -> dict:
        """Convert to API format"""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments)
            }
        }


@dataclass
class ToolCallResult:
    """Result from executing a tool call"""
    tool_call_id: str
    name: str
    content: str
    
    def to_message(self) -> dict:
        """Convert to OpenAI message format"""
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "content": self.content
        }


@dataclass
class Message:
    """Base message class"""
    role: str
    content: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to API format"""
        data = {"role": self.role}
        if self.content is not None:
            data["content"] = self.content
        return data


@dataclass
class UserMessage(Message):
    """User message"""
    def __init__(self, content: str):
        super().__init__(role="user", content=content)


@dataclass
class AssistantMessage(Message):
    """Assistant message with optional tool calls"""
    tool_calls: Optional[List[dict]] = None
    
    def __init__(self, content: Optional[str] = None, tool_calls: Optional[List[dict]] = None):
        super().__init__(role="assistant", content=content)
        self.tool_calls = tool_calls
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        return data


class ToolCallMessage(Message):
    """Tool call result message"""
    def __init__(self, tool_call_id: str, name: str, content: str):
        super().__init__(role="tool", content=content)
        self.tool_call_id = tool_call_id
        self.name = name
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "content": self.content
        }


@dataclass
class StreamAccumulator:
    """Accumulates streaming chunks for tool calls"""
    tool_calls: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    def add_chunk(self, chunk: dict) -> None:
        """Add a streaming chunk"""
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        tool_calls = delta.get("tool_calls", [])
        
        for tc in tool_calls:
            index = tc.get("index", 0)
            
            if index not in self.tool_calls:
                self.tool_calls[index] = {
                    "id": tc.get("id"),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": tc.get("function", {}).get("name"),
                        "arguments": []
                    }
                }
            
            # Accumulate arguments
            if "function" in tc and "arguments" in tc["function"]:
                self.tool_calls[index]["function"]["arguments"].append(tc["function"]["arguments"])
    
    def get_tool_calls(self) -> List[ToolCall]:
        """Get accumulated tool calls"""
        result = []
        for tc_data in self.tool_calls.values():
            if tc_data.get("id") and tc_data.get("function", {}).get("name"):
                # Join the arguments fragments into a single string
                tc_data["function"]["arguments"] = ''.join(tc_data["function"]["arguments"])
                result.append(ToolCall.from_api_response(tc_data))
        return result


class ToolCallHandler:
    """Handles tool calling following OpenAI/OpenRouter standards"""
    
    def __init__(self, model_capabilities: Optional[Dict[str, Any]] = None):
        self.tools: Dict[str, AITool] = {}
        self.model_capabilities = model_capabilities or {}
        self._continuation_depth = 0
        self._max_continuation_depth = 3
    
    def register_tool(self, tool: AITool) -> None:
        """Register a tool for use"""
        self.tools[tool.name] = tool
    
    def register_tools(self, tools: List[AITool]) -> None:
        """Register multiple tools"""
        for tool in tools:
            self.register_tool(tool)
    
    def get_tool_definitions(self) -> List[dict]:
        """Get all tool definitions in OpenAI format"""
        definitions = []
        for tool in self.tools.values():
            definition = tool.get_openrouter_tool_definition()
            # Ensure strict mode compatibility
            if "parameters" in definition.get("function", {}):
                params = definition["function"]["parameters"]
                if "additionalProperties" not in params:
                    params["additionalProperties"] = False
            definitions.append(definition)
        return definitions
    
    def parse_tool_calls(self, api_response: dict) -> List[ToolCall]:
        """Parse tool calls from API response"""
        tool_calls = []
        
        choices = api_response.get("choices", [])
        if not choices:
            return tool_calls
        
        message = choices[0].get("message", {})
        raw_tool_calls = message.get("tool_calls", [])
        
        for tc in raw_tool_calls:
            try:
                tool_calls.append(ToolCall.from_api_response(tc))
            except Exception as e:
                logger.error(f"Failed to parse tool call: {e}")
                continue
        
        return tool_calls
    
    async def execute_tool_call(self, tool_call: ToolCall) -> ToolCallResult:
        """Execute a single tool call"""
        try:
            tool = self.tools.get(tool_call.name)
            if not tool:
                raise ValueError(f"Unknown tool: {tool_call.name}")
            
            # Execute the tool
            result = await tool.execute(**tool_call.arguments)
            
            return ToolCallResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=str(result)
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolCallResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=f"Error: {str(e)}"
            )
    
    async def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolCallResult]:
        """Execute multiple tool calls"""
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool_call(tool_call)
            results.append(result)
        return results
    
    def format_messages(self, messages: List[Message]) -> List[dict]:
        """Format messages for API"""
        return [msg.to_dict() for msg in messages]
    
    def build_api_params(
        self,
        tool_choice: Optional[Union[str, dict]] = None,
        parallel_tool_calls: Optional[bool] = None,
        strict: bool = True
    ) -> dict:
        """Build API parameters for tool calling"""
        params = {}
        
        # Tool choice
        if tool_choice is not None:
            if isinstance(tool_choice, str) and tool_choice in {choice.value for choice in ToolChoice}:
                params["tool_choice"] = tool_choice
            elif isinstance(tool_choice, dict):
                params["tool_choice"] = tool_choice
        
        # Parallel tool calls
        if parallel_tool_calls is not None:
            params["parallel_tool_calls"] = parallel_tool_calls
        
        # Strict mode
        if strict and self.tools:
            # Ensure all tools have strict mode enabled
            tools = self.get_tool_definitions()
            for tool in tools:
                if "function" in tool:
                    tool["function"]["strict"] = True
            params["tools"] = tools
        
        return params
    
    def needs_continuation(self, response: dict) -> bool:
        """Check if continuation is needed (for single-tool models)"""
        # Don't continue if we've hit the depth limit
        if self._continuation_depth >= self._max_continuation_depth:
            return False
        
        # Multi-tool models don't need continuation
        if self.model_capabilities.get("multi_tool", True):
            return False
        
        # Check if there were tool calls
        choices = response.get("choices", [])
        if not choices:
            return False
        
        message = choices[0].get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        # Single tool model with tool calls needs continuation
        return len(tool_calls) > 0
    
    def get_continuation_message(self) -> dict:
        """Get continuation message for single-tool models"""
        self._continuation_depth += 1
        return {
            "role": "user",
            "content": "Please continue with the next step."
        }
    
    def reset_continuation(self) -> None:
        """Reset continuation tracking"""
        self._continuation_depth = 0
    
    def get_model_capabilities(self, model_name: str) -> dict:
        """Get model-specific capabilities"""
        model_lower = model_name.lower()
        
        # Known single-tool models
        if "gemini" in model_lower:
            return {"multi_tool": False}
        
        # Most other models support multi-tool
        return {"multi_tool": True}
    
    def create_stream_accumulator(self) -> StreamAccumulator:
        """Create a new stream accumulator for handling streaming responses"""
        return StreamAccumulator()