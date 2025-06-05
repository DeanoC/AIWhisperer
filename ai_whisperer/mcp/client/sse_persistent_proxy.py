#!/usr/bin/env python3
"""
SSE Persistent MCP proxy that maintains connection to Claude CLI while allowing AIWhisperer restarts.

This proxy acts as an SSE server that:
1. Forwards SSE events from the real AIWhisperer MCP server when it's running
2. Responds to heartbeats/pings when AIWhisperer is down to keep Claude CLI connected
3. Caches tools and provides minimal responses during restarts
4. Automatically reconnects to AIWhisperer when it comes back up
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import logging
import sys
from typing import Optional, Dict, Any, List
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SSEPersistentProxy:
    """SSE proxy that maintains connection while allowing upstream restarts."""
    
    def __init__(self, upstream_url: str, port: int = 3002):
        self.upstream_url = upstream_url.rstrip('/')
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
        # Connection tracking
        self.active_connections: List[web.StreamResponse] = []
        self.upstream_available = False
        self.last_heartbeat = time.time()
        
        # Cache for tools and initialization
        self.cached_tools: List[Dict[str, Any]] = []
        self.cached_init_response: Optional[Dict[str, Any]] = None
        self.connection_counter = 0
        
        # Session mappings (proxy connection -> upstream session)
        self.session_mappings: Dict[str, str] = {}
        
        # Session for upstream connections
        self.session: Optional[aiohttp.ClientSession] = None
        
    def setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get('/mcp/sse', self.handle_sse)
        self.app.router.add_post('/mcp/request', self.handle_request)
        self.app.router.add_get('/mcp/health', self.handle_health)
        
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'upstream_available': self.upstream_available,
            'active_connections': len(self.active_connections),
            'cached_tools': len(self.cached_tools)
        })
        
    async def handle_sse(self, request: web.Request) -> web.StreamResponse:
        """Handle SSE connection from Claude CLI."""
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        await response.prepare(request)
        
        # Don't send our own connection event - let upstream handle it
        self.connection_counter += 1
        connection_id = f"proxy-{self.connection_counter}"
        
        # Track connection
        self.active_connections.append(response)
        logger.info(f"New SSE connection established: {connection_id}")
        
        try:
            # Start forwarding from upstream if available
            if self.upstream_available:
                asyncio.create_task(self.forward_upstream_sse(response, connection_id))
                
            # Keep connection alive with heartbeats
            while True:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
                if not self.upstream_available:
                    # Send heartbeat to keep Claude CLI happy
                    await self.send_sse_event(response, {
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'type': 'heartbeat'
                    }, 'heartbeat')
                    
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
        finally:
            self.active_connections.remove(response)
            logger.info(f"SSE connection closed: {connection_id}")
            
        return response
        
    async def forward_upstream_sse(self, client_response: web.StreamResponse, connection_id: str):
        """Forward SSE events from upstream server to client."""
        try:
            # FastMCP uses /sse endpoint
            async with self.session.get(f"{self.upstream_url}/sse") as resp:
                # Extract session_id from endpoint event
                session_id = None
                async for line in resp.content.iter_any():
                    if line:
                        line_str = line.decode('utf-8')
                        # Check for endpoint event to extract session_id
                        if 'event: endpoint' in line_str:
                            # Look for the data line
                            continue
                        elif line_str.startswith('data: ') and 'session_id=' in line_str:
                            # Extract session_id from the URL
                            import re
                            match = re.search(r'session_id=([a-f0-9]+)', line_str)
                            if match:
                                session_id = match.group(1)
                                logger.info(f"Extracted session_id: {session_id}")
                                # Store for request forwarding
                                self.session_mappings[connection_id] = session_id
                        
                        # Forward the raw SSE data
                        await client_response.write(line)
                        
        except Exception as e:
            logger.error(f"Upstream SSE forwarding error: {e}")
            # Don't break the client connection, just stop forwarding
            
    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle JSON-RPC request from Claude CLI."""
        try:
            # Get connection ID from headers
            connection_id = request.headers.get('X-Connection-Id', 'unknown')
            
            # Parse request
            data = await request.json()
            method = data.get('method', '')
            request_id = data.get('id')
            
            logger.info(f"Request from {connection_id}: {method}")
            
            # Handle special cases when upstream is down
            if not self.upstream_available:
                if method == 'initialize':
                    # Return cached or default initialization response
                    response_data = self.cached_init_response or {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "0.1.0",
                            "serverInfo": {
                                "name": "aiwhisperer-proxy",
                                "version": "1.0.0"
                            },
                            "capabilities": {
                                "tools": {},
                                "resources": {"subscribe": True, "listChanged": True}
                            }
                        }
                    }
                    return web.json_response(response_data)
                    
                elif method == 'tools/list':
                    # Return cached tools
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": self.cached_tools
                        }
                    }
                    return web.json_response(response_data)
                    
                else:
                    # Return a soft error for other methods
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "AIWhisperer is restarting. Please try again in a moment."
                        }
                    }
                    return web.json_response(response_data)
                    
            # Forward to upstream if available
            try:
                # Use the session-specific endpoint if we have a mapping
                upstream_session_id = self.session_mappings.get(connection_id)
                if upstream_session_id:
                    url = f"{self.upstream_url}/messages/?session_id={upstream_session_id}"
                else:
                    # Fallback to generic rpc endpoint
                    url = f"{self.upstream_url}/rpc"
                    
                async with self.session.post(
                    url,
                    json=data,
                    headers={'X-Connection-Id': connection_id}
                ) as resp:
                    response_data = await resp.json()
                    
                    # Cache certain responses
                    if method == 'initialize' and 'result' in response_data:
                        self.cached_init_response = response_data
                        logger.info("Cached initialization response")
                        
                    elif method == 'tools/list' and 'result' in response_data:
                        self.cached_tools = response_data['result'].get('tools', [])
                        logger.info(f"Cached {len(self.cached_tools)} tools")
                        
                    return web.json_response(response_data)
                    
            except Exception as e:
                logger.error(f"Upstream request error: {e}")
                # Mark upstream as unavailable
                self.upstream_available = False
                
                # Recursively call to use cached response
                return await self.handle_request(request)
                
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "id": request.get('id') if hasattr(request, 'get') else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            })
            
    async def send_sse_event(self, response: web.StreamResponse, data: Dict[str, Any], event_type: str):
        """Send an SSE event to the client."""
        try:
            event_data = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            await response.write(event_data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to send SSE event: {e}")
            
    async def check_upstream_health(self):
        """Periodically check if upstream server is available."""
        while True:
            try:
                # FastMCP doesn't have a health endpoint, check SSE endpoint
                async with self.session.get(f"{self.upstream_url}/sse", timeout=5) as resp:
                    if resp.status == 200:
                        if not self.upstream_available:
                            logger.info("Upstream server is now available")
                            self.upstream_available = True
                            
                            # Notify all clients about reconnection
                            for client in self.active_connections:
                                await self.send_sse_event(client, {
                                    'status': 'reconnected',
                                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                                }, 'status')
                    else:
                        self.upstream_available = False
                        
            except Exception:
                if self.upstream_available:
                    logger.warning("Upstream server is now unavailable")
                    self.upstream_available = False
                    
                    # Notify all clients about disconnection
                    for client in self.active_connections:
                        await self.send_sse_event(client, {
                            'status': 'upstream_down',
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        }, 'status')
                        
            await asyncio.sleep(5)  # Check every 5 seconds
            
    async def startup(self, app):
        """Initialize the proxy on startup."""
        self.session = aiohttp.ClientSession()
        
        # Start health check task
        asyncio.create_task(self.check_upstream_health())
        
        logger.info(f"SSE Persistent Proxy started on port {self.port}")
        logger.info(f"Upstream URL: {self.upstream_url}")
        
    async def cleanup(self, app):
        """Cleanup on shutdown."""
        if self.session:
            await self.session.close()
            
        # Close all active connections
        for response in self.active_connections:
            await response.write_eof()
            
    def run(self):
        """Run the proxy server."""
        self.app.on_startup.append(self.startup)
        self.app.on_cleanup.append(self.cleanup)
        
        web.run_app(self.app, host='0.0.0.0', port=self.port)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SSE Persistent Proxy for AIWhisperer MCP')
    parser.add_argument('--upstream-url', default='http://localhost:3001', 
                        help='Upstream AIWhisperer MCP server URL')
    parser.add_argument('--port', type=int, default=3002, 
                        help='Port for the proxy server')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and run proxy
    proxy = SSEPersistentProxy(args.upstream_url, args.port)
    proxy.run()


if __name__ == '__main__':
    main()