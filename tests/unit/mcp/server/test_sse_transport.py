"""Tests for SSE transport."""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Skip if aiohttp not available
aiohttp = pytest.importorskip("aiohttp")

from ai_whisperer.mcp.server.transports.sse import (
    SSEServerTransport, SSEConnection
)
from ai_whisperer.mcp.server.config import MCPServerConfig


class TestSSETransport:
    """Tests for SSE transport."""
    
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
        return SSEServerTransport(
            mock_server,
            "localhost",
            8080,
            heartbeat_interval=1.0,
            max_connections=10,
            cors_origins={"*"}
        )
        
    @pytest.mark.asyncio
    async def test_init(self, transport):
        """Test transport initialization."""
        assert transport.host == "localhost"
        assert transport.port == 8080
        assert transport.heartbeat_interval == 1.0
        assert transport.max_connections == 10
        assert "*" in transport.cors_origins
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
                
                # Check routes
                routes = [str(r) for r in transport.app.router.routes()]
                assert any('/mcp/sse' in r for r in routes)
                assert any('/mcp/request' in r for r in routes)
                assert any('/mcp/health' in r for r in routes)
                
                # Stop transport
                await transport.stop()
                
                mock_site_instance.stop.assert_called_once()
                mock_runner_instance.cleanup.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_cors_middleware(self, transport):
        """Test CORS middleware."""
        # Create mock request and handler
        request = Mock()
        request.method = 'GET'
        request.headers = {'Origin': 'http://example.com'}
        
        handler = AsyncMock()
        response = Mock()
        response.headers = {}
        handler.return_value = response
        
        # Call middleware
        middleware = transport._cors_middleware
        result = await middleware(request, handler)
        
        # Verify CORS headers
        assert result.headers['Access-Control-Allow-Origin'] == 'http://example.com'
        assert result.headers['Access-Control-Allow-Credentials'] == 'true'
        
    @pytest.mark.asyncio
    async def test_cors_preflight(self, transport):
        """Test CORS preflight handling."""
        request = Mock()
        request.method = 'OPTIONS'
        
        with patch('aiohttp.web.Response') as mock_response:
            response = transport._create_cors_response()
            
            assert response.headers['Access-Control-Allow-Origin'] == '*'
            assert response.headers['Access-Control-Allow-Methods'] == 'GET, POST, OPTIONS'
            
    @pytest.mark.asyncio
    async def test_health_endpoint(self, transport):
        """Test health check endpoint."""
        request = Mock()
        
        with patch('aiohttp.web.json_response') as mock_response:
            await transport._handle_health(request)
            
            mock_response.assert_called_once()
            health_data = mock_response.call_args[0][0]
            
            assert health_data["status"] == "healthy"
            assert health_data["connections"] == 0
            assert health_data["max_connections"] == 10
            assert health_data["transport"] == "sse"
            
    @pytest.mark.asyncio
    async def test_connection_limit(self, transport):
        """Test connection limit enforcement."""
        # Fill up connections
        for i in range(10):
            transport.connections[str(i)] = Mock()
            
        request = Mock()
        
        with patch('aiohttp.web.Response') as mock_response:
            result = await transport._handle_sse(request)
            
            mock_response.assert_called_with(status=503, text="Connection limit reached")
            
    @pytest.mark.asyncio
    async def test_handle_request_success(self, transport, mock_server):
        """Test successful request handling."""
        # Create connection
        conn = SSEConnection(
            id="test-conn",
            response=Mock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow(),
            event_queue=asyncio.Queue()
        )
        transport.connections["test-conn"] = conn
        
        # Mock request
        request = Mock()
        request.headers = {'X-Connection-Id': 'test-conn'}
        request.json = AsyncMock(return_value={
            "jsonrpc": "2.0",
            "method": "test",
            "params": {},
            "id": 1
        })
        
        with patch('aiohttp.web.json_response') as mock_response:
            await transport._handle_request(request)
            
            # Verify server was called
            mock_server.handle_request.assert_called_once()
            
            # Verify response was queued
            assert conn.event_queue.qsize() == 1
            event = await conn.event_queue.get()
            assert event['event'] == 'response'
            assert event['data']['result']['test'] == 'success'
            
            # Verify acknowledgment
            mock_response.assert_called_with({"status": "accepted"})
            
    @pytest.mark.asyncio
    async def test_handle_request_invalid_connection(self, transport):
        """Test request with invalid connection ID."""
        request = Mock()
        request.headers = {'X-Connection-Id': 'invalid-id'}
        
        with patch('aiohttp.web.json_response') as mock_response:
            await transport._handle_request(request)
            
            mock_response.assert_called_with(
                {"error": "Invalid or missing connection ID"},
                status=400
            )
            
    @pytest.mark.asyncio
    async def test_handle_request_no_connection_id(self, transport):
        """Test request without connection ID."""
        request = Mock()
        request.headers = {}
        
        with patch('aiohttp.web.json_response') as mock_response:
            await transport._handle_request(request)
            
            mock_response.assert_called_with(
                {"error": "Invalid or missing connection ID"},
                status=400
            )
            
    @pytest.mark.asyncio
    async def test_send_sse_message(self, transport):
        """Test SSE message formatting."""
        conn = SSEConnection(
            id="test-conn",
            response=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow(),
            event_queue=asyncio.Queue()
        )
        
        event = {
            'event': 'test-event',
            'id': '123',
            'data': {'message': 'Hello SSE'}
        }
        
        await transport._send_sse_message(conn, event)
        
        # Verify message format
        conn.response.write.assert_called_once()
        written_data = conn.response.write.call_args[0][0]
        message = written_data.decode('utf-8')
        
        assert 'event: test-event' in message
        assert 'id: 123' in message
        assert 'data: {"message": "Hello SSE"}' in message
        assert message.endswith('\n\n')
        
    @pytest.mark.asyncio
    async def test_heartbeat_loop(self, transport):
        """Test SSE heartbeat."""
        conn = SSEConnection(
            id="test-conn",
            response=AsyncMock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow(),
            event_queue=asyncio.Queue()
        )
        
        # Run heartbeat once
        transport.heartbeat_interval = 0.01
        heartbeat_task = asyncio.create_task(transport._heartbeat_loop(conn))
        
        await asyncio.sleep(0.02)
        
        # Cancel heartbeat
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
            
        # Verify heartbeat was sent
        conn.response.write.assert_called()
        written_data = conn.response.write.call_args[0][0]
        assert written_data == b': heartbeat\n\n'
        
    @pytest.mark.asyncio
    async def test_close_connection(self, transport):
        """Test connection closing."""
        conn = SSEConnection(
            id="test-conn",
            response=Mock(),
            remote="127.0.0.1",
            connected_at=datetime.utcnow(),
            event_queue=asyncio.Queue()
        )
        conn.response._eof = False
        conn.response.write_eof = AsyncMock()
        
        # Add task
        conn.task = asyncio.create_task(asyncio.sleep(10))
        
        # Add to connections
        transport.connections[conn.id] = conn
        
        # Close connection
        await transport._close_connection(conn)
        
        # Verify cleanup
        assert conn.id not in transport.connections
        assert conn.task.cancelled()
        conn.response.write_eof.assert_called_once()
        
    def test_get_connection_stats(self, transport):
        """Test connection statistics."""
        # Add connections
        now = datetime.utcnow()
        
        conn1 = SSEConnection(
            id="conn-1",
            response=Mock(),
            remote="127.0.0.1",
            connected_at=now,
            event_queue=asyncio.Queue()
        )
        
        conn2 = SSEConnection(
            id="conn-2",
            response=Mock(),
            remote="192.168.1.1",
            connected_at=now,
            event_queue=asyncio.Queue()
        )
        
        # Add some events to queue
        conn1.event_queue.put_nowait({"event": "test"})
        conn1.event_queue.put_nowait({"event": "test2"})
        
        transport.connections = {
            "conn-1": conn1,
            "conn-2": conn2
        }
        
        stats = transport.get_connection_stats()
        
        assert stats["total_connections"] == 2
        assert stats["transport"] == "sse"
        assert len(stats["connections"]) == 2
        
        # Check first connection
        conn1_stats = next(c for c in stats["connections"] if c["id"] == "conn-1")
        assert conn1_stats["remote"] == "127.0.0.1"
        assert conn1_stats["queued_events"] == 2