#!/bin/bash
"""
Start AIWhisperer MCP Proxy

This script starts the MCP proxy that allows Claude CLI to maintain
connection during AIWhisperer development restarts.
"""

echo "Starting AIWhisperer MCP Proxy..."
echo "Proxy will run on: http://localhost:3002/sse"
echo "Forwarding to AIWhisperer on: http://localhost:8002/sse"
echo ""
echo "Configure Claude CLI MCP settings to use:"
echo "  http://localhost:3002/sse"
echo ""
echo "Press Ctrl+C to stop the proxy"
echo ""

python aiwhisperer_mcp_proxy.py