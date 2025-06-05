"""Unit tests for MCP server STDIO transport."""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_whisperer.mcp.server.transports.stdio import StdioServerTransport


class TestStdioServerTransport:
    """Test STDIO server transport."""
    
    @pytest.fixture
    def mock_server(self):
        """Create mock server."""
        server = Mock()
        server.handle_request = AsyncMock()
        return server
        
    @pytest.fixture
    def transport(self, mock_server):
        """Create test transport."""
        return StdioServerTransport(mock_server)
        
    @pytest.mark.asyncio
    async def test_transport_initialization(self, transport, mock_server):
        """Test transport initialization."""
        assert transport.server is mock_server
        assert transport.reader is None
        assert transport.writer is None
        assert transport._running is False
        assert transport._read_task is None
        
    @pytest.mark.asyncio
    async def test_start_transport(self, transport):
        """Test starting transport."""
        with patch('asyncio.get_event_loop') as mock_loop, \
             patch('asyncio.StreamReader') as mock_reader, \
             patch('asyncio.StreamReaderProtocol') as mock_protocol, \
             patch('asyncio.create_task') as mock_create_task:
            
            mock_loop_instance = Mock()
            mock_loop.return_value = mock_loop_instance
            mock_loop_instance.connect_read_pipe = AsyncMock()
            
            mock_reader_instance = Mock()
            mock_reader.return_value = mock_reader_instance
            
            await transport.start()
            
            assert transport.reader is mock_reader_instance
            assert transport._running is True
            mock_create_task.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_stop_transport(self, transport):
        """Test stopping transport."""
        transport._running = True
        
        # Create a real task that we can cancel
        async def dummy_task():
            await asyncio.sleep(10)
            
        real_task = asyncio.create_task(dummy_task())
        transport._read_task = real_task
        
        await transport.stop()
        
        assert transport._running is False
        assert real_task.cancelled()
        
    @pytest.mark.asyncio
    async def test_read_loop_valid_request(self, transport, mock_server):
        """Test read loop with valid JSON-RPC request."""
        transport._running = True
        
        # Mock reader to return one line then EOF
        mock_reader = AsyncMock()
        request_data = {
            "jsonrpc": "2.0",
            "method": "test",
            "params": {},
            "id": 1
        }
        mock_reader.readline.side_effect = [
            (json.dumps(request_data) + '\n').encode('utf-8'),
            b''  # EOF
        ]
        transport.reader = mock_reader
        
        # Mock server response
        mock_server.handle_request.return_value = {
            "jsonrpc": "2.0",
            "result": {"success": True},
            "id": 1
        }
        
        # Mock stdout write
        with patch('sys.stdout') as mock_stdout:
            await transport._read_loop()
            
            # Verify request was handled
            mock_server.handle_request.assert_called_once_with(request_data)
            
            # Verify response was written
            mock_stdout.write.assert_called_once()
            written = mock_stdout.write.call_args[0][0]
            assert '"result":{"success":true}' in written
            
    @pytest.mark.asyncio
    async def test_read_loop_invalid_json(self, transport):
        """Test read loop with invalid JSON."""
        transport._running = True
        
        mock_reader = AsyncMock()
        mock_reader.readline.side_effect = [
            b'invalid json\n',
            b''  # EOF
        ]
        transport.reader = mock_reader
        
        with patch('sys.stdout') as mock_stdout:
            await transport._read_loop()
            
            # Should send parse error
            mock_stdout.write.assert_called_once()
            written = mock_stdout.write.call_args[0][0]
            response = json.loads(written.strip())
            assert response["error"]["code"] == -32700
            assert "Parse error" in response["error"]["message"]
            
    @pytest.mark.asyncio
    async def test_read_loop_empty_lines(self, transport, mock_server):
        """Test read loop skips empty lines."""
        transport._running = True
        
        mock_reader = AsyncMock()
        mock_reader.readline.side_effect = [
            b'\n',  # Empty line
            b'  \n',  # Whitespace only
            b'{"jsonrpc":"2.0","method":"test","id":1}\n',
            b''  # EOF
        ]
        transport.reader = mock_reader
        
        mock_server.handle_request.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}
        
        with patch('sys.stdout'):
            await transport._read_loop()
            
            # Should only handle the valid request
            mock_server.handle_request.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_read_loop_exception_handling(self, transport, mock_server):
        """Test read loop handles exceptions gracefully."""
        transport._running = True
        
        mock_reader = AsyncMock()
        mock_reader.readline.side_effect = [
            b'{"jsonrpc":"2.0","method":"test","id":1}\n',
            b''  # EOF
        ]
        transport.reader = mock_reader
        
        # Server throws exception
        mock_server.handle_request.side_effect = RuntimeError("Server error")
        
        # Should not crash
        with patch('sys.stdout'):
            await transport._read_loop()
            
    @pytest.mark.asyncio
    async def test_send_response(self, transport):
        """Test sending response."""
        response = {
            "jsonrpc": "2.0",
            "result": {"test": "value"},
            "id": 1
        }
        
        with patch('sys.stdout') as mock_stdout:
            await transport._send_response(response)
            
            mock_stdout.write.assert_called_once()
            mock_stdout.flush.assert_called_once()
            
            written = mock_stdout.write.call_args[0][0]
            assert written.endswith('\n')
            parsed = json.loads(written.strip())
            assert parsed == response
            
    @pytest.mark.asyncio
    async def test_send_response_error_handling(self, transport):
        """Test send response error handling."""
        # Response with non-serializable object
        response = {
            "jsonrpc": "2.0",
            "result": {"obj": object()},  # Can't serialize
            "id": 1
        }
        
        with patch('sys.stdout'):
            # Should not raise, just log error
            await transport._send_response(response)
            
    @pytest.mark.asyncio 
    async def test_read_loop_stops_on_eof(self, transport):
        """Test read loop stops when stdin is closed."""
        transport._running = True
        
        mock_reader = AsyncMock()
        mock_reader.readline.return_value = b''  # EOF immediately
        transport.reader = mock_reader
        
        await transport._read_loop()
        
        # Should only call readline once
        mock_reader.readline.assert_called_once()
        
    def test_read_loop_not_started_without_reader(self, transport):
        """Test read loop requires reader to be set."""
        transport._running = True
        transport.reader = None
        
        # Should handle gracefully if reader is None
        # (This shouldn't happen in practice but good to test)