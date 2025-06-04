# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIWhisperer is a Python CLI tool that uses AI models via OpenRouter to automate software development planning and execution. It provides both CLI and web-based interfaces with specialized AI agents.

**For detailed architecture and module information, see [CODE_MAP.md](CODE_MAP.md).**

## CRITICAL: AI and Agent Testing Requirement

**ALL AI and agent-related code must be covered by tests:**
- Use the conversation replay mode for testing AI interactions
- Any new functionality (including prompt changes) that involves AI or agents must pass AI conversation replay tests
- Use Debbie to evaluate AI responses if complex evaluation is needed

## CRITICAL: Configuration Requirements

**ALL real AI invocations require a config file with OpenRouter API key:**
- `main\config.yaml` is an real config file that must be used for all AI interactions
- Set `OPENROUTER_API_KEY` environment variable or add to config
- All commands (CLI, conversation replay, interactive) must use `load_config()`
- Only unit tests with mocked AI can skip config requirements

## CRITICAL: Conversation Replay Mode

**IMPORTANT**: This replays conversations with AI agents, NOT batch processing:
- See `docs/CONVERSATION_REPLAY_USAGE_FOR_AI.md` for complete instructions
- **Correct Method**: `python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay <conversation_file>`
- **Config file is REQUIRED** - all real AI invocations need OpenRouter API key via `load_config()`
- The API key is loaded from the `.env` file automatically by `load_config()`
- Conversation files are plain text files where each line is a message

## Essential Development Commands

### Setup
```bash
# Setup (see setup_worktree_venv.sh for worktree environments)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd frontend && npm install
```

### Testing
```bash
# Run tests (uses pytest.ini configuration)
pytest                                    # All tests
pytest -m "not performance"              # Skip slow tests
pytest tests/unit/                       # Unit tests only
pytest tests/integration/                # Integration tests only
```

### Code Quality (MUST pass before PRs)
```bash
# Check for critical errors (required for CI)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Optional: Format code with black (not enforced in CI)
black . --line-length 120 --skip-magic-trailing-comma
```

### Running the Application
```bash
# Interactive mode (recommended)
python -m interactive_server.main

# Conversation replay mode (replays conversations with AI agents)
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay conversations/test.txt

# List models (legacy)
python -m ai_whisperer.main list-models --config config/main.yaml
```

## Key Architectural Principles

### Agent System
- **Agents work through the normal AI tool system** (not bypass handlers)
- Tools are registered in ToolRegistry and made available to AI
- Agent behavior controlled through system prompts
- AI makes autonomous decisions about tool usage

### Test-Driven Development
1. Write tests first (RED)
2. Implement functionality (GREEN) 
3. Refactor while keeping tests green (REFACTOR)
4. All tests must pass before committing

### Path Management
- **workspace_path**: Read-only access for source files
- **output_path**: Write access for generated artifacts
- Never use absolute paths directly; always resolve through PathManager

### Important File Locations
- **Agent prompts**: `prompts/agents/`
- **Core prompts**: `prompts/core/`
- **Configuration**: `config/`
- **Tool definitions**: `ai_whisperer/tools/`
- **Test organization**: See `pytest.ini` for test markers

## Security and Best Practices

- PathManager enforces directory restrictions
- Never commit API keys or secrets
- All file operations are sandboxed
- Sessions are resource-intensive - clean up properly
- Monitor memory usage with performance tests

## Current Development Focus

- Stateless architecture refinement
- Agent system enhancements  
- Interactive mode improvements
- Performance optimization for WebSocket streaming
- RFC-to-Plan conversion with structured output support

## VM Configuration Memories

- This is Claude's VM. You may install any tool that would be useful

For detailed implementation guidance, architecture details, and module documentation, see [CODE_MAP.md](CODE_MAP.md).