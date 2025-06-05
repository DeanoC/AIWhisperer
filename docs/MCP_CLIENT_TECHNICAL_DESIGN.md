# MCP Client Technical Design for AIWhisperer

## Overview

This document provides detailed technical design for implementing an MCP (Model Context Protocol) client in AIWhisperer, enabling agents to use external MCP tools from various providers.

## 1. Client Architecture

### 1.1 Core Components

```python
# ai_whisperer/mcp/client/client.py
class MCPClient:
    """MCP client for connecting to external MCP servers"""
    
    def __init__(self, server_config: MCPServerConfig):
        self.config = server_config
        self.transport = self._create_transport()
        self.tools = {}
        self.resources = {}
        self.initialized = False
        self._request_id = 0
        
    async def connect(self):
        """Establish connection to MCP server"""
        await self.transport.connect()
        await self._initialize()
        
    async def _initialize(self):
        """Initialize MCP session"""
        response = await self._send_request("initialize", {
            "clientInfo": {
                "name": "aiwhisperer",
                "version": "1.0.0"
            }
        })
        
        self.server_info = response.get("serverInfo", {})
        self.capabilities = response.get("capabilities", {})
        self.initialized = True
        
        # Cache available tools
        if self.capabilities.get("tools"):
            await self._cache_tools()
            
    async def _send_request(self, method: str, params: dict = None) -> dict:
        """Send JSON-RPC request to server"""
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._request_id
        }
        if params:
            request["params"] = params
            
        response = await self.transport.send_request(request)
        
        if "error" in response:
            raise MCPError(response["error"])
            
        return response.get("result", {})
```

### 1.2 Transport Abstraction

```python
# ai_whisperer/mcp/client/transports/base.py
class MCPTransport(ABC):
    """Abstract base class for MCP transports"""
    
    @abstractmethod
    async def connect(self):
        """Establish connection"""
        pass
        
    @abstractmethod
    async def send_request(self, request: dict) -> dict:
        """Send request and wait for response"""
        pass
        
    @abstractmethod
    async def close(self):
        """Close connection"""
        pass

# ai_whisperer/mcp/client/transports/stdio.py
class StdioTransport(MCPTransport):
    """Standard I/O transport for MCP"""
    
    def __init__(self, command: List[str]):
        self.command = command
        self.process = None
        self.pending_requests = {}
        
    async def connect(self):
        """Start subprocess and establish stdio communication"""
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Start reading responses
        asyncio.create_task(self._read_loop())
        
    async def send_request(self, request: dict) -> dict:
        """Send request via stdin and wait for response"""
        request_id = request.get("id")
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line.encode())
        await self.process.stdin.drain()
        
        # Wait for response
        return await future
        
    async def _read_loop(self):
        """Read responses from stdout"""
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
                
            try:
                response = json.loads(line.decode())
                request_id = response.get("id")
                
                if request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)
                    future.set_result(response)
            except Exception as e:
                logging.error(f"Error parsing MCP response: {e}")
```

## 2. Tool Discovery and Integration

### 2.1 Tool Discovery

```python
# ai_whisperer/mcp/client/discovery.py
class MCPToolDiscovery:
    """Discovers and manages MCP tools"""
    
    def __init__(self, client: MCPClient):
        self.client = client
        self.tools = {}
        
    async def discover_tools(self) -> List[MCPToolDefinition]:
        """Discover available tools from MCP server"""
        response = await self.client._send_request("tools/list")
        tools = response.get("tools", [])
        
        # Parse and validate tools
        discovered_tools = []
        for tool_data in tools:
            tool = MCPToolDefinition(
                name=tool_data["name"],
                description=tool_data["description"],
                input_schema=tool_data.get("inputSchema", {}),
                server_name=self.client.config.name
            )
            discovered_tools.append(tool)
            self.tools[tool.name] = tool
            
        return discovered_tools
        
    def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        """Get tool definition by name"""
        return self.tools.get(name)
```

### 2.2 Tool Adapter Implementation

