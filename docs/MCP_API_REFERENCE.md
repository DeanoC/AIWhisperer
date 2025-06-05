# AIWhisperer MCP API Reference

## Protocol Overview

AIWhisperer implements the Model Context Protocol (MCP) version 2024-11-05, providing JSON-RPC 2.0 based communication for tool execution and resource management.

## Transport Layers

### STDIO Transport

- **Format**: Line-delimited JSON over stdin/stdout
- **Encoding**: UTF-8
- **Message Termination**: Newline character (`\n`)

Example:
```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}},"id":1}' | aiwhisperer-mcp
```

### WebSocket Transport

- **Protocol**: WebSocket (ws://)
- **Default Port**: 3000
- **Endpoint**: `/mcp`
- **Message Format**: JSON text frames

Example:
```javascript
const ws = new WebSocket('ws://localhost:3000/mcp');
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  method: "initialize",
  params: { protocolVersion: "2024-11-05", capabilities: {} },
  id: 1
}));
```

## Core Methods

### initialize

Initialize the MCP session and perform capability negotiation.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {
        "subscribe": false
      }
    },
    "clientInfo": {
      "name": "example-client",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {
        "subscribe": false,
        "write": true
      },
      "prompts": {}
    },
    "serverInfo": {
      "name": "aiwhisperer-mcp",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### ping

Health check endpoint.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "ping",
  "params": {},
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "pong": true
  },
  "id": 2
}
```

## Tool Methods

### tools/list

List all available tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 3
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "read_file",
        "description": "Reads the content of a specified file within the workspace directory.",
        "inputSchema": {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "type": "object",
          "properties": {
            "path": {
              "type": "string",
              "description": "The file path relative to the workspace"
            },
            "start_line": {
              "type": "integer",
              "description": "Line number to start reading from (1-indexed)"
            },
            "end_line": {
              "type": "integer",
              "description": "Line number to stop reading at (inclusive)"
            }
          },
          "required": ["path"],
          "additionalProperties": false
        }
      }
    ]
  },
  "id": 3
}
```

### tools/call

Execute a tool with arguments.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "README.md"
    }
  },
  "id": 4
}
```

**Response (Success):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "# AIWhisperer\n\nAn AI-powered development assistant..."
      }
    ]
  },
  "id": 4
}
```

**Response (Error):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "isError": true,
    "content": [
      {
        "type": "text",
        "text": "Tool execution failed: File not found: README.md"
      }
    ]
  },
  "id": 4
}
```

## Resource Methods

### resources/list

List available resources (files) in the workspace.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "resources/list",
  "params": {},
  "id": 5
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "resources": [
      {
        "uri": "file://src/main.py",
        "name": "src/main.py",
        "mimeType": "text/x-python"
      },
      {
        "uri": "file://README.md",
        "name": "README.md",
        "mimeType": "text/markdown"
      }
    ]
  },
  "id": 5
}
```

### resources/read

Read resource contents.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "file://src/main.py"
  },
  "id": 6
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "contents": [
      {
        "uri": "file://src/main.py",
        "mimeType": "text/x-python",
        "text": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello, World!')\n"
      }
    ]
  },
  "id": 6
}
```

### resources/write

Write or update a resource.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "resources/write",
  "params": {
    "uri": "file://output/results.txt",
    "contents": [
      {
        "text": "Test results:\nAll tests passed!"
      }
    ]
  },
  "id": 7
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {},
  "id": 7
}
```

## Prompt Methods

### prompts/list

List available prompt templates.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "prompts/list",
  "params": {},
  "id": 8
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "prompts": [
      {
        "name": "alice_assistant",
        "description": "You are Alice, AIWhisperer's primary assistant. Follow ALL instructions in core.md.",
        "category": "agent",
        "arguments": [
          {
            "name": "task",
            "description": "The task or question to process",
            "required": true
          },
          {
            "name": "context",
            "description": "Additional context for the prompt",
            "required": false
          }
        ]
      }
    ]
  },
  "id": 8
}
```

**Filter by Category:**
```json
{
  "jsonrpc": "2.0",
  "method": "prompts/list",
  "params": {
    "category": "agent"
  },
  "id": 9
}
```

### prompts/get

Get a specific prompt template with optional argument substitution.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "prompts/get",
  "params": {
    "name": "alice_assistant",
    "arguments": {
      "task": "Write a Python function",
      "context": "The function should calculate fibonacci numbers"
    }
  },
  "id": 10
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "name": "alice_assistant",
    "description": "You are Alice, AIWhisperer's primary assistant.",
    "category": "agent",
    "content": "# Alice - AI Assistant\n\nYou are Alice...\n\nYour task is: Write a Python function\nContext: The function should calculate fibonacci numbers",
    "arguments": [
      {
        "name": "task",
        "description": "The task or question to process",
        "required": true
      }
    ],
    "raw_content": "# Alice - AI Assistant\n\nYou are Alice...\n\nYour task is: {{task}}\nContext: {{context}}"
  },
  "id": 10
}
```

## Tool Schemas

### File Operation Tools

