"""Unit tests for MCP protocol handler."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.mcp.server.protocol import (
    MCPProtocol, MCPError,
    PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR
)


class MockProtocol(MCPProtocol):
    """Mock protocol with implemented handlers for testing."""
    
    def __init__(self):
        # Call parent but then override handlers
        super().__init__()
        # Override with mock handlers
        self.handle_initialize = AsyncMock(return_value={"initialized": True})
        self.handle_tools_list = AsyncMock(return_value={"tools": []})
        self.handle_tools_call = AsyncMock(return_value={"result": "success"})
        self.handle_resources_list = AsyncMock(return_value={"resources": []})
        self.handle_resources_read = AsyncMock(return_value={"contents": []})
        self.handle_resources_write = AsyncMock(return_value={})
        self.handle_prompts_list = AsyncMock(return_value={"prompts": []})
        self.handle_prompts_get = AsyncMock(return_value={"prompt": {}})
        # Re-setup handlers with our mocks
        self._setup_handlers()
        
    async def handle_ping(self, params):
        """Override ping handler for testing."""
        return {"pong": True}
        
    def _setup_handlers(self):
        """Override to use our mock handlers."""
        self.handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
            "resources/list": self.handle_resources_list,
            "resources/read": self.handle_resources_read,
            "resources/write": self.handle_resources_write,
            "prompts/list": self.handle_prompts_list,
            "prompts/get": self.handle_prompts_get,
            "ping": self.handle_ping,
        }


class TestMCPProtocol:
    """Test MCP protocol handler."""
    
    @pytest.fixture
    def protocol(self):
        """Create a test protocol instance."""
        return MCPProtocol()
        
    @pytest.fixture
    def mock_handlers(self):
        """Create protocol with mock handlers."""
        return MockProtocol()
        
    @pytest.mark.asyncio
    async def test_valid_request(self, mock_handlers):
        """Test handling a valid request."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
            "id": 1
        }
        
        response = await mock_handlers.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["initialized"] is True
        mock_handlers.handle_initialize.assert_called_once_with({"protocolVersion": "2024-11-05"})
        
    @pytest.mark.asyncio
    async def test_invalid_jsonrpc_version(self, protocol):
        """Test handling request with invalid JSON-RPC version."""
        request = {
            "jsonrpc": "1.0",  # Invalid version
            "method": "initialize",
            "id": 1
        }
        
        response = await protocol.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == INVALID_REQUEST
        assert "JSON-RPC version" in response["error"]["message"]
        
    @pytest.mark.asyncio
    async def test_missing_method(self, protocol):
        """Test handling request without method."""
        request = {
            "jsonrpc": "2.0",
            "params": {},
            "id": 1
        }
        
        response = await protocol.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == INVALID_REQUEST
        assert "Missing method" in response["error"]["message"]
        
    @pytest.mark.asyncio
    async def test_method_not_found(self, protocol):
        """Test handling request with unknown method."""
        request = {
            "jsonrpc": "2.0",
            "method": "unknown/method",
            "params": {},
            "id": 1
        }
        
        response = await protocol.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == METHOD_NOT_FOUND
        assert "unknown/method" in response["error"]["message"]
        
    @pytest.mark.asyncio
    async def test_handler_exception(self, mock_handlers):
        """Test handling when handler raises exception."""
        mock_handlers.handle_initialize.side_effect = ValueError("Test error")
        
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        }
        
        response = await mock_handlers.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == INTERNAL_ERROR
        assert "Test error" in response["error"]["message"]
        
    @pytest.mark.asyncio
    async def test_notification_request(self, mock_handlers):
        """Test handling notification (no id)."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {}
            # No id - this is a notification
        }
        
        response = await mock_handlers.handle_request(request)
        
        # Response should still have result but no id
        assert "result" in response
        assert "id" not in response
        
    @pytest.mark.asyncio
    async def test_ping_handler(self, protocol):
        """Test ping handler."""
        request = {
            "jsonrpc": "2.0",
            "method": "ping",
            "params": {},
            "id": "test-ping"
        }
        
        response = await protocol.handle_request(request)
        
        assert response["id"] == "test-ping"
        assert "result" in response
        assert response["result"]["pong"] is True
        
    def test_mcp_error_to_dict(self):
        """Test MCPError conversion to dict."""
        error = MCPError(
            code=-32000,
            message="Custom error",
            data={"details": "Additional info"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["code"] == -32000
        assert error_dict["message"] == "Custom error"
        assert error_dict["data"]["details"] == "Additional info"
        
    def test_mcp_error_without_data(self):
        """Test MCPError without data field."""
        error = MCPError(code=-32000, message="Simple error")
        
        error_dict = error.to_dict()
        
        assert "data" not in error_dict
        
    @pytest.mark.asyncio
    async def test_all_handler_methods(self, mock_handlers):
        """Test all handler methods are properly routed."""
        methods = [
            ("tools/list", mock_handlers.handle_tools_list),
            ("tools/call", mock_handlers.handle_tools_call),
            ("resources/list", mock_handlers.handle_resources_list),
            ("resources/read", mock_handlers.handle_resources_read),
            ("resources/write", mock_handlers.handle_resources_write),
            ("prompts/list", mock_handlers.handle_prompts_list),
            ("prompts/get", mock_handlers.handle_prompts_get),
        ]
        
        for method_name, handler_mock in methods:
            request = {
                "jsonrpc": "2.0",
                "method": method_name,
                "params": {"test": "param"},
                "id": f"test-{method_name}"
            }
            
            await mock_handlers.handle_request(request)
            handler_mock.assert_called_once_with({"test": "param"})
            handler_mock.reset_mock()