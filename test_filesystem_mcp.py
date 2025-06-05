#!/usr/bin/env python3
"""Test script for filesystem MCP server integration."""

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_whisperer.mcp import initialize_mcp_client
from ai_whisperer.mcp.common.types import MCPServerConfig, MCPTransport
from ai_whisperer.mcp.client import MCPClient
from ai_whisperer.core.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_filesystem_mcp():
    """Test filesystem MCP server."""
    print("\n=== Testing Filesystem MCP Server ===\n")
    
    # Create a test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using temporary directory: {tmpdir}")
        
        # Create some test files
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello from MCP test!")
        
        # Create server configuration for filesystem
        config = MCPServerConfig(
            name="filesystem",
            transport=MCPTransport.STDIO,
            command=["npx", "-y", "@modelcontextprotocol/server-filesystem", tmpdir],
            timeout=30.0
        )
        
        try:
            print("Connecting to filesystem MCP server...")
            async with MCPClient(config) as client:
                print(f"✓ Connected successfully!")
                print(f"  Server: {client.server_info.name if client.server_info else 'Unknown'}")
                print(f"  Version: {client.server_info.version if client.server_info else 'Unknown'}")
                
                # List tools
                tools = await client.list_tools()
                print(f"\n✓ Discovered {len(tools)} tools:")
                
                for tool in tools:
                    print(f"\n  Tool: {tool.name}")
                    print(f"  Description: {tool.description}")
                    print(f"  Input schema: {tool.input_schema}")
                    
                # Try to read the test file
                if any(t.name == "read_file" for t in tools):
                    print("\n=== Testing read_file tool ===")
                    result = await client.call_tool("read_file", {
                        "path": "test.txt"
                    })
                    print(f"Result: {result}")
                    
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_with_registry():
    """Test filesystem MCP with registry."""
    print("\n=== Testing Filesystem MCP with Registry ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Load main configuration
            config = load_config("config/main.yaml")
            
            # Add filesystem MCP configuration
            if "mcp" not in config:
                config["mcp"] = {}
            config["mcp"]["client"] = {
                "enabled": True,
                "servers": [{
                    "name": "filesystem",
                    "transport": "stdio", 
                    "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", tmpdir],
                    "timeout": 30.0
                }],
                "agent_permissions": {
                    "alice": {"allowed_servers": ["filesystem"]},
                    "debbie": {"allowed_servers": ["filesystem"]}
                }
            }
            
            # Initialize MCP
            print("Initializing MCP client...")
            registry = await initialize_mcp_client(config)
            
            if not registry:
                print("✗ MCP initialization failed")
                return
                
            print("✓ MCP initialized successfully!")
            
            # Get filesystem tools
            fs_tools = registry.get_server_tools("filesystem")
            print(f"\nFilesystem tools ({len(fs_tools)}):")
            for tool_name in fs_tools:
                tool = registry.tool_registry.get_tool_by_name(tool_name)
                if tool:
                    print(f"  - {tool.name}: {tool.description}")
                    
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run filesystem MCP tests."""
    # First install the filesystem server
    print("Installing filesystem MCP server...")
    proc = await asyncio.create_subprocess_exec(
        "npm", "install", "-g", "@modelcontextprotocol/server-filesystem",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        print("✓ Filesystem MCP server installed")
    else:
        print(f"✗ Failed to install: {stderr.decode()}")
        
    # Run tests
    await test_filesystem_mcp()
    await test_with_registry()


if __name__ == "__main__":
    asyncio.run(main())