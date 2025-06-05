"""MCP server implementation."""

import logging
from typing import Dict, Any, List, Optional

from ...tools.tool_registry_lazy import LazyToolRegistry
from ...utils.path import PathManager
from ..common.types import MCPTransport
from .config import MCPServerConfig, TransportType
from .protocol import MCPProtocol
from .handlers.tools import ToolHandler
from .handlers.resources import ResourceHandler
from .handlers.prompts import PromptHandler

logger = logging.getLogger(__name__)


class MCPServer(MCPProtocol):
    """MCP server that exposes AIWhisperer tools."""
    
    def __init__(self, config: MCPServerConfig):
        super().__init__()
        self.config = config
        self.tool_registry = LazyToolRegistry()
        self.path_manager = PathManager()
        
        # Initialize PathManager if not already initialized
        if not hasattr(self.path_manager, '_initialized') or not self.path_manager._initialized:
            import os
            workspace = os.getcwd()
            self.path_manager.initialize(config_values={
                'project_path': workspace,
                'workspace_path': workspace,
                'output_path': os.path.join(workspace, 'output')
            })
        
        # Initialize handlers
        self.tool_handler = ToolHandler(self.tool_registry, config)
        self.resource_handler = ResourceHandler(self.path_manager, config)
        self.prompt_handler = PromptHandler(config)
        
        # Server state
        self.initialized = False
        self.client_info = {}
        
    async def start(self):
        """Start the MCP server."""
        # Only log for non-stdio transports
        if self.config.transport != TransportType.STDIO:
            logger.info(f"Starting MCP server with transport: {self.config.transport}")
        
        # Create transport based on config
        if self.config.transport == TransportType.STDIO:
            from .transports.stdio import StdioServerTransport
            self.transport = StdioServerTransport(self)
        elif self.config.transport == TransportType.WEBSOCKET:
            from .transports.websocket import WebSocketServerTransport
            self.transport = WebSocketServerTransport(
                self,
                self.config.host,
                self.config.port,
                max_connections=self.config.ws_max_connections,
                heartbeat_interval=self.config.ws_heartbeat_interval,
                heartbeat_timeout=self.config.ws_heartbeat_timeout,
                request_timeout=self.config.ws_request_timeout,
                max_queue_size=self.config.ws_max_queue_size,
                enable_compression=self.config.ws_enable_compression
            )
        elif self.config.transport == TransportType.SSE:
            from .transports.sse import SSEServerTransport
            self.transport = SSEServerTransport(
                self,
                self.config.host,
                self.config.port,
                heartbeat_interval=self.config.sse_heartbeat_interval,
                max_connections=self.config.sse_max_connections,
                cors_origins=set(self.config.sse_cors_origins) if self.config.sse_cors_origins else None
            )
        else:
            raise ValueError(f"Unknown transport: {self.config.transport}")
            
        await self.transport.start()
        
    async def stop(self):
        """Stop the MCP server."""
        if hasattr(self, 'transport'):
            await self.transport.stop()
            
    # Protocol handler implementations
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        # Validate required fields
        protocol_version = params.get("protocolVersion")
        if not protocol_version:
            raise ValueError("Missing required field: protocolVersion")
            
        capabilities = params.get("capabilities")
        if capabilities is None:
            raise ValueError("Missing required field: capabilities")
            
        # Store client info
        self.client_info = params.get("clientInfo", {})
        
        # Mark as initialized
        self.initialized = True
        
        logger.info(
            f"Initialized MCP session with client: "
            f"{self.client_info.get('name', 'unknown')} "
            f"v{self.client_info.get('version', 'unknown')}"
        )
        
        # Return server capabilities
        return {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {
                "tools": {},  # We support tools
                "resources": {
                    "subscribe": False,  # No subscription support yet
                    "write": True  # Support writing resources
                },
                "prompts": {},  # We support prompts
            },
            "serverInfo": {
                "name": self.config.server_name,
                "version": self.config.server_version,
            }
        }
        
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        tools = await self.tool_handler.list_tools(params)
        return {"tools": tools}
        
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        return await self.tool_handler.call_tool(params)
        
    async def handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        resources = await self.resource_handler.list_resources(params)
        return {"resources": resources}
        
    async def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        contents = await self.resource_handler.read_resource(params)
        return {"contents": contents}
        
    async def handle_resources_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/write request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        await self.resource_handler.write_resource(params)
        return {}  # Empty response on success
        
    async def handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        prompts = await self.prompt_handler.list_prompts(params)
        return {"prompts": prompts}
        
    async def handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        return await self.prompt_handler.get_prompt(params)