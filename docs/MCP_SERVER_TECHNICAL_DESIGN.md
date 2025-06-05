# MCP Server Technical Design for AIWhisperer

## Overview

This document provides detailed technical design for implementing an MCP (Model Context Protocol) server in AIWhisperer, enabling Claude Code and other MCP clients to access AIWhisperer's tools and resources.

## 1. Server Architecture

### 1.1 Core Components

```python
# ai_whisperer/mcp/server/server.py
class MCPServer:
    """Main MCP server implementation"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.tool_registry = LazyToolRegistry.get_instance()
        self.handlers = self._initialize_handlers()
        self.transport = self._create_transport()
        
    async def start(self):
        """Start the MCP server"""
        await self.transport.start()
        await self._register_handlers()
        
    async def handle_request(self, request: dict) -> dict:
        """Route incoming requests to appropriate handlers"""
        method = request.get("method")
        params = request.get("params", {})
        
        handler = self.handlers.get(method)
        if not handler:
            return self._error_response("Method not found", -32601)
            
        try:
            result = await handler(params)
            return self._success_response(result, request.get("id"))
        except Exception as e:
            return self._error_response(str(e), -32603)
```

### 1.2 Protocol Implementation

```python
# ai_whisperer/mcp/server/protocol.py
class MCPProtocol:
    """MCP protocol implementation"""
    
    VERSION = "0.1.0"
    
    # Standard MCP methods
    METHODS = {
        "initialize": "handle_initialize",
        "tools/list": "handle_tools_list",
        "tools/call": "handle_tools_call",
        "resources/list": "handle_resources_list",
        "resources/read": "handle_resources_read",
        "resources/write": "handle_resources_write",
        "prompts/list": "handle_prompts_list",
        "prompts/get": "handle_prompts_get",
        "completion/complete": "handle_completion",
    }
    
    async def handle_initialize(self, params: dict) -> dict:
        """Handle MCP initialization"""
        return {
            "protocolVersion": self.VERSION,
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True,
                "completion": False,  # Not supported initially
            },
            "serverInfo": {
                "name": "aiwhisperer-mcp",
                "version": "1.0.0",
            }
        }
```

## 2. Tool Exposure

### 2.1 Tool Handler Implementation

```python
# ai_whisperer/mcp/server/handlers/tools.py
class ToolHandler:
    """Handles MCP tool-related requests"""
    
    def __init__(self, tool_registry: LazyToolRegistry, config: MCPServerConfig):
        self.tool_registry = tool_registry
        self.exposed_tools = config.exposed_tools
        self.tool_cache = {}
        
    async def list_tools(self, params: dict) -> dict:
        """List available tools in MCP format"""
        tools = []
        
        for tool_name in self.exposed_tools:
            tool = self.tool_registry.get_tool_by_name(tool_name)
            if tool:
                mcp_tool = self._convert_to_mcp_format(tool)
                tools.append(mcp_tool)
                
        return {"tools": tools}
        
    def _convert_to_mcp_format(self, ai_tool: AITool) -> dict:
        """Convert AIWhisperer tool to MCP format"""
        return {
            "name": ai_tool.name,
            "description": ai_tool.description,
            "inputSchema": {
                "type": "object",
                "properties": ai_tool.parameters_schema.get("properties", {}),
                "required": ai_tool.parameters_schema.get("required", []),
            }
        }
        
    async def call_tool(self, params: dict) -> dict:
        """Execute a tool and return results"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Get tool from registry
        tool = self.tool_registry.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        # Check if tool is exposed
        if tool_name not in self.exposed_tools:
            raise ValueError(f"Tool '{tool_name}' not exposed via MCP")
            
        # Create a minimal agent context for tool execution
        agent_context = {
            "_agent_id": "mcp_client",
            "_from_agent": "mcp",
            "_session_id": params.get("sessionId", "mcp_session"),
        }
        
        # Execute tool
        try:
            # Merge agent context with arguments
            enriched_args = {**arguments, **agent_context}
            
            # Try new pattern first
            try:
                result = await tool.execute(arguments=enriched_args)
            except TypeError:
                # Fallback to legacy pattern
                result = await tool.execute(**enriched_args)
                
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result) if isinstance(result, dict) else str(result)
                    }
                ]
            }
        except Exception as e:
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool execution failed: {str(e)}"
                    }
                ]
            }
```

