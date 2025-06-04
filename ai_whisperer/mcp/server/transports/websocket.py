"""WebSocket transport for MCP server."""

import asyncio
import json
import logging
from typing import Set
import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)


class WebSocketServerTransport:
    """WebSocket transport for MCP server."""
    
    def __init__(self, server, host: str, port: int):
        self.server = server
        self.host = host
        self.port = port
        self.app: web.Application = None
        self.runner: web.AppRunner = None
        self.site: web.TCPSite = None
        self.websockets: Set[web.WebSocketResponse] = set()
        
    async def start(self):
        """Start WebSocket server."""
        logger.info(f"Starting MCP WebSocket server on {self.host}:{self.port}")
        
        # Create aiohttp app
        self.app = web.Application()
        self.app.router.add_get('/mcp', self._handle_websocket)
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"MCP WebSocket server listening on ws://{self.host}:{self.port}/mcp")
        
    async def stop(self):
        """Stop WebSocket server."""
        # Close all websockets
        for ws in list(self.websockets):
            await ws.close()
            
        # Stop server
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
            
        logger.info("MCP WebSocket transport stopped")
        
    async def _handle_websocket(self, request):
        """Handle WebSocket connection."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add to active connections
        self.websockets.add(ws)
        
        try:
            logger.info(f"New WebSocket connection from {request.remote}")
            
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        # Parse JSON-RPC request
                        request_data = json.loads(msg.data)
                        
                        # Handle request
                        response = await self.server.handle_request(request_data)
                        
                        # Send response
                        await ws.send_json(response)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON: {e}")
                        # Send parse error response
                        await ws.send_json({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            },
                            "id": None
                        })
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
            
        finally:
            # Remove from active connections
            self.websockets.discard(ws)
            await ws.close()
            logger.info("WebSocket connection closed")
            
        return ws