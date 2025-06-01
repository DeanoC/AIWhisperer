# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIWhisperer is a Python CLI tool that uses AI models via OpenRouter to automate software development planning and execution. It converts markdown requirements into structured JSON task plans, generates subtasks, and executes them through an AI-powered runner. The project provides both CLI and web-based interfaces.

## Key Architecture Components

### Core Systems
- **AI Loop** (`ai_whisperer/ai_loop/`): Manages AI interactions with stateless architecture and direct streaming
- **Agent System** (`ai_whisperer/agents/`): Modular handlers with specialized agents (Alice, Patricia, Tessa)
- **Stateless Session Management** (`interactive_server/stateless_session_manager.py`): Handles concurrent sessions without delegates
- **Tool Registry** (`ai_whisperer/tools/`): Pluggable tools for file operations and command execution
- **Postprocessing Pipeline** (`postprocessing/`): Cleans and enhances AI-generated content
- **Config Management** (`ai_whisperer/config.py`): Handles API keys and configuration

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

# Check for syntax errors and undefined names before committing
# This command MUST pass before creating PRs
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# The project uses pytest.ini with -W error to treat warnings as errors
```

### Running the Application
```bash
# Generate initial plan from requirements
python -m ai_whisperer.main generate initial-plan requirements.md

# List available models
python -m ai_whisperer.main list-models --config config.yaml --output-csv models.csv

# Interactive mode is now the primary way to execute plans
# CLI run command still available for batch processing
python -m ai_whisperer.main run --plan-file plan.json --state-file state.json --config config.yaml

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
1. Write tests first (RED)
2. Implement functionality to pass tests (GREEN)
3. Refactor while keeping tests green (REFRACTOR)
4. Verify all tests pass before committing

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

### Execution Logs for Large Tasks

When performing larger-sized jobs or complex investigations, create an execution log to track progress and maintain context:

1. **Create a dedicated log file**: `docs/[task-name]-execution-log.md`
2. **Document each tool use**: Record what tool was used, why, and what was found
3. **Track context preservation**: Note strategies for maintaining context across potential context compaction
4. **List tools wished for**: Document any tools that would have been helpful but weren't available
5. **Summarize key findings**: Build progressive summaries as you work

This practice helps with:
- Recovery from context loss or compaction
- Knowledge transfer to other team members
- Creating reusable patterns for similar tasks
- Identifying tooling gaps for future improvements

Example structure:
```markdown
# [Task Name] Execution Log
## Task: [Description]
**Started**: [Date]
**Status**: In Progress/Complete

### Tool Usage Log
#### 1. [Tool Name]
**Target**: [file/pattern]
**Purpose**: [why using this tool]
**Status**: COMPLETE
**Key Findings**: [what was discovered]

### Tools I Wished I Had
- [Tool description and use case]

### Context Preservation Strategy
- [How you're maintaining context]

### Summary of Findings
[Progressive summary of discoveries]
```

### Agent Architecture and Tool Integration

**IMPORTANT ARCHITECTURAL PRINCIPLE**: Agents should work **through the normal AI tool system**, not through separate handlers that bypass the AI loop.

**The Right Way**:
- Agent receives message → AI processes with system prompt → AI decides to use tools → Tools execute through ToolRegistry → Results incorporated into response
- Tools are registered in the ToolRegistry and made available to the AI
- Agent behavior is controlled through system prompts, not custom code paths
- The AI makes autonomous decisions about when and how to use tools

**The Wrong Way**:
- Agent receives message → Custom handler intercepts → Handler bypasses AI to execute tools directly
- This breaks the AI's autonomy and creates fragile, hard-coded behavior
- Results in agents that don't feel natural or intelligent

**Example**: Agent Patricia (RFC specialist) should use her system prompt to instruct the AI to call `create_rfc()`, `analyze_languages()`, etc. The AI should decide when to use these tools based on context, not through predetermined logic.

**Key Implementation Points**:
1. Register all tools in `ToolRegistry` during session initialization
2. Make agent system prompts explicit about tool usage with examples
3. Let the AI decide which tools to use and when
4. Avoid custom message routing that bypasses the AI loop