### 2.2 Tool Filtering and Permissions

```python
# ai_whisperer/mcp/server/security.py
class MCPSecurityManager:
    """Manages security and permissions for MCP server"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.allowed_tools = set(config.exposed_tools)
        self.resource_permissions = config.resource_permissions
        
    def can_execute_tool(self, tool_name: str, client_info: dict) -> bool:
        """Check if client can execute tool"""
        # Basic check: is tool exposed?
        if tool_name not in self.allowed_tools:
            return False
            
        # Future: Add client-specific permissions
        # if client_info.get("clientId") in self.config.blocked_clients:
        #     return False
            
        return True
        
    def can_access_resource(self, resource_path: str, operation: str) -> bool:
        """Check if resource access is allowed"""
        # Implement path-based permissions
        for rule in self.resource_permissions:
            if self._matches_rule(resource_path, rule):
                return operation in rule.get("operations", [])
        return False
```

## 3. Resource Management

### 3.1 Resource Handler

```python
# ai_whisperer/mcp/server/handlers/resources.py
class ResourceHandler:
    """Handles MCP resource-related requests"""
    
    def __init__(self, path_manager: PathManager, security: MCPSecurityManager):
        self.path_manager = path_manager
        self.security = security
        
    async def list_resources(self, params: dict) -> dict:
        """List available resources"""
        resources = []
        
        # Expose workspace files
        workspace_path = self.path_manager.get_workspace_path()
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), workspace_path)
                resources.append({
                    "uri": f"file:///{rel_path}",
                    "name": rel_path,
                    "mimeType": self._get_mime_type(file),
                })
                
        return {"resources": resources}
        
    async def read_resource(self, params: dict) -> dict:
        """Read a resource"""
        uri = params.get("uri")
        
        # Parse URI and validate access
        file_path = self._parse_uri(uri)
        if not self.security.can_access_resource(file_path, "read"):
            raise PermissionError(f"Access denied to {uri}")
            
        # Read file content
        full_path = self.path_manager.resolve_path(file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": self._get_mime_type(file_path),
                    "text": content,
                }
            ]
        }
```

## 4. Transport Layer

### 4.1 Standard I/O Transport

```python
# ai_whisperer/mcp/server/transports/stdio.py
class StdioTransport:
    """Standard I/O transport for MCP"""
    
    def __init__(self, server: MCPServer):
        self.server = server
        self.reader = None
        self.writer = None
        
    async def start(self):
        """Start listening on stdio"""
        self.reader = asyncio.StreamReader()
        self.writer = asyncio.StreamWriter(
            sys.stdout.buffer,
            sys.stdout.buffer,
            None,
            None
        )
        
        # Start reading from stdin
        asyncio.create_task(self._read_loop())
        
    async def _read_loop(self):
        """Read JSON-RPC messages from stdin"""
        while True:
            try:
                # Read line from stdin
                line = await self._read_line()
                if not line:
                    break
                    
                # Parse JSON-RPC request
                request = json.loads(line)
                
                # Handle request
                response = await self.server.handle_request(request)
                
                # Send response
                await self._send_response(response)
                
            except Exception as e:
                logging.error(f"Error in stdio transport: {e}")
                
    async def _send_response(self, response: dict):
        """Send JSON-RPC response to stdout"""
        response_line = json.dumps(response) + "\n"
        self.writer.write(response_line.encode())
        await self.writer.drain()
```

### 4.2 WebSocket Transport (Future)

```python
# ai_whisperer/mcp/server/transports/websocket.py
class WebSocketTransport:
    """WebSocket transport for MCP"""
    
    def __init__(self, server: MCPServer, host: str, port: int):
        self.server = server
        self.host = host
        self.port = port
        self.app = None
        
    async def start(self):
        """Start WebSocket server"""
        self.app = web.Application()
        self.app.router.add_get('/mcp', self.websocket_handler)
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
    async def websocket_handler(self, request):
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                request_data = json.loads(msg.data)
                response = await self.server.handle_request(request_data)
                await ws.send_str(json.dumps(response))
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logging.error(f'WebSocket error: {ws.exception()}')
                
        return ws
```

## 5. Integration with AIWhisperer

### 5.1 Server Runner

