"""Tool handler for MCP server."""

import json
import logging
import time
from typing import Dict, Any, List, Optional
import asyncio

from ....tools.tool_registry_lazy import LazyToolRegistry
from ....tools.base_tool import AITool
from ..config import MCPServerConfig

logger = logging.getLogger(__name__)


class ToolHandler:
    """Handles MCP tool-related requests."""
    
    def __init__(self, tool_registry: LazyToolRegistry, config: MCPServerConfig, monitor=None):
        self.tool_registry = tool_registry
        self.config = config
        self.exposed_tools = set(config.exposed_tools)
        self._tool_cache: Dict[str, AITool] = {}
        self.monitor = monitor
        
    async def list_tools(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List available tools in MCP format."""
        tools = []
        
        logger.debug(f"Listing tools from exposed set: {self.exposed_tools}")
        
        for tool_name in self.exposed_tools:
            try:
                tool = self._get_tool(tool_name)
                if tool:
                    mcp_tool = self._convert_to_mcp_format(tool)
                    tools.append(mcp_tool)
                    logger.debug(f"Added tool '{tool_name}' to MCP list")
                else:
                    logger.warning(f"Tool '{tool_name}' not found in registry")
                    
            except Exception as e:
                logger.error(f"Error loading tool '{tool_name}': {e}")
                
        logger.info(f"Returning {len(tools)} tools to MCP client")
        return tools
        
    def _get_tool(self, tool_name: str) -> Optional[AITool]:
        """Get tool from registry with caching."""
        if tool_name not in self._tool_cache:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                self._tool_cache[tool_name] = tool
        return self._tool_cache.get(tool_name)
        
    def _convert_to_mcp_format(self, tool: AITool) -> Dict[str, Any]:
        """Convert AIWhisperer tool to MCP format."""
        # Get parameter schema
        params_schema = tool.parameters_schema
        
        # Build MCP tool definition
        mcp_tool = {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": {
                "type": "object",
                "properties": params_schema.get("properties", {}),
                "required": params_schema.get("required", []),
                "additionalProperties": params_schema.get("additionalProperties", False),
            }
        }
        
        # Add JSON schema reference
        if "$schema" not in mcp_tool["inputSchema"]:
            mcp_tool["inputSchema"]["$schema"] = "http://json-schema.org/draft-07/schema#"
            
        return mcp_tool
        
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        tool_name = params.get("name")
        if not tool_name:
            raise ValueError("Missing required field: name")
            
        arguments = params.get("arguments", {})
        
        # Check if tool is exposed
        if tool_name not in self.exposed_tools:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        # Get tool from registry
        tool = self._get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not available")
            
        # Create a context for tool execution
        tool_context = {
            "_agent_id": "mcp_client",
            "_from_agent": "mcp",
            "_session_id": params.get("sessionId", "mcp_session"),
        }
        
        # Track execution time
        start_time = time.time()
        
        # Execute tool
        try:
            # Merge context with arguments
            enriched_args = {**arguments, **tool_context}
            
            # Execute tool (handle both sync and async)
            if asyncio.iscoroutinefunction(tool.execute):
                # Try new pattern first
                try:
                    result = await tool.execute(arguments=enriched_args)
                except TypeError:
                    # Fallback to legacy pattern
                    result = await tool.execute(**enriched_args)
            else:
                # Sync execution
                try:
                    result = tool.execute(arguments=enriched_args)
                except TypeError:
                    result = tool.execute(**enriched_args)
            
            # Track successful execution if monitor is available
            if self.monitor:
                self.monitor.track_tool_execution(
                    tool_name=tool_name,
                    start_time=start_time,
                    success=True
                )
                    
            # Format result for MCP
            return self._format_tool_result(result)
            
        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_name}': {e}", exc_info=True)
            
            # Track failed execution if monitor is available
            if self.monitor:
                self.monitor.track_tool_execution(
                    tool_name=tool_name,
                    start_time=start_time,
                    success=False,
                    error=str(e)
                )
            
            # Return error in MCP format
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool execution failed: {str(e)}"
                    }
                ]
            }
            
    def _format_tool_result(self, result: Any) -> Dict[str, Any]:
        """Format tool result for MCP response."""
        # Handle different result types
        if isinstance(result, dict):
            # JSON-serializable dict
            text_result = json.dumps(result, indent=2)
        elif isinstance(result, (list, tuple)):
            # JSON-serializable sequence
            text_result = json.dumps(result, indent=2)
        elif isinstance(result, str):
            # Plain text
            text_result = result
        else:
            # Convert to string
            text_result = str(result)
            
        # Return in MCP content format
        return {
            "content": [
                {
                    "type": "text",
                    "text": text_result
                }
            ]
        }