"""Base class for MCP transports."""

from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio

from ...common.types import MCPRequest, MCPResponse


class MCPTransportBase(ABC):
    """Abstract base class for MCP transport implementations."""
    
    def __init__(self):
        self._connected = False
        self._closing = False
        
    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected and not self._closing
        
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to MCP server."""
        pass
        
    @abstractmethod
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """Send request and wait for response."""
        pass
        
    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""
        pass
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()