"""CLI command for running MCP server."""

import asyncio
import click
import logging
import yaml
from pathlib import Path
from typing import Optional

from ....mcp.server import MCPServer
from ....mcp.server.config import MCPServerConfig
from ....utils.path import PathManager

logger = logging.getLogger(__name__)


@click.command(name="mcp-server")
@click.option(
    '--config', 
    type=click.Path(exists=True),
    help='Path to MCP server configuration file'
)
@click.option(
    '--transport',
    type=click.Choice(['stdio', 'websocket']),
    default='stdio',
    help='Transport type (default: stdio)'
)
@click.option(
    '--port',
    type=int,
    default=3000,
    help='Port for WebSocket transport (default: 3000)'
)
@click.option(
    '--expose-tool',
    multiple=True,
    help='Tool to expose via MCP (can be specified multiple times)'
)
@click.option(
    '--workspace',
    type=click.Path(exists=True),
    help='Workspace directory to expose as resources'
)
@click.pass_context
def mcp_server(ctx, config, transport, port, expose_tool, workspace):
    """Run AIWhisperer as an MCP server.
    
    This allows Claude Code and other MCP clients to use AIWhisperer tools.
    
    Examples:
    
        # Run with stdio transport (for Claude Code)
        aiwhisperer mcp-server
        
        # Run with specific tools
        aiwhisperer mcp-server --expose-tool read_file --expose-tool search_files
        
        # Run with WebSocket transport
        aiwhisperer mcp-server --transport websocket --port 3001
        
        # Run with custom config
        aiwhisperer mcp-server --config mcp-server.yaml
    """
    # Load configuration
    server_config = _load_config(config, transport, port, expose_tool, workspace)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run server
    asyncio.run(_run_server(server_config))
    

def _load_config(
    config_path: Optional[str],
    transport: str,
    port: int,
    expose_tools: tuple,
    workspace: Optional[str]
) -> MCPServerConfig:
    """Load MCP server configuration."""
    if config_path:
        # Load from file
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            server_config = MCPServerConfig.from_dict(config_data)
    else:
        # Use defaults
        server_config = MCPServerConfig()
        
    # Override with CLI options
    if transport:
        server_config.transport = transport
        
    if port and transport == 'websocket':
        server_config.port = port
        
    if expose_tools:
        server_config.exposed_tools = list(expose_tools)
        
    if workspace:
        # Update path manager workspace
        path_manager = PathManager()
        path_manager.workspace_path = Path(workspace)
        
    return server_config


async def _run_server(config: MCPServerConfig):
    """Run the MCP server."""
    server = MCPServer(config)
    
    try:
        # Start server
        await server.start()
        
        logger.info(f"MCP server started with transport: {config.transport}")
        logger.info(f"Exposing {len(config.exposed_tools)} tools")
        
        if config.transport == 'stdio':
            logger.info("Ready for MCP client connections via stdio")
            logger.info("Press Ctrl+C to stop the server")
        else:
            logger.info(f"MCP server listening on {config.host}:{config.port}")
            
        # Keep server running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        await server.stop()