#### read_file
```json
{
  "name": "read_file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "File path relative to workspace"
      },
      "start_line": {
        "type": "integer",
        "description": "Starting line number (1-indexed)"
      },
      "end_line": {
        "type": "integer",
        "description": "Ending line number (inclusive)"
      }
    },
    "required": ["path"]
  }
}
```

#### write_file
```json
{
  "name": "write_file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "File path relative to workspace"
      },
      "content": {
        "type": "string",
        "description": "Content to write to the file"
      }
    },
    "required": ["path", "content"]
  }
}
```

#### list_directory
```json
{
  "name": "list_directory",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Directory path relative to workspace",
        "default": "."
      },
      "recursive": {
        "type": "boolean",
        "description": "Include subdirectories",
        "default": false
      },
      "max_depth": {
        "type": "integer",
        "description": "Maximum recursion depth"
      },
      "include_hidden": {
        "type": "boolean",
        "description": "Include hidden files",
        "default": false
      }
    }
  }
}
```

### Search Tools

#### search_files
```json
{
  "name": "search_files",
  "inputSchema": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "Search pattern (regex)"
      },
      "search_type": {
        "type": "string",
        "enum": ["content", "filename"],
        "default": "content"
      },
      "file_types": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "File extensions to search"
      },
      "max_results": {
        "type": "integer",
        "default": 50
      },
      "ignore_case": {
        "type": "boolean",
        "default": true
      },
      "search_path": {
        "type": "string",
        "description": "Directory to search in"
      }
    },
    "required": ["pattern"]
  }
}
```

### Execution Tools

#### execute_command
```json
{
  "name": "execute_command",
  "inputSchema": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "Shell command to execute"
      },
      "working_directory": {
        "type": "string",
        "description": "Working directory for command execution"
      },
      "timeout": {
        "type": "integer",
        "description": "Timeout in seconds",
        "default": 30
      }
    },
    "required": ["command"]
  }
}
```

#### python_executor
```json
{
  "name": "python_executor",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "string",
        "description": "Python code to execute"
      },
      "timeout": {
        "type": "integer",
        "description": "Execution timeout in seconds",
        "default": 30
      }
    },
    "required": ["code"]
  }
}
```

## Error Codes

AIWhisperer MCP server uses standard JSON-RPC 2.0 error codes:

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid request | Missing required fields |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Server error |

Additional application-specific errors may be returned in the error data field.

## Security Considerations

### Permission Model

Resource access is controlled by glob patterns:

```yaml
resource_permissions:
  - pattern: "**/*.py"
    operations: ["read"]
  - pattern: "output/**/*"
    operations: ["read", "write"]
  - pattern: ".env*"
    operations: []  # Explicitly deny
```

### Tool Exposure

Only explicitly exposed tools are available:

```bash
aiwhisperer-mcp --expose-tool read_file --expose-tool list_directory
```

### Context Injection

Tools receive context about the MCP session:

```python
{
  "_agent_id": "mcp_client",
  "_from_agent": "mcp",
  "_session_id": "mcp_session_123",
  # ... user arguments
}
```

## Implementation Notes

### Content Format

All tool results are returned in MCP content format:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Result text here"
    }
  ]
}
```

### Binary Data

Binary resources use base64 encoding:

```json
{
  "contents": [
    {
      "uri": "file://image.png",
      "mimeType": "image/png",
      "blob": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
    }
  ]
}
```

### Streaming

The current implementation does not support streaming responses. Large outputs are returned in a single response.

### Concurrency

The STDIO transport processes requests sequentially. The WebSocket transport can handle concurrent requests from multiple connections.

## Client Examples

### Python Client

```python
import json
import subprocess

# Start MCP server
proc = subprocess.Popen(
    ["aiwhisperer-mcp", "--expose-tool", "read_file"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Send request
request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "read_file",
        "arguments": {"path": "test.py"}
    },
    "id": 1
}

proc.stdin.write(json.dumps(request) + '\n')
proc.stdin.flush()

# Read response
response = json.loads(proc.stdout.readline())
print(response["result"]["content"][0]["text"])
```

### JavaScript Client (WebSocket)

```javascript
class MCPClient {
  constructor(url) {
    this.ws = new WebSocket(url);
    this.id = 0;
    this.pending = new Map();
    
    this.ws.onmessage = (event) => {
      const response = JSON.parse(event.data);
      const handler = this.pending.get(response.id);
      if (handler) {
        handler(response);
        this.pending.delete(response.id);
      }
    };
  }
  
  async call(method, params) {
    const id = ++this.id;
    const request = {
      jsonrpc: "2.0",
      method,
      params,
      id
    };
    
    return new Promise((resolve) => {
      this.pending.set(id, resolve);
      this.ws.send(JSON.stringify(request));
    });
  }
}

// Usage
const client = new MCPClient('ws://localhost:3000/mcp');
await client.call('initialize', {
  protocolVersion: '2024-11-05',
  capabilities: {}
});

const result = await client.call('tools/call', {
  name: 'read_file',
  arguments: { path: 'README.md' }
});
```

## Version History

- **1.0.0** - Initial MCP implementation
  - STDIO and WebSocket transports
  - Core tool set
  - Resource management
  - Basic security model