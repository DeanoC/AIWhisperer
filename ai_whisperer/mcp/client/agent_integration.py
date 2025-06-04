"""Integration of MCP tools with AIWhisperer agents."""

import logging
from typing import List, Dict, Any, Optional

from .registry import MCPToolRegistry
from .config_loader import MCPConfigLoader

logger = logging.getLogger(__name__)


class AgentMCPIntegration:
    """Manages MCP tools for specific agents."""
    
    def __init__(self, mcp_registry: MCPToolRegistry, config_data: Dict[str, Any]):
        self.mcp_registry = mcp_registry
        self.config_data = config_data
        
    def get_mcp_tools_for_agent(self, agent_name: str) -> List[str]:
        """
        Get allowed MCP tools for an agent based on configuration.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of MCP tool names the agent can use
        """
        # Get allowed servers for this agent
        allowed_servers = MCPConfigLoader.get_allowed_servers_for_agent(
            self.config_data, agent_name
        )
        
        if not allowed_servers:
            logger.debug(f"No MCP servers allowed for agent '{agent_name}'")
            return []
            
        # Collect tools from allowed servers
        allowed_tools = []
        for server_name in allowed_servers:
            server_tools = self.mcp_registry.get_server_tools(server_name)
            if server_tools:
                allowed_tools.extend(server_tools)
                logger.debug(
                    f"Agent '{agent_name}' allowed {len(server_tools)} tools "
                    f"from MCP server '{server_name}'"
                )
            else:
                logger.warning(
                    f"MCP server '{server_name}' allowed for agent '{agent_name}' "
                    f"but not registered or has no tools"
                )
                
        return allowed_tools
        
    def filter_tools_for_agent(self, agent_name: str, all_tools: List[str]) -> List[str]:
        """
        Filter a list of tools to only include allowed MCP tools for an agent.
        
        Args:
            agent_name: Name of the agent
            all_tools: List of all tool names to filter
            
        Returns:
            Filtered list containing only allowed MCP tools
        """
        allowed_mcp_tools = set(self.get_mcp_tools_for_agent(agent_name))
        
        if not allowed_mcp_tools:
            # No MCP tools allowed, filter out all MCP tools
            return [tool for tool in all_tools if not tool.startswith("mcp_")]
            
        # Filter to only allowed MCP tools
        filtered = []
        for tool in all_tools:
            if tool.startswith("mcp_"):
                if tool in allowed_mcp_tools:
                    filtered.append(tool)
            else:
                # Non-MCP tool, keep it
                filtered.append(tool)
                
        return filtered
        
    def get_agent_mcp_info(self, agent_name: str) -> Dict[str, Any]:
        """
        Get detailed MCP information for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with MCP configuration and available tools
        """
        permissions = MCPConfigLoader.get_agent_permissions(self.config_data, agent_name)
        allowed_servers = permissions.get("allowed_servers", [])
        
        # Get detailed info for each allowed server
        server_info = {}
        for server_name in allowed_servers:
            if server_name in self.mcp_registry.registered_servers:
                tools = self.mcp_registry.get_server_tools(server_name)
                server_info[server_name] = {
                    "registered": True,
                    "tools_count": len(tools),
                    "tools": tools[:5],  # First 5 as sample
                }
            else:
                server_info[server_name] = {
                    "registered": False,
                    "tools_count": 0,
                    "tools": []
                }
                
        return {
            "enabled": bool(allowed_servers),
            "allowed_servers": allowed_servers,
            "server_info": server_info,
            "total_tools": len(self.get_mcp_tools_for_agent(agent_name))
        }