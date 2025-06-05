"""Server-Sent Events (SSE) transport for MCP server."""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

try:
    import aiohttp
    from aiohttp import web
    from aiohttp.web_response import StreamResponse
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None
    web = None
    StreamResponse = None

logger = logging.getLogger(__name__)


@dataclass
class SSEConnection:
    """Information about an SSE connection."""
    id: str
    response: StreamResponse
    remote: str
    connected_at: datetime
    event_queue: asyncio.Queue
    task: Optional[asyncio.Task] = None
    

class SSEServerTransport:
    """Server-Sent Events transport for MCP server.
    
    SSE is a one-way communication protocol where the server can push
    messages to the client. For MCP, we need to handle requests via
    HTTP POST and send responses via SSE.
    """
    
    def __init__(
        self,
        server,
        host: str,
        port: int,
        heartbeat_interval: float = 30.0,
        max_connections: int = 100,
        cors_origins: Optional[Set[str]] = None
    ):
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp is required for SSE transport. "
                "Install it with: pip install aiohttp"
            )
        self.server = server
        self.host = host
        self.port = port
        self.heartbeat_interval = heartbeat_interval
        self.max_connections = max_connections
        self.cors_origins = cors_origins or {"*"}
        
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.connections: Dict[str, SSEConnection] = {}
        self._shutdown = False
        
    async def start(self):
        """Start SSE server."""
        logger.info(f"Starting MCP SSE server on {self.host}:{self.port}")
        
        # Create aiohttp app
        self.app = web.Application()
        
        # Add CORS middleware if needed
        if self.cors_origins:
            self.app.middlewares.append(self._cors_middleware)
            
        # Add routes
        self.app.router.add_get('/mcp/sse', self._handle_sse)
        self.app.router.add_post('/mcp/request', self._handle_request)
        self.app.router.add_options('/mcp/request', self._handle_preflight)
        self.app.router.add_get('/mcp/health', self._handle_health)
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"MCP SSE server listening on http://{self.host}:{self.port}")
        logger.info(f"  SSE endpoint: http://{self.host}:{self.port}/mcp/sse")
        logger.info(f"  Request endpoint: http://{self.host}:{self.port}/mcp/request")
        
    async def stop(self):
        """Stop SSE server."""
        logger.info("Stopping SSE transport...")
        self._shutdown = True
        
        # Close all connections
        for conn in list(self.connections.values()):
            await self._close_connection(conn)
            
        # Stop server
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
            
        logger.info("SSE transport stopped")
        
    @web.middleware
    async def _cors_middleware(self, request, handler):
        """CORS middleware for cross-origin requests."""
        # Handle preflight
        if request.method == 'OPTIONS':
            return self._create_cors_response()
            
        # Handle actual request
        response = await handler(request)
        
        # Add CORS headers
        origin = request.headers.get('Origin', '*')
        if origin in self.cors_origins or '*' in self.cors_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Connection-Id'
            
        return response
        
    def _create_cors_response(self):
        """Create CORS preflight response."""
        response = web.Response(status=204)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Connection-Id'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
        
    async def _handle_preflight(self, request):
        """Handle CORS preflight requests."""
        return self._create_cors_response()
        
    async def _handle_health(self, request):
        """Health check endpoint."""
        health_data = {
            "status": "healthy" if not self._shutdown else "shutting_down",
            "connections": len(self.connections),
            "max_connections": self.max_connections,
            "transport": "sse"
        }
        return web.json_response(health_data)
        
    async def _handle_sse(self, request):
        """Handle SSE connection."""
        # Check connection limit
        if len(self.connections) >= self.max_connections:
            return web.Response(status=503, text="Connection limit reached")
            
        # Create SSE response
        response = StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        
        await response.prepare(request)
        
        # Create connection
        conn_id = str(uuid.uuid4())
        conn = SSEConnection(
            id=conn_id,
            response=response,
            remote=request.headers.get('X-Forwarded-For', request.remote),
            connected_at=datetime.utcnow(),
            event_queue=asyncio.Queue()
        )
        self.connections[conn_id] = conn
        
        # Send connection ID to client
        await self._send_event(conn, 'connection', {
            'connectionId': conn_id,
            'serverInfo': {
                'name': self.server.config.server_name,
                'version': self.server.config.server_version
            }
        })
        
        logger.info(f"New SSE connection {conn_id} from {conn.remote}")
        
        # Start event loop for this connection
        conn.task = asyncio.create_task(self._connection_loop(conn))
        
        try:
            # Wait for connection to close
            await conn.task
        except asyncio.CancelledError:
            pass
        finally:
            await self._close_connection(conn)
            
        return response
        
    async def _connection_loop(self, conn: SSEConnection):
        """Main event loop for an SSE connection."""
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(conn))
        
        try:
            while not self._shutdown:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(
                        conn.event_queue.get(),
                        timeout=1.0
                    )
                    
                    # Send event
                    await self._send_sse_message(conn, event)
                    
                except asyncio.TimeoutError:
                    # Check if connection is still alive
                    if conn.response._eof:
                        break
                        
        except Exception as e:
            logger.error(f"Error in SSE connection loop {conn.id}: {e}", exc_info=True)
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
                
    async def _heartbeat_loop(self, conn: SSEConnection):
        """Send periodic heartbeats to keep connection alive."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat comment
                await conn.response.write(b': heartbeat\n\n')
                
            except Exception as e:
                logger.error(f"Error sending heartbeat to {conn.id}: {e}")
                break
                
    async def _handle_request(self, request):
        """Handle MCP request via POST."""
        # Get connection ID from header
        conn_id = request.headers.get('X-Connection-Id')
        if not conn_id or conn_id not in self.connections:
            return web.json_response(
                {"error": "Invalid or missing connection ID"},
                status=400
            )
            
        conn = self.connections[conn_id]
        
        try:
            # Parse request
            request_data = await request.json()
            
            # Handle request
            response = await self.server.handle_request(request_data)
            
            # Queue response for SSE delivery
            await conn.event_queue.put({
                'event': 'response',
                'data': response
            })
            
            # Return acknowledgment
            return web.json_response({"status": "accepted"})
            
        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400
            )
        except Exception as e:
            logger.error(f"Error handling request from {conn_id}: {e}", exc_info=True)
            return web.json_response(
                {"error": "Internal server error"},
                status=500
            )
            
    async def _send_event(self, conn: SSEConnection, event_type: str, data: Any):
        """Queue an event for sending."""
        await conn.event_queue.put({
            'event': event_type,
            'data': data
        })
        
    async def _send_sse_message(self, conn: SSEConnection, event: Dict[str, Any]):
        """Send an SSE message."""
        try:
            # Format SSE message
            lines = []
            
            # Add event type if specified
            if 'event' in event:
                lines.append(f"event: {event['event']}")
                
            # Add ID if specified
            if 'id' in event:
                lines.append(f"id: {event['id']}")
                
            # Add data (JSON encoded)
            data = json.dumps(event['data'])
            for line in data.split('\n'):
                lines.append(f"data: {line}")
                
            # Add empty line to end message
            lines.append('')
            lines.append('')
            
            # Send message
            message = '\n'.join(lines)
            await conn.response.write(message.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error sending SSE message to {conn.id}: {e}")
            raise
            
    async def _close_connection(self, conn: SSEConnection):
        """Close an SSE connection."""
        try:
            # Cancel task
            if conn.task and not conn.task.done():
                conn.task.cancel()
                
            # Send close event
            try:
                await self._send_event(conn, 'close', {'reason': 'Connection closing'})
                await asyncio.sleep(0.1)  # Give time for final message
            except:
                pass
                
            # Close response
            if not conn.response._eof:
                await conn.response.write_eof()
                
            # Remove from connections
            self.connections.pop(conn.id, None)
            
            logger.info(f"Closed SSE connection {conn.id}")
            
        except Exception as e:
            logger.error(f"Error closing SSE connection {conn.id}: {e}")
            
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        now = datetime.utcnow()
        stats = {
            "total_connections": len(self.connections),
            "transport": "sse",
            "connections": []
        }
        
        for conn in self.connections.values():
            conn_stats = {
                "id": conn.id,
                "remote": conn.remote,
                "connected_duration": (now - conn.connected_at).total_seconds(),
                "queued_events": conn.event_queue.qsize()
            }
            stats["connections"].append(conn_stats)
            
        return stats