### Agent Development
When creating new agents:
1. Define agent in `agents.yaml` configuration
2. Create system prompt in `prompts/agents/agent_name.prompt.md`
3. Register in `AgentRegistry` if needed
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

- Our back and frontends communicate exclusively via JSON-RPC over websockets

### Security
- PathManager enforces directory restrictions
- Never commit API keys or secrets
- All file operations are sandboxed

### Performance
- Sessions are resource-intensive
- Monitor memory usage with performance tests
- Clean up resources properly in all error paths

### Current Development Focus
- Stateless architecture refinement
- Agent system enhancements
- Interactive mode improvements
- Performance optimization for WebSocket streaming
- RFC-to-Plan conversion with structured output support

### Agent Architecture and Tool Integration

**IMPORTANT ARCHITECTURAL PRINCIPLE**: Agents should work **through the normal AI tool system**, not through separate handlers that bypass the AI loop.

#### Continuation Mechanism
The stateless session manager implements automatic continuation for multi-step tool operations:
- **Single-tool models** (like Gemini): Automatically continues after each tool call
- **Multi-tool models** (like GPT-4): Executes all tools in one turn
- **Depth limiting**: Maximum 3 continuation levels to prevent infinite loops
- **Smart detection**: Only continues when the AI indicates more steps are needed

This ensures that agents like Patricia can perform complex multi-step operations (e.g., creating RFCs after listing them) regardless of the underlying model's capabilities.

## Plan Management (RFC-to-Plan Conversion)

### Overview
AIWhisperer supports converting RFC documents into structured execution plans through Agent Patricia. Plans are stored in `.WHISPER/plans/` with bidirectional linkage to their source RFCs.

### Key Features
- **Structured Output Support**: Automatically uses OpenAI's structured output for compatible models
- **TDD Enforcement**: All generated plans follow Red-Green-Refactor methodology
- **Bidirectional Sync**: RFC updates can trigger plan regeneration
- **Natural Naming**: Plans use descriptive names like `feature-name-plan-YYYY-MM-DD`

### Workflow Example
```python
# Interactive conversation with Patricia
User: "Create an RFC for adding dark mode"
Patricia: [Creates RFC with create_rfc tool]

User: "The RFC looks good, can you convert it to a plan?"
Patricia: [Uses prepare_plan_from_rfc and save_generated_plan tools]
# If using GPT-4o/GPT-4o-mini, structured output ensures valid JSON

User: "Update the RFC to include system preference detection"
Patricia: [Updates RFC with update_rfc tool]

User: "Update the plan to reflect the RFC changes"
Patricia: [Uses update_plan_from_rfc tool to sync changes]
```

### Plan Storage Structure
```
.WHISPER/
└── plans/
    ├── in_progress/
    │   └── dark-mode-plan-2025-05-31/
    │       ├── plan.json          # Main plan file
    │       └── rfc_reference.json # Link to source RFC
    └── archived/
```

### Available Plan Tools
- `prepare_plan_from_rfc` - Load RFC content for plan generation
- `save_generated_plan` - Save generated plan with validation
- `list_plans` - List plans by status
- `read_plan` - View plan details
- `update_plan_from_rfc` - Sync plan with RFC changes
- `move_plan` - Archive/unarchive plans
- `delete_plan` - Permanently delete plans (requires confirmation)

### Testing Plan Generation
```bash
# Run integration tests
pytest tests/integration/test_rfc_plan_bidirectional.py

# Run batch mode tests
python -m ai_whisperer.batch.batch_client scripts/test_plan_generation_quality.json
python -m ai_whisperer.batch.batch_client scripts/test_rfc_plan_lifecycle.json
```

## Development Best Practices

### Execution Logs for Complex Tasks
When implementing complex features or debugging issues, create execution logs to maintain context:
- Create logs in `docs/` directory with descriptive names
- Include: Overview, Implementation Steps, Key Decisions, Issues Faced, Solutions
- Example: `docs/agent-e-implementation-execution-log.md`
- Helps maintain context across sessions and provides documentation