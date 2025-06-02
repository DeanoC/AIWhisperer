# AIWhisperer Code Map (Updated)

## Overview
AIWhisperer is a Python CLI tool that uses AI models via OpenRouter to automate software development planning and execution. Following the refactor, the codebase is now organized into a clean, modular structure.

## Directory Structure

```
AIWhisperer/
├── ai_whisperer/           # Main package
│   ├── __init__.py
│   ├── __main__.py        # Entry point
│   ├── version.py         # Version info
│   │
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── exceptions.py  # Custom exceptions
│   │   └── logging.py     # Enhanced logging
│   │
│   ├── utils/             # Utilities
│   │   ├── path.py        # Path management
│   │   ├── validation.py  # Input validation
│   │   ├── workspace.py   # Workspace detection
│   │   └── utils.py       # General utilities
│   │
│   ├── services/          # Service layer
│   │   ├── ai/           # AI service implementations
│   │   │   ├── base.py
│   │   │   ├── openrouter.py
│   │   │   └── tool_calling.py
│   │   ├── execution/    # Execution engine
│   │   │   ├── ai_loop.py
│   │   │   ├── ai_config.py
│   │   │   ├── context.py
│   │   │   ├── state.py
│   │   │   └── tool_call_accumulator.py
│   │   └── agents/       # Agent system
│   │       ├── base_handler.py
│   │       ├── config.py
│   │       ├── context_manager.py
│   │       ├── factory.py
│   │       ├── registry.py
│   │       └── stateless.py
│   │
│   ├── interfaces/        # User interfaces
│   │   └── cli/          # Command-line interface
│   │       ├── main.py
│   │       ├── commands.py
│   │       ├── batch.py
│   │       └── commands/
│   │           ├── agent.py
│   │           ├── debbie.py
│   │           └── session.py
│   │
│   ├── extensions/        # Optional features
│   │   ├── agents/       # Agent extensions
│   │   │   ├── prompt_optimizer.py
│   │   │   ├── task_decomposer.py
│   │   │   └── decomposed_task.py
│   │   ├── batch/        # Batch processing
│   │   │   ├── client.py
│   │   │   ├── server_manager.py
│   │   │   ├── intervention.py
│   │   │   └── monitoring.py
│   │   ├── mailbox/      # Agent communication
│   │   │   ├── mailbox.py
│   │   │   └── notification.py
│   │   └── monitoring/   # Logging and monitoring
│   │       ├── debbie_logger.py
│   │       └── log_aggregator.py
│   │
│   ├── tools/             # AI-usable tools (45+ tools)
│   │   ├── base_tool.py   # Base class
│   │   ├── tool_registry.py # Lazy-loading registry
│   │   ├── tool_set.py    # Tool set management
│   │   ├── tool_registration.py
│   │   │
│   │   # File operations
│   │   ├── read_file_tool.py
│   │   ├── write_file_tool.py
│   │   ├── execute_command_tool.py
│   │   ├── list_directory_tool.py
│   │   ├── search_files_tool.py
│   │   │
│   │   # Analysis tools
│   │   ├── find_pattern_tool.py
│   │   ├── python_ast_json_tool.py
│   │   ├── ast_constants.py    # Extracted constants
│   │   ├── ast_helpers.py      # Helper functions
│   │   ├── ast_processors.py   # Processing functions
│   │   │
│   │   # Project management
│   │   ├── create_rfc_tool.py
│   │   ├── create_plan_from_rfc_tool.py
│   │   └── ... (40+ more tools)
│   │
│   ├── context/           # Context management
│   │   ├── agent_context.py
│   │   ├── context_item.py
│   │   └── provider.py
│   │
│   └── prompts/           # System prompts
│       ├── agents/        # Agent-specific prompts
│       └── core/          # Core prompts
│
├── interactive_server/    # Web interface backend
│   ├── main.py           # FastAPI app
│   ├── handlers/         # Request handlers
│   ├── models/           # Data models
│   └── services/         # Server services
│
├── frontend/             # React TypeScript UI
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API clients
│   │   ├── hooks/        # Custom hooks
│   │   └── types/        # TypeScript types
│   └── build/           # Production build
│
├── tests/               # Test suite
│   ├── unit/           # Unit tests (fast, isolated)
│   ├── integration/    # Integration tests
│   ├── performance/    # Performance benchmarks
│   └── scripts/        # AI regression test scripts
│
├── config/             # Configuration files
│   ├── main.yaml       # Main configuration
│   ├── agents/         # Agent configurations
│   ├── models/         # Model definitions
│   └── schemas/        # JSON schemas
│
├── scripts/            # Utility scripts
│   └── test_*.json     # Batch test scripts
│
├── docs/               # Documentation
│   ├── README.md
│   ├── QUICK_START.md
│   ├── TEST_RUNNING_GUIDE.md
│   └── architecture/   # Architecture docs
│
└── .github/            # GitHub configuration
    └── workflows/      # CI/CD pipelines
        └── tests.yml   # Test workflow
```

