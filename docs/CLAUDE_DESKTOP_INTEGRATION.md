# Claude Desktop + AIWhisperer Integration Guide

This guide walks you through setting up AIWhisperer as an MCP server for Claude Desktop, enabling powerful file management and code analysis capabilities directly in Claude.

## Prerequisites

Before you begin, ensure you have:

1. **Claude Desktop** installed (version with MCP support)
2. **Python 3.8+** installed
3. **AIWhisperer** installed:
   ```bash
   pip install ai-whisperer
   # Or from source:
   git clone https://github.com/DeanoC/AIWhisperer.git
   cd AIWhisperer
   pip install -e .
   ```

**Windows Users with WSL**: If you're running Claude Desktop on Windows and AIWhisperer in WSL, see [CLAUDE_DESKTOP_WINDOWS_WSL.md](CLAUDE_DESKTOP_WINDOWS_WSL.md) for specific setup instructions using SSE transport.

## Step 1: Locate Claude Desktop Configuration

Claude Desktop stores its configuration in a platform-specific location:

### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Linux
```
~/.config/Claude/claude_desktop_config.json
```

## Step 2: Configure AIWhisperer MCP Server

Edit the Claude Desktop configuration file to add AIWhisperer:

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
        "--expose-tool", "execute_command",
        "--workspace", "/path/to/your/project"
      ]
    }
  }
}
```

### Important Configuration Notes:

1. **Update the workspace path** to point to your actual project directory
2. **Choose tools carefully** - only expose tools you need
3. **Use absolute paths** for the workspace parameter

## Step 3: Tool Selection Guide

Choose which AIWhisperer tools to expose based on your needs.

**Why Agent Communication Tools?** 
Most AI systems (including Claude) already have excellent file operation capabilities. AIWhisperer's unique value lies in its multi-agent system where specialized agents (Alice, Patricia, Tessa, etc.) can collaborate on complex tasks. By exposing the mailbox and agent tools, you enable Claude to:
- Delegate specialized tasks to the right AIWhisperer agent
- Participate in multi-agent workflows
- Access AIWhisperer's unique planning and RFC systems
- Leverage specialized code analysis tools

### Agent Communication Focus (Recommended)
```json
"args": [
  "--expose-tool", "check_mail",
  "--expose-tool", "send_mail",
  "--expose-tool", "switch_agent",
  "--expose-tool", "create_rfc",
  "--expose-tool", "python_ast_json",
  "--workspace", "/path/to/project"
]
```

### Using Pre-configured Profiles
```json
"args": [
  "--config", "/path/to/AIWhisperer/config/mcp_agent_focused.yaml",
  "--workspace", "/path/to/project"
]
```

### Basic File Operations (If Needed)
```json
"args": [
  "--expose-tool", "read_file",
  "--expose-tool", "list_directory",
  "--workspace", "/path/to/project"
]
```

### Full Development Setup
```json
"args": [
  "--expose-tool", "read_file",
  "--expose-tool", "write_file",
  "--expose-tool", "list_directory",
  "--expose-tool", "search_files",
  "--expose-tool", "execute_command",
  "--expose-tool", "python_executor",
  "--workspace", "/path/to/project"
]
```

### Code Analysis Only
```json
"args": [
  "--expose-tool", "read_file",
  "--expose-tool", "search_files",
  "--expose-tool", "python_ast_json",
  "--expose-tool", "analyze_dependencies",
  "--workspace", "/path/to/project"
]
```

## Step 4: Multiple Project Setup

You can configure multiple AIWhisperer instances for different projects:

```json
{
  "mcpServers": {
    "project-frontend": {
      "command": "aiwhisperer-mcp",
      "args": [
        "--expose-tool", "read_file",
        "--expose-tool", "write_file",
        "--expose-tool", "list_directory",
        "--workspace", "/home/user/projects/my-app/frontend"
      ]
    },
    "project-backend": {
      "command": "aiwhisperer-mcp",
      "args": [
        "--expose-tool", "read_file",
        "--expose-tool", "write_file",
        "--expose-tool", "execute_command",
        "--expose-tool", "python_executor",
        "--workspace", "/home/user/projects/my-app/backend"
      ]
    },
    "documentation": {
      "command": "aiwhisperer-mcp",
      "args": [
        "--expose-tool", "read_file",
        "--expose-tool", "search_files",
        "--workspace", "/home/user/projects/docs"
      ]
    }
  }
}
```

## Step 5: Restart Claude Desktop

After updating the configuration:

1. **Completely quit Claude Desktop** (not just close the window)
2. **Restart Claude Desktop**
3. The MCP servers will start automatically

## Step 6: Verify Integration

In Claude Desktop, you can verify the integration is working:

1. Ask Claude: "What MCP tools do you have available?"
2. Try a simple command: "Can you list the files in the current directory?"
3. Test file reading: "Can you read the README.md file?"

## Usage Examples

Once configured, you can use natural language to interact with your codebase:

### Example 1: Explore Project Structure
```
"Show me the structure of this project"
"What files are in the src directory?"
"Find all Python files in the project"
```

### Example 2: Code Analysis
```
"Search for all TODO comments in the codebase"
"Find all functions that contain 'error' in their name"
"Show me all imports in main.py"
```

### Example 3: File Operations
```
"Read the configuration file"
"Create a new file called test_results.txt with the test output"
"Update the version number in setup.py to 2.0.0"
```

### Example 4: Code Execution
```
"Run the test suite"
"Execute the build script"
"Run python main.py with --help flag"
```

## Security Best Practices

### 1. Limit Tool Exposure

Only expose tools you actually need:

```json
// Good - minimal exposure
"args": [
  "--expose-tool", "read_file",
  "--expose-tool", "list_directory"
]

