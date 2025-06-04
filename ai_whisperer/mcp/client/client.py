"""MCP client implementation."""

import logging
from typing import Dict, List, Optional, Any

from ..common.types import (
    MCPServerConfig, MCPRequest, MCPResponse, MCPServerInfo,
    MCPToolDefinition, MCPResourceDefinition, MCPTransport
)
from .transports import MCPTransportBase, StdioTransport
from .exceptions import MCPError, MCPConnectionError, MCPProtocolError

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP client for connecting to external MCP servers."""
    
    def __init__(self, server_config: MCPServerConfig):
        self.config = server_config
        self.transport: Optional[MCPTransportBase] = None
        self.server_info: Optional[MCPServerInfo] = None
        self.tools: Dict[str, MCPToolDefinition] = {}
        self.resources: Dict[str, MCPResourceDefinition] = {}
        self.initialized = False
        
    def _create_transport(self) -> MCPTransportBase:
        """Create transport based on configuration."""
        if self.config.transport == MCPTransport.STDIO:
            if not self.config.command:
                raise ValueError("Command required for stdio transport")
            return StdioTransport(
                command=self.config.command,
                env=self.config.env,
                timeout=self.config.timeout
            )
        elif self.config.transport == MCPTransport.WEBSOCKET:
            # TODO: Implement WebSocket transport
            raise NotImplementedError("WebSocket transport not yet implemented")
        else:
            raise ValueError(f"Unknown transport type: {self.config.transport}")
            
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        if self.initialized:
            return
            
        # Create and connect transport
        self.transport = self._create_transport()
        await self.transport.connect()
        
        # Initialize MCP session
        await self._initialize()
        
    async def _initialize(self) -> None:
        """Initialize MCP session."""
        try:
            # Send initialize request
            response = await self._send_request("initialize", {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "roots": {"listChanged": False},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "aiwhisperer",
                    "version": "1.0.0"
                }
            })
            
            # Parse server info
            self.server_info = MCPServerInfo(
                name=response.get("serverInfo", {}).get("name", "unknown"),
                version=response.get("serverInfo", {}).get("version", "unknown"),
                protocol_version=response.get("protocolVersion", "unknown"),
                capabilities=response.get("capabilities", {})
            )
            
            self.initialized = True
            logger.info(f"Initialized MCP session with {self.server_info.name} v{self.server_info.version}")
            
            # Don't cache tools during initialization - some servers need time
            # Tools will be cached on first access
            logger.debug("Skipping tool caching during initialization")
                
            # Cache available resources if supported
            if self.server_info.capabilities.get("resources", False):
                await self._cache_resources()
                
        except Exception as e:
            raise MCPConnectionError(f"Failed to initialize MCP session: {e}")
            
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to server."""
        if not self.transport:
            raise MCPConnectionError("Client not connected")
            
        request = MCPRequest(method=method, params=params)
        response = await self.transport.send_request(request)
        
        if response.is_error:
            error = response.error
            raise MCPError(
                message=error.get("message", "Unknown error"),
                code=error.get("code"),
                data=error.get("data")
            )
            
        return response.result or {}
        
    async def _cache_tools(self) -> None:
        """Cache available tools from server."""
        try:
            response = await self._send_request("tools/list")
            logger.debug(f"Tools list response: {response}")
            tools = response.get("tools", [])
            
            self.tools.clear()
            for tool_data in tools:
                tool = MCPToolDefinition(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    input_schema=tool_data.get("inputSchema", {}),
                    server_name=self.config.name
                )
                self.tools[tool.name] = tool
                
            logger.info(f"Cached {len(self.tools)} tools from {self.config.name}")
            
        except Exception as e:
            logger.error(f"Failed to cache tools: {e}", exc_info=True)
            
    async def _cache_resources(self) -> None:
        """Cache available resources from server."""
        try:
            response = await self._send_request("resources/list")
            resources = response.get("resources", [])
            
            self.resources.clear()
            for resource_data in resources:
                resource = MCPResourceDefinition(
                    uri=resource_data["uri"],
                    name=resource_data["name"],
                    mime_type=resource_data.get("mimeType"),
                    description=resource_data.get("description")
                )
                self.resources[resource.uri] = resource
                
            logger.info(f"Cached {len(self.resources)} resources from {self.config.name}")
            
        except Exception as e:
            logger.error(f"Failed to cache resources: {e}")
            
    async def list_tools(self) -> List[MCPToolDefinition]:
        """List available tools."""
        if not self.initialized:
            raise MCPConnectionError("Client not initialized")
            
        # Cache tools on first access if not already cached
        if not self.tools and "tools" in self.server_info.capabilities:
            await self._cache_tools()
            
        return list(self.tools.values())
        
    async def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        """Get tool definition by name."""
        return self.tools.get(name)
        
    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Call an MCP tool."""
        if not self.initialized:
            raise MCPConnectionError("Client not initialized")
            
        if name not in self.tools:
            raise MCPError(f"Tool '{name}' not found")
            
        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        
        return response
        
    async def list_resources(self) -> List[MCPResourceDefinition]:
        """List available resources."""
        if not self.initialized:
            raise MCPConnectionError("Client not initialized")
            
        return list(self.resources.values())
        
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource."""
        if not self.initialized:
            raise MCPConnectionError("Client not initialized")
            
        response = await self._send_request("resources/read", {
            "uri": uri
        })
        
        return response
        
    async def is_alive(self) -> bool:
        """Check if connection is still alive."""
        if not self.transport or not self.initialized:
            return False
            
        try:
            # Send a simple request to check connection
            await self._send_request("ping", {})
            return True
        except:
            return False
            
    async def close(self) -> None:
        """Close the connection."""
        if self.transport:
            await self.transport.close()
            self.transport = None
            self.initialized = False
            
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()