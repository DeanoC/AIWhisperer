"""Standard I/O transport for MCP."""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Any

from .base import MCPTransportBase
from ...common.types import MCPRequest, MCPResponse
from ..exceptions import MCPConnectionError, MCPTimeoutError, MCPProtocolError

logger = logging.getLogger(__name__)


class StdioTransport(MCPTransportBase):
    """MCP transport using subprocess stdio communication."""
    
    def __init__(self, command: List[str], env: Optional[Dict[str, str]] = None, timeout: float = 30.0):
        super().__init__()
        self.command = command
        self.env = env or {}
        self.timeout = timeout
        self.process: Optional[asyncio.subprocess.Process] = None
        self._read_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[Any, asyncio.Future] = {}
        self._next_id = 1
        self._closing = False
        
    async def connect(self) -> None:
        """Start subprocess and establish stdio communication."""
        if self._connected:
            return
            
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.env)
            env["PYTHONUNBUFFERED"] = "1"  # Ensure unbuffered output
            
            # Start subprocess
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # Start reading responses
            self._read_task = asyncio.create_task(self._read_loop())
            
            self._connected = True
            logger.info(f"Connected to MCP server via stdio: {' '.join(self.command)}")
            
        except Exception as e:
            raise MCPConnectionError(f"Failed to start MCP server: {e}")
            
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """Send request via stdin and wait for response."""
        if not self._connected:
            raise MCPConnectionError("Transport not connected")
            
        # Assign ID if not provided
        if request.id is None:
            request.id = self._next_id
            self._next_id += 1
            
        # Create future for response
        future = asyncio.Future()
        self._pending_requests[request.id] = future
        
        try:
            # Send request
            request_data = request.to_dict()
            request_line = json.dumps(request_data) + "\n"
            
            self.process.stdin.write(request_line.encode("utf-8"))
            await self.process.stdin.drain()
            
            # Wait for response with timeout
            response_data = await asyncio.wait_for(future, timeout=self.timeout)
            return MCPResponse.from_dict(response_data)
            
        except asyncio.TimeoutError:
            # Remove pending request
            self._pending_requests.pop(request.id, None)
            raise MCPTimeoutError(f"Request timed out after {self.timeout}s")
            
        except Exception as e:
            # Remove pending request
            self._pending_requests.pop(request.id, None)
            raise MCPProtocolError(f"Failed to send request: {e}")
            
    async def _read_loop(self) -> None:
        """Read responses from stdout."""
        try:
            while self._connected and not self._closing:
                # Read line from stdout
                line_bytes = await self.process.stdout.readline()
                if not line_bytes:
                    # Process ended
                    break
                    
                try:
                    # Parse JSON response
                    line = line_bytes.decode("utf-8").strip()
                    if not line:
                        continue
                        
                    response_data = json.loads(line)
                    
                    # Handle response
                    request_id = response_data.get("id")
                    if request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        if not future.done():
                            future.set_result(response_data)
                    else:
                        # Log unexpected response
                        logger.warning(f"Received response for unknown request ID: {request_id}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse MCP response: {e}")
                    logger.debug(f"Raw response: {line_bytes}")
                    
        except Exception as e:
            logger.error(f"Error in read loop: {e}")
            
        finally:
            # Cancel all pending requests
            for future in self._pending_requests.values():
                if not future.done():
                    future.set_exception(MCPConnectionError("Connection closed"))
            self._pending_requests.clear()
            
    async def close(self) -> None:
        """Close the connection."""
        if not self._connected:
            return
            
        self._closing = True
        self._connected = False
        
        # Cancel read task
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
                
        # Terminate process
        if self.process:
            try:
                # Try graceful shutdown first
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if needed
                    self.process.kill()
                    await self.process.wait()
            except Exception as e:
                logger.error(f"Error closing process: {e}")
                
        logger.info("MCP stdio transport closed")