// Risky - full exposure
"args": [
  "--expose-tool", "execute_command",
  "--expose-tool", "write_file"
]
```

### 2. Use Specific Workspaces

Always specify a workspace directory:

```json
// Good - specific project
"--workspace", "/home/user/projects/my-safe-project"

// Bad - home directory
"--workspace", "/home/user"

// Worst - root directory
"--workspace", "/"
```

### 3. Read-Only Access for Sensitive Projects

For sensitive codebases, use read-only tools:

```json
{
  "mcpServers": {
    "sensitive-project": {
      "command": "aiwhisperer-mcp",
      "args": [
        "--expose-tool", "read_file",
        "--expose-tool", "list_directory",
        "--expose-tool", "search_files",
        "--workspace", "/path/to/sensitive/project"
      ]
    }
  }
}
```

## Troubleshooting

### Issue: "MCP tools not available"

**Solution 1**: Check if AIWhisperer is installed correctly
```bash
which aiwhisperer-mcp
# Should output the path to the executable
```

**Solution 2**: Use full path in configuration
```json
"command": "/usr/local/bin/aiwhisperer-mcp"
// or
"command": "/home/user/.local/bin/aiwhisperer-mcp"
```

**Solution 3**: Use Python module directly
```json
"command": "python",
"args": [
  "-m", "ai_whisperer.mcp.server.runner",
  "--expose-tool", "read_file",
  "--workspace", "/path/to/project"
]
```

### Issue: "Permission denied" errors

**Solution**: Check workspace path and permissions
```bash
# Verify you can access the workspace
ls -la /path/to/your/project

# Check AIWhisperer can read files
python -m ai_whisperer.mcp.server.runner --workspace /path/to/project
```

### Issue: Tools not working as expected

**Solution**: Test AIWhisperer directly
```bash
# Test the MCP server manually
aiwhisperer-mcp --expose-tool read_file --workspace /path/to/project

# In another terminal, send a test request
echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}' | aiwhisperer-mcp
```

### Viewing Logs

Enable debug logging by setting environment variables in the configuration:

```json
{
  "mcpServers": {
    "aiwhisperer": {
      "command": "aiwhisperer-mcp",
      "args": ["--workspace", "/path/to/project"],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Advanced Configuration

### Using a Configuration File

For complex setups, use a configuration file:

1. Create `mcp-config.yaml`:
```yaml
mcp:
  server:
    exposed_tools:
      - read_file
      - write_file
      - list_directory
      - search_files
      - execute_command
    
    resource_permissions:
      - pattern: "**/*.py"
        operations: ["read", "write"]
      - pattern: "**/*.md"
        operations: ["read", "write"]
      - pattern: ".env*"
        operations: []  # Explicitly deny access
```

2. Reference in Claude Desktop config:
```json
{
  "mcpServers": {
    "aiwhisperer": {
      "command": "aiwhisperer-mcp",
      "args": [
        "--config", "/path/to/mcp-config.yaml",
        "--workspace", "/path/to/project"
      ]
    }
  }
}
```

### Environment-Specific Configuration

Use environment variables for flexibility:

```json
{
  "mcpServers": {
    "aiwhisperer": {
      "command": "aiwhisperer-mcp",
      "args": [
        "--workspace", "${HOME}/projects/current"
      ],
      "env": {
        "AIWHISPERER_TOOLS": "read_file,list_directory,search_files"
      }
    }
  }
}
```

## Tips and Tricks

### 1. Quick Project Switching

Create aliases for different projects:

```json
{
  "mcpServers": {
    "work": {
      "command": "aiwhisperer-mcp",
      "args": ["--workspace", "/home/user/work/current-project"]
    },
    "personal": {
      "command": "aiwhisperer-mcp",
      "args": ["--workspace", "/home/user/personal/side-project"]
    }
  }
}
```

### 2. Safe Exploration Mode

For exploring unfamiliar codebases:

```json
"args": [
  "--expose-tool", "read_file",
  "--expose-tool", "list_directory",
  "--expose-tool", "search_files",
  "--expose-tool", "workspace_stats"
]
```

### 3. Development Workflow

For active development:

```json
"args": [
  "--expose-tool", "read_file",
  "--expose-tool", "write_file",
  "--expose-tool", "list_directory",
  "--expose-tool", "search_files",
  "--expose-tool", "execute_command",
  "--expose-tool", "python_executor"
]
```

## Conclusion

You now have AIWhisperer integrated with Claude Desktop! This powerful combination allows you to:

- 📁 Browse and read files naturally
- 🔍 Search codebases efficiently  
- ✏️ Make code changes with AI assistance
- 🚀 Execute commands and scripts
- 📊 Analyze code structure and dependencies

Remember to always follow security best practices and only expose the tools and directories you need.

For more help:
- [AIWhisperer Documentation](https://github.com/DeanoC/AIWhisperer)
- [MCP Specification](https://modelcontextprotocol.com)
- [Report Issues](https://github.com/DeanoC/AIWhisperer/issues)