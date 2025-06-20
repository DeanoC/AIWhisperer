# AIWhisperer MCP Server User Guide

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Available Tools](#available-tools)
6. [Resource Access](#resource-access)
7. [Transport Options](#transport-options)
8. [Security](#security)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

## Overview

AIWhisperer can function as an MCP (Model Context Protocol) server, exposing its powerful development tools to MCP-compatible clients like Claude Desktop. This allows you to use AIWhisperer's file management, code search, and execution capabilities directly from your AI assistant.

### What is MCP?

The Model Context Protocol (MCP) is a standardized protocol for communication between AI applications and external tools. It provides:

- **Standardized Tool Interface**: Common format for tool definitions and invocations
- **Resource Management**: Secure access to files and directories
- **Multiple Transport Options**: Support for stdio and WebSocket communications
- **Security Model**: Permission-based access control

## Installation

AIWhisperer's MCP server is included in the standard installation. No additional dependencies are required for basic stdio transport.

### Prerequisites

- Python 3.8 or higher
- AIWhisperer installed and configured
- For WebSocket transport: `pip install aiohttp`

### Verifying Installation

```bash
# Check if the MCP server is available
aiwhisperer-mcp --help

# Or use the Python module directly
python -m ai_whisperer.mcp.server.runner --help
```

### Running with Interactive Server

AIWhisperer can run the MCP server alongside the main interactive server, allowing you to use both the web interface and MCP capabilities simultaneously:

```bash
# Start both servers together
python -m interactive_server.main --mcp --mcp-port 3001

# With custom tools
python -m interactive_server.main --mcp --mcp-tools read_file write_file search_files

# Or use the convenience script
./start_with_mcp.sh
```

## Quick Start

### 1. Basic Server Start

Start the MCP server with default settings:

```bash
aiwhisperer-mcp
```

This starts the server with:
- STDIO transport (for CLI integration)
- Default tool set (read_file, write_file, list_directory, search_files, get_file_content, execute_command)
- Current directory as workspace

### 2. Expose Specific Tools

Choose which tools to expose:

```bash
aiwhisperer-mcp --expose-tool read_file --expose-tool list_directory
```

### 3. Set Workspace Directory

Specify the workspace for file operations:

```bash
aiwhisperer-mcp --workspace /path/to/your/project
```

## Configuration

### Command-Line Options

```bash
aiwhisperer-mcp [OPTIONS]

Options:
  --config PATH              Path to configuration file
  --transport [stdio|websocket]  Transport type (default: stdio)
  --port INTEGER            Port for WebSocket transport (default: 3000)
  --expose-tool TEXT        Tool to expose (can be specified multiple times)
  --workspace PATH          Workspace directory for file operations
  --help                    Show this message and exit
```

### Configuration File

Create a YAML configuration file for advanced settings:

```yaml
# mcp-server.yaml
mcp:
  server:
    transport: stdio
    server_name: "my-aiwhisperer"
    server_version: "1.0.0"
    
    # Tools to expose
    exposed_tools:
      - read_file
      - write_file
      - list_directory
      - search_files
      - get_file_content
      - execute_command
      - python_executor
      - web_search
    
    # Resource permissions
    resource_permissions:
      - pattern: "**/*.py"
        operations: ["read"]
      - pattern: "**/*.md"
        operations: ["read", "write"]
      - pattern: "config/**/*"
        operations: ["read"]
      - pattern: "output/**/*"
        operations: ["read", "write"]
```

Use the configuration file:

```bash
aiwhisperer-mcp --config mcp-server.yaml
```

## Tool Selection Strategy

### Why Selective Tool Exposure?

Most AI systems already have their own file operations, making AIWhisperer's generic file tools redundant. Instead, focus on exposing AIWhisperer's unique capabilities:

1. **Agent Communication** - Mailbox system for inter-agent messaging
2. **Planning Tools** - RFC and plan generation unique to AIWhisperer
3. **Code Analysis** - Advanced AST parsing and analysis
4. **Session Management** - Multi-agent session coordination

### Recommended Configurations

#### Agent-Focused Configuration
```bash
# Use the agent-focused configuration
aiwhisperer-mcp --config config/mcp_agent_focused.yaml

# Or specify key tools manually
aiwhisperer-mcp \
  --expose-tool check_mail \
  --expose-tool send_mail \
  --expose-tool switch_agent \
  --expose-tool create_rfc \
  --expose-tool python_ast_json
```

#### Minimal Configuration
```bash
# Absolute minimum for agent interaction
aiwhisperer-mcp --config config/mcp_minimal.yaml
```

## Available Tools

AIWhisperer exposes various tools through MCP. Here are the categories and most useful tools:

### Agent Communication Tools (Unique to AIWhisperer)

#### check_mail
Check messages in the agent's mailbox.

**Parameters:**
- `sender` (string, optional): Filter by sender agent
- `status` (string, optional): Filter by status ("unread", "read", "all")

**Example:**
```json
{
  "name": "check_mail",
  "arguments": {
    "status": "unread"
  }
}
```

#### send_mail
Send a message to another agent or user.

**Parameters:**
- `to` (string, required): Recipient agent name
- `subject` (string, required): Message subject
- `body` (string, required): Message content
- `priority` (string, optional): Message priority ("high", "normal", "low")

**Example:**
```json
{
  "name": "send_mail",
  "arguments": {
    "to": "alice",
    "subject": "Code Review Request",
    "body": "Please review the authentication module changes.",
    "priority": "high"
  }
}
```

#### switch_agent
Switch the active agent in the current session.

**Parameters:**
- `agent_name` (string, required): Name of agent to switch to
- `reason` (string, optional): Reason for switching

**Example:**
```json
{
  "name": "switch_agent",
  "arguments": {
    "agent_name": "patricia",
    "reason": "Need planning expertise for RFC creation"
  }
}
```

### Planning and RFC Tools

#### create_rfc
Create a Request for Comments document.

**Parameters:**
- `title` (string, required): RFC title
- `content` (string, required): RFC content in Markdown
- `tags` (array, optional): Tags for categorization

#### create_plan_from_rfc
Convert an RFC into an executable plan.

**Parameters:**
- `rfc_path` (string, required): Path to RFC file
- `output_path` (string, optional): Where to save the plan

### Code Analysis Tools

#### python_ast_json
Parse Python code into AST JSON format.

**Parameters:**
- `source_code` (string): Python source code to parse
- `file_path` (string): Path to Python file (alternative to source_code)

### File Operations (Standard)

#### read_file
Read contents of a file within the workspace.

**Parameters:**
- `path` (string, required): File path relative to workspace
- `start_line` (integer, optional): Starting line number
- `end_line` (integer, optional): Ending line number

**Example:**
```json
{
  "name": "read_file",
  "arguments": {
    "path": "src/main.py",
    "start_line": 10,
    "end_line": 50
  }
}
```

#### write_file
Write or update a file in the workspace.

**Parameters:**
- `path` (string, required): File path relative to workspace
- `content` (string, required): File content to write

**Example:**
```json
{
  "name": "write_file",
  "arguments": {
    "path": "output/results.txt",
    "content": "Analysis complete\n"
  }
}
```

#### list_directory
List contents of a directory.

**Parameters:**
- `path` (string, optional): Directory path (default: ".")
- `recursive` (boolean, optional): Include subdirectories
- `max_depth` (integer, optional): Maximum recursion depth
- `include_hidden` (boolean, optional): Include hidden files

**Example:**
```json
{
  "name": "list_directory",
  "arguments": {
    "path": "src",
    "recursive": true,
    "max_depth": 2
  }
}
```

### Code Search and Analysis

#### search_files
Search for patterns in files.

**Parameters:**
- `pattern` (string, required): Search pattern (regex supported)
- `search_type` (string, optional): "content" or "filename"
- `file_types` (array, optional): File extensions to search
- `max_results` (integer, optional): Maximum results to return

**Example:**
```json
{
  "name": "search_files",
  "arguments": {
    "pattern": "TODO|FIXME",
    "file_types": [".py", ".js"],
    "max_results": 20
  }
}
```

#### get_file_content
Advanced file reading with preview mode.

**Parameters:**
- `path` (string, required): File path
- `preview_only` (boolean, optional): Show only first/last lines
- `start_line` (integer, optional): Starting line
- `end_line` (integer, optional): Ending line

### Code Execution

#### execute_command
Execute shell commands in the workspace.

**Parameters:**
- `command` (string, required): Command to execute
- `working_directory` (string, optional): Working directory

**Example:**
```json
{
  "name": "execute_command",
  "arguments": {
    "command": "python test_script.py",
    "working_directory": "tests"
  }
}
```

#### python_executor
Execute Python code snippets.

**Parameters:**
- `code` (string, required): Python code to execute
- `timeout` (integer, optional): Execution timeout in seconds

### Web Tools

#### web_search
Search the web for information.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results

## Resource Access

The MCP server provides controlled access to workspace files as resources.

### Listing Resources

Resources are automatically discovered based on permissions:

```yaml
resource_permissions:
  - pattern: "**/*.py"
    operations: ["read"]
  - pattern: "docs/**/*.md"
    operations: ["read", "write"]
```

### Resource URIs

Resources are identified by file URIs:
- `file://path/to/file.py` - Relative to workspace
- `file:///absolute/path/file.py` - Absolute path (if permitted)

### Operations

- **read**: Read file contents
- **write**: Create or update files
- **subscribe**: (Not yet implemented) Watch for changes

## Transport Options

### STDIO Transport (Default)

Best for CLI integration and subprocess communication. **Currently the only transport supported by Claude Desktop.**

```bash
# Start with stdio transport
aiwhisperer-mcp --transport stdio
```

**Advantages:**
- Simple setup
- No network exposure
- Works with subprocess-based clients
- Native support in Claude Desktop

**Limitations:**
- Cannot work across system boundaries (e.g., Windows to WSL)
- Requires direct process spawning
- No remote access capability

**Use Cases:**
- Claude Desktop integration (same OS only)
- CLI-based MCP clients
- Secure local operations

### WebSocket Transport

Production-ready WebSocket implementation for network access.

```bash
# Start with WebSocket transport
aiwhisperer-mcp --transport websocket --port 3001
```

**Features:**
- Network accessible
- Multiple concurrent connections
- Real-time bidirectional communication
- Connection health monitoring with heartbeat/ping-pong
- Request timeout handling
- Message queuing for reliability
- Connection limits and statistics
- Graceful shutdown handling
- Compression support

**Use Cases:**
- Web-based AI assistants
- Remote development environments
- Multi-user scenarios
- Production deployments

**Configuration:**
```yaml
mcp:
  server:
    transport: websocket
    ws_max_connections: 100
    ws_heartbeat_interval: 30.0
    ws_heartbeat_timeout: 60.0
    ws_request_timeout: 300.0
    ws_enable_compression: true
```

### Server-Sent Events (SSE) Transport

One-way server-to-client communication with HTTP POST for requests. **Ready for future network-based MCP clients.**

```bash
# Start with SSE transport
aiwhisperer-mcp --transport sse --port 3001

# For network access (bind to all interfaces)
aiwhisperer-mcp --config config/mcp_sse_windows.yaml
```

**Features:**
- Simpler than WebSocket for one-way communication
- Built-in CORS support
- Automatic reconnection in browsers
- Works through proxies and firewalls
- Cross-platform network communication

**Endpoints:**
- `/mcp/sse` - SSE event stream
- `/mcp/request` - HTTP POST for requests
- `/mcp/health` - Health check

**Note:** SSE transport is fully implemented and tested but not yet supported by Claude Desktop. It's available for other MCP clients or future Claude Desktop versions.

**Client Example:**
```javascript
// Connect to SSE
const eventSource = new EventSource('http://localhost:3001/mcp/sse');
let connectionId;

eventSource.addEventListener('connection', (e) => {
  const data = JSON.parse(e.data);
  connectionId = data.connectionId;
});

// Send request via POST
fetch('http://localhost:3001/mcp/request', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Connection-Id': connectionId
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/list',
    params: {},
    id: 1
  })
});
```

**Note:** All network transports require `aiohttp` package: `pip install aiohttp`

## Security

### Permission Model

AIWhisperer MCP server implements a permission-based security model:

1. **Tool Permissions**: Only explicitly exposed tools are available
2. **Resource Permissions**: File access controlled by glob patterns
3. **Workspace Isolation**: Operations confined to workspace directory

### Best Practices

1. **Limit Tool Exposure**: Only expose tools you need
   ```bash
   aiwhisperer-mcp --expose-tool read_file --expose-tool list_directory
   ```

2. **Restrict File Access**: Use specific permission patterns
   ```yaml
   resource_permissions:
     - pattern: "src/**/*.py"
       operations: ["read"]
     - pattern: "tests/**/*.py"
       operations: ["read"]
   ```

3. **Set Explicit Workspace**: Don't use system root
   ```bash
   aiwhisperer-mcp --workspace /home/user/safe-project
   ```

4. **Use STDIO for Local**: Prefer stdio transport for local use
   ```bash
   aiwhisperer-mcp --transport stdio
   ```

## Troubleshooting

### Common Issues

#### 1. Server Won't Start

**Problem**: `aiwhisperer-mcp: command not found`

**Solution**: Ensure AIWhisperer is properly installed and the script is in your PATH:
```bash
# Install AIWhisperer
pip install ai-whisperer

# Or use Python module directly
python -m ai_whisperer.mcp.server.runner
```

#### 2. Permission Denied Errors

**Problem**: "Access denied to resource"

**Solution**: Check resource permissions in configuration:
```yaml
resource_permissions:
  - pattern: "path/to/files/*"
    operations: ["read", "write"]
```

#### 3. Tool Not Found

**Problem**: "Tool 'tool_name' not found"

**Solution**: Ensure tool is exposed:
```bash
aiwhisperer-mcp --expose-tool tool_name
```

#### 4. WebSocket Connection Failed

**Problem**: Cannot connect to WebSocket server

**Solution**: 
- Check if aiohttp is installed: `pip install aiohttp`
- Verify port is not in use: `lsof -i :3000`
- Check firewall settings

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set log level
export LOG_LEVEL=DEBUG
aiwhisperer-mcp

# Or redirect logs
aiwhisperer-mcp 2>mcp-debug.log
```

## Examples

### Example 1: Claude Desktop Integration

Add to Claude Desktop's MCP configuration:

```json
{
  "mcpServers": {
    "aiwhisperer": {
      "command": "aiwhisperer-mcp",
      "args": [
        "--expose-tool", "read_file",
        "--expose-tool", "write_file",
        "--expose-tool", "list_directory",
        "--expose-tool", "search_files",
        "--workspace", "/path/to/your/project"
      ]
    }
  }
}
```

### Example 2: Python Development Setup

Configuration for Python development:

```bash
aiwhisperer-mcp \
  --expose-tool read_file \
  --expose-tool write_file \
  --expose-tool list_directory \
  --expose-tool search_files \
  --expose-tool python_executor \
  --expose-tool execute_command \
  --workspace ~/projects/my-python-app
```

### Example 3: Read-Only Documentation Server

Safe configuration for documentation access:

```yaml
# docs-server.yaml
mcp:
  server:
    exposed_tools:
      - read_file
      - list_directory
      - search_files
    
    resource_permissions:
      - pattern: "**/*.md"
        operations: ["read"]
      - pattern: "**/*.rst"
        operations: ["read"]
      - pattern: "docs/**/*"
        operations: ["read"]
```

```bash
aiwhisperer-mcp --config docs-server.yaml --workspace ~/projects/docs
```

### Example 4: Web Development with Live Preview

```bash
aiwhisperer-mcp \
  --transport websocket \
  --port 3001 \
  --expose-tool read_file \
  --expose-tool write_file \
  --expose-tool execute_command \
  --workspace ~/projects/web-app
```

## Monitoring and Logging

AIWhisperer's MCP server includes comprehensive monitoring and logging capabilities for production deployments.

### Metrics Collection

The server automatically tracks:
- Request counts and latencies
- Error rates and types
- Tool execution times
- Transport-specific metrics (connections, messages, bytes)
- Slow request detection

Access metrics via MCP:
```json
{
  "jsonrpc": "2.0",
  "method": "monitoring/metrics",
  "params": {},
  "id": 1
}
```

### Health Checks

Get server health status:
```json
{
  "jsonrpc": "2.0",
  "method": "monitoring/health",
  "params": {},
  "id": 1
}
```

Response includes:
- Overall health status (healthy/degraded/unhealthy)
- Uptime information
- Error rates
- Active connections
- Average latency

### Structured Logging

Enable JSON logging for production:
```yaml
mcp:
  server:
    log_level: INFO
    log_file: /var/log/aiwhisperer/mcp.json
    enable_json_logging: true
```

Log entries include:
- Structured JSON format
- Request tracking with IDs
- Duration measurements
- Error details with stack traces
- Transport events

### Audit Logging

Track all MCP operations:
```yaml
mcp:
  server:
    enable_audit_log: true
    audit_log_file: /var/log/aiwhisperer/mcp-audit.json
```

Audit logs capture:
- All requests with parameters (sensitive data redacted)
- User/connection information
- Execution results
- Timing information

### Performance Monitoring

Configure slow request detection:
```yaml
mcp:
  server:
    slow_request_threshold_ms: 5000
    metrics_retention_minutes: 60
```

### Monitoring Dashboard Example

```python
import asyncio
import json

async def monitor_mcp_server(url):
    """Monitor MCP server health."""
    while True:
        # Get health status
        health = await mcp_request("monitoring/health", {})
        print(f"Status: {health['status']}")
        print(f"Uptime: {health['uptime']}")
        print(f"Error Rate: {health['metrics']['error_rate']}")
        
        # Get detailed metrics
        if health['status'] != 'healthy':
            metrics = await mcp_request("monitoring/metrics", {})
            print(f"Recent errors: {metrics['recent_errors']}")
            print(f"Slow requests: {metrics['slow_requests']}")
            
        await asyncio.sleep(30)
```

## Controlling MCP via Web Interface

When running AIWhisperer's interactive server, you can control the MCP server through the web interface or programmatically via WebSocket:

### Starting MCP Server

Send a JSON-RPC request to start the MCP server:

```javascript
// Connect to AIWhisperer interactive server
const ws = new WebSocket('ws://localhost:8000/ws');

// Start MCP server
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  method: "mcp.start",
  params: {
    transport: "websocket",
    port: 3001,
    exposed_tools: ["read_file", "write_file", "search_files"],
    workspace: "/path/to/project"
  },
  id: 1
}));
```

### Checking MCP Status

```javascript
// Check if MCP server is running
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  method: "mcp.status",
  params: {},
  id: 2
}));

