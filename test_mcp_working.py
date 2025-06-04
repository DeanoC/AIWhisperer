#!/usr/bin/env python3
"""Working test for MCP GitHub integration."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ai_whisperer.mcp.common.types import MCPServerConfig, MCPTransport
from ai_whisperer.mcp.client import MCPClient


async def main():
    """Test GitHub MCP server with proper tool discovery."""
    
    print("=== GitHub MCP Server Test ===\n")
    
    # Check token
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        print(f"✓ Using GitHub token: {token[:20]}...")
    else:
        print("⚠️  No GitHub token found")
    
    # Create configuration
    config = MCPServerConfig(
        name="github",
        transport=MCPTransport.STDIO,
        command=["npx", "-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": token or ""},
        timeout=30.0
    )
    
    try:
        # Connect to server
        print("\nConnecting to GitHub MCP server...")
        async with MCPClient(config) as client:
            print("✓ Connected successfully!")
            print(f"  Server: {client.server_info.name}")
            print(f"  Version: {client.server_info.version}")
            
            # Wait a moment for server to fully initialize
            await asyncio.sleep(1.0)
            
            # Manually request tools to debug
            print("\nManually requesting tools...")
            try:
                response = await client._send_request("tools/list")
                print(f"Number of tools in response: {len(response.get('tools', []))}")
            except Exception as e:
                print(f"Manual request failed: {e}")
            
            # Get tools
            print("\nDiscovering tools...")
            tools = await client.list_tools()
            
            print(f"\n✓ Found {len(tools)} tools!")
            
            # List first 10 tools
            print("\nAvailable GitHub tools:")
            for i, tool in enumerate(tools[:10], 1):
                print(f"{i:2}. {tool.name}")
                print(f"    {tool.description}")
            
            if len(tools) > 10:
                print(f"\n... and {len(tools) - 10} more tools")
            
            # Test a simple tool
            if any(t.name == "search_repositories" for t in tools):
                print("\n=== Testing search_repositories tool ===")
                result = await client.call_tool("search_repositories", {
                    "query": "language:python mcp",
                    "perPage": 3
                })
                
                # Extract content from response
                if isinstance(result, dict) and "content" in result:
                    content = result["content"]
                    if content and isinstance(content[0], dict) and content[0].get("type") == "text":
                        import json
                        data = json.loads(content[0]["text"])
                        print(f"\nFound {data.get('total_count', 0)} repositories")
                        
                        items = data.get("items", [])
                        for repo in items[:3]:
                            desc = repo.get('description') or 'No description'
                            print(f"  - {repo['full_name']}: {desc[:60]}...")
                else:
                    print(f"Result: {result}")
                    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())