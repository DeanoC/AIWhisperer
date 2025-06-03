"""
Unit tests for ai_whisperer.extensions.conversation_replay.websocket_client

Tests for the WebSocketClient that handles WebSocket connection and communication
with the interactive server. This is a HIGH PRIORITY module with 10/10 complexity
score.
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_whisperer.extensions.conversation_replay.websocket_client import (
    WebSocketClient, WebSocketError, WebSocketConnectionError
)

# Skip entire module in CI to prevent hanging issues with WebSocket operations
pytestmark = pytest.mark.skipif(os.environ.get('CI') == 'true', reason="Skip websocket_client tests in CI due to hanging issues")

# Mock websockets module since it might not be available in test environment
try:
    from websockets.client import ClientConnection as WebSocketClientProtocol
except ImportError:
    try:
        from websockets.legacy.client import WebSocketClientProtocol
    except ImportError:
        # Create a mock for tests
        WebSocketClientProtocol = Mock


class TestWebSocketClientInit:
    """Test WebSocketClient initialization."""
    
    def test_init_default(self):
        """Test initialization with defaults."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        assert client.uri == "ws://localhost:8000/ws"
        assert client.timeout == 30.0
        assert client.connection is None
        assert client._response_handlers == {}
        assert client._notification_handler is None
        assert client._receive_task is None
    
    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = WebSocketClient("ws://example.com/ws", timeout=60.0)
        
        assert client.uri == "ws://example.com/ws"
        assert client.timeout == 60.0


class TestWebSocketClientConnection:
    """Test WebSocket connection functionality."""
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.websockets.connect')
    async def test_connect_success(self, mock_connect):
        """Test successful connection."""
        mock_connection = AsyncMock()
        # Make connect return a coroutine
        async def connect_coro(*args, **kwargs):
            return mock_connection
        mock_connect.side_effect = connect_coro
        
        client = WebSocketClient("ws://localhost:8000/ws")
        
        await client.connect()
        
        assert client.connection == mock_connection
        assert client._receive_task is not None
        mock_connect.assert_called_once()
        
        # Clean up
        client._receive_task.cancel()
        try:
            await client._receive_task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.websockets.connect')
    async def test_connect_timeout(self, mock_connect):
        """Test connection timeout."""
        mock_connect.side_effect = asyncio.TimeoutError()
        
        client = WebSocketClient("ws://localhost:8000/ws", timeout=5.0)
        
        with pytest.raises(WebSocketConnectionError) as exc_info:
            await client.connect()
        
        assert "Connection timeout after 5.0s" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.websockets.connect')
    async def test_connect_general_error(self, mock_connect):
        """Test connection general error."""
        mock_connect.side_effect = Exception("Network error")
        
        client = WebSocketClient("ws://localhost:8000/ws")
        
        with pytest.raises(WebSocketConnectionError) as exc_info:
            await client.connect()
        
        assert "Failed to connect: Network error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_close_with_connection(self):
        """Test closing active connection."""
        mock_connection = AsyncMock()
        
        # Create a proper mock task that can be cancelled and awaited
        mock_task = asyncio.create_task(asyncio.sleep(0))
        mock_task.cancel()
        
        client = WebSocketClient("ws://localhost:8000/ws")
        client.connection = mock_connection
        client._receive_task = mock_task
        
        await client.close()
        
        mock_connection.close.assert_called_once()
        assert client.connection is None
    
    @pytest.mark.asyncio
    async def test_close_without_connection(self):
        """Test closing when not connected."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Should not raise error
        await client.close()
        
        assert client.connection is None
    
    @pytest.mark.asyncio
    async def test_close_with_error(self):
        """Test closing with error in connection close."""
        mock_connection = AsyncMock()
        mock_connection.close.side_effect = Exception("Close error")
        
        client = WebSocketClient("ws://localhost:8000/ws")
        client.connection = mock_connection
        
        # Should handle error gracefully
        await client.close()
        
        assert client.connection is None


class TestWebSocketClientRequests:
    """Test request/response functionality."""
    
    @pytest.mark.asyncio
    async def test_send_request_not_connected(self):
        """Test sending request when not connected."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        with pytest.raises(WebSocketError) as exc_info:
            await client.send_request("test_method", {}, 1)
        
        assert "Not connected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_request_success(self):
        """Test successful request/response."""
        mock_connection = AsyncMock()
        
        client = WebSocketClient("ws://localhost:8000/ws")
        client.connection = mock_connection
        
        # Set up response
        async def mock_send(data):
            # Parse request
            request = json.loads(data)
            assert request["jsonrpc"] == "2.0"
            assert request["id"] == 1
            assert request["method"] == "test_method"
            assert request["params"] == {"key": "value"}
            
            # Simulate response
            response = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"success": True}
            }
            # Set result in response handler
            client._response_handlers[1].set_result(response)
        
        mock_connection.send.side_effect = mock_send
        
        result = await client.send_request("test_method", {"key": "value"}, 1)
        
        assert result == {"success": True}
        assert 1 not in client._response_handlers  # Cleaned up
    
    @pytest.mark.asyncio
    async def test_send_request_error_response(self):
        """Test request with error response."""
        mock_connection = AsyncMock()
        
        client = WebSocketClient("ws://localhost:8000/ws")
        client.connection = mock_connection
        
        # Set up error response
        async def mock_send(data):
            response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32601, "message": "Method not found"}
            }
            client._response_handlers[1].set_result(response)
        
        mock_connection.send.side_effect = mock_send
        
        with pytest.raises(WebSocketError) as exc_info:
            await client.send_request("unknown_method", {}, 1)
        
        assert "JSON-RPC error" in str(exc_info.value)
        assert "Method not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_request_timeout(self):
        """Test request timeout."""
        mock_connection = AsyncMock()
        
        client = WebSocketClient("ws://localhost:8000/ws", timeout=0.1)
        client.connection = mock_connection
        
        # Don't set response to simulate timeout
        mock_connection.send.return_value = None
        
        with pytest.raises(asyncio.TimeoutError):
            await client.send_request("test_method", {}, 1)
        
        assert 1 not in client._response_handlers  # Cleaned up
    
    @pytest.mark.asyncio
    async def test_send_request_cleanup_on_error(self):
        """Test that response handler is cleaned up on error."""
        mock_connection = AsyncMock()
        mock_connection.send.side_effect = Exception("Send failed")
        
        client = WebSocketClient("ws://localhost:8000/ws")
        client.connection = mock_connection
        
        with pytest.raises(Exception):
            await client.send_request("test_method", {}, 1)
        
        assert 1 not in client._response_handlers  # Cleaned up


