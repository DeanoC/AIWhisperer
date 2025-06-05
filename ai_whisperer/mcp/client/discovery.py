"""MCP tool discovery and management."""

import logging
from typing import List, Optional, Dict, Any

from .client import MCPClient
from ..common.types import MCPToolDefinition

logger = logging.getLogger(__name__)


class MCPToolDiscovery:
    """Discovers and manages MCP tools from servers."""
    
    def __init__(self, client: MCPClient):
        self.client = client
        self.tools: Dict[str, MCPToolDefinition] = {}
        
    async def discover_tools(self) -> List[MCPToolDefinition]:
        """Discover available tools from MCP server."""
        if not self.client.initialized:
            await self.client.connect()
            
        # Get tools from client (already cached during initialization)
        discovered_tools = await self.client.list_tools()
        
        # Update our local cache
        self.tools.clear()
        for tool in discovered_tools:
            self.tools[tool.name] = tool
            
        logger.info(f"Discovered {len(discovered_tools)} tools from {self.client.config.name}")
        return discovered_tools
        
    def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        """Get tool definition by name."""
        return self.tools.get(name)
        
    def get_all_tools(self) -> List[MCPToolDefinition]:
        """Get all discovered tools."""
        return list(self.tools.values())
        
    def get_qualified_tool_names(self) -> List[str]:
        """Get list of fully qualified tool names."""
        return [tool.qualified_name for tool in self.tools.values()]
        
    async def validate_tool(self, name: str) -> bool:
        """Validate that a tool exists and is callable."""
        tool = self.get_tool(name)
        if not tool:
            return False
            
        # TODO: Add more sophisticated validation
        # For now, just check that the tool exists
        return True