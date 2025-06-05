"""Unit tests for MCP server tool handler."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, MagicMock

from ai_whisperer.mcp.server.handlers.tools import ToolHandler
from ai_whisperer.mcp.server.config import MCPServerConfig
from ai_whisperer.tools.base_tool import AITool


class MockTool(AITool):
    """Mock tool for testing."""
    
    def __init__(self, tool_name, tool_description, async_execute=False):
        self._name = tool_name
        self._description = tool_description
        self._parameters_schema = {
            "type": "object",
            "properties": {
                "test_param": {"type": "string", "description": "Test parameter"}
            },
            "required": ["test_param"]
        }
        self._async = async_execute
        
    @property
    def name(self):
        return self._name
        
    @property
    def description(self):
        return self._description
        
    @property
    def parameters_schema(self):
        return self._parameters_schema
        
    def get_ai_prompt_instructions(self):
        """Return prompt instructions."""
        return f"Use {self.name} to test things"
        
    async def execute_async(self, **kwargs):
        """Async execution."""
        return {"result": f"async {self.name}", "params": kwargs}
        
    def execute(self, **kwargs):
        """Sync execution."""
        if self._async:
            # This shouldn't be called for async tools
            raise RuntimeError("Should use execute_async")
        return {"result": f"sync {self.name}", "params": kwargs}


class TestToolHandler:
    """Test MCP tool handler."""
    
    @pytest.fixture
    def config(self):
        """Create test config."""
        return MCPServerConfig(
            exposed_tools=["tool1", "tool2", "tool3"]
        )
        
    @pytest.fixture
    def mock_registry(self):
        """Create mock tool registry."""
        registry = Mock()
        
        # Create tools once
        tools = {
            "tool1": MockTool("tool1", "Test tool 1"),
            "tool2": MockTool("tool2", "Test tool 2", async_execute=True),
            "tool3": MockTool("tool3", "Test tool 3"),
        }
        
        registry.get_tool = Mock(side_effect=lambda name: tools.get(name))
        return registry
        
    @pytest.fixture
    def handler(self, mock_registry, config):
        """Create test handler."""
        return ToolHandler(mock_registry, config)
        
    @pytest.mark.asyncio
    async def test_list_tools(self, handler):
        """Test listing exposed tools."""
        tools = await handler.list_tools({})
        
        assert len(tools) == 3
        assert tools[0]["name"] == "tool1"
        assert tools[0]["description"] == "Test tool 1"
        assert "inputSchema" in tools[0]
        assert tools[0]["inputSchema"]["type"] == "object"
        assert "test_param" in tools[0]["inputSchema"]["properties"]
        
    @pytest.mark.asyncio
    async def test_list_tools_with_missing_tool(self, handler, mock_registry):
        """Test listing when a tool is not found."""
        # Create tools
        tools = {
            "tool1": MockTool("tool1", "Test tool 1"),
            "tool3": MockTool("tool3", "Test tool 3"),
        }
        
        # Make tool2 not found
        def get_tool_side_effect(name):
            if name == "tool2":
                return None
            return tools.get(name)
            
        mock_registry.get_tool.side_effect = get_tool_side_effect
        
        tools = await handler.list_tools({})
        
        # Should only return 2 tools
        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["name"] == "tool3"
        
    @pytest.mark.asyncio
    async def test_list_tools_with_error(self, handler, mock_registry):
        """Test listing when tool loading fails."""
        # Create tools
        tools = {
            "tool1": MockTool("tool1", "Test tool 1"),
            "tool3": MockTool("tool3", "Test tool 3"),
        }
        
        def get_tool_side_effect(name):
            if name == "tool2":
                raise RuntimeError("Tool loading failed")
            return tools.get(name)
            
        mock_registry.get_tool.side_effect = get_tool_side_effect
        
        tools = await handler.list_tools({})
        
        # Should return tools that loaded successfully
        assert len(tools) == 2
        
    def test_get_tool_caching(self, handler, mock_registry):
        """Test tool caching."""
        # Get tool twice
        tool1 = handler._get_tool("tool1")
        tool2 = handler._get_tool("tool1")
        
        # Should be the same instance
        assert tool1 is tool2
        # Registry should only be called once
        assert mock_registry.get_tool.call_count == 1
        
    def test_convert_to_mcp_format(self, handler):
        """Test converting AITool to MCP format."""
        tool = MockTool("test", "Test tool")
        
        mcp_tool = handler._convert_to_mcp_format(tool)
        
        assert mcp_tool["name"] == "test"
        assert mcp_tool["description"] == "Test tool"
        assert mcp_tool["inputSchema"]["type"] == "object"
        assert mcp_tool["inputSchema"]["properties"]["test_param"]["type"] == "string"
        assert mcp_tool["inputSchema"]["required"] == ["test_param"]
        assert "$schema" in mcp_tool["inputSchema"]
        
    @pytest.mark.asyncio
    async def test_call_tool_sync(self, handler):
        """Test calling a synchronous tool."""
        params = {
            "name": "tool1",
            "arguments": {"test_param": "value1"}
        }
        
        result = await handler.call_tool(params)
        
        assert "content" in result
        assert result["content"][0]["type"] == "text"
        content = json.loads(result["content"][0]["text"])
        assert content["result"] == "sync tool1"
        assert "test_param" in content["params"]
        
    @pytest.mark.asyncio
    async def test_call_tool_async(self, handler):
        """Test calling an asynchronous tool."""
        # Mock async tool execution
        tool2 = handler._get_tool("tool2")
        tool2.execute = AsyncMock(return_value={"result": "async tool2"})
        
        params = {
            "name": "tool2",
            "arguments": {"test_param": "value2"}
        }
        
        result = await handler.call_tool(params)
        
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert content["result"] == "async tool2"
        
    @pytest.mark.asyncio
    async def test_call_tool_missing_name(self, handler):
        """Test calling tool without name."""
        params = {"arguments": {}}
        
        with pytest.raises(ValueError, match="Missing required field: name"):
            await handler.call_tool(params)
            
    @pytest.mark.asyncio
    async def test_call_tool_not_exposed(self, handler):
        """Test calling tool that's not exposed."""
        params = {
            "name": "unexposed_tool",
            "arguments": {}
        }
        
        with pytest.raises(ValueError, match="Tool 'unexposed_tool' not found"):
            await handler.call_tool(params)
            
    @pytest.mark.asyncio
    async def test_call_tool_not_available(self, handler, mock_registry):
        """Test calling tool that doesn't exist in registry."""
        mock_registry.get_tool.return_value = None
        
        params = {
            "name": "tool1",
            "arguments": {}
        }
        
        with pytest.raises(ValueError, match="Tool 'tool1' not available"):
            await handler.call_tool(params)
            
    @pytest.mark.asyncio
    async def test_call_tool_execution_error(self, handler):
        """Test tool execution error handling."""
        tool = handler._get_tool("tool1")
        tool.execute = Mock(side_effect=RuntimeError("Execution failed"))
        
        params = {
            "name": "tool1",
            "arguments": {"test_param": "value"}
        }
        
        result = await handler.call_tool(params)
        
        assert result["isError"] is True
        assert "content" in result
        assert "Execution failed" in result["content"][0]["text"]
        
    @pytest.mark.asyncio
    async def test_call_tool_with_context(self, handler):
        """Test tool execution with context."""
        params = {
            "name": "tool1",
            "arguments": {"test_param": "value"},
            "sessionId": "test-session"
        }
        
        result = await handler.call_tool(params)
        
        content = json.loads(result["content"][0]["text"])
        # Check that context was added
        assert "_agent_id" in content["params"]
        assert content["params"]["_agent_id"] == "mcp_client"
        assert "_from_agent" in content["params"]
        assert "_session_id" in content["params"]
        
    def test_format_tool_result_dict(self, handler):
        """Test formatting dict result."""
        result = handler._format_tool_result({"key": "value"})
        
        assert result["content"][0]["type"] == "text"
        assert json.loads(result["content"][0]["text"]) == {"key": "value"}
        
    def test_format_tool_result_list(self, handler):
        """Test formatting list result."""
        result = handler._format_tool_result([1, 2, 3])
        
        assert result["content"][0]["type"] == "text"
        assert json.loads(result["content"][0]["text"]) == [1, 2, 3]
        
    def test_format_tool_result_string(self, handler):
        """Test formatting string result."""
        result = handler._format_tool_result("Hello world")
        
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Hello world"
        
    def test_format_tool_result_other(self, handler):
        """Test formatting other types."""
        result = handler._format_tool_result(12345)
        
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "12345"