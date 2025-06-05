"""MCP server integration for interactive server."""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ai_whisperer.mcp.server.fastmcp_runner import FastMCPServer
from ai_whisperer.mcp.server.config import MCPServerConfig, TransportType

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages MCP server lifecycle within interactive server."""
    
    def __init__(self):
        self.server: Optional[FastMCPServer] = None
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
            transport = config.get("transport", "sse")
            port = config.get("port", 8002)  # Different from main server
            exposed_tools = config.get("exposed_tools", [
                "read_file", "write_file", "list_directory", 
                "search_files", "execute_command", "python_executor",
                "claude_mailbox", "claude_check_mail", "claude_user_message",
                "claude_enable_all_tools", "claude_set_toolset"
            ])
            workspace = config.get("workspace", Path.cwd())
            
            # Create FastMCP server configuration
            mcp_config = MCPServerConfig()
            mcp_config.transport = TransportType(transport)
            mcp_config.port = port
            mcp_config.exposed_tools = exposed_tools
            mcp_config.workspace_path = str(workspace)
            mcp_config.server_name = "aiwhisperer-interactive"
            
            # Create FastMCP server
            self.server = FastMCPServer(mcp_config)
            
            # Initialize tools
            await self.server.initialize()
            
            # Start FastMCP server in background on its own port
            self.server_task = asyncio.create_task(self._run_fastmcp_server())
            self.is_running = True
            
            # Give server a moment to start
            await asyncio.sleep(1.0)
            
            # FastMCP runs on its own port
            server_url = f"http://localhost:{port}/sse"
                
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
            
    async def _run_fastmcp_server(self):
        """Run the FastMCP server."""
        try:
            logger.info("Starting FastMCP server...")
            # FastMCP run is synchronous, so we run it in a thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._run_fastmcp_sync)
        except asyncio.CancelledError:
            logger.info("FastMCP server task cancelled")
        except Exception as e:
            logger.error(f"FastMCP server error: {e}", exc_info=True)
        finally:
            logger.info("FastMCP server finished")
            self.is_running = False
            
    def _run_fastmcp_sync(self):
        """Run FastMCP synchronously."""
        self.server.mcp.run(transport="sse")
            
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
                    
            # FastMCP will stop when task is cancelled
                
            self.is_running = False
            self.server = None
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