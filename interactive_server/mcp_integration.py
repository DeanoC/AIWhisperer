"""MCP server integration for interactive server."""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ai_whisperer.mcp.server.runner import MCPServerRunner
from ai_whisperer.mcp.server.config import TransportType

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages MCP server lifecycle within interactive server."""
    
    def __init__(self):
        self.runner: Optional[MCPServerRunner] = None
        self.server_task: Optional[asyncio.Task] = None
        self.is_running = False
        
    async def start_mcp_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start MCP server with given configuration."""
        if self.is_running:
            return {
                "success": False,
                "message": "MCP server is already running"
            }
            
        try:
            # Extract configuration
            transport = config.get("transport", "websocket")
            port = config.get("port", 3001)  # Different from main server
            exposed_tools = config.get("exposed_tools", [
                "read_file", "write_file", "list_directory", 
                "search_files", "execute_command"
            ])
            workspace = config.get("workspace", Path.cwd())
            
            # Create runner with configuration
            self.runner = MCPServerRunner(
                transport=transport,
                port=port,
                exposed_tools=exposed_tools,
                workspace=str(workspace),
                enable_metrics=config.get("enable_metrics", True),
                log_level=config.get("log_level", "INFO")
            )
            
            # Start server in background task
            self.server_task = asyncio.create_task(self._run_server())
            self.is_running = True
            
            # Give server a moment to start
            await asyncio.sleep(0.5)
            
            # Construct server URL based on transport
            if transport == "websocket":
                server_url = f"ws://localhost:{port}/mcp"
            elif transport == "sse":
                server_url = f"http://localhost:{port}/mcp/sse"
            else:
                server_url = "stdio"
                
            return {
                "success": True,
                "message": f"MCP server started on {transport} transport",
                "transport": transport,
                "port": port if transport != "stdio" else None,
                "server_url": server_url,
                "exposed_tools": exposed_tools,
                "workspace": str(workspace)
            }
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return {
                "success": False,
                "message": f"Failed to start MCP server: {str(e)}"
            }
            
    async def _run_server(self):
        """Run the MCP server."""
        try:
            logger.info("Starting MCP server runner...")
            await self.runner.run()
        except asyncio.CancelledError:
            logger.info("MCP server task cancelled")
        except Exception as e:
            logger.error(f"MCP server error: {e}", exc_info=True)
        finally:
            logger.info("MCP server runner finished")
            self.is_running = False
            
    async def stop_mcp_server(self) -> Dict[str, Any]:
        """Stop the running MCP server."""
        if not self.is_running:
            return {
                "success": False,
                "message": "MCP server is not running"
            }
            
        try:
            # Cancel the server task
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
                    
            # Stop the server
            if self.runner and self.runner.server:
                await self.runner.server.stop()
                
            self.is_running = False
            self.runner = None
            self.server_task = None
            
            return {
                "success": True,
                "message": "MCP server stopped"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server: {e}")
            return {
                "success": False,
                "message": f"Failed to stop MCP server: {str(e)}"
            }
            
    def get_status(self) -> Dict[str, Any]:
        """Get MCP server status."""
        if not self.is_running:
            return {
                "running": False,
                "message": "MCP server is not running"
            }
            
        config = self.runner.config if self.runner else None
        if not config:
            return {
                "running": True,
                "message": "MCP server is running (configuration unavailable)"
            }
            
        # Build status response
        status = {
            "running": True,
            "transport": config.transport.value,
            "server_name": config.server_name,
            "server_version": config.server_version,
            "exposed_tools": config.exposed_tools,
        }
        
        # Add transport-specific info
        if config.transport == TransportType.WEBSOCKET:
            status["port"] = config.port
            status["server_url"] = f"ws://localhost:{config.port}/mcp"
        elif config.transport == TransportType.SSE:
            status["port"] = config.port
            status["server_url"] = f"http://localhost:{config.port}/mcp/sse"
        else:
            status["server_url"] = "stdio"
            
        # Add monitoring info if available
        if self.runner.server and hasattr(self.runner.server, 'monitor'):
            monitor = self.runner.server.monitor
            health = monitor.get_health()
            status["health"] = health["status"]
            status["uptime"] = health["uptime"]
            status["metrics"] = health["metrics"]
            
        return status


# Global MCP server manager instance
_mcp_manager = None


def get_mcp_manager() -> MCPServerManager:
    """Get the global MCP server manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPServerManager()
    return _mcp_manager


# JSON-RPC handlers for interactive server
async def mcp_start_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Start MCP server via JSON-RPC."""
    manager = get_mcp_manager()
    return await manager.start_mcp_server(params)


async def mcp_stop_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Stop MCP server via JSON-RPC."""
    manager = get_mcp_manager()
    return await manager.stop_mcp_server()


async def mcp_status_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Get MCP server status via JSON-RPC."""
    manager = get_mcp_manager()
    return manager.get_status()


# Export handlers for registration
MCP_HANDLERS = {
    "mcp.start": mcp_start_handler,
    "mcp.stop": mcp_stop_handler,
    "mcp.status": mcp_status_handler,
}