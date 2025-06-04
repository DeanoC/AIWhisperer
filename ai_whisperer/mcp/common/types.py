"""Type definitions for MCP protocol."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class MCPTransport(str, Enum):
    """Supported MCP transport types."""
    STDIO = "stdio"
    WEBSOCKET = "websocket"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    name: str
    transport: MCPTransport
    command: Optional[List[str]] = None  # For stdio transport
    url: Optional[str] = None  # For websocket transport
    env: Optional[Dict[str, str]] = None
    timeout: float = 30.0  # Connection timeout in seconds


@dataclass
class MCPToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    
    @property
    def qualified_name(self) -> str:
        """Get fully qualified tool name."""
        return f"mcp_{self.server_name}_{self.name}"


@dataclass
class MCPResourceDefinition:
    """Definition of an MCP resource."""
    uri: str
    name: str
    mime_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""
    name: str
    version: str
    protocol_version: str
    capabilities: Dict[str, bool]


@dataclass 
class MCPRequest:
    """JSON-RPC request for MCP."""
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    
    def to_dict(self) -> dict:
        """Convert to JSON-RPC format."""
        request = {
            "jsonrpc": "2.0",
            "method": self.method,
        }
        if self.params is not None:
            request["params"] = self.params
        if self.id is not None:
            request["id"] = self.id
        return request


@dataclass
class MCPResponse:
    """JSON-RPC response from MCP."""
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    
    @property
    def is_error(self) -> bool:
        """Check if response is an error."""
        return self.error is not None
        
    @classmethod
    def from_dict(cls, data: dict) -> "MCPResponse":
        """Create from JSON-RPC response dict."""
        return cls(
            result=data.get("result"),
            error=data.get("error"),
            id=data.get("id")
        )