# MCP Reconnection Solutions for Claude Desktop

## Problem
Claude Desktop caches MCP tools at startup and doesn't refresh them when the MCP server restarts. This makes development iteration difficult as you need to exit and restart Claude Desktop every time you modify the AIWhisperer MCP server.

## Solution: Persistent MCP Proxy

A persistent proxy that manages the MCP server as a subprocess, providing continuous availability to Claude Desktop even when AIWhisperer needs to restart.

### How It Works

```
Claude Desktop <--stdio--> Persistent Proxy <--subprocess--> MCP Server
```

1. **Subprocess Management**: The proxy runs the actual MCP server as a subprocess
2. **Automatic Restart**: If the server crashes or is stopped, the proxy automatically restarts it
3. **Tool Caching**: Caches tool definitions to provide them during server restarts
4. **Transparent Operation**: Claude Desktop sees a continuously running MCP server

### Installation

1. **Copy the configuration**:
   ```bash
   cp claude_mcp_config_persistent.json ~/.config/claude/claude_mcp_config.json
   ```

2. **Restart Claude Desktop** to load the new configuration

### Usage

Once configured, the persistent proxy will:
- Start automatically when Claude Desktop connects
- Keep running even when you restart AIWhisperer
- Automatically restart the MCP server if it crashes
- Cache tools so they remain available during restarts

### Development Workflow

1. **Make changes to AIWhisperer code**
2. **Stop the running server** (Ctrl+C in the terminal)
3. **Start the server again** - the proxy will automatically reconnect
4. **Tools remain available in Claude Desktop** throughout

### Testing the Proxy

```bash
# Run the proxy manually to see logs
python -m ai_whisperer.mcp.client.persistent_proxy --log-level DEBUG

# In another terminal, check if it's running
ps aux | grep persistent_proxy
```

### Architecture

The persistent proxy:
- Uses **stdio transport** for maximum compatibility
- Runs MCP server as a **managed subprocess**
- **Caches responses** from `initialize` and `tools/list`
- **Monitors subprocess health** and restarts as needed
- **Forwards all other requests** transparently

### Configuration Options

```bash
python -m ai_whisperer.mcp.client.persistent_proxy --help

Options:
  --config CONFIG       Configuration file for MCP server (default: config/mcp_minimal.yaml)
  --transport TYPE      Transport type (default: stdio)
  --log-level LEVEL     Logging level (default: INFO)
  --restart-delay SECS  Delay before restarting crashed server (default: 2.0)
```

### Benefits

- **Zero downtime** during AIWhisperer development
- **Automatic recovery** from server crashes
- **Tool availability** even during restarts
- **Simple stdio interface** - no network complexity
- **Transparent to Claude Desktop** - no client changes needed

### Troubleshooting

1. **Check proxy logs**: Logs are written to stderr when running manually
2. **Verify subprocess**: The proxy shows the PID of the MCP server subprocess
3. **Tool caching**: Watch for "Cached N tools" messages in the logs
4. **Restart detection**: Look for "MCP server not running, attempting to restart..." messages

### Alternative Solutions

If the persistent proxy doesn't meet your needs:

1. **Use interactive server with SSE**:
   ```bash
   ./start_mcp_sse_for_windows.sh
   ```

2. **Use screen/tmux** to keep servers running:
   ```bash
   screen -S mcp-server
   python -m ai_whisperer.mcp.server.fastmcp_runner --transport stdio
   # Detach with Ctrl+A, D
   ```

### Notes

- The proxy adds minimal overhead (<1ms latency)
- Memory usage is negligible (only caches tool definitions)
- Works with any MCP transport but stdio is recommended
- Can handle multiple reconnection cycles without issues