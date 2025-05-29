# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIWhisperer is a Python CLI tool that uses AI models via OpenRouter to automate software development planning and execution. It converts markdown requirements into structured JSON task plans, generates subtasks, and executes them through an AI-powered runner. The project provides both CLI and web-based interfaces.

## Key Architecture Components

### Core Systems
- **AI Loop** (`ai_whisperer/ai_loop/`): Manages AI interactions and conversation flow with delegate-based event handling
- **Agent System** (`ai_whisperer/agents/`): Modular handlers for different task types (code generation, planning, validation)
- **Execution Engine** (`ai_whisperer/execution_engine.py`): Orchestrates plan execution with state management
- **Tool Registry** (`ai_whisperer/tools/`): Pluggable tools for file operations and command execution
- **Postprocessing Pipeline** (`postprocessing/`): Cleans and enhances AI-generated content
- **Config Management** (`@ai_whisperer/config.py`): Handles API keys and other important configuration items

### Interactive Mode
- **Backend** (`interactive_server/`): FastAPI server with WebSocket support for real-time communication
- **Frontend** (`frontend/`): React TypeScript app providing chat interface
- **Session Management**: Handles concurrent users with isolated sessions

## Common Development Commands

### Setup and Dependencies
```bash
# Create virtual environment (Python 3.12)
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Frontend setup
cd frontend && npm install
```

### Running Tests
```bash
# Run all tests
pytest

# Skip performance tests
pytest -m "not performance"

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest -k "test_agent"  # Run tests matching pattern
```

### Code Quality
```bash
# Format code (project standard)
black . --line-length 120 --skip-magic-trailing-comma

# The project uses pytest.ini with -W error to treat warnings as errors
```

### Running the Application
```bash
# Generate initial plan from requirements
python -m ai_whisperer.main generate initial-plan requirements.md

# List available models
python -m ai_whisperer.main list-models --config config.yaml --output-csv models.csv

# Run a plan with monitoring
python -m ai_whisperer.main run --plan-file plan.json --state-file state.json --config config.yaml --monitor

# Start interactive server
python -m interactive_server.main

# Start frontend development server
cd frontend && npm start

# Run frontend tests
cd frontend && npm test
```

## Development Workflow

### Project Development Structure
The project uses a "dogfooding" approach where AIWhisperer develops itself:
- `project_dev/rfc/`: Feature requests and specifications
- `project_dev/in_dev/`: Active development tracking
- `project_dev/done/`: Completed features with artifacts

### Test-Driven Development
The project enforces TDD methodology. When implementing features:
1. Write tests first
2. Implement functionality to pass tests
3. Refactor while keeping tests green

### Path Management
All file operations use the PathManager system:
- **workspace_path**: Read-only access for source files
- **output_path**: Write access for generated artifacts
- Never use absolute paths directly; always resolve through PathManager

### Prompt System
Prompts are loaded from files, never inlined:
- Core prompts: `prompts/core/`
- Agent prompts: `prompts/agents/`
- Custom prompts can override built-ins by placing them in project directories

### Configuration
1. Copy `config.yaml.example` to `config.yaml`
2. Set `OPENROUTER_API_KEY` environment variable
3. Configure models and parameters as needed

## Key Development Patterns

### Agent Development
When creating new agents:
1. Extend `BaseAgentHandler`
2. Register in `agent_handlers/__init__.py`
3. Create corresponding prompt in `prompts/agents/`
4. Add tests in `tests/unit/test_agent_*.py`

### Tool Development
New tools must:
1. Extend `BaseTool`
2. Register in `ToolRegistry`
3. Respect PathManager restrictions
4. Include comprehensive error handling

### Postprocessing Steps
Add new postprocessing steps by:
1. Creating class in `postprocessing/scripted_steps/`
2. Implementing `process()` method
3. Adding to pipeline configuration
4. Writing tests for edge cases

### WebSocket Protocol
Interactive mode uses JSON-RPC 2.0 over WebSocket:
- Request/response for commands
- Notifications for real-time updates
- See `interactive_server/message_models.py` for message types

## Important Considerations

### Security
- PathManager enforces directory restrictions
- Never commit API keys or secrets
- All file operations are sandboxed

### Performance
- Sessions are resource-intensive
- Monitor memory usage with performance tests
- Clean up resources properly in all error paths

### Current Development Focus
- Agent Inspector feature for debugging context
- Command system refactoring for modularity
- Enhanced interactive mode capabilities