```python
# ai_whisperer/mcp/client/tool_adapter.py
class MCPToolAdapter(AITool):
    """Adapts MCP tools to AIWhisperer's tool interface"""
    
    def __init__(self, tool_def: MCPToolDefinition, client: MCPClient):
        self.tool_def = tool_def
        self.client = client
        self._name = f"mcp_{tool_def.server_name}_{tool_def.name}"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def description(self) -> str:
        return f"[MCP:{self.tool_def.server_name}] {self.tool_def.description}"
        
    @property
    def parameters_schema(self) -> dict:
        """Convert MCP schema to AIWhisperer format"""
        return {
            "type": "object",
            "properties": self.tool_def.input_schema.get("properties", {}),
            "required": self.tool_def.input_schema.get("required", []),
            "additionalProperties": False
        }
        
    def get_ai_prompt_instructions(self) -> str:
        """Generate instructions for AI"""
        return f"""Tool: {self.name}
Description: {self.description}
This is an external MCP tool provided by '{self.tool_def.server_name}'.
Parameters: {json.dumps(self.parameters_schema, indent=2)}
"""
        
    async def execute(self, arguments: dict = None, **kwargs) -> Any:
        """Execute MCP tool through client"""
        # Merge arguments
        args = arguments or kwargs
        
        # Remove AIWhisperer-specific fields
        clean_args = {k: v for k, v in args.items() 
                     if not k.startswith('_')}
        
        # Call MCP tool
        try:
            response = await self.client._send_request("tools/call", {
                "name": self.tool_def.name,
                "arguments": clean_args
            })
            
            # Extract content from MCP response
            content = response.get("content", [])
            if content and len(content) > 0:
                # Return text content if available
                text_content = next(
                    (c["text"] for c in content if c["type"] == "text"),
                    None
                )
                if text_content:
                    # Try to parse as JSON
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        return text_content
                        
            return response
            
        except MCPError as e:
            raise ToolExecutionError(f"MCP tool failed: {e}")
```

## 3. Connection Management

### 3.1 Connection Pool

```python
# ai_whisperer/mcp/client/connection_pool.py
class MCPConnectionPool:
    """Manages pool of MCP client connections"""
    
    def __init__(self):
        self.connections = {}
        self.lock = asyncio.Lock()
        
    async def get_client(self, server_config: MCPServerConfig) -> MCPClient:
        """Get or create client for server"""
        async with self.lock:
            key = self._get_key(server_config)
            
            if key in self.connections:
                client = self.connections[key]
                # Check if connection is still alive
                if await client.is_alive():
                    return client
                else:
                    # Remove dead connection
                    del self.connections[key]
                    
            # Create new connection
            client = MCPClient(server_config)
            await client.connect()
            self.connections[key] = client
            return client
            
    def _get_key(self, config: MCPServerConfig) -> str:
        """Generate unique key for server config"""
        if config.transport == "stdio":
            return f"stdio:{':'.join(config.command)}"
        elif config.transport == "websocket":
            return f"ws:{config.url}"
        else:
            return f"{config.transport}:{config.name}"
            
    async def close_all(self):
        """Close all connections"""
        async with self.lock:
            for client in self.connections.values():
                await client.close()
            self.connections.clear()
```

### 3.2 Automatic Reconnection

```python
# ai_whisperer/mcp/client/reconnect.py
class ReconnectingMCPClient(MCPClient):
    """MCP client with automatic reconnection"""
    
    def __init__(self, server_config: MCPServerConfig, max_retries: int = 3):
        super().__init__(server_config)
        self.max_retries = max_retries
        self.retry_delay = 1.0
        
    async def _send_request(self, method: str, params: dict = None) -> dict:
        """Send request with automatic retry on connection failure"""
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                # Check if connected
                if not self.initialized:
                    await self.connect()
                    
                # Try to send request
                return await super()._send_request(method, params)
                
            except (ConnectionError, MCPError) as e:
                last_error = e
                retries += 1
                
                if retries < self.max_retries:
                    # Exponential backoff
                    await asyncio.sleep(self.retry_delay * (2 ** retries))
                    
                    # Try to reconnect
                    try:
                        await self.close()
                        await self.connect()
                    except Exception:
                        pass
                        
        raise ConnectionError(f"Failed after {retries} retries: {last_error}")
```

## 4. Registry Integration

### 4.1 MCP Tool Registry