```python
# ai_whisperer/mcp/server/runner.py
class MCPServerRunner:
    """Manages MCP server lifecycle"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.server = None
        
    def _load_config(self, config_path: str) -> MCPServerConfig:
        """Load MCP server configuration"""
        if config_path:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            # Use default configuration
            config_data = {
                "transport": "stdio",
                "exposed_tools": [
                    "read_file",
                    "write_file",
                    "search_files",
                    "list_directory",
                ],
                "resource_permissions": [
                    {
                        "pattern": "**/*.py",
                        "operations": ["read"],
                    },
                    {
                        "pattern": "output/**/*",
                        "operations": ["read", "write"],
                    }
                ]
            }
        return MCPServerConfig(**config_data)
        
    async def run(self):
        """Run the MCP server"""
        # Initialize AIWhisperer components
        path_manager = PathManager()
        tool_registry = LazyToolRegistry.get_instance()
        
        # Create and start server
        self.server = MCPServer(self.config)
        await self.server.start()
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shutdown server"""
        if self.server:
            await self.server.stop()
```

### 5.2 CLI Integration

```python
# ai_whisperer/interfaces/cli/commands/mcp_server.py
@click.command()
@click.option('--config', help='Path to MCP server config file')
@click.option('--transport', type=click.Choice(['stdio', 'websocket']), default='stdio')
@click.option('--expose-tool', multiple=True, help='Tool to expose via MCP')
def mcp_server(config, transport, expose_tool):
    """Run AIWhisperer as an MCP server"""
    
    # Override config with CLI options
    server_config = {}
    if transport:
        server_config['transport'] = transport
    if expose_tool:
        server_config['exposed_tools'] = list(expose_tool)
        
    # Run server
    runner = MCPServerRunner(config)
    if server_config:
        runner.config.update(server_config)
        
    asyncio.run(runner.run())
```

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# tests/unit/mcp/test_mcp_server.py
class TestMCPServer:
    """Test MCP server functionality"""
    
    async def test_initialize(self):
        """Test MCP initialization"""
        server = MCPServer(test_config)
        response = await server.handle_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        })
        
        assert response["result"]["protocolVersion"] == "0.1.0"
        assert response["result"]["capabilities"]["tools"] is True
        
    async def test_tool_listing(self):
        """Test tool listing"""
        server = MCPServer(test_config)
        response = await server.handle_request({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        })
        
        tools = response["result"]["tools"]
        assert len(tools) > 0
        assert all("name" in tool for tool in tools)
```

### 6.2 Integration Tests

```python
# tests/integration/mcp/test_mcp_integration.py
class TestMCPIntegration:
    """Test MCP integration with Claude Code"""
    
    async def test_stdio_communication(self):
        """Test stdio transport with real messages"""
        # Start MCP server in subprocess
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "ai_whisperer.mcp.server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        
        # Send initialize request
        request = json.dumps({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        }) + "\n"
        
        proc.stdin.write(request.encode())
        await proc.stdin.drain()
        
        # Read response
        response_line = await proc.stdout.readline()
        response = json.loads(response_line)
        
        assert response["result"]["protocolVersion"] == "0.1.0"
```

## 7. Deployment

### 7.1 Packaging for Claude Code

```json
// package.json addition
{
  "bin": {
    "aiwhisperer-mcp": "./mcp-server.js"
  },
  "mcp": {
    "configSchema": {
      "type": "object",
      "properties": {
        "exposedTools": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

### 7.2 Wrapper Script

```javascript
// mcp-server.js
#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// Start Python MCP server
const server = spawn('python', [
  '-m', 'ai_whisperer.mcp.server',
  '--transport', 'stdio',
  ...process.argv.slice(2)
], {
  stdio: 'inherit',
  env: { ...process.env, PYTHONUNBUFFERED: '1' }
});

server.on('exit', (code) => {
  process.exit(code);
});
```

## 8. Future Enhancements

1. **Streaming Support**: Add server-sent events for long-running tools
2. **Authentication**: Implement token-based authentication
3. **Rate Limiting**: Add rate limiting for tool calls
4. **Metrics**: Add prometheus metrics for monitoring
5. **Tool Composition**: Allow combining multiple tools into workflows

This technical design provides a solid foundation for implementing an MCP server that exposes AIWhisperer's capabilities to Claude Code and other MCP clients while maintaining security and performance.