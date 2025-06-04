# MCP (Model Context Protocol) Integration

This directory contains the MCP integration for AIWhisperer, enabling both client and server capabilities.

## Overview

The Model Context Protocol (MCP) is a standardized protocol for AI applications to interact with external tools and resources. This implementation allows:

- **MCP Client**: AIWhisperer agents can use external MCP tools
- **MCP Server** (Phase 2): Expose AIWhisperer tools to Claude Code and other MCP clients

## Current Status

### Phase 1: MCP Client ✅ Complete
- Core MCP client implementation
- Standard I/O transport
- Tool discovery and adaptation
- Integration with AIWhisperer's tool registry
- Agent-specific permissions
- Connection pooling
- Basic unit tests

### Phase 2: MCP Server 🚧 Not Started
- Will expose AIWhisperer tools via MCP
- Planned for next phase

## Quick Start

### 1. Enable MCP in Configuration

Edit your configuration file to enable MCP:

```yaml
# config/mcp_client.yaml or add to main.yaml
mcp:
  client:
    enabled: true
    servers:
      - name: filesystem
        transport: stdio
        command: ["mcp-server-filesystem", "--root", "/tmp/safe"]
        
    agent_permissions:
      alice:
        allowed_servers: ["filesystem"]
```

### 2. Install MCP Servers

Install the MCP servers you want to use:

```bash
# Example: File system server
npm install -g @modelcontextprotocol/server-filesystem

# Example: GitHub server
npm install -g @modelcontextprotocol/server-github
```

### 3. Use MCP Tools

MCP tools are automatically available to agents based on permissions:

```python
# In agent conversation
# Tools appear with "mcp_" prefix
result = await execute_tool("mcp_filesystem_read_file", {"path": "data.txt"})
```

## Architecture

### Directory Structure

```
ai_whisperer/mcp/
├── client/                 # MCP client implementation
│   ├── client.py          # Core client
│   ├── transports/        # Transport implementations
│   ├── adapters/          # Tool adapters
│   ├── registry.py        # MCP tool registry
│   └── config_loader.py   # Configuration loading
├── server/                # MCP server (future)
└── common/                # Shared types and utilities
```

### Key Components

1. **MCPClient**: Manages connection to MCP servers
2. **MCPToolAdapter**: Adapts MCP tools to AIWhisperer's tool interface
3. **MCPToolRegistry**: Manages MCP tool registration
4. **AgentMCPIntegration**: Controls agent access to MCP tools

## Configuration

### Server Configuration

```yaml
servers:
  - name: my_server
    transport: stdio         # or websocket
    command: ["mcp-server"]  # Command to start server
    env:                     # Environment variables
      API_KEY: "${API_KEY}"  # Supports env var expansion
    timeout: 30.0            # Connection timeout
```

### Agent Permissions

```yaml
agent_permissions:
  agent_name:
    allowed_servers:
      - server1
      - server2
```

## Testing

Run MCP tests:

```bash
# Unit tests
pytest tests/unit/mcp/

# Integration tests (requires MCP servers)
pytest tests/integration/mcp/
```

## Example Usage

See `examples/mcp_example.py` for complete examples.

```python
from ai_whisperer.mcp import initialize_mcp_client

# Initialize MCP with config
config = load_config()
mcp_registry = await initialize_mcp_client(config)

# MCP tools are now available to agents
```

## Troubleshooting

### MCP Server Not Found
- Ensure the MCP server command is installed and in PATH
- Check server logs for errors
- Verify command in configuration

### Tools Not Available
- Check agent permissions in configuration
- Verify MCP is enabled
- Check server connection status

### Connection Issues
- Increase timeout in configuration
- Check firewall/permissions
- Enable debug logging

## Future Enhancements

1. WebSocket transport support
2. MCP server implementation
3. Tool composition and workflows
4. Enhanced error handling
5. Performance optimizations

## References

- [MCP Specification](https://modelcontextprotocol.io/spec)
- [MCP GitHub](https://github.com/modelcontextprotocol)
- [AIWhisperer Docs](../../docs/)