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
        
        # Check if we should apply Claude tool filtering
        if self.config.server_name == "aiwhisperer-aggregator":
            # This is the Claude proxy - apply tool filtering
            await self._register_claude_tools()
        else:
            # Normal registration for direct MCP servers
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
    
    async def _register_claude_tools(self):
        """Register tools for Claude CLI based on settings."""
        try:
            from ...tools.claude.claude_tool_manager import get_claude_tool_manager
            
            manager = get_claude_tool_manager()
            
            # Get all available tools
            all_tools = {}
            for tool_name in self.tool_registry.list_tools():
                try:
                    all_tools[tool_name] = self.tool_registry.get_tool(tool_name)
                except Exception as e:
                    logger.warning(f"Could not load tool {tool_name}: {e}")
            
            # Filter tools for Claude
            claude_tools = manager.filter_tools_for_claude(all_tools)
            
            # Register filtered tools
            for tool_name, tool in claude_tools.items():
                try:
                    await self._register_tool(tool_name, tool)
                    logger.info(f"Registered Claude tool: {tool_name}")
                except Exception as e:
                    logger.warning(f"Failed to register Claude tool '{tool_name}': {e}")
            
            # Log summary
            enabled_tools = manager.get_enabled_tools()
            if enabled_tools is None:
                logger.info("Claude has access to ALL tools (emergency mode)")
            else:
                logger.info(f"Claude has access to {len(claude_tools)} tools: {list(claude_tools.keys())}")
                
        except Exception as e:
            logger.error(f"Error registering Claude tools: {e}", exc_info=True)
            # Fall back to default tools on error
            default_tools = ["read_file", "write_file", "list_directory", "search_files", "execute_command"]
            for tool_name in default_tools:
                try:
                    tool = self.tool_registry.get_tool(tool_name)
                    await self._register_tool(tool_name, tool)
                    logger.info(f"Registered fallback tool: {tool_name}")
                except Exception as e2:
                    logger.warning(f"Failed to register fallback tool '{tool_name}': {e2}")


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