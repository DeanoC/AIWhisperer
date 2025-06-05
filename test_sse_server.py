#!/usr/bin/env python3
"""Test SSE server startup."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_whisperer.mcp.server.runner import MCPServerRunner
import logging

logging.basicConfig(level=logging.INFO)

async def test_sse_server():
    """Test starting MCP server with SSE transport."""
    print("Testing SSE server startup...")
    
    # Create runner with SSE configuration
    runner = MCPServerRunner(
        transport="sse",
        port=3001,
        exposed_tools=["read_file", "list_directory", "search_files"],
        workspace="/tmp",
        enable_metrics=True
    )
    
    # Start server
    server_task = asyncio.create_task(runner.run())
    
    # Give it time to start
    await asyncio.sleep(2)
    
    print("SSE server should be running on:")
    print("  - SSE endpoint: http://localhost:3001/mcp/sse")
    print("  - Request endpoint: http://localhost:3001/mcp/request")
    print("  - Health check: http://localhost:3001/mcp/health")
    print("")
    print("Press Ctrl+C to stop")
    
    try:
        await server_task
    except KeyboardInterrupt:
        print("\nShutting down...")
        if runner.server:
            await runner.server.stop()

if __name__ == "__main__":
    asyncio.run(test_sse_server())