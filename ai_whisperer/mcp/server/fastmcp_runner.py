"""FastMCP-based MCP server runner for AIWhisperer."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional, Any, Dict

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, CallToolResult

from ...tools.tool_registry import ToolRegistry
from ...utils.path import PathManager
from .config import MCPServerConfig

logger = logging.getLogger(__name__)


class FastMCPServer:
    """MCP server using FastMCP for proper SSE transport."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        # Initialize FastMCP with specified port
        self.mcp = FastMCP(name=config.server_name, port=config.port)
        self.tool_registry = None
        
    async def initialize(self):
        """Initialize the server with tools."""
        # Initialize path manager
        if hasattr(self.config, 'workspace_path') and self.config.workspace_path:
            path_manager = PathManager()
            path_manager.initialize(config_values={
                'project_path': self.config.workspace_path,
                'workspace_path': self.config.workspace_path,
                'output_path': Path(self.config.workspace_path) / 'output'
            })
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        
        # Register exposed tools
        for tool_name in self.config.exposed_tools:
            try:
                tool = self.tool_registry.get_tool(tool_name)
                await self._register_tool(tool_name, tool)
                logger.info(f"Registered tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Tool '{tool_name}' not found in registry: {e}")
                
    async def _register_tool(self, tool_name: str, tool):
        """Register a tool with FastMCP."""
        
        # Create a unique function for each tool
        async def tool_func(**kwargs) -> str:
            """Wrapper for AIWhisperer tools."""
            try:
                # Create a minimal context for the tool
                context = type('Context', (), {
                    'user_message_level': 'info',
                    'workspace_path': getattr(self.config, 'workspace_path', '.'),
                    'output_path': Path(getattr(self.config, 'workspace_path', '.')) / 'output'
                })()
                
                # Call the tool (tools expect kwargs, not context as first param)
                # Handle both sync and async tools
                import inspect
                if inspect.iscoroutinefunction(tool.execute):
                    result = await tool.execute(**kwargs)
                else:
                    result = tool.execute(**kwargs)
                
                # Convert result to string
                if isinstance(result, dict):
                    if 'content' in result:
                        return str(result['content'])
                    else:
                        return str(result)
                else:
                    return str(result)
                    
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
                return f"Error executing {tool_name}: {str(e)}"
        
        # Set the function name for FastMCP
        tool_func.__name__ = tool_name
        
        # Register with FastMCP using the decorator
        self.mcp.tool(description=getattr(tool, 'description', f"Tool: {tool_name}"))(tool_func)
        


def main():
    """Main entry point for FastMCP server."""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(
        description="Run AIWhisperer with FastMCP SSE transport",
        prog="aiwhisperer-fastmcp"
    )
    
    parser.add_argument(
        '--config',
        required=True,
        help='Path to configuration file with MCP server settings'
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'sse'],
        default='sse',
        help='Transport type (default: sse)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8002,
        help='Port for SSE transport (default: 8002)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config_data = yaml.safe_load(f)
        config = MCPServerConfig.from_dict(config_data.get('mcp', {}).get('server', {}))
    
    # Override transport and port
    config.transport = args.transport
    config.port = args.port  # Always set the port from CLI args
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    
    # Create and run server
    server = FastMCPServer(config)
    
    # Initialize async parts
    async def init():
        await server.initialize()
    
    asyncio.run(init())
    
    # Run server (synchronous)
    transport_str = config.transport if isinstance(config.transport, str) else config.transport.value
    if transport_str == 'sse':
        server.mcp.run(transport="sse")
    else:
        server.mcp.run(transport="stdio")


if __name__ == "__main__":
    main()