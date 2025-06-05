"""Standard I/O transport for MCP server."""

import asyncio
import json
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class StdioServerTransport:
    """Standard I/O transport for MCP server."""
    
    def __init__(self, server):
        self.server = server
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._running = False
        self._read_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start listening on stdio."""
        # Don't log to stdout when using stdio transport
        # logger.info("Starting MCP server on stdio transport")
        
        # Create stream reader for stdin
        loop = asyncio.get_event_loop()
        self.reader = asyncio.StreamReader()
        
        # Create protocol for stdin
        protocol = asyncio.StreamReaderProtocol(self.reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        # Use stdout for writing
        # Note: We write directly to sys.stdout.buffer to avoid encoding issues
        
        self._running = True
        
        # Start read loop
        self._read_task = asyncio.create_task(self._read_loop())
        
        # logger.info("MCP server listening on stdio")
        
    async def stop(self):
        """Stop the transport."""
        self._running = False
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
                
        logger.info("MCP stdio transport stopped")
        
    async def _read_loop(self):
        """Read JSON-RPC messages from stdin."""
        while self._running:
            try:
                # Read line from stdin
                line = await self.reader.readline()
                
                if not line:
                    # EOF - stdin closed
                    logger.info("EOF on stdin, stopping server")
                    break
                    
                # Decode line
                line_str = line.decode('utf-8').strip()
                
                if not line_str:
                    # Empty line, skip
                    continue
                    
                # Parse JSON-RPC request
                try:
                    request = json.loads(line_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")
                    # Send parse error response
                    await self._send_response({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        },
                        "id": None
                    })
                    continue
                    
                # Handle request
                response = await self.server.handle_request(request)
                
                # Send response
                await self._send_response(response)
                
            except Exception as e:
                logger.error(f"Error in stdio read loop: {e}", exc_info=True)
                
    async def _send_response(self, response: dict):
        """Send JSON-RPC response to stdout."""
        try:
            # Convert to JSON
            response_json = json.dumps(response, separators=(',', ':'))
            response_line = response_json + '\n'
            
            # Write to stdout
            sys.stdout.write(response_line)
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Failed to send response: {e}", exc_info=True)