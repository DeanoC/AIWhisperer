#!/usr/bin/env python3
"""
AIWhisperer MCP Proxy

A FastMCP-based proxy that maintains Claude CLI's connection to AIWhisperer 
during development restarts. This allows developers to restart AIWhisperer 
without losing their Claude CLI session.

Features:
- Automatic reconnection when AIWhisperer restarts
- Transparent tool forwarding via MCP protocol
- SSE transport for compatibility with Claude Desktop
- Session management and error handling

Usage:
    python aiwhisperer_mcp_proxy.py

The proxy runs on port 3002 and connects to AIWhisperer on port 8002.
Configure Claude CLI to connect to http://localhost:3002/sse
"""

import logging
import sys
from fastmcp import FastMCP

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def main():
    """Start the AIWhisperer MCP proxy."""
    logger.info("Starting AIWhisperer MCP Proxy...")
    
    # Create a proxy to the AIWhisperer MCP server
    # FastMCP handles all the complex SSE event forwarding automatically
    proxy = FastMCP.as_proxy(
        "http://localhost:8002/sse",  # AIWhisperer MCP server endpoint
        name="aiwhisperer-aggregator",  # Name shown in Claude CLI
        port=3002
    )
    
    logger.info("Proxy started on http://localhost:3002/sse")
    logger.info("Forwarding to AIWhisperer MCP server at http://localhost:8002/sse")
    logger.info("Configure Claude CLI to use: http://localhost:3002/sse")
    
    # Run the proxy with SSE transport for Claude Desktop compatibility
    proxy.run(transport="sse")

if __name__ == "__main__":
    main()