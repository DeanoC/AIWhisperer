"""Unit tests for MCP server."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_whisperer.mcp.server.server import MCPServer
from ai_whisperer.mcp.server.config import MCPServerConfig, TransportType


class TestMCPServer:
    """Test MCP server."""
    
    @pytest.fixture
    def config(self):
        """Create test server config."""
        return MCPServerConfig(
            transport=TransportType.STDIO,
            exposed_tools=["read_file", "list_directory"],
            server_name="test-server",
            server_version="1.0.0"
        )
        
    @pytest.fixture
    def server(self, config):
        """Create test server instance."""
        with patch('ai_whisperer.mcp.server.server.LazyToolRegistry'), \
             patch('ai_whisperer.mcp.server.server.PathManager') as mock_pm:
            # Mock PathManager initialization
            mock_pm.return_value._initialized = True
            return MCPServer(config)
            
    @pytest.mark.asyncio
    async def test_server_initialization(self, config):
        """Test server initialization."""
        with patch('ai_whisperer.mcp.server.server.LazyToolRegistry') as mock_registry, \
             patch('ai_whisperer.mcp.server.server.PathManager') as mock_pm, \
             patch('ai_whisperer.mcp.server.server.ToolHandler') as mock_tool_handler, \
             patch('ai_whisperer.mcp.server.server.ResourceHandler') as mock_resource_handler:
            
            mock_pm.return_value._initialized = True
            
            server = MCPServer(config)
            
            assert server.config == config
            assert not server.initialized
            assert server.client_info == {}
            mock_tool_handler.assert_called_once()
            mock_resource_handler.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_start_stdio_transport(self, server):
        """Test starting server with stdio transport."""
        with patch('ai_whisperer.mcp.server.transports.stdio.StdioServerTransport') as mock_transport:
            mock_transport_instance = AsyncMock()
            mock_transport.return_value = mock_transport_instance
            
            await server.start()
            
            mock_transport.assert_called_once_with(server)
            mock_transport_instance.start.assert_called_once()
            
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="aiohttp not installed in test environment")
    async def test_start_websocket_transport(self, config):
        """Test starting server with websocket transport."""
        config.transport = TransportType.WEBSOCKET
        config.host = "localhost"
        config.port = 3000
        
        # Import the module first to ensure it exists
        from ai_whisperer.mcp.server.transports import websocket
        
        with patch('ai_whisperer.mcp.server.server.LazyToolRegistry'), \
             patch('ai_whisperer.mcp.server.server.PathManager') as mock_pm, \
             patch.object(websocket, 'WebSocketServerTransport') as mock_transport:
            
            mock_pm.return_value._initialized = True
            mock_transport_instance = AsyncMock()
            mock_transport.return_value = mock_transport_instance
            
            server = MCPServer(config)
            await server.start()
            
            mock_transport.assert_called_once_with(server, "localhost", 3000)
            mock_transport_instance.start.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_stop_server(self, server):
        """Test stopping server."""
        server.transport = AsyncMock()
        
        await server.stop()
        
        server.transport.stop.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_handle_initialize(self, server):
        """Test initialize request handling."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {"subscribe": False}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0"
            }
        }
        
        result = await server.handle_initialize(params)
        
        assert server.initialized is True
        assert server.client_info == params["clientInfo"]
        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "test-server"
        assert result["serverInfo"]["version"] == "1.0.0"
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]
        assert "prompts" in result["capabilities"]
        
    @pytest.mark.asyncio
    async def test_handle_initialize_missing_protocol_version(self, server):
        """Test initialize with missing protocol version."""
        params = {
            "capabilities": {}
        }
        
        with pytest.raises(ValueError, match="Missing required field: protocolVersion"):
            await server.handle_initialize(params)
            
    @pytest.mark.asyncio
    async def test_handle_initialize_missing_capabilities(self, server):
        """Test initialize with missing capabilities."""
        params = {
            "protocolVersion": "2024-11-05"
        }
        
        with pytest.raises(ValueError, match="Missing required field: capabilities"):
            await server.handle_initialize(params)
            
    @pytest.mark.asyncio
    async def test_handle_tools_list_not_initialized(self, server):
        """Test tools/list when server not initialized."""
        with pytest.raises(RuntimeError, match="Server not initialized"):
            await server.handle_tools_list({})
            
    @pytest.mark.asyncio
    async def test_handle_tools_list(self, server):
        """Test tools/list request."""
        server.initialized = True
        server.tool_handler.list_tools = AsyncMock(return_value=[
            {"name": "test_tool", "description": "Test tool"}
        ])
        
        result = await server.handle_tools_list({})
        
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "test_tool"
        
    @pytest.mark.asyncio
    async def test_handle_tools_call(self, server):
        """Test tools/call request."""
        server.initialized = True
        server.tool_handler.call_tool = AsyncMock(return_value={
            "content": [{"type": "text", "text": "Result"}]
        })
        
        params = {
            "name": "test_tool",
            "arguments": {"arg": "value"}
        }
        
        result = await server.handle_tools_call(params)
        
        assert result["content"][0]["text"] == "Result"
        server.tool_handler.call_tool.assert_called_once_with(params)
        
    @pytest.mark.asyncio
    async def test_handle_resources_list(self, server):
        """Test resources/list request."""
        server.initialized = True
        server.resource_handler.list_resources = AsyncMock(return_value=[
            {"uri": "file:///test.py", "name": "test.py"}
        ])
        
        result = await server.handle_resources_list({})
        
        assert "resources" in result
        assert len(result["resources"]) == 1
        assert result["resources"][0]["name"] == "test.py"
        
    @pytest.mark.asyncio
    async def test_handle_resources_read(self, server):
        """Test resources/read request."""
        server.initialized = True
        server.resource_handler.read_resource = AsyncMock(return_value=[
            {"uri": "file:///test.py", "text": "print('hello')"}
        ])
        
        params = {"uri": "file:///test.py"}
        
        result = await server.handle_resources_read(params)
        
        assert "contents" in result
        assert result["contents"][0]["text"] == "print('hello')"
        
    @pytest.mark.asyncio
    async def test_handle_resources_write(self, server):
        """Test resources/write request."""
        server.initialized = True
        server.resource_handler.write_resource = AsyncMock()
        
        params = {
            "uri": "file:///test.py",
            "contents": [{"text": "print('hello')"}]
        }
        
        result = await server.handle_resources_write(params)
        
        assert result == {}
        server.resource_handler.write_resource.assert_called_once_with(params)
        
    @pytest.mark.asyncio
    async def test_handle_prompts_list(self, server):
        """Test prompts/list request."""
        server.initialized = True
        
        result = await server.handle_prompts_list({})
        
        assert "prompts" in result
        assert result["prompts"] == []  # Currently returns empty list
        
    @pytest.mark.asyncio
    async def test_handle_prompts_get(self, server):
        """Test prompts/get request."""
        server.initialized = True
        
        params = {"name": "test_prompt"}
        
        with pytest.raises(ValueError, match="Prompt 'test_prompt' not found"):
            await server.handle_prompts_get(params)
            
    @pytest.mark.asyncio
    async def test_handle_prompts_get_missing_name(self, server):
        """Test prompts/get with missing name."""
        server.initialized = True
        
        with pytest.raises(ValueError, match="Missing required field: name"):
            await server.handle_prompts_get({})