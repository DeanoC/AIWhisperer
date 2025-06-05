"""Tests for enhanced WebSocket transport."""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Skip if aiohttp not available
aiohttp = pytest.importorskip("aiohttp")

from ai_whisperer.mcp.server.transports.websocket_enhanced import (
    WebSocketEnhancedTransport, ConnectionInfo
)
from ai_whisperer.mcp.server.config import MCPServerConfig


class TestWebSocketEnhancedTransport:
    """Tests for enhanced WebSocket transport."""
    
    @pytest.fixture
    def mock_server(self):
        """Create mock MCP server."""
        server = Mock()
        server.config = MCPServerConfig()
        server.handle_request = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "result": {"test": "success"},
            "id": 1
        })
        return server
        
    @pytest.fixture
    def transport(self, mock_server):
        """Create transport instance."""
        return WebSocketEnhancedTransport(
            mock_server,
            "localhost",
            8080,
            max_connections=10,
            heartbeat_interval=1.0
        )
        
    @pytest.mark.asyncio
    async def test_init(self, transport):
        """Test transport initialization."""
        assert transport.host == "localhost"
        assert transport.port == 8080
        assert transport.max_connections == 10
        assert transport.heartbeat_interval == 1.0
        assert len(transport.connections) == 0
        
    @pytest.mark.asyncio
    async def test_start_stop(self, transport):
        """Test starting and stopping transport."""
        with patch('aiohttp.web.AppRunner') as mock_runner:
            with patch('aiohttp.web.TCPSite') as mock_site:
                # Setup mocks
                mock_runner_instance = AsyncMock()
                mock_site_instance = AsyncMock()
                mock_runner.return_value = mock_runner_instance
                mock_site.return_value = mock_site_instance
                
                # Start transport
                await transport.start()
                
                assert transport.app is not None
                assert transport.runner is not None
                assert transport.site is not None
                assert transport._heartbeat_task is not None
                
                # Stop transport
                await transport.stop()
                
                mock_site_instance.stop.assert_called_once()
                mock_runner_instance.cleanup.assert_called_once()
                
    def test_connection_info(self):
        """Test ConnectionInfo dataclass."""
        ws = Mock()
        conn = ConnectionInfo(
            id="test-123",
            ws=ws,
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        
        assert conn.id == "test-123"
        assert conn.ws == ws
        assert conn.remote == "127.0.0.1"
        assert isinstance(conn.connected_at, datetime)
        assert conn.last_ping is None
        assert conn.last_pong is None
        assert len(conn.pending_requests) == 0
        assert len(conn.message_queue) == 0
        
    @pytest.mark.asyncio
    async def test_handle_health(self, transport):
        """Test health check endpoint."""
        request = Mock()
        
        # Mock web.json_response
        with patch('aiohttp.web.json_response') as mock_response:
            await transport._handle_health(request)
            
            mock_response.assert_called_once()
            health_data = mock_response.call_args[0][0]
            
            assert health_data["status"] == "healthy"
            assert health_data["connections"] == 0
            assert health_data["max_connections"] == 10
            
    @pytest.mark.asyncio
    async def test_connection_limit(self, transport):
        """Test connection limit enforcement."""
        # Fill up connections
        for i in range(10):
            transport.connections[str(i)] = Mock()
            
        # Mock request and WebSocketResponse
        request = Mock()
        
        with patch('aiohttp.web.Response') as mock_response:
            result = await transport._handle_websocket(request)
            
            mock_response.assert_called_with(status=503, text="Connection limit reached")
            
    @pytest.mark.asyncio
    async def test_handle_message_success(self, transport, mock_server):
        """Test successful message handling."""
        # Create connection
        conn = ConnectionInfo(
            id="test-conn",
            ws=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        
        # Test message
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "test",
            "params": {},
            "id": 1
        })
        
        await transport._handle_message(conn, data)
        
        # Verify server was called
        mock_server.handle_request.assert_called_once()
        
        # Verify response was sent
        conn.ws.send_json.assert_called_once()
        sent_data = conn.ws.send_json.call_args[0][0]
        assert sent_data["result"]["test"] == "success"
        
    @pytest.mark.asyncio
    async def test_handle_message_parse_error(self, transport):
        """Test handling of JSON parse errors."""
        conn = ConnectionInfo(
            id="test-conn",
            ws=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        
        # Invalid JSON
        await transport._handle_message(conn, "invalid json{")
        
        # Verify error response
        conn.ws.send_json.assert_called_once()
        sent_data = conn.ws.send_json.call_args[0][0]
        assert sent_data["error"]["code"] == -32700
        assert "Parse error" in sent_data["error"]["message"]
        
    @pytest.mark.asyncio
    async def test_handle_message_timeout(self, transport, mock_server):
        """Test request timeout handling."""
        # Make server slow
        async def slow_handler(request):
            await asyncio.sleep(2)
            return {"result": "too late"}
            
        mock_server.handle_request = slow_handler
        transport.request_timeout = 0.1
        
        conn = ConnectionInfo(
            id="test-conn",
            ws=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "test",
            "id": 1
        })
        
        await transport._handle_message(conn, data)
        
        # Verify timeout error
        conn.ws.send_json.assert_called_once()
        sent_data = conn.ws.send_json.call_args[0][0]
        assert sent_data["error"]["code"] == -32000
        assert "timeout" in sent_data["error"]["message"].lower()
        
    @pytest.mark.asyncio
    async def test_message_queueing(self, transport):
        """Test message queueing when connection is closed."""
        conn = ConnectionInfo(
            id="test-conn",
            ws=Mock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        conn.ws.closed = True
        
        # Try to send message
        message = {"test": "data"}
        await transport._send_message(conn, message)
        
        # Verify message was queued
        assert len(conn.message_queue) == 1
        assert conn.message_queue[0] == message
        
    @pytest.mark.asyncio
    async def test_heartbeat_loop(self, transport):
        """Test heartbeat functionality."""
        # Create connection
        conn = ConnectionInfo(
            id="test-conn",
            ws=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        conn.ws.closed = False
        transport.connections[conn.id] = conn
        
        # Run one heartbeat iteration
        transport.heartbeat_interval = 0.01
        transport.heartbeat_timeout = 0.1
        
        # Start heartbeat
        heartbeat_task = asyncio.create_task(transport._heartbeat_loop())
        
        # Wait for heartbeat
        await asyncio.sleep(0.02)
        
        # Stop heartbeat
        transport._shutdown = True
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
            
        # Verify ping was sent
        conn.ws.ping.assert_called()
        assert conn.last_ping is not None
        
    @pytest.mark.asyncio
    async def test_close_connection(self, transport):
        """Test connection closing."""
        conn = ConnectionInfo(
            id="test-conn",
            ws=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        conn.ws.closed = False
        
        # Add pending request
        future = asyncio.Future()
        conn.pending_requests["req-1"] = future
        
        # Add to connections
        transport.connections[conn.id] = conn
        
        # Close connection
        await transport._close_connection(conn, "Test close")
        
        # Verify cleanup
        assert conn.id not in transport.connections
        assert future.cancelled()
        conn.ws.close.assert_called_once()
        
    def test_get_connection_stats(self, transport):
        """Test connection statistics."""
        # Add some connections
        now = datetime.utcnow()
        
        conn1 = ConnectionInfo(
            id="conn-1",
            ws=Mock(),
            remote="127.0.0.1",
            connected_at=now - timedelta(minutes=5)
        )
        conn1.last_pong = now - timedelta(seconds=30)
        
        conn2 = ConnectionInfo(
            id="conn-2",
            ws=Mock(),
            remote="192.168.1.1",
            connected_at=now - timedelta(minutes=2)
        )
        
        transport.connections = {
            "conn-1": conn1,
            "conn-2": conn2
        }
        
        stats = transport.get_connection_stats()
        
        assert stats["total_connections"] == 2
        assert len(stats["connections"]) == 2
        
        # Check first connection
        conn1_stats = next(c for c in stats["connections"] if c["id"] == "conn-1")
        assert conn1_stats["remote"] == "127.0.0.1"
        assert conn1_stats["connected_duration"] > 0
        assert conn1_stats["last_activity"] is not None
        
    @pytest.mark.asyncio
    async def test_send_notification(self, transport):
        """Test sending notifications."""
        conn = ConnectionInfo(
            id="test-conn",
            ws=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow()
        )
        conn.ws.closed = False
        
        await transport._send_notification(conn, "test.event", {"data": "value"})
        
        # Verify notification was sent
        conn.ws.send_json.assert_called_once()
        sent_data = conn.ws.send_json.call_args[0][0]
        assert sent_data["jsonrpc"] == "2.0"
        assert sent_data["method"] == "test.event"
        assert sent_data["params"]["data"] == "value"
        assert "id" not in sent_data  # Notifications have no ID