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
        workspace: Optional[str] = None,
        log_level: Optional[str] = None,
        log_file: Optional[str] = None,
        audit_log: Optional[str] = None,
        enable_metrics: bool = True,
        slow_request_threshold: Optional[float] = None
    ):
        self.config = self._load_config(
            config_path, transport, port, exposed_tools, workspace,
            log_level, log_file, audit_log, enable_metrics, slow_request_threshold
        )
        self.server = None
        
    def _load_config(
        self,
        config_path: Optional[str],
        transport: Optional[str],
        port: Optional[int],
        exposed_tools: Optional[List[str]],
        workspace: Optional[str],
        log_level: Optional[str],
        log_file: Optional[str],
        audit_log: Optional[str],
        enable_metrics: bool,
        slow_request_threshold: Optional[float]
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
        
        # Override monitoring options
        if log_level:
            config.log_level = log_level
        if log_file:
            config.log_file = log_file
            config.enable_json_logging = True
        if audit_log:
            config.audit_log_file = audit_log
            config.enable_audit_log = True
        if not enable_metrics:
            config.enable_metrics = False
        if slow_request_threshold:
            config.slow_request_threshold_ms = slow_request_threshold
            
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
        choices=['stdio', 'websocket', 'sse'],
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
    
    # Monitoring options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file',
        help='Path to log file (JSON format)'
    )
    parser.add_argument(
        '--audit-log',
        help='Path to audit log file'
    )
    parser.add_argument(
        '--no-metrics',
        action='store_true',
        help='Disable metrics collection'
    )
    parser.add_argument(
        '--slow-request-threshold',
        type=float,
        default=5000.0,
        help='Threshold for slow request detection in milliseconds (default: 5000)'
    )
    
    args = parser.parse_args()
    
    # Create and run server
    runner = MCPServerRunner(
        config_path=args.config,
        transport=args.transport,
        port=args.port,
        exposed_tools=args.tools,
        workspace=args.workspace,
        log_level=args.log_level,
        log_file=args.log_file,
        audit_log=args.audit_log,
        enable_metrics=not args.no_metrics,
        slow_request_threshold=args.slow_request_threshold
    )
    
    runner.run_sync()


if __name__ == "__main__":
    main()