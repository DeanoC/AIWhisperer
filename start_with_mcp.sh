#!/bin/bash
# Start AIWhisperer interactive server with MCP server

echo "Starting AIWhisperer interactive server with MCP server..."
echo "Interactive server will run on port 8000"
echo "MCP server will run on port 3001 (WebSocket)"
echo ""
echo "To connect Claude Desktop to the MCP server, add this to your claude_desktop_config.json:"
echo '
{
  "mcpServers": {
    "aiwhisperer-live": {
      "command": "python",
      "args": [
        "-c",
        "import websocket; ws = websocket.WebSocket(); ws.connect(\"ws://localhost:3001/mcp\"); # ... handle MCP protocol"
      ]
    }
  }
}
'
echo ""
echo "Starting servers..."

# Start the interactive server with MCP enabled
python -m interactive_server.main \
    --mcp \
    --mcp-port 3001 \
    --mcp-transport websocket \
    --mcp-tools read_file write_file list_directory search_files execute_command python_executor