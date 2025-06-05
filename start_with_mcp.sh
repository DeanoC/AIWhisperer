#!/bin/bash
# Start AIWhisperer interactive server with MCP server

echo "Starting AIWhisperer interactive server with MCP server..."
echo "Interactive server will run on port 8000"
echo "MCP server mounted at /mcp (SSE via FastMCP)"
echo ""
echo "The MCP server will be accessible at:"
echo "  SSE endpoint: http://localhost:8000/mcp/sse"
echo ""
echo "Starting servers..."

# Start the interactive server with MCP enabled using SSE transport
python -m interactive_server.main \
    --config config/main.yaml \
    --mcp_server_enable \
    --mcp_server_port 8002 \
    --mcp_server_transport sse \
    --mcp_server_tools read_file write_file list_directory search_files execute_command python_executor "$@"