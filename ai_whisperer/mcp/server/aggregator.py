#!/usr/bin/env python3
"""
MCP Aggregator Server - A FastMCP server that aggregates other MCP servers.

This server:
1. Presents a stable MCP interface to clients (like Claude CLI)
2. Internally connects to other MCP servers as a client
3. Handles reconnections transparently
4. Aggregates tools from multiple MCP servers (currently just AIWhisperer)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import aiohttp
import json
import time

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, Tool, CallToolResult

logger = logging.getLogger(__name__)


class MCPClient:
    """Simple MCP client for connecting to upstream servers."""
    
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.session: Optional[aiohttp.ClientSession] = None
        self.connection_id: Optional[str] = None
        self.available = False
        self.tools: List[Dict[str, Any]] = []
        self.initialized = False
        self._reconnect_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """Connect to the upstream MCP server."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            # Connect to SSE endpoint
            async with self.session.get(self.url) as resp:
                if resp.status == 200:
                    # Read the first event to get connection info
                    async for line in resp.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: ') and 'session_id=' in line_str:
                                # Extract session_id
                                import re
                                match = re.search(r'session_id=([a-f0-9-]+)', line_str)
                                if match:
                                    self.connection_id = match.group(1)
                                    self.available = True
                                    logger.info(f"Connected to {self.name} with session {self.connection_id}")
                                    break
                                    
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            self.available = False
            
    async def initialize(self):
        """Initialize the MCP session."""
        if not self.available or not self.connection_id:
            return False
            
        try:
            # Send initialization request
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "0.1.0",
                    "clientInfo": {
                        "name": "mcp-aggregator",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            }
            
            result = await self._send_request(init_request)
            if result and "result" in result:
                self.initialized = True
                logger.info(f"Initialized {self.name}")
                
                # Get available tools
                await self.refresh_tools()
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            
        return False
        
    async def refresh_tools(self):
        """Get the list of available tools."""
        if not self.initialized:
            return
            
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }
            
            result = await self._send_request(tools_request)
            if result and "result" in result:
                self.tools = result["result"].get("tools", [])
                logger.info(f"Got {len(self.tools)} tools from {self.name}")
                
        except Exception as e:
            logger.error(f"Failed to get tools from {self.name}: {e}")
            
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the upstream server."""
        if not self.initialized:
            # Try to reconnect
            await self.ensure_connected()
            if not self.initialized:
                return {"error": f"{self.name} is not available"}
                
        try:
            tool_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": int(time.time() * 1000)  # Use timestamp as ID
            }
            
            result = await self._send_request(tool_request)
            if result:
                if "result" in result:
                    return result["result"]
                elif "error" in result:
                    return {"error": result["error"].get("message", "Unknown error")}
                    
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {self.name}: {e}")
            return {"error": str(e)}
            
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request to the upstream server."""
        if not self.connection_id:
            return None
            
        url = self.url.replace('/sse', f'/messages/?session_id={self.connection_id}')
        
        try:
            async with self.session.post(url, json=request) as resp:
                if resp.status == 202:
                    # For async responses, we might need to wait for SSE events
                    # For now, return success
                    return {"result": {"status": "accepted"}}
                else:
                    return await resp.json()
                    
        except Exception as e:
            logger.error(f"Request failed: {e}")
            self.available = False
            self.initialized = False
            return None
            
    async def ensure_connected(self):
        """Ensure we're connected and initialized."""
        if not self.available:
            await self.connect()
            
        if self.available and not self.initialized:
            await self.initialize()
            
    async def start_reconnect_loop(self):
        """Start a background task to maintain connection."""
        async def reconnect_loop():
            while True:
                try:
                    if not self.available or not self.initialized:
                        logger.info(f"Attempting to reconnect to {self.name}")
                        await self.connect()
                        if self.available:
                            await self.initialize()
                            
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Reconnect error for {self.name}: {e}")
                    await asyncio.sleep(5)
                    
        self._reconnect_task = asyncio.create_task(reconnect_loop())
        
    async def close(self):
        """Close the client connection."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            
        if self.session:
            await self.session.close()


class MCPAggregatorServer:
    """MCP server that aggregates other MCP servers."""
    
    def __init__(self, port: int = 3002):
        self.mcp = FastMCP(name="mcp-aggregator", port=port)
        self.clients: Dict[str, MCPClient] = {}
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup the aggregator's info handler."""
        
        @self.mcp.tool(description="Get information about the aggregator")
        async def aggregator_info() -> str:
            """Get information about connected MCP servers."""
            info = {
                "aggregator": "MCP Aggregator v1.0",
                "connected_servers": {}
            }
            
            for name, client in self.clients.items():
                info["connected_servers"][name] = {
                    "available": client.available,
                    "initialized": client.initialized,
                    "tools_count": len(client.tools),
                    "url": client.url
                }
                
            return json.dumps(info, indent=2)
            
    async def add_client(self, name: str, url: str):
        """Add an MCP client to aggregate."""
        client = MCPClient(name, url)
        self.clients[name] = client
        
        # Start connection
        await client.start_reconnect_loop()
        
        # Wait a bit for initial connection
        await asyncio.sleep(2)
        
        # Register tools from this client
        await self._register_client_tools(client)
        
    async def _register_client_tools(self, client: MCPClient):
        """Register tools from a client with our server."""
        for tool_def in client.tools:
            tool_name = tool_def.get("name", "")
            tool_description = tool_def.get("description", "")
            
            # Create a wrapper function for this tool
            async def make_tool_wrapper(client_ref: MCPClient, original_name: str):
                async def tool_wrapper(**kwargs) -> str:
                    """Wrapper that calls the tool on the upstream server."""
                    result = await client_ref.call_tool(original_name, kwargs)
                    
                    # Convert result to string
                    if isinstance(result, dict):
                        if 'error' in result:
                            return f"Error: {result['error']}"
                        elif 'content' in result:
                            return str(result['content'])
                        else:
                            return json.dumps(result, indent=2)
                    else:
                        return str(result)
                        
                return tool_wrapper
                
            # Create the wrapper with captured variables
            wrapper = await make_tool_wrapper(client, tool_name)
            wrapper.__name__ = tool_name
            
            # Register with FastMCP
            self.mcp.tool(description=f"[{client.name}] {tool_description}")(wrapper)
            
        logger.info(f"Registered {len(client.tools)} tools from {client.name}")
        
    def run(self):
        """Run the aggregator server."""
        # The mcp.run() method needs to be called after all async setup
        logger.info("Starting MCP Aggregator Server")
        
        # Note: FastMCP's run is synchronous, so we need to set up async parts first
        import nest_asyncio
        nest_asyncio.apply()  # Allow nested event loops
        
        # Run async setup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def setup_and_run():
            # Add AIWhisperer as a client
            await self.add_client("aiwhisperer", "http://localhost:8002/sse")
            
            # Keep the setup task running
            while True:
                # Periodically check for new tools
                for client in self.clients.values():
                    if client.initialized and client.tools:
                        # Re-register tools if needed
                        pass
                        
                await asyncio.sleep(30)
                
        # Start setup task
        setup_task = loop.create_task(setup_and_run())
        
        # Run the MCP server (this blocks)
        try:
            self.mcp.run(transport="sse")
        finally:
            setup_task.cancel()
            loop.run_until_complete(asyncio.gather(*[c.close() for c in self.clients.values()], return_exceptions=True))


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Aggregator Server')
    parser.add_argument('--port', type=int, default=3002, help='Port to listen on')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = MCPAggregatorServer(port=args.port)
    server.run()


if __name__ == '__main__':
    main()