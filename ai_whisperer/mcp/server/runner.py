"""MCP server runner."""

import asyncio
import logging
import sys
import yaml
from pathlib import Path
from typing import Optional, List

from .server import MCPServer
from .config import MCPServerConfig, TransportType
from ...utils.path import PathManager

logger = logging.getLogger(__name__)


class MCPServerRunner:
    """Manages MCP server lifecycle."""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        transport: Optional[str] = None,
        port: Optional[int] = None,
        exposed_tools: Optional[List[str]] = None,
        workspace: Optional[str] = None
    ):
        self.config = self._load_config(config_path, transport, port, exposed_tools, workspace)
        self.server = None
        
    def _load_config(
        self,
        config_path: Optional[str],
        transport: Optional[str],
        port: Optional[int],
        exposed_tools: Optional[List[str]],
        workspace: Optional[str]
    ) -> MCPServerConfig:
        """Load MCP server configuration."""
        if config_path:
            # Load from file
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                config = MCPServerConfig.from_dict(config_data.get('mcp', {}).get('server', {}))
        else:
            # Use defaults
            config = MCPServerConfig()
            
        # Override with provided options
        if transport:
            config.transport = TransportType(transport)
            
        if port and config.transport == TransportType.WEBSOCKET:
            config.port = port
            
        if exposed_tools:
            config.exposed_tools = exposed_tools
            
        if workspace:
            # Initialize path manager with workspace
            path_manager = PathManager()
            path_manager.initialize(config_values={
                'project_path': workspace,
                'workspace_path': workspace,
                'output_path': Path(workspace) / 'output'
            })
            
        return config
        
    async def run(self):
        """Run the MCP server."""
        # Setup logging only if not already configured
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.WARNING,  # Use WARNING to reduce noise
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stderr)]  # Log to stderr not stdout
            )
        
        # Create server
        self.server = MCPServer(self.config)
        
        try:
            # Start server
            await self.server.start()
            
            # Don't log to stdout when using stdio transport
            if self.config.transport != TransportType.STDIO:
                logger.info(f"MCP server started with transport: {self.config.transport}")
                logger.info(f"Server: {self.config.server_name} v{self.config.server_version}")
                logger.info(f"Exposing {len(self.config.exposed_tools)} tools: {', '.join(self.config.exposed_tools[:5])}...")
                logger.info(f"MCP server listening on {self.config.host}:{self.config.port}")
                
            # Keep server running
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            logger.info("Shutting down MCP server...")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
        finally:
            if self.server:
                await self.server.stop()
                
    def run_sync(self):
        """Run the server synchronously."""
        asyncio.run(self.run())


def main():
    """Main entry point for MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run AIWhisperer as an MCP server",
        prog="aiwhisperer-mcp"
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file with MCP server settings'
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'websocket', 'websocket_enhanced', 'sse'],
        default='stdio',
        help='Transport type (default: stdio)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3000,
        help='Port for WebSocket transport (default: 3000)'
    )
    parser.add_argument(
        '--expose-tool',
        action='append',
        dest='tools',
        help='Tool to expose via MCP (can be specified multiple times)'
    )
    parser.add_argument(
        '--workspace',
        help='Workspace directory to expose as resources'
    )
    
    args = parser.parse_args()
    
    # Create and run server
    runner = MCPServerRunner(
        config_path=args.config,
        transport=args.transport,
        port=args.port,
        exposed_tools=args.tools,
        workspace=args.workspace
    )
    
    runner.run_sync()


if __name__ == "__main__":
    main()