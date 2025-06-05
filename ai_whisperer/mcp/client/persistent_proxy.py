#!/usr/bin/env python3
"""
Persistent MCP proxy that maintains connection to Claude while allowing AIWhisperer restarts.

This proxy acts as a subprocess manager that:
1. Runs the actual MCP server as a subprocess
2. Automatically restarts it if it crashes
3. Provides stdio interface to Claude Desktop
4. Caches tool information for availability during restarts
"""

import sys
import json
import logging
import asyncio
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path
import signal
import os

# Configure logging to stderr to avoid interfering with stdio protocol
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class PersistentMCPProxy:
    """Persistent proxy that manages MCP server subprocess."""
    
    def __init__(self, server_command: List[str], restart_delay: float = 2.0):
        self.server_command = server_command
        self.restart_delay = restart_delay
        self.server_process: Optional[subprocess.Popen] = None
        self.running = False
        
        # Cache for tools and server info
        self.cached_tools: List[Dict[str, Any]] = []
        self.cached_server_info: Dict[str, Any] = {
            "name": "aiwhisperer",
            "version": "1.0.0"
        }
        
        # Track initialization state
        self.initialized = False
        self.capabilities = {
            "tools": {},
            "resources": {"subscribe": True, "listChanged": True}
        }
        
    def start_server(self) -> bool:
        """Start the MCP server subprocess."""
        try:
            logger.info(f"Starting MCP server: {' '.join(self.server_command)}")
            
            # Start the subprocess with pipes for stdio
            self.server_process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env={**os.environ, "PYTHONUNBUFFERED": "1"}  # Ensure Python output is unbuffered
            )
            
            logger.info(f"MCP server started with PID: {self.server_process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
            
    def stop_server(self):
        """Stop the MCP server subprocess."""
        if self.server_process:
            try:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                    self.server_process.wait()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            finally:
                self.server_process = None
                
    def is_server_running(self) -> bool:
        """Check if the server process is still running."""
        return self.server_process is not None and self.server_process.poll() is None
        
    async def maintain_server(self):
        """Background task to monitor and restart server if needed."""
        while self.running:
            if not self.is_server_running():
                logger.info("MCP server not running, attempting to restart...")
                if self.start_server():
                    # If we've already initialized with Claude, reinitialize the subprocess
                    if self.initialized:
                        await self.reinitialize_server()
                        
            await asyncio.sleep(self.restart_delay)
            
    async def reinitialize_server(self):
        """Send initialization to newly started server."""
        if self.is_server_running():
            init_msg = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "0.1.0",
                    "clientInfo": {
                        "name": "persistent-proxy",
                        "version": "1.0.0"
                    }
                },
                "id": "reinit"
            }
            
            try:
                self.server_process.stdin.write(json.dumps(init_msg) + '\n')
                self.server_process.stdin.flush()
                # We don't wait for response as we're just priming the server
            except Exception as e:
                logger.error(f"Failed to reinitialize server: {e}")
                
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a message from Claude, with special cases for initialization."""
        method = message.get("method", "")
        
        # Special handling for initialization
        if method == "initialize":
            self.initialized = True
            
            # Always respond immediately with success
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "protocolVersion": "0.1.0",
                    "serverInfo": self.cached_server_info,
                    "capabilities": self.capabilities
                }
            }
            
            # Also forward to server if running
            if self.is_server_running():
                asyncio.create_task(self.forward_to_server_async(message))
                
            return response
            
        # Special handling for tools/list when server is down
        elif method == "tools/list" and not self.is_server_running():
            # Return cached tools if available
            if self.cached_tools:
                logger.info("Returning cached tools while server is down")
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "tools": self.cached_tools
                    }
                }
            else:
                # Return empty tools list
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "tools": []
                    }
                }
                
        # For all other requests, forward to server
        else:
            return await self.forward_to_server(message)
            
    async def forward_to_server_async(self, message: Dict[str, Any]):
        """Forward a message to server without waiting for response."""
        if self.is_server_running():
            try:
                self.server_process.stdin.write(json.dumps(message) + '\n')
                self.server_process.stdin.flush()
            except Exception as e:
                logger.error(f"Failed to forward message: {e}")
                
    async def forward_to_server(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Forward a message to server and wait for response."""
        if not self.is_server_running():
            # Return error for non-cached requests
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": "MCP server is restarting. Please try again in a moment."
                }
            }
            
        try:
            # Send to server
            self.server_process.stdin.write(json.dumps(message) + '\n')
            self.server_process.stdin.flush()
            
            # Read response
            response_line = self.server_process.stdout.readline()
            if not response_line:
                # Server closed stdout
                logger.error("Server closed stdout")
                return None
                
            response = json.loads(response_line.strip())
            
            # Cache tools if this was a tools/list response
            if message.get("method") == "tools/list" and "result" in response:
                self.cached_tools = response["result"].get("tools", [])
                logger.info(f"Cached {len(self.cached_tools)} tools")
                
            # Cache server info from initialization responses
            if message.get("method") == "initialize" and "result" in response:
                result = response["result"]
                if "serverInfo" in result:
                    self.cached_server_info = result["serverInfo"]
                if "capabilities" in result:
                    self.capabilities = result["capabilities"]
                    
            return response
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from server: {e}")
            return None
        except Exception as e:
            logger.error(f"Error forwarding to server: {e}")
            return None
            
    async def read_stdin(self):
        """Read JSON-RPC messages from stdin."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while self.running:
            try:
                line = await reader.readline()
                if not line:
                    break
                    
                try:
                    message = json.loads(line.decode('utf-8').strip())
                    logger.debug(f"Received from Claude: {message}")
                    
                    # Handle the message
                    response = await self.handle_message(message)
                    
                    if response:
                        print(json.dumps(response), flush=True)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from stdin: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    
            except Exception as e:
                logger.error(f"Error reading stdin: {e}")
                break
                
    async def monitor_server_output(self):
        """Monitor server stderr for logging."""
        if not self.is_server_running():
            return
            
        while self.running and self.is_server_running():
            try:
                line = self.server_process.stderr.readline()
                if line:
                    logger.info(f"[MCP Server] {line.strip()}")
                else:
                    # EOF - server has exited
                    break
            except Exception as e:
                logger.error(f"Error reading server stderr: {e}")
                break
                
            await asyncio.sleep(0.1)
            
    async def run(self):
        """Run the proxy."""
        self.running = True
        
        # Start the server initially
        self.start_server()
        
        # Start background tasks
        maintain_task = asyncio.create_task(self.maintain_server())
        monitor_task = asyncio.create_task(self.monitor_server_output())
        
        try:
            # Read from stdin
            await self.read_stdin()
        except KeyboardInterrupt:
            logger.info("Proxy interrupted")
        except Exception as e:
            logger.error(f"Proxy error: {e}", exc_info=True)
        finally:
            self.running = False
            maintain_task.cancel()
            monitor_task.cancel()
            self.stop_server()
            
            # Wait for tasks to complete
            try:
                await maintain_task
            except asyncio.CancelledError:
                pass
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass


def main():
    """Main entry point for the persistent proxy."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Persistent MCP proxy for AIWhisperer"
    )
    
    parser.add_argument(
        '--config',
        default='config/mcp_minimal.yaml',
        help='Configuration file for MCP server'
    )
    parser.add_argument(
        '--transport',
        default='stdio',
        help='Transport type (stdio recommended for proxy)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    parser.add_argument(
        '--restart-delay',
        type=float,
        default=2.0,
        help='Delay before restarting crashed server'
    )
    
    args = parser.parse_args()
    
    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Construct server command
    server_command = [
        sys.executable,
        "-m", "ai_whisperer.mcp.server.fastmcp_runner",
        "--config", args.config,
        "--transport", args.transport
    ]
    
    # Create and run proxy
    proxy = PersistentMCPProxy(server_command, restart_delay=args.restart_delay)
    
    # Handle signals gracefully
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        proxy.running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(proxy.run())
    except Exception as e:
        logger.error(f"Proxy failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()