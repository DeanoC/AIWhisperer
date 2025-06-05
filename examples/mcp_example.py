#!/usr/bin/env python3
"""
Example of using MCP client in AIWhisperer.

This script demonstrates:
1. Loading MCP configuration
2. Connecting to MCP servers
3. Discovering available tools
4. Executing MCP tools
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_whisperer.mcp import initialize_mcp_client, get_mcp_registry
from ai_whisperer.mcp.common.types import MCPServerConfig, MCPTransport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def example_with_config():
    """Example using configuration file."""
    print("=== MCP Example with Configuration ===\n")
    
    # Example configuration (normally loaded from YAML)
    config_data = {
        "mcp": {
            "client": {
                "enabled": True,
                "servers": [
                    {
                        "name": "example",
                        "transport": "stdio",
                        "command": ["echo", "MCP server would run here"],
                        "timeout": 30.0
                    }
                ]
            }
        }
    }
    
    # Initialize MCP client
    registry = await initialize_mcp_client(config_data)
    
    if registry:
        print(f"Registered servers: {registry.get_registered_servers()}")
        print(f"Total MCP tools: {len(registry.get_mcp_tools())}")
        
        # Get tools for a specific server
        example_tools = registry.get_server_tools("example")
        print(f"\nTools from 'example' server: {example_tools}")
    else:
        print("MCP client initialization failed or is disabled")


async def example_direct_usage():
    """Example of direct MCP client usage."""
    print("\n=== Direct MCP Client Usage ===\n")
    
    from ai_whisperer.mcp.client import MCPClient
    from ai_whisperer.mcp.client.discovery import MCPToolDiscovery
    
    # Create server configuration
    config = MCPServerConfig(
        name="test_server",
        transport=MCPTransport.STDIO,
        command=["echo", "test"],  # Replace with actual MCP server command
        timeout=10.0
    )
    
    try:
        # Create and connect client
        async with MCPClient(config) as client:
            print(f"Connected to: {client.server_info.name if client.server_info else 'Unknown'}")
            print(f"Protocol version: {client.server_info.protocol_version if client.server_info else 'Unknown'}")
            
            # Discover tools
            discovery = MCPToolDiscovery(client)
            tools = await discovery.discover_tools()
            
            print(f"\nDiscovered {len(tools)} tools:")
            for tool in tools[:5]:  # Show first 5
                print(f"  - {tool.qualified_name}: {tool.description}")
                
            # Example tool execution (would work with real MCP server)
            if tools:
                tool = tools[0]
                print(f"\nWould execute tool: {tool.name}")
                # result = await client.call_tool(tool.name, {"example": "params"})
                # print(f"Result: {result}")
                
    except Exception as e:
        print(f"Error: {e}")


async def example_with_agent():
    """Example showing MCP tools with agents."""
    print("\n=== MCP Tools with Agents ===\n")
    
    from ai_whisperer.mcp.client.agent_integration import AgentMCPIntegration
    
    # Example configuration with agent permissions
    config_data = {
        "mcp": {
            "client": {
                "enabled": True,
                "servers": [
                    {"name": "filesystem", "transport": "stdio", "command": ["mcp-fs"]},
                    {"name": "github", "transport": "stdio", "command": ["mcp-github"]}
                ],
                "agent_permissions": {
                    "alice": {
                        "allowed_servers": ["filesystem"]
                    },
                    "bob": {
                        "allowed_servers": ["filesystem", "github"]
                    }
                }
            }
        }
    }
    
    # Initialize MCP
    registry = await initialize_mcp_client(config_data)
    
    if registry:
        integration = AgentMCPIntegration(registry, config_data)
        
        # Check tools for different agents
        for agent_name in ["alice", "bob", "charlie"]:
            info = integration.get_agent_mcp_info(agent_name)
            print(f"\nAgent '{agent_name}':")
            print(f"  MCP enabled: {info['enabled']}")
            print(f"  Allowed servers: {info['allowed_servers']}")
            print(f"  Total tools: {info['total_tools']}")


async def main():
    """Run all examples."""
    await example_with_config()
    await example_direct_usage()
    await example_with_agent()


if __name__ == "__main__":
    asyncio.run(main())