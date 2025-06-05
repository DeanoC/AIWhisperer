"""Configuration loader for MCP client."""

import logging
import os
from typing import Dict, List, Optional, Any

import yaml

from ..common.types import MCPServerConfig, MCPTransport
from .registry import MCPToolRegistry

logger = logging.getLogger(__name__)


class MCPConfigLoader:
    """Loads and manages MCP client configuration."""
    
    @staticmethod
    def load_server_configs(config_data: Dict[str, Any]) -> List[MCPServerConfig]:
        """
        Load MCP server configurations from config data.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            List of MCPServerConfig objects
        """
        mcp_config = config_data.get("mcp", {}).get("client", {})
        
        if not mcp_config.get("enabled", False):
            logger.info("MCP client is disabled in configuration")
            return []
            
        server_configs = []
        servers = mcp_config.get("servers", [])
        
        for server_data in servers:
            try:
                # Parse transport type
                transport = MCPTransport(server_data.get("transport", "stdio"))
                
                # Create config object
                config = MCPServerConfig(
                    name=server_data["name"],
                    transport=transport,
                    command=server_data.get("command"),
                    url=server_data.get("url"),
                    env=MCPConfigLoader._expand_env_vars(server_data.get("env", {})),
                    timeout=server_data.get("timeout", 30.0)
                )
                
                # Validate config
                if transport == MCPTransport.STDIO and not config.command:
                    logger.error(f"Server '{config.name}': stdio transport requires 'command'")
                    continue
                    
                if transport == MCPTransport.WEBSOCKET and not config.url:
                    logger.error(f"Server '{config.name}': websocket transport requires 'url'")
                    continue
                    
                server_configs.append(config)
                
            except Exception as e:
                logger.error(f"Failed to parse server config: {e}")
                logger.debug(f"Server data: {server_data}")
                
        return server_configs
        
    @staticmethod
    def _expand_env_vars(env_dict: Dict[str, str]) -> Dict[str, str]:
        """Expand environment variables in configuration."""
        expanded = {}
        for key, value in env_dict.items():
            # Expand ${VAR} or $VAR patterns
            if isinstance(value, str) and "$" in value:
                expanded[key] = os.path.expandvars(value)
            else:
                expanded[key] = value
        return expanded
        
    @staticmethod
    async def load_and_register(
        config_path: Optional[str] = None,
        config_data: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None
    ) -> MCPToolRegistry:
        """
        Load MCP configuration and register all servers.
        
        Args:
            config_path: Path to configuration file
            config_data: Configuration dictionary (if config_path not provided)
            tool_registry: AIWhisperer tool registry instance
            
        Returns:
            MCPToolRegistry with registered servers
        """
        # Load configuration
        if config_data is None:
            if not config_path:
                raise ValueError("Either config_path or config_data must be provided")
                
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
        # Get server configurations
        server_configs = MCPConfigLoader.load_server_configs(config_data)
        
        if not server_configs:
            logger.info("No MCP servers configured")
            return MCPToolRegistry(tool_registry)
            
        # Create registry and register servers
        registry = MCPToolRegistry(tool_registry)
        
        for config in server_configs:
            try:
                logger.info(f"Registering MCP server: {config.name}")
                await registry.register_mcp_server(config)
                
            except Exception as e:
                logger.error(f"Failed to register MCP server '{config.name}': {e}")
                
        return registry
        
    @staticmethod
    def get_agent_permissions(config_data: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """
        Get MCP permissions for a specific agent.
        
        Args:
            config_data: Configuration dictionary
            agent_name: Name of the agent
            
        Returns:
            Dictionary of agent permissions
        """
        mcp_config = config_data.get("mcp", {}).get("client", {})
        agent_permissions = mcp_config.get("agent_permissions", {})
        
        return agent_permissions.get(agent_name, {})
        
    @staticmethod
    def get_allowed_servers_for_agent(config_data: Dict[str, Any], agent_name: str) -> List[str]:
        """
        Get list of allowed MCP servers for an agent.
        
        Args:
            config_data: Configuration dictionary
            agent_name: Name of the agent
            
        Returns:
            List of allowed server names
        """
        permissions = MCPConfigLoader.get_agent_permissions(config_data, agent_name)
        return permissions.get("allowed_servers", [])