## Key Components

### 1. Core System (`ai_whisperer/core/`)
- **config.py**: Hierarchical configuration with environment support
- **logging.py**: Enhanced logging with component tracking
- **exceptions.py**: Custom exception hierarchy

### 2. Service Layer (`ai_whisperer/services/`)
- **AI Service**: OpenRouter integration with streaming support
- **Execution Engine**: Stateless AI loop with tool calling
- **Agent System**: Modular agent architecture

### 3. Tool System (`ai_whisperer/tools/`)
- **45+ Tools**: File ops, analysis, RFC/plan management, web, debugging
- **Lazy Loading**: Tools load on-demand for better performance
- **Tool Sets**: Grouped tools for different agent capabilities

### 4. Interactive Mode (`interactive_server/`)
- **FastAPI Backend**: WebSocket support for real-time communication
- **React Frontend**: Modern UI with TypeScript
- **Session Management**: Concurrent user support

### 5. Testing (`tests/`)
- **Categories**: unit, integration, slow, network, requires_api, ai_regression
- **Coverage**: 72.4% and growing
- **CI-Safe**: ~413 tests run without external dependencies

## Performance Optimizations

1. **Lazy Tool Loading**: Tools load on-demand (~0.25ms per tool)
2. **Import Cleanup**: 205 unused imports removed
3. **Modular Structure**: Clear separation of concerns
4. **Efficient Startup**: Registry initialization in 0.0056s

## Test Running

```bash
# Fast unit tests (CI-safe)
pytest -m "not (slow or network or requires_api or performance or ai_regression)"

# All tests (requires API key)
OPENROUTER_API_KEY=your_key pytest

# AI regression tests
pytest -m ai_regression
```

## Development Workflow

1. **Configuration**: Copy `config.yaml.example` to `config.yaml`
2. **API Key**: Set `OPENROUTER_API_KEY` environment variable
3. **Install**: `pip install -r requirements.txt`
4. **Frontend**: `cd frontend && npm install`
5. **Run Tests**: `pytest -m unit` for quick feedback
6. **Start Server**: `python -m interactive_server.main`

## Recent Improvements

- ✅ Module reorganization (55 files restructured)
- ✅ Test coverage increased from 66.4% to 72.4%
- ✅ Lazy loading implementation
- ✅ Import optimization (205 imports removed)
- ✅ Test categorization system
- ✅ CI/CD pipeline configuration
- ✅ Dead code removal and cleanup

## Architecture Principles

1. **Stateless Design**: No global state, easy testing
2. **Tool Autonomy**: AI decides tool usage, not hardcoded
3. **Lazy Loading**: Import only what's needed
4. **Clear Boundaries**: Well-defined module responsibilities
5. **Test Categories**: Different test levels for different needs

This code map reflects the current state of the AIWhisperer codebase after the major refactoring effort.