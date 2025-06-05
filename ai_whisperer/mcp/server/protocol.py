"""MCP protocol implementation for server."""

import logging
from typing import Dict, Any, Optional, Callable, Coroutine
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPError:
    """MCP error response."""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-RPC error format."""
        error = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            error["data"] = self.data
        return error


# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPProtocol:
    """MCP protocol handler for server."""
    
    # Protocol version
    PROTOCOL_VERSION = "2024-11-05"
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup method handlers."""
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
            "monitoring/metrics": self.handle_monitoring_metrics,
            "monitoring/health": self.handle_monitoring_health,
        }
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request."""
        # Validate request structure
        if not isinstance(request, dict):
            return self._error_response(
                MCPError(PARSE_ERROR, "Request must be a JSON object"),
                None
            )
            
        # Check required fields
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            return self._error_response(
                MCPError(INVALID_REQUEST, "Invalid JSON-RPC version"),
                request.get("id")
            )
            
        method = request.get("method")
        if not method:
            return self._error_response(
                MCPError(INVALID_REQUEST, "Missing method"),
                request.get("id")
            )
            
        # Get handler
        handler = self.handlers.get(method)
        if not handler:
            return self._error_response(
                MCPError(METHOD_NOT_FOUND, f"Method '{method}' not found"),
                request.get("id")
            )
            
        # Execute handler
        try:
            params = request.get("params", {})
            result = await handler(params)
            return self._success_response(result, request.get("id"))
            
        except Exception as e:
            logger.error(f"Error handling method '{method}': {e}", exc_info=True)
            return self._error_response(
                MCPError(INTERNAL_ERROR, str(e)),
                request.get("id")
            )
            
    def _success_response(self, result: Any, request_id: Optional[Any]) -> Dict[str, Any]:
        """Create success response."""
        response = {
            "jsonrpc": "2.0",
            "result": result
        }
        if request_id is not None:
            response["id"] = request_id
        return response
        
    def _error_response(self, error: MCPError, request_id: Optional[Any]) -> Dict[str, Any]:
        """Create error response."""
        response = {
            "jsonrpc": "2.0",
            "error": error.to_dict()
        }
        if request_id is not None:
            response["id"] = request_id
        return response
        
    # Handler methods (to be implemented in server.py)
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        raise NotImplementedError
        
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        raise NotImplementedError
        
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        raise NotImplementedError
        
    async def handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        raise NotImplementedError
        
    async def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        raise NotImplementedError
        
    async def handle_resources_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/write request."""
        raise NotImplementedError
        
    async def handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        raise NotImplementedError
        
    async def handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        raise NotImplementedError
        
    async def handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request."""
        return {"pong": True}
        
    async def handle_monitoring_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitoring/metrics request."""
        raise NotImplementedError
        
    async def handle_monitoring_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitoring/health request."""
        raise NotImplementedError