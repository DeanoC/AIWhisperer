# MCP (Model Context Protocol) Integration Plan for AIWhisperer

## Overview

This document outlines the plan to integrate MCP (Model Context Protocol) support into AIWhisperer, enabling both server capabilities (for Claude Code integration) and client capabilities (for AIWhisperer agents to use MCP tools).

## 1. MCP Protocol Overview

The Model Context Protocol (MCP) is a standardized protocol for communication between AI applications and external tools/resources. It provides:

- **Standardized Tool Interface**: Common format for tool definitions and invocations
- **Resource Management**: Access to files, databases, and external services
- **Transport Layer**: Support for stdio, SSE, and WebSocket transports
- **Security Model**: Capability-based permissions and sandboxing

## 2. Architecture Design

### 2.1 MCP Server Implementation (For Claude Code)

The MCP server will expose AIWhisperer's capabilities to Claude Code and other MCP clients.

#### Components:

```
ai_whisperer/mcp/
├── server/
│   ├── __init__.py
│   ├── server.py          # Main MCP server implementation
│   ├── handlers/
│   │   ├── tools.py       # Tool request handlers
│   │   ├── resources.py   # Resource access handlers
│   │   └── prompts.py     # Prompt template handlers
│   ├── adapters/
│   │   └── tool_adapter.py # Adapt AIWhisperer tools to MCP format
│   └── transports/
│       ├── stdio.py       # Standard I/O transport
│       └── websocket.py   # WebSocket transport
```

#### Key Features:

1. **Tool Exposure**:
   - Convert existing AIWhisperer tools to MCP tool format
   - Maintain tool permissions and agent context
   - Support streaming responses for long-running tools

2. **Resource Access**:
   - Expose workspace files as MCP resources
   - Implement read/write permissions based on PathManager
   - Support file watching and change notifications

3. **Transport Support**:
   - Primary: stdio for Claude Code integration
   - Secondary: WebSocket for network-based access

### 2.2 MCP Client Implementation (For AIWhisperer Agents)

The MCP client will allow AIWhisperer agents to use external MCP tools.

#### Components:

```
ai_whisperer/mcp/
├── client/
│   ├── __init__.py
│   ├── client.py          # Main MCP client implementation
│   ├── discovery.py       # MCP server discovery and registry
│   ├── connection.py      # Connection management
│   └── tool_proxy.py      # Proxy MCP tools as AIWhisperer tools
```

#### Key Features:

1. **Tool Discovery**:
   - Discover available MCP servers
   - Query tool capabilities
   - Cache tool definitions

2. **Tool Integration**:
   - Create AITool proxies for MCP tools
   - Handle parameter mapping and validation
   - Support async execution

3. **Connection Management**:
   - Connection pooling for performance
   - Automatic reconnection
   - Error handling and fallbacks

## 3. Integration with Existing Tool System

### 3.1 MCP Tool Adapter Pattern

Create an adapter that bridges MCP tools with AIWhisperer's tool system:

```python
class MCPToolAdapter(AITool):
    """Adapts an MCP tool to AIWhisperer's AITool interface"""
    
    def __init__(self, mcp_tool_definition, mcp_client):
        self.mcp_tool = mcp_tool_definition
        self.mcp_client = mcp_client
        self._name = f"mcp_{mcp_tool.name}"
        
    @property
    def name(self):
        return self._name
        
    @property
    def description(self):
        return self.mcp_tool.description
        
    @property
    def parameters_schema(self):
        return self._convert_mcp_schema(self.mcp_tool.inputSchema)
        
    async def execute(self, arguments=None, **kwargs):
        # Execute MCP tool through client
        result = await self.mcp_client.call_tool(
            self.mcp_tool.name,
            arguments or kwargs
        )
        return result
```

### 3.2 Tool Registry Integration

Extend the LazyToolRegistry to support MCP tools:

```python
class MCPToolRegistry:
    """Registry for MCP tool providers"""
    
    def register_mcp_server(self, server_config):
        """Register an MCP server and its tools"""
        client = MCPClient(server_config)
        tools = await client.list_tools()
        
        for tool in tools:
            adapter = MCPToolAdapter(tool, client)
            self.tool_registry.register_tool(adapter)
            
    def get_mcp_tools(self):
        """Get all registered MCP tools"""
        return [t for t in self.get_all_tools() if t.name.startswith('mcp_')]
```

## 4. Configuration

### 4.1 MCP Server Configuration

```yaml
# config/mcp_server.yaml
mcp:
  server:
    enabled: true
    transport: stdio  # or websocket
    host: localhost
    port: 3000
    
    # Tools to expose via MCP
    exposed_tools:
      - read_file
      - write_file
      - search_files
      - execute_command
      
    # Resource access rules
    resources:
      workspace:
        path: "${workspace_path}"
        permissions: read
      output:
        path: "${output_path}"
        permissions: read_write
```

### 4.2 MCP Client Configuration

```yaml
# config/mcp_client.yaml
mcp:
  client:
    enabled: true
    servers:
      - name: vscode-tools
        transport: stdio
        command: ["npx", "-y", "@vscode/mcp-server"]
        
      - name: github-tools
        transport: websocket
        url: "ws://localhost:3001"
        
    # Agent-specific MCP tool permissions
    agent_permissions:
      alice:
        allowed_servers: ["vscode-tools"]
      eamonn:
        allowed_servers: ["github-tools", "vscode-tools"]
```

## 5. Implementation Phases

### Phase 1: MCP Client Implementation (2-3 weeks)
1. Implement basic MCP client with stdio transport
2. Create MCPToolAdapter for tool integration
3. Add tool discovery and registration
4. Test with existing MCP servers

### Phase 2: MCP Server Implementation (2-3 weeks)
1. Implement MCP server with stdio transport
2. Create tool exposure mechanism
3. Add resource management
4. Test with Claude Code

### Phase 3: Advanced Features (2-3 weeks)
1. Add WebSocket transport support
2. Implement connection pooling
3. Add monitoring and logging
4. Performance optimization

### Phase 4: Documentation and Testing (1-2 weeks)
1. Write comprehensive documentation
2. Create integration tests
3. Add example configurations
4. Create tutorials

## 6. Benefits

### For Claude Code Integration:
- Seamless access to AIWhisperer's planning and execution tools
- Consistent tool interface across different AI systems
- Better integration with Claude's capabilities

### For AIWhisperer Agents:
- Access to vast ecosystem of MCP tools
- Reduced maintenance burden (external tools managed by their authors)
- Enhanced capabilities without code changes

## 7. Technical Considerations

### Security:
- Implement capability-based permissions
- Sandbox external tool execution
- Validate all inputs/outputs

### Performance:
- Connection pooling for MCP clients
- Caching of tool definitions
- Async execution for all operations

### Compatibility:
- Support MCP protocol version negotiation
- Graceful degradation for missing features
- Backward compatibility with existing tools

## 8. Success Metrics

- Number of MCP tools successfully integrated
- Performance overhead < 10ms per tool call
- Zero breaking changes to existing tool system
- Full test coverage for MCP components
- Successful integration with Claude Code

## 9. Risks and Mitigations

### Risk: Protocol Changes
- **Mitigation**: Version negotiation and abstraction layers

### Risk: Performance Impact
- **Mitigation**: Lazy loading, caching, connection pooling

### Risk: Security Vulnerabilities
- **Mitigation**: Sandboxing, input validation, capability model

## 10. Next Steps

1. Review and approve this plan
2. Create detailed RFC for MCP integration
3. Set up development environment with MCP test servers
4. Begin Phase 1 implementation

---

This plan provides a comprehensive approach to integrating MCP support into AIWhisperer while maintaining compatibility with the existing tool system and enhancing capabilities for both server and client use cases.