class TestWebSocketClientNotifications:
    """Test notification handling."""
    
    def test_set_notification_handler(self):
        """Test setting notification handler."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        handler = Mock()
        client.set_notification_handler(handler)
        
        assert client._notification_handler == handler
    
    @pytest.mark.asyncio
    async def test_receive_messages_response(self):
        """Test receiving response message."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Set up mock connection that yields messages
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"test": True}
            })
        ]
        
        mock_connection = AsyncMock()
        mock_connection.__aiter__.return_value = messages
        client.connection = mock_connection
        
        # Set up response handler
        future = asyncio.Future()
        client._response_handlers[1] = future
        
        # Run receive task briefly
        receive_task = asyncio.create_task(client._receive_messages())
        await asyncio.sleep(0.1)
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass
        
        # Check response was handled
        assert future.done()
        result = future.result()
        assert result["result"] == {"test": True}
    
    @pytest.mark.asyncio
    async def test_receive_messages_notification(self):
        """Test receiving notification message."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Set up notification handler
        notification_received = None
        async def handler(notification):
            nonlocal notification_received
            notification_received = notification
        
        client.set_notification_handler(handler)
        
        # Set up mock connection that yields notification
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "method": "status_update",
                "params": {"status": "active"}
            })
        ]
        
        mock_connection = AsyncMock()
        mock_connection.__aiter__.return_value = messages
        client.connection = mock_connection
        
        # Run receive task briefly
        receive_task = asyncio.create_task(client._receive_messages())
        await asyncio.sleep(0.1)
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass
        
        # Check notification was handled
        assert notification_received is not None
        assert notification_received["method"] == "status_update"
        assert notification_received["params"] == {"status": "active"}
    
    @pytest.mark.asyncio
    async def test_receive_messages_no_handler(self):
        """Test receiving notification without handler."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # No notification handler set
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "method": "ignored_update",
                "params": {}
            })
        ]
        
        mock_connection = AsyncMock()
        mock_connection.__aiter__.return_value = messages
        client.connection = mock_connection
        
        # Run receive task - should not raise error
        receive_task = asyncio.create_task(client._receive_messages())
        await asyncio.sleep(0.1)
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.logger')
    async def test_receive_messages_json_error(self, mock_logger):
        """Test receiving invalid JSON message."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        messages = ["invalid json{"]
        
        mock_connection = AsyncMock()
        mock_connection.__aiter__.return_value = messages
        client.connection = mock_connection
        
        # Run receive task
        receive_task = asyncio.create_task(client._receive_messages())
        await asyncio.sleep(0.1)
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass
        
        # Should log error
        mock_logger.error.assert_called()
        assert "Failed to parse message" in mock_logger.error.call_args[0][0]
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.logger')
    async def test_receive_messages_handler_error(self, mock_logger):
        """Test error in message handler."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Set up response handler that raises error
        future = asyncio.Future()
        future.set_exception(Exception("Handler error"))
        client._response_handlers[1] = future
        
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {}
            })
        ]
        
        mock_connection = AsyncMock()
        mock_connection.__aiter__.return_value = messages
        client.connection = mock_connection
        
        # Run receive task
        receive_task = asyncio.create_task(client._receive_messages())
        await asyncio.sleep(0.1)
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass
        
        # Should log error
        mock_logger.error.assert_called()
        assert "Error handling message" in mock_logger.error.call_args[0][0]
    
    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="Test hangs and causes system slowdown")
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.logger')
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.websockets')
    async def test_receive_messages_connection_closed(self, mock_websockets, mock_logger):
        """Test handling connection closed."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Mock connection that raises ConnectionClosed
        mock_connection = AsyncMock()
        mock_connection.__aiter__.side_effect = mock_websockets.ConnectionClosed(None, None)
        client.connection = mock_connection
        
        # Run receive task
        await client._receive_messages()
        
        # Should log info
        mock_logger.info.assert_called()
        assert "closed by server" in mock_logger.info.call_args[0][0]


class TestWebSocketClientWaitForNotification:
    """Test wait_for_notification functionality."""
    
    @pytest.mark.asyncio
    async def test_wait_for_notification_success(self):
        """Test successfully waiting for notification."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Simulate notification arrival
        async def send_notification():
            await asyncio.sleep(0.1)
            if client._notification_handler:
                await client._notification_handler({
                    "method": "expected_notification",
                    "params": {"data": "test"}
                })
        
        # Start notification task
        asyncio.create_task(send_notification())
        
        # Wait for notification
        result = await client.wait_for_notification("expected_notification", timeout=1.0)
        
        assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_wait_for_notification_different_method(self):
        """Test ignoring notifications with different method."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Simulate wrong notification
        async def send_notification():
            await asyncio.sleep(0.1)
            if client._notification_handler:
                await client._notification_handler({
                    "method": "other_notification",
                    "params": {}
                })
        
        asyncio.create_task(send_notification())
        
        # Should timeout waiting for expected notification
        with pytest.raises(asyncio.TimeoutError):
            await client.wait_for_notification("expected_notification", timeout=0.3)
    
    @pytest.mark.asyncio
    async def test_wait_for_notification_default_timeout(self):
        """Test using default timeout."""
        client = WebSocketClient("ws://localhost:8000/ws", timeout=0.2)
        
        # Don't send notification - should use default timeout
        with pytest.raises(asyncio.TimeoutError):
            await client.wait_for_notification("never_arrives")
    
    @pytest.mark.asyncio
    async def test_wait_for_notification_restores_handler(self):
        """Test that original handler is restored."""
        client = WebSocketClient("ws://localhost:8000/ws")
        
        original_handler = Mock()
        client.set_notification_handler(original_handler)
        
        # Wait for notification that times out
        try:
            await client.wait_for_notification("test", timeout=0.1)
        except asyncio.TimeoutError:
            pass
        
        # Original handler should be restored
        assert client._notification_handler == original_handler


class TestWebSocketExceptions:
    """Test custom exception classes."""
    
    def test_websocket_error(self):
        """Test WebSocketError exception."""
        error = WebSocketError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_websocket_connection_error(self):
        """Test WebSocketConnectionError exception."""
        error = WebSocketConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, WebSocketError)


class TestWebSocketClientIntegration:
    """Integration tests for WebSocketClient."""
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.extensions.conversation_replay.websocket_client.websockets.connect')
    async def test_full_request_response_flow(self, mock_connect):
        """Test complete request/response flow."""
        mock_connection = AsyncMock()
        # Make connect return a coroutine
        async def connect_coro(*args, **kwargs):
            return mock_connection
        mock_connect.side_effect = connect_coro
        
        client = WebSocketClient("ws://localhost:8000/ws")
        
        # Connect
        await client.connect()
        
        # Simulate server response
        async def handle_send(data):
            request = json.loads(data)
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {"echo": request["params"]["message"]}
            }
            # Simulate async response
            await asyncio.sleep(0.01)
            client._response_handlers[request["id"]].set_result(response)
        
        mock_connection.send.side_effect = handle_send
        
        # Send request
        result = await client.send_request("echo", {"message": "Hello"}, 1)
        
        assert result == {"echo": "Hello"}
        
        # Clean up
        await client.close()
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Test causes system resource issues")
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        mock_connection = AsyncMock()
        
        client = WebSocketClient("ws://localhost:8000/ws")
        client.connection = mock_connection
        
        # Track sent requests
        sent_requests = []
        
        async def handle_send(data):
            request = json.loads(data)
            sent_requests.append(request)
            # Simulate responses with different delays
            delay = 0.01 * request["id"]
            await asyncio.sleep(delay)
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {"request_id": request["id"]}
            }
            client._response_handlers[request["id"]].set_result(response)
        
        mock_connection.send.side_effect = handle_send
        
        # Send multiple requests concurrently
        tasks = [
            client.send_request("test", {}, i)
            for i in range(1, 4)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all requests were handled
        assert len(results) == 3
        assert all(r["request_id"] == i+1 for i, r in enumerate(results))
        assert len(sent_requests) == 3