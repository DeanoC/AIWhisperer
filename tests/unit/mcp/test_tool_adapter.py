"""Tests for MCP tool adapter."""

import pytest
import json
from unittest.mock import Mock, AsyncMock

from ai_whisperer.mcp.client.adapters.tool_adapter import MCPToolAdapter
from ai_whisperer.mcp.common.types import MCPToolDefinition
from ai_whisperer.mcp.client.exceptions import MCPToolError
from ai_whisperer.core.exceptions import ToolExecutionError


class TestMCPToolAdapter:
    """Test MCPToolAdapter functionality."""
    
    @pytest.fixture
    def tool_definition(self):
        """Create test tool definition."""
        return MCPToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "count": {"type": "integer"}
                },
                "required": ["message"]
            },
            server_name="test_server"
        )
        
    @pytest.fixture
    def mock_client(self):
        """Create mock MCP client."""
        client = AsyncMock()
        client.initialized = True
        client.call_tool = AsyncMock()
        return client
        
    def test_adapter_properties(self, tool_definition, mock_client):
        """Test adapter property methods."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        
        assert adapter.name == "mcp_test_server_test_tool"
        assert "[MCP:test_server]" in adapter.description
        assert "A test tool" in adapter.description
        assert adapter.category == "MCP External Tools"
        assert "mcp" in adapter.tags
        assert "test_server" in adapter.tags
        
    def test_adapter_schema_conversion(self, tool_definition, mock_client):
        """Test schema conversion."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        schema = adapter.parameters_schema
        
        assert schema["type"] == "object"
        assert "message" in schema["properties"]
        assert schema["required"] == ["message"]
        assert schema["additionalProperties"] is False
        
    def test_ai_prompt_instructions(self, tool_definition, mock_client):
        """Test AI prompt generation."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        instructions = adapter.get_ai_prompt_instructions()
        
        assert "mcp_test_server_test_tool" in instructions
        assert "external MCP tool" in instructions
        assert "test_server" in instructions
        assert '"message"' in instructions  # Parameter should be shown
        
    @pytest.mark.asyncio
    async def test_execute_with_arguments(self, tool_definition, mock_client):
        """Test tool execution with arguments dict."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        
        # Mock successful response
        mock_client.call_tool.return_value = {
            "content": [
                {"type": "text", "text": '{"result": "success"}'}
            ]
        }
        
        result = await adapter.execute(arguments={"message": "test", "_agent_id": "test_agent"})
        
        assert result == {"result": "success"}
        mock_client.call_tool.assert_called_once_with(
            "test_tool",
            {"message": "test"}  # Internal fields stripped
        )
        
    @pytest.mark.asyncio
    async def test_execute_with_kwargs(self, tool_definition, mock_client):
        """Test tool execution with kwargs (legacy pattern)."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        
        # Mock text response
        mock_client.call_tool.return_value = {
            "content": [
                {"type": "text", "text": "Simple text response"}
            ]
        }
        
        result = await adapter.execute(message="test", _from_agent="alice")
        
        assert result == "Simple text response"
        mock_client.call_tool.assert_called_once_with(
            "test_tool",
            {"message": "test"}  # Internal fields stripped
        )
        
    @pytest.mark.asyncio
    async def test_execute_error_response(self, tool_definition, mock_client):
        """Test handling error responses."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        
        # Mock error response
        mock_client.call_tool.return_value = {
            "isError": True,
            "content": [
                {"type": "text", "text": "Tool failed: Invalid input"}
            ]
        }
        
        with pytest.raises(ToolExecutionError, match="Tool failed: Invalid input"):
            await adapter.execute(arguments={"message": "test"})
            
    @pytest.mark.asyncio
    async def test_execute_mcp_error(self, tool_definition, mock_client):
        """Test handling MCP errors."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        
        # Mock MCP error
        mock_client.call_tool.side_effect = MCPToolError("Connection lost")
        
        with pytest.raises(ToolExecutionError, match="Connection lost"):
            await adapter.execute(arguments={"message": "test"})
            
    @pytest.mark.asyncio
    async def test_execute_auto_connect(self, tool_definition, mock_client):
        """Test automatic connection if not initialized."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        mock_client.initialized = False
        mock_client.connect = AsyncMock()
        
        # Mock response after connection
        mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Connected and executed"}]
        }
        
        result = await adapter.execute(arguments={"message": "test"})
        
        assert result == "Connected and executed"
        mock_client.connect.assert_called_once()
        
    def test_extract_content_multiple_items(self, tool_definition, mock_client):
        """Test content extraction with multiple items."""
        adapter = MCPToolAdapter(tool_definition, mock_client)
        
        response = {
            "content": [
                {"type": "text", "text": "First item"},
                {"type": "text", "text": "Second item"},
                {"type": "image", "data": "base64data"}
            ]
        }
        
        result = adapter._extract_content(response)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "First item"
        assert result[1] == "Second item"
        assert result[2]["type"] == "image"