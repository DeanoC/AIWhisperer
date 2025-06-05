#!/bin/bash
# Start AIWhisperer MCP server with SSE transport for Claude Desktop on Windows

echo "Starting AIWhisperer MCP server with SSE transport for Windows/WSL integration..."
echo ""
echo "The server will be accessible at:"
echo "  SSE endpoint: http://localhost:3001/mcp/sse"
echo "  Request endpoint: http://localhost:3001/mcp/request"
echo "  Health check: http://localhost:3001/mcp/health"
echo ""

# Get the WSL IP address that Windows can use
WSL_IP=$(hostname -I | awk '{print $1}')
echo "WSL IP address: $WSL_IP"
echo "Windows can also access via: http://$WSL_IP:3001/mcp/sse"
echo ""

# Option 1: Standalone MCP server with SSE
#echo "Option 1: Starting standalone MCP server..."
#python -m ai_whisperer.mcp.server.runner --config config/mcp_sse_windows.yaml
# Option 2: With interactive server (uncomment to use)
echo "Option 2: Starting interactive server with MCP..."
python -m interactive_server.main \
    --mcp \
    --mcp-transport sse \
    --mcp-port 3001 \
    --mcp-tools read_file write_file list_directory search_files execute_command python_executor