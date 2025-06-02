# AIWhisperer Module Reorganization Plan

## Current Issues
1. **20 files at root level** - too many, poor organization
2. **Inconsistent naming** - mix of concepts (commands vs cli_commands)
3. **Poor discoverability** - hard to find related functionality
4. **Mixed responsibilities** - some modules do too much
5. **Unclear public/private** - no clear API boundaries

## Proposed New Structure

```
ai_whisperer/
├── __init__.py          # Public API exports
├── __main__.py          # Entry point
│
├── core/                # Core functionality
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── exceptions.py    # Exception hierarchy
│   ├── logging.py       # Logging setup
│   └── types.py         # Shared type definitions
│
├── models/              # Data models and schemas
│   ├── __init__.py
│   ├── agent.py         # Agent models
│   ├── session.py       # Session models
│   ├── task.py          # Task/Plan models
│   └── tool.py          # Tool models
│
├── services/            # Business logic services
│   ├── __init__.py
│   ├── ai/              # AI service integration
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openrouter.py
│   │   └── tool_calling.py
│   ├── agents/          # Agent system
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── registry.py
│   │   └── handlers/    # Specific agent handlers
│   ├── execution/       # Execution engine
│   │   ├── __init__.py
│   │   ├── ai_loop.py
│   │   ├── session.py
│   │   └── context.py
│   └── tools/           # Tool system
│       ├── __init__.py
│       ├── base.py
│       ├── registry.py
│       └── implementations/
│
├── interfaces/          # User interfaces
│   ├── __init__.py
│   ├── cli/             # Command line interface
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── commands/
│   │   └── batch.py
│   ├── api/             # REST/WebSocket API
│   │   ├── __init__.py
│   │   └── handlers/
│   └── interactive/     # Interactive mode
│       ├── __init__.py
│       └── server.py
│
├── utils/               # Utility modules
│   ├── __init__.py
│   ├── path.py          # Path management
│   ├── prompt.py        # Prompt loading
│   ├── validation.py    # JSON/YAML validation
│   └── workspace.py     # Workspace detection
│
└── extensions/          # Optional/plugin features
    ├── __init__.py
    ├── batch/           # Batch mode extension
    ├── monitoring/      # Monitoring/debugging
    └── mailbox/         # Agent communication
```

## Migration Plan

### Phase 1: Create New Structure (Day 1)
1. Create new directory structure
2. Move files to appropriate locations
3. Update imports using automated script
4. Ensure tests still pass

### Phase 2: Refactor Modules (Day 2)
1. Split large modules into focused components
2. Define clear public APIs (__init__.py exports)
3. Add __all__ to control exports
4. Mark private functions with underscore prefix

### Phase 3: Update Dependencies (Day 3)
1. Update all imports in codebase
2. Update tests to use new paths
3. Update documentation references
4. Update configuration files

## File Movement Mapping

### Core Module Moves
```
config.py → core/config.py
exceptions.py → core/exceptions.py
logging_custom.py → core/logging.py
```

### Model Extractions
```
(from various) → models/agent.py
(from various) → models/session.py
(from various) → models/task.py
```

### Service Reorganization
```
ai_service/* → services/ai/*
agents/* → services/agents/*
ai_loop/* → services/execution/*
tools/* → services/tools/implementations/*
```

### Interface Consolidation
```
cli.py → interfaces/cli/main.py
cli_commands.py → interfaces/cli/commands/base.py
cli_commands_batch_mode.py → interfaces/cli/batch.py
commands/* → interfaces/cli/commands/*
```

### Utility Consolidation
```
path_management.py → utils/path.py
prompt_system.py → utils/prompt.py
json_validator.py → utils/validation.py
workspace_detection.py → utils/workspace.py
```

### Extension Grouping
```
batch/* → extensions/batch/*
logging/debbie_logger.py → extensions/monitoring/debbie.py
agents/mailbox*.py → extensions/mailbox/*
```

## Public API Definition

The root `__init__.py` will export only the public API:

```python
# ai_whisperer/__init__.py
from ai_whisperer.core import (
    load_config,
    AIWhispererError,
)
from ai_whisperer.services.agents import (
    AgentFactory,
    register_agent,
)
from ai_whisperer.services.tools import (
    ToolRegistry,
    register_tool,
)

__all__ = [
    'load_config',
    'AIWhispererError',
    'AgentFactory',
    'register_agent',
    'ToolRegistry', 
    'register_tool',
]
```

## Benefits

1. **Clear organization** - Easy to find related code
2. **Better encapsulation** - Clear public/private boundaries
3. **Reduced coupling** - Dependencies flow down the hierarchy
4. **Easier testing** - Focused modules are easier to test
5. **Better discoverability** - Logical grouping of functionality
6. **Plugin architecture** - Extensions are clearly separated

## Implementation Script

Create automated script to:
1. Move files maintaining git history
2. Update all imports automatically
3. Run tests to verify nothing broke
4. Generate import mapping for documentation