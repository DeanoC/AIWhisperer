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

**Before fixing conversation issues:**
1. Create a test conversation file that reproduces the issue
2. Run conversation replay to verify the issue exists
3. Implement the fix
4. Run conversation replay again to verify the fix works
5. Add the test to the regression suite in `tests/integration/conversation_replay/`

**Test corpus location:** `scripts/conversations/test_corpus/`
- Contains standard test conversations for common issues
- Run individual tests: `python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay scripts/conversations/test_corpus/test_<issue_name>.txt`

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

## Claude CLI Tool Access (Hybrid-Hybrid System)

When working through MCP proxy, Claude has access to a carefully managed set of tools:

### Core Tools (Always Available)
- **claude_mailbox**: Send messages to AIWhisperer agents (especially Debbie for complex tasks)
- **claude_check_mail**: Check for responses from agents
- **claude_user_message**: Send messages as if typed in UI (supports markdown, @files, /commands)
- **claude_enable_all_tools**: Emergency access to all tools when needed
- **claude_set_toolset**: Manage your custom tool collection

### Current Available Tools (via proxy)
When connected through `aiwhisperer-aggregator` proxy, standard tools available include:
- **list_directory**: Browse file system
- **read_file**: Read file contents
- **write_file**: Write/update files
- **search_files**: Search for files by pattern or content
- **execute_command**: Run shell commands
- **python_executor**: Execute Python code for analysis

### Workflow Examples

**Normal operation (delegate to Debbie):**
```
claude_mailbox(to_agent="Debbie", subject="Task Request", body="Please run the test suite and report results")
claude_check_mail()
```

**Emergency access (when Debbie is broken):**
```
claude_enable_all_tools(enable=true, reason="Debbie not responding, need to debug")
# Fix the issue with direct access to all tools
claude_enable_all_tools(enable=false, reason="Recovery complete")
```

**Build custom toolset:**
```
claude_set_toolset(action="list")  # See current tools
claude_set_toolset(action="add", tools=["analyze_dependencies", "create_rfc"])
```

### Note on Tool Availability
The Claude tools are registered in the tool registry but may not be exposed through the current FastMCP proxy implementation. Use the standard tools (list_directory, read_file, etc.) for now while the Claude-specific tool filtering is being refined.

For detailed implementation guidance, architecture details, and module documentation, see [CODE_MAP.md](CODE_MAP.md).