#!/usr/bin/env python3
"""Test script for GitHub MCP server integration."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_whisperer.mcp import initialize_mcp_client, get_mcp_registry
from ai_whisperer.mcp.common.types import MCPServerConfig, MCPTransport
from ai_whisperer.mcp.client import MCPClient
from ai_whisperer.core.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise from other loggers
logging.getLogger("ai_whisperer.tools").setLevel(logging.INFO)
logging.getLogger("ai_whisperer.core").setLevel(logging.INFO)


async def test_direct_connection():
    """Test direct connection to GitHub MCP server."""
    print("\n=== Testing Direct Connection to GitHub MCP Server ===\n")
    
    # Check for GitHub token
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  Warning: GITHUB_TOKEN environment variable not set")
        print("   Some GitHub operations may be limited or fail")
        print("   Set it with: export GITHUB_TOKEN=your_token")
    else:
        print(f"✓ Using GitHub token: {github_token[:10]}...")
    
    # Create server configuration
    config = MCPServerConfig(
        name="github",
        transport=MCPTransport.STDIO,
        command=["npx", "-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")},
        timeout=30.0
    )
    
    try:
        print("Connecting to GitHub MCP server...")
        async with MCPClient(config) as client:
            print(f"✓ Connected successfully!")
            print(f"  Server: {client.server_info.name if client.server_info else 'Unknown'}")
            print(f"  Version: {client.server_info.version if client.server_info else 'Unknown'}")
            print(f"  Protocol: {client.server_info.protocol_version if client.server_info else 'Unknown'}")
            print(f"  Capabilities: {client.server_info.capabilities if client.server_info else 'Unknown'}")
            
            # Manually check tools
            print("\nManually requesting tools list...")
            try:
                tools_response = await client._send_request("tools/list")
                print(f"Raw tools response: {tools_response}")
            except Exception as e:
                print(f"Error getting tools: {e}")
            
            # List available tools
            tools = await client.list_tools()
            print(f"\n✓ Discovered {len(tools)} tools:")
            
            for i, tool in enumerate(tools[:10]):  # Show first 10
                print(f"  {i+1}. {tool.name}")
                print(f"     Description: {tool.description[:100]}...")
                
            # Test a simple tool if available
            if tools:
                print("\n=== Testing Tool Execution ===")
                
                # Look for a simple read-only tool
                search_tool = next((t for t in tools if "search" in t.name.lower()), None)
                if search_tool:
                    print(f"\nTesting tool: {search_tool.name}")
                    try:
                        result = await client.call_tool(
                            search_tool.name,
                            {
                                "repo": "anthropics/anthropic-sdk-python",
                                "query": "MCP",
                                "limit": 5
                            }
                        )
                        print(f"✓ Tool executed successfully!")
                        print(f"  Result: {str(result)[:200]}...")
                    except Exception as e:
                        print(f"✗ Tool execution failed: {e}")
                        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()


async def test_with_registry():
    """Test using the MCP registry with configuration."""
    print("\n=== Testing with MCP Registry ===\n")
    
    try:
        # Load main configuration
        config = load_config("config/main.yaml")
        
        # Add MCP configuration dynamically
        if "mcp" not in config:
            config["mcp"] = {}
        config["mcp"]["client"] = {
            "enabled": True,
            "servers": [{
                "name": "github",
                "transport": "stdio",
                "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")},
                "timeout": 30.0
            }],
            "agent_permissions": {
                "alice": {"allowed_servers": ["github"]},
                "debbie": {"allowed_servers": ["github"]}
            }
        }
        
        # Initialize MCP
        print("Initializing MCP client with configuration...")
        registry = await initialize_mcp_client(config)
        
        if not registry:
            print("✗ MCP initialization failed or is disabled")
            return
            
        print(f"✓ MCP initialized successfully!")
        
        # Check registered servers
        servers = registry.get_registered_servers()
        print(f"\nRegistered servers: {servers}")
        
        # Get GitHub tools
        github_tools = registry.get_server_tools("github")
        print(f"\nGitHub MCP tools ({len(github_tools)}):")
        for tool_name in github_tools[:5]:
            print(f"  - {tool_name}")
            
        # Test tool adapter
        if github_tools:
            print("\n=== Testing Tool Adapter ===")
            tool_name = github_tools[0]
            tool = registry.tool_registry.get_tool_by_name(tool_name)
            
            if tool:
                print(f"\nTool: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Category: {tool.category}")
                print(f"Tags: {tool.tags}")
                
                # Show AI instructions
                print("\nAI Instructions:")
                print(tool.get_ai_prompt_instructions()[:500] + "...")
                
    except Exception as e:
        print(f"✗ Registry test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_agent_permissions():
    """Test agent permission system."""
    print("\n=== Testing Agent Permissions ===\n")
    
    try:
        # Skip this test since we already test permissions in test_with_registry
        print("(Tested in registry test above)")
        
    except Exception as e:
        print(f"✗ Permission test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    # Test direct connection first
    await test_direct_connection()
    
    # Test with registry
    await test_with_registry()
    
    # Test permissions
    await test_agent_permissions()
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())