```python
# ai_whisperer/mcp/client/registry.py
class MCPToolRegistry:
    """Registry for MCP tools"""
    
    def __init__(self, tool_registry: LazyToolRegistry):
        self.tool_registry = tool_registry
        self.connection_pool = MCPConnectionPool()
        self.registered_servers = {}
        
    async def register_mcp_server(self, config: MCPServerConfig):
        """Register an MCP server and its tools"""
        # Connect to server
        client = await self.connection_pool.get_client(config)
        
        # Discover tools
        discovery = MCPToolDiscovery(client)
        tools = await discovery.discover_tools()
        
        # Register each tool
        registered_tools = []
        for tool_def in tools:
            adapter = MCPToolAdapter(tool_def, client)
            self.tool_registry.register_tool(adapter)
            registered_tools.append(adapter.name)
            
        # Store registration info
        self.registered_servers[config.name] = {
            "config": config,
            "client": client,
            "tools": registered_tools
        }
        
        logging.info(f"Registered {len(tools)} tools from MCP server '{config.name}'")
        
    async def unregister_mcp_server(self, server_name: str):
        """Unregister an MCP server and its tools"""
        if server_name not in self.registered_servers:
            return
            
        info = self.registered_servers[server_name]
        
        # Unregister tools
        for tool_name in info["tools"]:
            self.tool_registry.unregister_tool(tool_name)
            
        # Close connection
        await info["client"].close()
        
        del self.registered_servers[server_name]
```

### 4.2 Configuration Integration

```python
# ai_whisperer/mcp/client/config_loader.py
class MCPConfigLoader:
    """Loads MCP client configuration"""
    
    @staticmethod
    async def load_and_register(config_path: str, tool_registry: LazyToolRegistry):
        """Load MCP config and register all servers"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        mcp_config = config.get("mcp", {}).get("client", {})
        if not mcp_config.get("enabled", False):
            return
            
        registry = MCPToolRegistry(tool_registry)
        
        # Register each configured server
        for server_config in mcp_config.get("servers", []):
            try:
                config_obj = MCPServerConfig(
                    name=server_config["name"],
                    transport=server_config["transport"],
                    command=server_config.get("command"),
                    url=server_config.get("url"),
                    env=server_config.get("env", {})
                )
                
                await registry.register_mcp_server(config_obj)
                
            except Exception as e:
                logging.error(f"Failed to register MCP server '{server_config['name']}': {e}")
```

## 5. Agent Integration

### 5.1 Agent-Specific MCP Tools

```python
# ai_whisperer/services/agents/mcp_integration.py
class AgentMCPIntegration:
    """Manages MCP tools for specific agents"""
    
    def __init__(self, mcp_registry: MCPToolRegistry):
        self.mcp_registry = mcp_registry
        
    def get_mcp_tools_for_agent(self, agent_name: str, config: dict) -> List[str]:
        """Get allowed MCP tools for an agent"""
        # Get agent's MCP permissions
        agent_permissions = config.get("mcp", {}).get("client", {}).get(
            "agent_permissions", {}
        ).get(agent_name, {})
        
        allowed_servers = agent_permissions.get("allowed_servers", [])
        
        # Collect tools from allowed servers
        allowed_tools = []
        for server_name in allowed_servers:
            if server_name in self.mcp_registry.registered_servers:
                server_info = self.mcp_registry.registered_servers[server_name]
                allowed_tools.extend(server_info["tools"])
                
        return allowed_tools
```

### 5.2 Tool Filtering

```python
# ai_whisperer/services/agents/factory.py (modification)
class AgentFactory:
    """Modified to support MCP tools"""
    
    async def create_agent(self, agent_name: str, ...) -> Agent:
        """Create agent with MCP tools"""
        # ... existing code ...
        
        # Get base tools
        tools = self._get_agent_tools(agent_name)
        
        # Add MCP tools if enabled
        if hasattr(self, 'mcp_integration'):
            mcp_tools = self.mcp_integration.get_mcp_tools_for_agent(
                agent_name, self.config
            )
            tools.extend(mcp_tools)
            
        # ... rest of agent creation ...
```

## 6. Error Handling and Monitoring

### 6.1 Error Types

```python
# ai_whisperer/mcp/client/exceptions.py
class MCPError(Exception):
    """Base exception for MCP errors"""
    pass
    
class MCPConnectionError(MCPError):
    """Connection-related errors"""
    pass
    
class MCPToolError(MCPError):
    """Tool execution errors"""
    pass
    
class MCPTimeoutError(MCPError):
    """Timeout errors"""
    pass
```

### 6.2 Monitoring

