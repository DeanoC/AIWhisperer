"""Model Context Protocol (MCP) integration for AIWhisperer."""

import logging
from typing import Optional, Dict, Any

from .client.registry import MCPToolRegistry
from .client.config_loader import MCPConfigLoader
from .client.agent_integration import AgentMCPIntegration

logger = logging.getLogger(__name__)

# Global MCP registry instance
_mcp_registry: Optional[MCPToolRegistry] = None
_mcp_agent_integration: Optional[AgentMCPIntegration] = None


async def initialize_mcp_client(config_data: Dict[str, Any]) -> Optional[MCPToolRegistry]:
    """
    Initialize MCP client with given configuration.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        MCPToolRegistry instance if MCP is enabled, None otherwise
    """
    global _mcp_registry, _mcp_agent_integration
    
    try:
        # Check if MCP client is enabled
        mcp_config = config_data.get("mcp", {}).get("client", {})
        if not mcp_config.get("enabled", False):
            logger.info("MCP client is disabled in configuration")
            return None
            
        # Initialize MCP registry
        logger.info("Initializing MCP client...")
        _mcp_registry = await MCPConfigLoader.load_and_register(
            config_data=config_data
        )
        
        # Initialize agent integration
        _mcp_agent_integration = AgentMCPIntegration(_mcp_registry, config_data)
        
        # Log summary
        registered_servers = _mcp_registry.get_registered_servers()
        total_tools = len(_mcp_registry.get_mcp_tools())
        logger.info(
            f"MCP client initialized with {len(registered_servers)} servers "
            f"and {total_tools} tools"
        )
        
        return _mcp_registry
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        return None


def get_mcp_registry() -> Optional[MCPToolRegistry]:
    """Get the global MCP registry instance."""
    return _mcp_registry


def get_mcp_agent_integration() -> Optional[AgentMCPIntegration]:
    """Get the global MCP agent integration instance."""
    return _mcp_agent_integration


async def shutdown_mcp_client() -> None:
    """Shutdown MCP client and close all connections."""
    global _mcp_registry, _mcp_agent_integration
    
    if _mcp_registry:
        logger.info("Shutting down MCP client...")
        await _mcp_registry.close_all()
        _mcp_registry = None
        _mcp_agent_integration = None


__all__ = [
    "initialize_mcp_client",
    "get_mcp_registry",
    "get_mcp_agent_integration",
    "shutdown_mcp_client",
    "MCPToolRegistry",
    "MCPConfigLoader",
    "AgentMCPIntegration",
]