// Response:
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "running": true,
    "transport": "websocket",
    "port": 3001,
    "server_url": "ws://localhost:3001/mcp",
    "exposed_tools": ["read_file", "write_file", "search_files"],
    "health": "healthy",
    "uptime": "0:05:23"
  }
}
```

### Stopping MCP Server

```javascript
// Stop MCP server
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  method: "mcp.stop",
  params: {},
  id: 3
}));
```

## Advanced Usage

### Custom Tool Sets

Create a configuration with specific tool combinations:

```yaml
# analysis-tools.yaml
mcp:
  server:
    exposed_tools:
      - read_file
      - search_files
      - python_ast_json  # Parse Python AST
      - analyze_dependencies  # Analyze project dependencies
      - workspace_stats  # Get workspace statistics
```

### Batch Operations

Use MCP client libraries to perform batch operations:

```python
# Example using MCP client
async with MCPClient(config) as client:
    # List all Python files
    files = await client.call_tool("search_files", {
        "pattern": "*.py",
        "search_type": "filename"
    })
    
    # Read and analyze each file
    for file in files:
        content = await client.call_tool("read_file", {
            "path": file["path"]
        })
        # Process content...
```

## Next Steps

1. **Explore Available Tools**: Run `aiwhisperer-mcp` and use an MCP client to discover all available tools
2. **Customize Permissions**: Create a configuration file tailored to your security needs
3. **Integrate with AI Tools**: Add AIWhisperer to your preferred AI assistant
4. **Contribute**: Help improve AIWhisperer's MCP implementation on GitHub

For more information:
- [MCP Specification](https://modelcontextprotocol.com)
- [AIWhisperer Documentation](https://github.com/DeanoC/AIWhisperer)
- [Report Issues](https://github.com/DeanoC/AIWhisperer/issues)