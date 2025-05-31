"""
WebSocket client for Debbie the Debugger.
Handles WebSocket connection and communication with the interactive server.
"""

import asyncio
import json
import logging
import websockets
from typing import Optional, Dict, Any, Callable
# Use the new import path for websockets 11+
try:
    from websockets.client import ClientConnection as WebSocketClientProtocol
except ImportError:
    # Fall back to old import for older versions
    from websockets.legacy.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class WebSocketError(Exception):
    """Base exception for WebSocket operations."""
    pass


class WebSocketConnectionError(WebSocketError):
    """Raised when WebSocket connection fails."""
    pass


class WebSocketClient:
    """WebSocket client for communicating with the interactive server."""
    
    def __init__(self, uri: str, timeout: float = 30.0):
        """
        Initialize WebSocket client.
        
        Args:
            uri: WebSocket URI to connect to (e.g., ws://localhost:8000/ws)
            timeout: Connection and operation timeout in seconds
        """
        self.uri = uri
        self.timeout = timeout
        self.connection: Optional[WebSocketClientProtocol] = None
        self._response_handlers: Dict[int, asyncio.Future] = {}
        self._notification_handler: Optional[Callable] = None
        self._receive_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> None:
        """
        Establish WebSocket connection.
        
        Raises:
            WebSocketConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to WebSocket at {self.uri}")
            self.connection = await asyncio.wait_for(
                websockets.connect(self.uri),
                timeout=self.timeout
            )
            
            # Start message receiver task
            self._receive_task = asyncio.create_task(self._receive_messages())
            
            logger.info("WebSocket connection established")
            
        except asyncio.TimeoutError:
            raise WebSocketConnectionError(f"Connection timeout after {self.timeout}s")
        except Exception as e:
            raise WebSocketConnectionError(f"Failed to connect: {e}")
            
    async def close(self) -> None:
        """Close the WebSocket connection gracefully."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
                
        if self.connection:
            try:
                await self.connection.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            finally:
                self.connection = None
                
    async def send_request(self, method: str, params: Dict[str, Any], request_id: int) -> Dict[str, Any]:
        """
        Send a JSON-RPC request and wait for response.
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            request_id: Unique request ID
            
        Returns:
            Response result
            
        Raises:
            WebSocketError: If send fails or response indicates error
        """
        if not self.connection:
            raise WebSocketError("Not connected")
            
        # Create response future
        response_future = asyncio.Future()
        self._response_handlers[request_id] = response_future
        
        # Build request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        try:
            # Send request
            await self.connection.send(json.dumps(request))
            logger.debug(f"Sent request: {method} (id={request_id})")
            
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=self.timeout)
            
            # Check for error
            if "error" in response:
                raise WebSocketError(f"JSON-RPC error: {response['error']}")
                
            return response.get("result", {})
            
        finally:
            # Clean up handler
            self._response_handlers.pop(request_id, None)
            
    def set_notification_handler(self, handler: Callable) -> None:
        """
        Set handler for JSON-RPC notifications.
        
        Args:
            handler: Async function to handle notifications
        """
        self._notification_handler = handler
        
    async def _route_message(self, data: Dict[str, Any]):
        """Routes a received message data to either response or notification handler."""
        if "id" in data:
            request_id = data["id"]
            if request_id in self._response_handlers:
                self._response_handlers[request_id].set_result(data)
            else:
                logger.warning(f"Received response for unknown request_id: {request_id}")
        else:
            if self._notification_handler:
                # Schedule as a task to avoid blocking the receive loop if handler is slow
                asyncio.create_task(self._notification_handler(data))
            else:
                logger.debug(f"Unhandled notification: {data.get('method', 'unknown')}")

    async def _receive_messages(self) -> None:
        """Background task to receive and route messages."""
        if not self.connection: # Should not happen if called after connect()
            logger.error("_receive_messages called with no active connection.")
            return

        try:
            async for message in self.connection:
                try:
                    data = json.loads(message)
                    await self._route_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse incoming JSON message: {e}. Message: '{message}'")
                except Exception as e: # Catch errors from _route_message or other processing
                    logger.error(f"Error handling received message: {e}")
                    
        except websockets.ConnectionClosed:
            logger.info("WebSocket connection closed by server.")
        except asyncio.CancelledError:
            logger.info("Receive loop cancelled.")
            raise # Propagate cancellation
        except Exception as e: # Catch other unexpected errors from the connection itself
            logger.error(f"Receive loop encountered an error: {e}", exc_info=True)
            # Depending on the error, may need to signal connection loss to the client object
            
    async def wait_for_notification(self, method: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for a specific notification.
        
        Args:
            method: Notification method to wait for
            timeout: Maximum time to wait (uses default if None)
            
        Returns:
            Notification params
            
        Raises:
            asyncio.TimeoutError: If timeout occurs
        """
        if timeout is None:
            timeout = self.timeout
            
        future = asyncio.Future()
        
        async def handler(notification):
            if notification.get("method") == method:
                future.set_result(notification.get("params", {}))
                
        old_handler = self._notification_handler
        self._notification_handler = handler
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._notification_handler = old_handler