```python
# ai_whisperer/mcp/client/monitoring.py
class MCPMonitor:
    """Monitors MCP client performance and health"""
    
    def __init__(self):
        self.metrics = {
            "connections": 0,
            "requests": 0,
            "errors": 0,
            "tool_calls": 0,
            "response_times": []
        }
        
    async def record_request(self, server: str, method: str, duration: float):
        """Record request metrics"""
        self.metrics["requests"] += 1
        self.metrics["response_times"].append(duration)
        
        # Log slow requests
        if duration > 5.0:
            logging.warning(f"Slow MCP request: {server}/{method} took {duration:.2f}s")
            
    def get_stats(self) -> dict:
        """Get current statistics"""
        response_times = self.metrics["response_times"]
        return {
            "total_connections": self.metrics["connections"],
            "total_requests": self.metrics["requests"],
            "total_errors": self.metrics["errors"],
            "total_tool_calls": self.metrics["tool_calls"],
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
        }
```

## 7. Testing Strategy

### 7.1 Mock MCP Server

```python
# tests/mocks/mock_mcp_server.py
class MockMCPServer:
    """Mock MCP server for testing"""
    
    def __init__(self, tools: List[dict]):
        self.tools = tools
        self.requests = []
        
    async def handle_request(self, request: dict) -> dict:
        """Handle mock requests"""
        self.requests.append(request)
        
        method = request.get("method")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {"tools": True}
                }
            }
            
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {"tools": self.tools}
            }
            
        elif method == "tools/call":
            tool_name = request["params"]["name"]
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "content": [{
                        "type": "text",
                        "text": f"Mock result for {tool_name}"
                    }]
                }
            }
```

### 7.2 Integration Tests

```python
# tests/integration/mcp/test_mcp_client.py
class TestMCPClient:
    """Test MCP client functionality"""
    
    async def test_tool_discovery_and_execution(self):
        """Test discovering and executing MCP tools"""
        # Create mock server
        mock_tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    }
                }
            }
        ]
        
        # Create client with mock transport
        config = MCPServerConfig(
            name="test_server",
            transport="mock",
            mock_server=MockMCPServer(mock_tools)
        )
        
        client = MCPClient(config)
        await client.connect()
        
        # Discover tools
        discovery = MCPToolDiscovery(client)
        tools = await discovery.discover_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        
        # Create adapter and execute
        adapter = MCPToolAdapter(tools[0], client)
        result = await adapter.execute({"message": "Hello"})
        
        assert "Mock result" in result
```

## 8. Example Usage

### 8.1 Configuration Example

```yaml
# config/mcp_client.yaml
mcp:
  client:
    enabled: true
    servers:
      # GitHub integration
      - name: github
        transport: stdio
        command: ["npx", "-y", "@modelcontextprotocol/server-github"]
        env:
          GITHUB_TOKEN: "${GITHUB_TOKEN}"
          
      # File system tools
      - name: filesystem  
        transport: stdio
        command: ["mcp-server-filesystem", "--root", "/tmp/safe"]
        
      # Database tools
      - name: postgres
        transport: websocket
        url: "ws://localhost:3002/mcp"
        
    agent_permissions:
      alice:
        allowed_servers: ["filesystem"]
      eamonn:
        allowed_servers: ["github", "filesystem", "postgres"]
      patricia:
        allowed_servers: ["filesystem"]
```

### 8.2 Usage in Agent

```python
# Agent using MCP tools
async def agent_task():
    # MCP tools are automatically available
    # They appear with "mcp_" prefix
    
    # Use GitHub MCP tool
    result = await tool_registry.execute_tool(
        "mcp_github_create_issue",
        {
            "repository": "aiwhisperer/aiwhisperer",
            "title": "Test issue",
            "body": "Created via MCP"
        }
    )
    
    # Use filesystem MCP tool  
    content = await tool_registry.execute_tool(
        "mcp_filesystem_read_file",
        {"path": "/tmp/safe/data.txt"}
    )
```

## 9. Performance Considerations

1. **Connection Pooling**: Reuse connections to avoid startup overhead
2. **Tool Caching**: Cache tool definitions to avoid repeated discovery
3. **Async Execution**: All operations are async for non-blocking execution
4. **Timeout Handling**: Implement timeouts for all MCP operations
5. **Resource Cleanup**: Proper cleanup of subprocesses and connections

This technical design provides a comprehensive approach to integrating MCP client capabilities into AIWhisperer, allowing agents to leverage the growing ecosystem of MCP tools while maintaining compatibility with the existing tool system.