# AI Whisperer

[![Python application](https://github.com/DeanoC/AIWhisperer/actions/workflows/python-app.yml/badge.svg)](https://github.com/DeanoC/AIWhisperer/actions/workflows/python-app.yml)

AI Whisperer is a AI development tool that takes requirements and implements them. It features both command-line and interactive web interfaces for AI-powered software development workflows.

## Key Features

* **Dual Interface**: Command-line for batch processing and interactive web UI for real-time development
* **Multi-Agent System**: Specialized AI agents (Alice, Patricia, Tessa) for different development tasks
* **Requirements Processing**: Converts Markdown requirements into structured JSON task plans
* **Real-time Collaboration**: WebSocket-based communication for instant AI responses
* **OpenRouter Integration**: Access to multiple AI models through a unified API
* **MCP Server**: Expose AIWhisperer tools to Claude Desktop and other MCP clients
* **Test-Driven Development**: Built with TDD methodology using pytest

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js (for web interface)
- OpenRouter API key

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd AIWhisperer
   
   # Setup virtual environment (or use ./setup_worktree_venv.sh for worktrees)
   python3.12 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   
   pip install -r requirements.txt
   ```

2. **Configure API access:**
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml and add your OpenRouter API key
   ```

3. **Run interactive mode (recommended):**
   ```bash
   # Backend
   python -m interactive_server.main
   
   # Frontend (separate terminal)
   cd frontend && npm install && npm start
   ```
   
   Open http://localhost:3000 in your browser.

### Alternative: Batch Mode
```bash
# Run batch scripts
python -m ai_whisperer.cli --config config.yaml batch scripts/script_name.json
```

## MCP Server (Claude Desktop Integration)

AIWhisperer can run as an MCP server, allowing Claude Desktop and other MCP clients to use its tools:

```bash
# Standalone MCP server
aiwhisperer-mcp --workspace /path/to/project

# With specific tools
aiwhisperer-mcp --expose-tool read_file --expose-tool search_files --workspace /path/to/project

# Run alongside interactive server
python -m interactive_server.main --mcp --mcp-port 3001

# Or use the convenience script
./start_with_mcp.sh
```

### Development Mode with MCP Proxy

For development, use the MCP proxy to maintain Claude CLI connections during AIWhisperer restarts:

```bash
# 1. Start AIWhisperer with MCP server
python -m interactive_server.main --config config/main.yaml --mcp_server_enable --mcp_server_port 8002 --mcp_server_transport sse

# 2. Start the MCP proxy (in another terminal)
./start_mcp_proxy.sh

# 3. Configure Claude CLI to connect to the proxy:
#    http://localhost:3002/sse
```

**Benefits:**
- ✅ Claude CLI stays connected during AIWhisperer restarts
- ✅ Automatic reconnection when AIWhisperer comes back online  
- ✅ Seamless development workflow without session interruption
- ✅ All MCP tools work transparently through the proxy

The MCP server can also be controlled via the web interface when running the interactive server.

See [docs/CLAUDE_DESKTOP_INTEGRATION.md](docs/CLAUDE_DESKTOP_INTEGRATION.md) for setup instructions.

## Agent System

- **Alice the Assistant** - General development support and guidance
- **Patricia the Planner** - Creates structured implementation plans from requirements  
- **Tessa the Tester** - Generates comprehensive test suites and test plans

Switch agents on-the-fly in the interactive interface for specialized help.

## Development

For development setup, testing, and architecture details, see:

- **[CODE_MAP.md](CODE_MAP.md)** - Complete codebase structure and module documentation
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Detailed getting started guide
- **[docs/BATCH_MODE_USAGE_FOR_AI.md](docs/BATCH_MODE_USAGE_FOR_AI.md)** - Batch processing guide
- **[docs/MCP_USER_GUIDE.md](docs/MCP_USER_GUIDE.md)** - MCP server user guide
- **[docs/MCP_API_REFERENCE.md](docs/MCP_API_REFERENCE.md)** - MCP API technical reference

### Quick Development Commands

```bash
# Run tests
pytest                          # All tests
pytest -m "not performance"     # Skip slow tests

# Code quality (required for CI)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## Architecture

AI Whisperer uses a modern, stateless architecture:

* **Backend**: FastAPI server with WebSocket support
* **Frontend**: React TypeScript application  
* **Agent System**: Modular design with specialized AI agents
* **Session Management**: Isolated sessions for concurrent users
* **Tool System**: Pluggable tools for file operations and command execution

For detailed architecture information, see [CODE_MAP.md](CODE_MAP.md) and [docs/architecture/](docs/architecture/).

## Project Development