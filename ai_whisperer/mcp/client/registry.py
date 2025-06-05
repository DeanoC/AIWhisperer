"""MCP tool registry for managing external tools."""

import logging
from typing import Dict, List, Optional, Set

from ...tools.tool_registry_lazy import LazyToolRegistry
from ...tools.base_tool import AITool
from ..common.types import MCPServerConfig
from .client import MCPClient
from .discovery import MCPToolDiscovery
from .adapters import MCPToolAdapter
from .connection_pool import MCPConnectionPool

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Registry for MCP tools from external servers."""
    
    def __init__(self, tool_registry: LazyToolRegistry = None):
        self.tool_registry = tool_registry or LazyToolRegistry()
        self.connection_pool = MCPConnectionPool()
        self.registered_servers: Dict[str, Dict] = {}
        self._registered_tool_names: Set[str] = set()
        
    async def register_mcp_server(self, config: MCPServerConfig) -> List[str]:
        """
        Register an MCP server and its tools.
        
        Args:
            config: MCP server configuration
            
        Returns:
            List of registered tool names
        """
        if config.name in self.registered_servers:
            logger.warning(f"MCP server '{config.name}' already registered, skipping")
            return []
            
        try:
            # Get or create client connection
            client = await self.connection_pool.get_client(config)
            
            # Discover tools
            discovery = MCPToolDiscovery(client)
            tools = await discovery.discover_tools()
            
            # Register each tool with AIWhisperer
            registered_tools = []
            for tool_def in tools:
                try:
                    # Create adapter
                    adapter = MCPToolAdapter(tool_def, client)
                    
                    # Register with tool registry
                    self.tool_registry.register_tool(adapter)
                    registered_tools.append(adapter.name)
                    self._registered_tool_names.add(adapter.name)
                    
                    logger.debug(f"Registered MCP tool: {adapter.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to register tool '{tool_def.name}': {e}")
                    
            # Store registration info
            self.registered_servers[config.name] = {
                "config": config,
                "client": client,
                "discovery": discovery,
                "tools": registered_tools
            }
            
            logger.info(
                f"Registered {len(registered_tools)} tools from MCP server '{config.name}': "
                f"{', '.join(registered_tools[:3])}{'...' if len(registered_tools) > 3 else ''}"
            )
            
            return registered_tools
            
        except Exception as e:
            logger.error(f"Failed to register MCP server '{config.name}': {e}")
            return []
            
    async def unregister_mcp_server(self, server_name: str) -> None:
        """
        Unregister an MCP server and remove its tools.
        
        Args:
            server_name: Name of the server to unregister
        """
        if server_name not in self.registered_servers:
            logger.warning(f"MCP server '{server_name}' not registered")
            return
            
        info = self.registered_servers[server_name]
        
        # Unregister tools from AIWhisperer
        for tool_name in info["tools"]:
            try:
                self.tool_registry.unregister_tool(tool_name)
                self._registered_tool_names.discard(tool_name)
                logger.debug(f"Unregistered MCP tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to unregister tool '{tool_name}': {e}")
                
        # Remove from connection pool (will close connection if no other users)
        await self.connection_pool.remove_client(info["config"])
        
        # Remove registration info
        del self.registered_servers[server_name]
        
        logger.info(f"Unregistered MCP server '{server_name}' and {len(info['tools'])} tools")
        
    async def refresh_server_tools(self, server_name: str) -> List[str]:
        """
        Refresh tools from a registered MCP server.
        
        Args:
            server_name: Name of the server to refresh
            
        Returns:
            List of newly registered tool names
        """
        if server_name not in self.registered_servers:
            logger.error(f"MCP server '{server_name}' not registered")
            return []
            
        # Unregister and re-register
        config = self.registered_servers[server_name]["config"]
        await self.unregister_mcp_server(server_name)
        return await self.register_mcp_server(config)
        
    def get_mcp_tools(self) -> List[AITool]:
        """Get all registered MCP tools."""
        mcp_tools = []
        for tool_name in self._registered_tool_names:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                mcp_tools.append(tool)
        return mcp_tools
        
    def get_server_tools(self, server_name: str) -> List[str]:
        """Get tool names from a specific MCP server."""
        if server_name not in self.registered_servers:
            return []
        return self.registered_servers[server_name]["tools"]
        
    def get_registered_servers(self) -> List[str]:
        """Get list of registered MCP server names."""
        return list(self.registered_servers.keys())
        
    async def close_all(self) -> None:
        """Close all MCP connections."""
        # Unregister all servers
        server_names = list(self.registered_servers.keys())
        for server_name in server_names:
            await self.unregister_mcp_server(server_name)
            
        # Close connection pool
        await self.connection_pool.close_all()
        
        logger.info("Closed all MCP connections")