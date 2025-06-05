# Claude Desktop + AIWhisperer on Windows/WSL

**Important Note**: Claude Desktop currently only supports stdio transport, which cannot work across the Windows/WSL boundary. This guide documents the technical possibilities and workarounds.

## The Challenge

When Claude Desktop runs on Windows and AIWhisperer runs in WSL:
- **stdio transport won't work** - Can't pipe stdin/stdout across the Windows/WSL boundary
- **SSE transport** - Not currently supported by Claude Desktop
- **WebSocket transport** - Not currently supported by Claude Desktop

## Workaround Options

### Option 1: Run AIWhisperer on Windows (Recommended)

The most straightforward solution is to install Python and AIWhisperer directly on Windows:

1. Install Python on Windows (not WSL)
2. Install AIWhisperer:
   ```powershell
   pip install ai-whisperer
   ```
3. Configure Claude Desktop normally with stdio transport

### Option 2: WSL2 with Windows Terminal Integration

If you must use WSL, you can try using `wsl.exe` as a bridge:

```json
{
  "mcpServers": {
    "aiwhisperer-wsl": {
      "command": "wsl",
      "args": [
        "-e",
        "bash",
        "-c",
        "cd /home/user/projects/AIWhisperer && python -m ai_whisperer.mcp.server.runner"
      ]
    }
  }
}
```

**Note**: This may have issues with path resolution and file access.

### Option 3: Wait for Network Transport Support

The SSE and WebSocket transports are fully implemented in AIWhisperer and work well. Once Claude Desktop adds support for network transports, you can use the configuration below.

## Future Setup (When Network Transports are Supported)

### 1. Start AIWhisperer MCP Server in WSL

```bash
# Navigate to AIWhisperer directory
cd ~/projects/AIWhisperer

# Use the SSE startup script
./start_mcp_sse_for_windows.sh

# Or start manually with config
aiwhisperer-mcp --config config/mcp_sse_windows.yaml
```

The server will start on:
- SSE endpoint: `http://localhost:3001/mcp/sse`
- Request endpoint: `http://localhost:3001/mcp/request`
- Health check: `http://localhost:3001/mcp/health`

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "aiwhisperer-wsl": {
      "command": "cmd",
      "args": [
        "/c",
        "echo SSE connection to http://localhost:3001/mcp/sse"
      ],
      "env": {
        "MCP_SSE_URL": "http://localhost:3001/mcp/sse",
        "MCP_REQUEST_URL": "http://localhost:3001/mcp/request"
      }
    }
  }
}
```

**Note**: Claude Desktop's SSE support may require a specific configuration format. If the above doesn't work, try:

```json
{
  "mcpServers": {
    "aiwhisperer-wsl": {
      "transport": "sse",
      "url": "http://localhost:3001/mcp",
      "sseEndpoint": "/sse",
      "requestEndpoint": "/request"
    }
  }
}
```

### 3. Verify Connection

1. In WSL, check that the server is running:
   ```bash
   curl http://localhost:3001/mcp/health
   ```

2. From Windows PowerShell, verify access:
   ```powershell
   Invoke-WebRequest -Uri http://localhost:3001/mcp/health
   ```

3. Restart Claude Desktop and check if AIWhisperer tools are available

## Troubleshooting

### Connection Issues

1. **Check WSL network settings**:
   ```bash
   # In WSL, get the IP address
   hostname -I
   ```

2. **Try using WSL IP directly**:
   Instead of `localhost`, use the WSL IP address in Claude Desktop config:
   ```json
   "url": "http://172.x.x.x:3001/mcp"
   ```

3. **Firewall issues**:
   - Windows Firewall may block connections
   - Try temporarily disabling it to test
   - Add a rule for port 3001 if needed

### Port Conflicts

If port 3001 is in use:
```bash
# Check what's using the port
netstat -an | grep 3001

# Use a different port
./start_mcp_sse_for_windows.sh
# Then edit the script to use a different port
```

### CORS Issues

The default configuration allows all origins (`*`). For better security in production:

```yaml
sse_cors_origins:
  - "http://localhost:*"
  - "app://claude-desktop"  # If Claude uses a custom protocol
```

## Advanced Configuration

### Running with Interactive Server

You can run both the interactive web UI and MCP SSE server:

```bash
python -m interactive_server.main \
    --mcp \
    --mcp-transport sse \
    --mcp-port 3001 \
    --host 0.0.0.0 \
    --port 8000
```

This gives you:
- Web UI at `http://localhost:8000`
- MCP SSE at `http://localhost:3001/mcp/sse`

### Custom Tool Selection

Edit `config/mcp_sse_windows.yaml` to expose only the tools you need:

```yaml
exposed_tools:
  # Minimal set for code reading
  - read_file
  - list_directory
  - search_files
  
  # Add more as needed
  # - write_file
  # - execute_command
  # - python_executor
```

### Security Considerations

When exposing AIWhisperer to network access:

1. **Limit exposed tools** - Only expose what you need
2. **Set workspace boundaries** - Use specific project directories
3. **Configure resource permissions** - Restrict file access patterns
4. **Use localhost only** - Don't expose to external networks
5. **Enable audit logging** - Track all operations

```yaml
mcp:
  server:
    # Bind to localhost only for security
    host: "127.0.0.1"  
    
    # Enable audit logging
    enable_audit_log: true
    audit_log_file: "mcp-audit.log"
    
    # Strict resource permissions
    resource_permissions:
      - pattern: "src/**/*.py"
        operations: ["read"]
      - pattern: "docs/**/*.md"
        operations: ["read"]
```

## Example Usage

Once connected, you can use AIWhisperer tools in Claude Desktop:

```
"Can you read the main.py file in my AIWhisperer project?"

"Search for all TODO comments in the Python files"

"List all the test files in the project"

"Show me the structure of the interactive_server directory"
```

## Next Steps

1. Start with read-only tools to test the connection
2. Gradually add more tools as needed
3. Configure project-specific workspaces
4. Set up proper security restrictions
5. Consider using the interactive server for full functionality