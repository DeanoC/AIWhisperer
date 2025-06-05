"""Adapter to integrate MCP tools with AIWhisperer's tool system."""

import json
import logging
from typing import Any, Dict, List, Optional

from ....tools.base_tool import AITool
from ....core.exceptions import ToolExecutionError
from ...common.types import MCPToolDefinition
from ..client import MCPClient
from ..exceptions import MCPError, MCPToolError

logger = logging.getLogger(__name__)


class MCPToolAdapter(AITool):
    """Adapts MCP tools to AIWhisperer's AITool interface."""
    
    def __init__(self, tool_def: MCPToolDefinition, client: MCPClient):
        self.tool_def = tool_def
        self.client = client
        self._name = tool_def.qualified_name
        self._cached_schema = None
        
    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return self._name
        
    @property 
    def description(self) -> str:
        """Human-readable description."""
        return f"[MCP:{self.tool_def.server_name}] {self.tool_def.description}"
        
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON schema for input parameters."""
        if self._cached_schema is None:
            # Convert MCP schema to AIWhisperer format
            self._cached_schema = {
                "type": "object",
                "properties": self.tool_def.input_schema.get("properties", {}),
                "required": self.tool_def.input_schema.get("required", []),
                "additionalProperties": False
            }
        return self._cached_schema
        
    @property
    def category(self) -> Optional[str]:
        """Tool category."""
        return "MCP External Tools"
        
    @property
    def tags(self) -> List[str]:
        """Tool tags."""
        return ["mcp", "external", self.tool_def.server_name]
        
    def get_ai_prompt_instructions(self) -> str:
        """Generate instructions for AI on how to use this tool."""
        params_str = json.dumps(self.parameters_schema, indent=2)
        
        return f"""Tool: {self.name}
Description: {self.description}

This is an external MCP tool provided by the '{self.tool_def.server_name}' server.

Parameters:
{params_str}

Usage Notes:
- This tool executes on an external MCP server
- Response format may vary based on the tool implementation
- Errors from the external server will be reported as ToolExecutionError
"""
        
    async def execute(self, arguments: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """Execute the MCP tool through the client."""
        # Handle both new (arguments dict) and legacy (**kwargs) patterns
        if arguments is not None:
            # New pattern: arguments dict
            args = arguments.copy()
        else:
            # Legacy pattern: **kwargs
            args = kwargs.copy()
            
        # Remove AIWhisperer-specific internal fields
        clean_args = {
            k: v for k, v in args.items() 
            if not k.startswith('_')
        }
        
        try:
            # Ensure client is connected
            if not self.client.initialized:
                await self.client.connect()
                
            # Call MCP tool
            logger.debug(f"Calling MCP tool {self.tool_def.name} with args: {clean_args}")
            response = await self.client.call_tool(self.tool_def.name, clean_args)
            
            # Extract content from MCP response format
            if isinstance(response, dict):
                # Check for error response
                if response.get("isError", False):
                    error_content = self._extract_content(response)
                    raise MCPToolError(f"MCP tool error: {error_content}")
                    
                # Extract content
                content = response.get("content", [])
                if content:
                    # Return extracted text content
                    return self._extract_content(response)
                    
            # Return raw response if no special formatting
            return response
            
        except MCPError as e:
            logger.error(f"MCP tool execution failed: {e}")
            raise ToolExecutionError(f"MCP tool '{self.tool_def.name}' failed: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error executing MCP tool: {e}")
            raise ToolExecutionError(f"Failed to execute MCP tool '{self.tool_def.name}': {e}")
            
    def _extract_content(self, response: Dict[str, Any]) -> Any:
        """Extract content from MCP response format."""
        content = response.get("content", [])
        
        if not content:
            return None
            
        # Handle different content types
        extracted = []
        for item in content:
            if isinstance(item, dict):
                content_type = item.get("type", "")
                
                if content_type == "text":
                    text = item.get("text", "")
                    # Try to parse as JSON
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        extracted.append(text)
                        
                elif content_type == "image":
                    # Return image data as-is
                    extracted.append(item)
                    
                elif content_type == "resource":
                    # Return resource reference
                    extracted.append(item)
                    
            else:
                extracted.append(item)
                
        # Return single item if only one, otherwise return list
        if len(extracted) == 1:
            return extracted[0]
        return extracted
        
    def __repr__(self) -> str:
        """String representation."""
        return f"MCPToolAdapter(name='{self.name}', server='{self.tool_def.server_name}')"