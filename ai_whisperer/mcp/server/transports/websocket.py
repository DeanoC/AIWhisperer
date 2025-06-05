"""WebSocket transport for MCP server with production features."""

import asyncio
import json
import logging
import time
import uuid
from typing import Set, Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

try:
    import aiohttp
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None
    web = None

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    id: str
    ws: web.WebSocketResponse
    remote: str
    connected_at: datetime
    last_ping: Optional[datetime] = None
    last_pong: Optional[datetime] = None
    pending_requests: Dict[Any, asyncio.Future] = field(default_factory=dict)
    message_queue: List[Dict[str, Any]] = field(default_factory=list)
    

class WebSocketServerTransport:
    """WebSocket transport with production features."""
    
    def __init__(
        self,
        server,
        host: str,
        port: int,
        max_connections: int = 100,
        heartbeat_interval: float = 30.0,
        heartbeat_timeout: float = 60.0,
        request_timeout: float = 300.0,
        max_queue_size: int = 1000,
        enable_compression: bool = True
    ):
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp is required for WebSocket transport. "
                "Install it with: pip install aiohttp"
            )
        self.server = server
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.request_timeout = request_timeout
        self.max_queue_size = max_queue_size
        self.enable_compression = enable_compression
        
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.connections: Dict[str, ConnectionInfo] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def start(self):
        """Start WebSocket server."""
        logger.info(f"Starting MCP WebSocket server on {self.host}:{self.port}")
        
        # Create aiohttp app with middleware
        self.app = web.Application(middlewares=[self._error_middleware])
        self.app.router.add_get('/mcp', self._handle_websocket)
        self.app.router.add_get('/health', self._handle_health)
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info(f"MCP WebSocket server listening on ws://{self.host}:{self.port}/mcp")
        
    async def stop(self):
        """Stop WebSocket server gracefully."""
        logger.info("Stopping WebSocket transport...")
        self._shutdown = True
        
        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
                
        # Close all connections gracefully
        close_tasks = []
        for conn_info in list(self.connections.values()):
            close_tasks.append(self._close_connection(conn_info, "Server shutting down"))
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
            
        # Stop server
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
            
        logger.info("WebSocket transport stopped")
        
    @web.middleware
    async def _error_middleware(self, request, handler):
        """Middleware for error handling."""
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unhandled error in request handler: {e}", exc_info=True)
            return web.json_response(
                {"error": "Internal server error"},
                status=500
            )
            
    async def _handle_health(self, request):
        """Health check endpoint."""
        health_data = {
            "status": "healthy" if not self._shutdown else "shutting_down",
            "connections": len(self.connections),
            "max_connections": self.max_connections,
            "uptime": time.time() - self._start_time if hasattr(self, '_start_time') else 0
        }
        return web.json_response(health_data)
        
    async def _handle_websocket(self, request):
        """Handle WebSocket connection with enhanced features."""
        # Check connection limit
        if len(self.connections) >= self.max_connections:
            logger.warning(f"Connection limit reached ({self.max_connections})")
            return web.Response(status=503, text="Connection limit reached")
            
        # Create WebSocket response with compression
        ws = web.WebSocketResponse(
            compress=self.enable_compression,
            heartbeat=self.heartbeat_interval
        )
        await ws.prepare(request)
        
        # Create connection info
        conn_id = str(uuid.uuid4())
        conn_info = ConnectionInfo(
            id=conn_id,
            ws=ws,
            remote=request.headers.get('X-Forwarded-For', request.remote),
            connected_at=datetime.now(timezone.utc)
        )
        self.connections[conn_id] = conn_info
        
        try:
            logger.info(f"New WebSocket connection {conn_id} from {conn_info.remote}")
            
            # Send welcome message
            await self._send_notification(conn_info, "connection.established", {
                "connectionId": conn_id,
                "serverInfo": {
                    "name": self.server.config.server_name,
                    "version": self.server.config.server_version
                }
            })
            
            # Update monitoring
            if hasattr(self.server, 'monitor'):
                self.server.monitor.update_transport_metrics(
                    "websocket", "connection_opened"
                )
                
            # Handle messages
            async for msg in ws:
                if self._shutdown:
                    break
                    
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Update monitoring
                    if hasattr(self.server, 'monitor'):
                        self.server.monitor.update_transport_metrics(
                            "websocket", "message_received"
                        )
                        self.server.monitor.update_transport_metrics(
                            "websocket", "bytes_received", len(msg.data)
                        )
                        
                    # Set context for monitoring
                    self.server._current_transport = "websocket"
                    self.server._current_connection_id = conn_id
                    
                    asyncio.create_task(self._handle_message(conn_info, msg.data))
                    
                elif msg.type == aiohttp.WSMsgType.PONG:
                    conn_info.last_pong = datetime.now(timezone.utc)
                    logger.debug(f"Received pong from {conn_id}")
                    
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f'WebSocket error on {conn_id}: {ws.exception()}')
                    break
                    
        except Exception as e:
            logger.error(f"Error in WebSocket handler for {conn_id}: {e}", exc_info=True)
            
        finally:
            # Update monitoring
            if hasattr(self.server, 'monitor'):
                self.server.monitor.update_transport_metrics(
                    "websocket", "connection_closed"
                )
                
            await self._close_connection(conn_info, "Connection closed")
            
        return ws
        
    async def _handle_message(self, conn_info: ConnectionInfo, data: str):
        """Handle incoming message with timeout and error handling."""
        try:
            # Parse JSON-RPC request
            request_data = json.loads(data)
            request_id = request_data.get("id")
            
            # Add to pending requests if it has an ID
            if request_id is not None:
                future = asyncio.Future()
                conn_info.pending_requests[request_id] = future
                
            # Handle request with timeout
            try:
                response = await asyncio.wait_for(
                    self.server.handle_request(request_data),
                    timeout=self.request_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Request timeout for {conn_info.id}: {request_data.get('method')}")
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Request timeout"
                    },
                    "id": request_id
                }
                
            # Send response
            await self._send_message(conn_info, response)
            
            # Complete future if exists
            if request_id in conn_info.pending_requests:
                conn_info.pending_requests[request_id].set_result(response)
                del conn_info.pending_requests[request_id]
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {conn_info.id}: {e}")
            await self._send_message(conn_info, {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                },
                "id": None
            })
        except Exception as e:
            logger.error(f"Error handling message from {conn_info.id}: {e}", exc_info=True)
            
    async def _send_message(self, conn_info: ConnectionInfo, message: Dict[str, Any]):
        """Send message with queue support for reliability."""
        try:
            if conn_info.ws.closed:
                # Queue message if connection is temporarily unavailable
                if len(conn_info.message_queue) < self.max_queue_size:
                    conn_info.message_queue.append(message)
                    logger.debug(f"Queued message for {conn_info.id}")
                else:
                    logger.warning(f"Message queue full for {conn_info.id}, dropping message")
                return
                
            # Send queued messages first
            while conn_info.message_queue and not conn_info.ws.closed:
                queued_msg = conn_info.message_queue.pop(0)
                await conn_info.ws.send_json(queued_msg)
                
            # Send current message
            await conn_info.ws.send_json(message)
            
        except ConnectionResetError:
            logger.warning(f"Connection reset for {conn_info.id}, queuing message")
            if len(conn_info.message_queue) < self.max_queue_size:
                conn_info.message_queue.append(message)
        except Exception as e:
            logger.error(f"Error sending message to {conn_info.id}: {e}")
            
    async def _send_notification(self, conn_info: ConnectionInfo, method: str, params: Dict[str, Any]):
        """Send JSON-RPC notification."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        await self._send_message(conn_info, notification)
        
    async def _close_connection(self, conn_info: ConnectionInfo, reason: str):
        """Close connection gracefully."""
        try:
            # Cancel pending requests
            for future in conn_info.pending_requests.values():
                if not future.done():
                    future.cancel()
                    
            # Send close notification
            await self._send_notification(conn_info, "connection.closing", {
                "reason": reason
            })
            
            # Close WebSocket
            if not conn_info.ws.closed:
                await conn_info.ws.close()
                
            # Remove from connections
            self.connections.pop(conn_info.id, None)
            
            logger.info(f"Closed connection {conn_info.id}: {reason}")
            
        except Exception as e:
            logger.error(f"Error closing connection {conn_info.id}: {e}")
            
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to detect dead connections."""
        self._start_time = time.time()
        
        while not self._shutdown:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check each connection
                for conn_info in list(self.connections.values()):
                    try:
                        # Check if connection is alive
                        if conn_info.last_ping:
                            time_since_ping = (datetime.now(timezone.utc) - conn_info.last_ping).total_seconds()
                            if time_since_ping > self.heartbeat_timeout:
                                logger.warning(f"Connection {conn_info.id} timed out")
                                await self._close_connection(conn_info, "Heartbeat timeout")
                                continue
                                
                        # Send ping
                        if not conn_info.ws.closed:
                            await conn_info.ws.ping()
                            conn_info.last_ping = datetime.now(timezone.utc)
                            
                    except Exception as e:
                        logger.error(f"Error in heartbeat for {conn_info.id}: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
                
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        now = datetime.now(timezone.utc)
        stats = {
            "total_connections": len(self.connections),
            "connections": []
        }
        
        for conn_info in self.connections.values():
            conn_stats = {
                "id": conn_info.id,
                "remote": conn_info.remote,
                "connected_duration": (now - conn_info.connected_at).total_seconds(),
                "pending_requests": len(conn_info.pending_requests),
                "queued_messages": len(conn_info.message_queue),
                "last_activity": conn_info.last_pong.isoformat() if conn_info.last_pong else None
            }
            stats["connections"].append(conn_stats)
            
        return stats