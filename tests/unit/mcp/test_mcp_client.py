"""Tests for MCP client."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.mcp.client.client import MCPClient
from ai_whisperer.mcp.common.types import MCPServerConfig, MCPTransport, MCPToolDefinition
from ai_whisperer.mcp.client.exceptions import MCPConnectionError, MCPError


class TestMCPClient:
    """Test MCP client functionality."""
    
    @pytest.fixture
    def server_config(self):
        """Create test server configuration."""
        return MCPServerConfig(
            name="test_server",
            transport=MCPTransport.STDIO,
            command=["echo", "test"],
            timeout=5.0
        )
        
    @pytest.fixture
    def mock_transport(self):
        """Create mock transport."""
        transport = AsyncMock()
        transport.is_connected = True
        transport.connect = AsyncMock()
        transport.send_request = AsyncMock()
        transport.close = AsyncMock()
        return transport
        
    @pytest.mark.asyncio
    async def test_client_initialization(self, server_config):
        """Test client initialization."""
        client = MCPClient(server_config)
        
        assert client.config == server_config
        assert not client.initialized
        assert client.transport is None
        assert len(client.tools) == 0
        
    @pytest.mark.asyncio
    async def test_client_connect(self, server_config, mock_transport):
        """Test client connection."""
        client = MCPClient(server_config)
        
        # Mock transport creation
        with patch.object(client, '_create_transport', return_value=mock_transport):
            # Mock successful initialization
            mock_transport.send_request.return_value = AsyncMock(
                is_error=False,
                result={
                    "protocolVersion": "0.1.0",
                    "serverInfo": {"name": "test", "version": "1.0"},
                    "capabilities": {"tools": True}
                }
            )
            
            await client.connect()
            
            assert client.initialized
            assert client.transport == mock_transport
            assert client.server_info.name == "test"
            assert client.server_info.version == "1.0"
            mock_transport.connect.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_client_list_tools(self, server_config, mock_transport):
        """Test listing tools."""
        client = MCPClient(server_config)
        client.transport = mock_transport
        client.initialized = True
        
        # Add test tools
        test_tool = MCPToolDefinition(
            name="test_tool",
            description="Test tool",
            input_schema={},
            server_name="test_server"
        )
        client.tools = {"test_tool": test_tool}
        
        tools = await client.list_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        
    @pytest.mark.asyncio
    async def test_client_call_tool(self, server_config, mock_transport):
        """Test calling a tool."""
        client = MCPClient(server_config)
        client.transport = mock_transport
        client.initialized = True
        
        # Add test tool
        test_tool = MCPToolDefinition(
            name="test_tool",
            description="Test tool",
            input_schema={},
            server_name="test_server"
        )
        client.tools = {"test_tool": test_tool}
        
        # Mock tool call response
        mock_transport.send_request.return_value = AsyncMock(
            is_error=False,
            result={
                "content": [
                    {"type": "text", "text": "Tool executed successfully"}
                ]
            }
        )
        
        result = await client.call_tool("test_tool", {"param": "value"})
        
        assert result["content"][0]["text"] == "Tool executed successfully"
        
    @pytest.mark.asyncio
    async def test_client_call_unknown_tool(self, server_config):
        """Test calling unknown tool raises error."""
        client = MCPClient(server_config)
        client.initialized = True
        
        with pytest.raises(MCPError, match="Tool 'unknown' not found"):
            await client.call_tool("unknown")
            
    @pytest.mark.asyncio
    async def test_client_context_manager(self, server_config, mock_transport):
        """Test client as async context manager."""
        with patch('ai_whisperer.mcp.client.client.MCPClient._create_transport', return_value=mock_transport):
            # Mock successful initialization
            mock_transport.send_request.return_value = AsyncMock(
                is_error=False,
                result={
                    "protocolVersion": "0.1.0",
                    "capabilities": {}
                }
            )
            
            async with MCPClient(server_config) as client:
                assert client.initialized
                
            mock_transport.close.assert_called_once()