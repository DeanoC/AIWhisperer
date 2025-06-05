"""MCP server implementation."""

import logging
import time
from typing import Dict, Any, List, Optional

from ...tools.tool_registry_lazy import LazyToolRegistry
from ...utils.path import PathManager
from ..common.types import MCPTransport
from .config import MCPServerConfig, TransportType
from .protocol import MCPProtocol
from .handlers.tools import ToolHandler
from .handlers.resources import ResourceHandler
from .handlers.prompts import PromptHandler
from .monitoring import MCPMonitor
from .logging import setup_mcp_logging, MCPLogger

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
        
        # Initialize monitoring and logging
        self.monitor = MCPMonitor(
            server_name=config.server_name,
            enable_metrics=config.enable_metrics,
            enable_audit_log=config.enable_audit_log,
            metrics_retention_minutes=config.metrics_retention_minutes,
            slow_request_threshold_ms=config.slow_request_threshold_ms,
            max_recent_errors=config.max_recent_errors,
            audit_log_file=config.audit_log_file
        )
        
        # Initialize handlers with monitor
        self.tool_handler = ToolHandler(self.tool_registry, config, self.monitor)
        self.resource_handler = ResourceHandler(self.path_manager, config)
        self.prompt_handler = PromptHandler(config)
        
        # Setup structured logging
        self.mcp_logger = setup_mcp_logging(
            server_name=config.server_name,
            transport=config.transport.value,
            log_level=config.log_level,
            log_file=config.log_file,
            enable_json=config.enable_json_logging
        )
        
        # Server state
        self.initialized = False
        self.client_info = {}
        
    async def start(self):
        """Start the MCP server."""
        # Start monitoring
        await self.monitor.start()
        
        # Only log for non-stdio transports
        if self.config.transport != TransportType.STDIO:
            logger.info(f"Starting MCP server with transport: {self.config.transport}")
            self.mcp_logger.log_transport(
                logging.INFO,
                f"Starting MCP server",
                transport=self.config.transport.value,
                event="server_start"
            )
        
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
            # SSE transport removed - use FastMCP instead
            raise NotImplementedError("SSE transport is handled by FastMCP. Use ai_whisperer.mcp.server.fastmcp_runner instead.")
        else:
            raise ValueError(f"Unknown transport: {self.config.transport}")
            
        await self.transport.start()
        
    async def stop(self):
        """Stop the MCP server."""
        # Stop transport
        if hasattr(self, 'transport'):
            await self.transport.stop()
            
        # Stop monitoring
        await self.monitor.stop()
        
        if self.config.transport != TransportType.STDIO:
            self.mcp_logger.log_transport(
                logging.INFO,
                "MCP server stopped",
                transport=self.config.transport.value,
                event="server_stop"
            )
            
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming request with monitoring."""
        method = request.get("method", "unknown")
        params = request.get("params", {})
        
        # Get transport info from context if available
        transport = getattr(self, '_current_transport', None)
        connection_id = getattr(self, '_current_connection_id', None)
        
        # Track request with monitoring
        async with self.monitor.track_request(
            method=method,
            params=params,
            transport=transport,
            connection_id=connection_id
        ) as metrics:
            # Call parent's handle_request
            response = await super().handle_request(request)
            
            # Log request completion
            if "error" not in response:
                self.mcp_logger.log_request(
                    logging.INFO,
                    f"Request completed: {method}",
                    method=method,
                    request_id=request.get("id"),
                    duration_ms=metrics.duration_ms
                )
            else:
                self.mcp_logger.log_request(
                    logging.ERROR,
                    f"Request failed: {method}",
                    method=method,
                    request_id=request.get("id"),
                    duration_ms=metrics.duration_ms,
                    error=response["error"]
                )
                
            return response
            
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
        
    async def handle_monitoring_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitoring/metrics request."""
        if not self.initialized:
            raise RuntimeError("Server not initialized")
            
        return self.monitor.get_metrics()
        
    async def handle_monitoring_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitoring/health request."""
        return self.monitor.get_health()