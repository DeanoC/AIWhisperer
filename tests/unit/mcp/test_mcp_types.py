"""Tests for MCP type definitions."""

import pytest
from ai_whisperer.mcp.common.types import (
    MCPServerConfig, MCPToolDefinition, MCPRequest, MCPResponse,
    MCPTransport
)


class TestMCPTypes:
    """Test MCP type definitions."""
    
    def test_mcp_server_config(self):
        """Test MCPServerConfig creation."""
        config = MCPServerConfig(
            name="test_server",
            transport=MCPTransport.STDIO,
            command=["echo", "test"],
            env={"KEY": "value"},
            timeout=60.0
        )
        
        assert config.name == "test_server"
        assert config.transport == MCPTransport.STDIO
        assert config.command == ["echo", "test"]
        assert config.env == {"KEY": "value"}
        assert config.timeout == 60.0
        
    def test_mcp_tool_definition(self):
        """Test MCPToolDefinition."""
        tool = MCPToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            server_name="test_server"
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.qualified_name == "mcp_test_server_test_tool"
        
    def test_mcp_request(self):
        """Test MCPRequest creation and serialization."""
        request = MCPRequest(
            method="test_method",
            params={"key": "value"},
            id=123
        )
        
        data = request.to_dict()
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "test_method"
        assert data["params"] == {"key": "value"}
        assert data["id"] == 123
        
    def test_mcp_response(self):
        """Test MCPResponse parsing."""
        # Success response
        success_data = {
            "jsonrpc": "2.0",
            "result": {"data": "test"},
            "id": 123
        }
        response = MCPResponse.from_dict(success_data)
        
        assert not response.is_error
        assert response.result == {"data": "test"}
        assert response.id == 123
        
        # Error response
        error_data = {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request"},
            "id": 124
        }
        error_response = MCPResponse.from_dict(error_data)
        
        assert error_response.is_error
        assert error_response.error["code"] == -32600
        assert error_response.error["message"] == "Invalid Request"