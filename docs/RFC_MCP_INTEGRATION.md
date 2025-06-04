# RFC: Model Context Protocol (MCP) Integration

**RFC Number**: 001  
**Title**: Model Context Protocol (MCP) Integration  
**Status**: Draft  
**Created**: 2025-01-04  
**Author**: AIWhisperer Team  

## Summary

This RFC proposes integrating Model Context Protocol (MCP) support into AIWhisperer, enabling the system to act as both an MCP server (exposing tools to Claude Code and other clients) and an MCP client (allowing AIWhisperer agents to use external MCP tools).

## Motivation

The Model Context Protocol is becoming a standard for AI tool integration, with growing adoption across the AI ecosystem. Integrating MCP support would:

1. **Enable Claude Code Integration**: Allow Claude Code to directly use AIWhisperer's planning and execution capabilities
2. **Expand Tool Ecosystem**: Give AIWhisperer agents access to hundreds of existing MCP tools
3. **Reduce Maintenance**: Leverage community-maintained tools instead of building everything in-house
4. **Improve Interoperability**: Work seamlessly with other AI systems that support MCP

## Detailed Design

### Architecture Overview

The integration consists of two main components:

1. **MCP Server**: Exposes AIWhisperer tools via MCP protocol
2. **MCP Client**: Enables AIWhisperer to use external MCP tools

```
┌─────────────────┐         ┌─────────────────┐
│   Claude Code   │         │  External MCP   │
│                 │         │     Servers     │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │ MCP Protocol              │ MCP Protocol
         │                           │
┌────────▼────────┐         ┌────────▼────────┐
│   MCP Server    │         │   MCP Client    │
│   Component     │         │   Component     │
└────────┬────────┘         └────────┬────────┘
         │                           │
         └───────────┬───────────────┘
                     │
           ┌─────────▼─────────┐
           │   AIWhisperer     │
           │   Tool System     │
           └───────────────────┘
```

### MCP Server Component

The server component exposes selected AIWhisperer tools via MCP:

- **Transport**: Standard I/O (stdio) for Claude Code, WebSocket for network access
- **Exposed Tools**: Configurable subset of AIWhisperer tools
- **Security**: Path-based permissions, tool allowlisting
- **Resource Access**: Read/write access to workspace and output directories

Example configuration:
```yaml
mcp:
  server:
    enabled: true
    transport: stdio
    exposed_tools:
      - read_file
      - write_file
      - search_files
      - execute_command
```

### MCP Client Component

The client component allows AIWhisperer agents to use external MCP tools:

- **Tool Discovery**: Automatic discovery of available MCP tools
- **Tool Adaptation**: MCP tools wrapped as AIWhisperer AITool instances
- **Connection Management**: Connection pooling and automatic reconnection
- **Agent Permissions**: Per-agent configuration of allowed MCP servers

Example configuration:
```yaml
mcp:
  client:
    enabled: true
    servers:
      - name: github
        transport: stdio
        command: ["npx", "-y", "@modelcontextprotocol/server-github"]
      - name: filesystem
        transport: stdio
        command: ["mcp-server-filesystem", "--root", "/tmp/safe"]
```

### Integration Points

1. **Tool Registry**: MCP tools registered alongside native tools
2. **Agent Factory**: Agents receive MCP tools based on permissions
3. **AI Loop**: No changes needed - MCP tools work like native tools
4. **CLI**: New `mcp-server` command to run AIWhisperer as MCP server

## Implementation Plan

### Phase 1: MCP Client (2-3 weeks)
- Basic MCP client with stdio transport
- Tool adapter for AIWhisperer integration
- Connection management
- Integration tests

### Phase 2: MCP Server (2-3 weeks)
- MCP server with stdio transport
- Tool exposure mechanism
- Resource management
- Claude Code testing

### Phase 3: Advanced Features (2-3 weeks)
- WebSocket transport
- Connection pooling
- Performance optimization
- Error handling improvements

### Phase 4: Documentation (1-2 weeks)
- User documentation
- Integration guides
- Example configurations
- Tutorial videos

## Backwards Compatibility

This proposal maintains full backwards compatibility:

- Existing tools continue to work unchanged
- MCP support is opt-in via configuration
- No changes to existing APIs or interfaces
- MCP tools namespaced with `mcp_` prefix

## Security Considerations

1. **Tool Permissions**: Only explicitly exposed tools available via MCP
2. **Path Restrictions**: Existing PathManager restrictions apply
3. **Authentication**: Future support for token-based auth
4. **Input Validation**: All MCP inputs validated before execution
5. **Process Isolation**: MCP servers run in separate processes

## Performance Impact

Expected performance characteristics:

- **Startup**: ~100-500ms to connect to MCP server
- **Tool Discovery**: One-time cost, results cached
- **Tool Execution**: Additional 5-10ms overhead per call
- **Memory**: ~10-20MB per MCP connection

Mitigation strategies:
- Connection pooling
- Tool definition caching
- Lazy connection establishment
- Async execution throughout

## Alternatives Considered

1. **Custom Protocol**: Build our own tool protocol
   - Rejected: MCP has momentum and ecosystem
   
2. **Direct Integration**: Integrate tools directly
   - Rejected: High maintenance burden
   
3. **Plugin System**: Create plugin architecture
   - Rejected: More complex than MCP

## Open Questions

1. Should we support MCP's prompt and completion features?
2. How should we handle MCP tool versioning?
3. Should we implement rate limiting for MCP tools?
4. What telemetry should we collect for MCP usage?

## Success Criteria

1. Successfully expose 10+ AIWhisperer tools via MCP
2. Successfully integrate 5+ external MCP tool servers
3. Claude Code can use AIWhisperer tools seamlessly
4. Performance overhead < 10ms per tool call
5. Zero breaking changes to existing functionality

## References

- [MCP Specification](https://modelcontextprotocol.io/spec)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)

## Appendix: Example Usage

### Using AIWhisperer from Claude Code

```javascript
// In Claude Code settings
{
  "mcpServers": {
    "aiwhisperer": {
      "command": "aiwhisperer",
      "args": ["mcp-server"],
      "env": {
        "AIWHISPERER_CONFIG": "/path/to/config.yaml"
      }
    }
  }
}
```

### Using MCP Tools in AIWhisperer

```python
# Automatically available to agents
result = await execute_tool("mcp_github_create_issue", {
    "repository": "aiwhisperer/aiwhisperer",
    "title": "Feature request",
    "body": "Add support for X"
})
```

---

This RFC is open for discussion and feedback. Please submit comments via GitHub issues or the project discussion forum.