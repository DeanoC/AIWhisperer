"""Connection pool for MCP clients."""

import asyncio
import logging
from typing import Dict, Optional

from ..common.types import MCPServerConfig
from .client import MCPClient

logger = logging.getLogger(__name__)


class MCPConnectionPool:
    """Manages a pool of MCP client connections."""
    
    def __init__(self):
        self.connections: Dict[str, MCPClient] = {}
        self.lock = asyncio.Lock()
        self._closing = False
        
    def _get_key(self, config: MCPServerConfig) -> str:
        """Generate unique key for server configuration."""
        if config.transport == "stdio":
            # For stdio, use command as key
            return f"stdio:{':'.join(config.command or [])}"
        elif config.transport == "websocket":
            # For websocket, use URL as key
            return f"ws:{config.url}"
        else:
            # Fallback to name
            return f"{config.transport}:{config.name}"
            
    async def get_client(self, server_config: MCPServerConfig) -> MCPClient:
        """
        Get or create a client for the given server configuration.
        
        Args:
            server_config: MCP server configuration
            
        Returns:
            Connected MCP client
        """
        async with self.lock:
            if self._closing:
                raise RuntimeError("Connection pool is closing")
                
            key = self._get_key(server_config)
            
            # Check if we have an existing connection
            if key in self.connections:
                client = self.connections[key]
                
                # Verify connection is still alive
                if await client.is_alive():
                    logger.debug(f"Reusing existing connection for {server_config.name}")
                    return client
                else:
                    # Remove dead connection
                    logger.info(f"Removing dead connection for {server_config.name}")
                    await self._close_client(client)
                    del self.connections[key]
                    
            # Create new connection
            logger.info(f"Creating new MCP connection for {server_config.name}")
            client = MCPClient(server_config)
            
            try:
                await client.connect()
                self.connections[key] = client
                return client
                
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {server_config.name}: {e}")
                raise
                
    async def remove_client(self, server_config: MCPServerConfig) -> None:
        """
        Remove a client from the pool and close it.
        
        Args:
            server_config: MCP server configuration
        """
        async with self.lock:
            key = self._get_key(server_config)
            
            if key in self.connections:
                client = self.connections[key]
                await self._close_client(client)
                del self.connections[key]
                logger.info(f"Removed client for {server_config.name} from pool")
                
    async def _close_client(self, client: MCPClient) -> None:
        """Close a client connection safely."""
        try:
            await client.close()
        except Exception as e:
            logger.error(f"Error closing MCP client: {e}")
            
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self.lock:
            self._closing = True
            
            # Close all clients
            close_tasks = []
            for client in self.connections.values():
                close_tasks.append(self._close_client(client))
                
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
                
            self.connections.clear()
            logger.info("Closed all MCP connections in pool")
            
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.connections)
        
    def get_connection_info(self) -> Dict[str, str]:
        """Get information about active connections."""
        info = {}
        for key, client in self.connections.items():
            info[key] = {
                "server_name": client.config.name,
                "transport": client.config.transport,
                "initialized": client.initialized,
                "tools_count": len(client.tools)
            }
        return info