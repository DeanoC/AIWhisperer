# AIWhisperer Tools Directory 🛠️

This directory contains various tools used by AIWhisperer agents and special utilities for development.

## Categories

### 🤖 Agent Tools
Regular tools that agents can call during execution:
- File operations (read, write, execute)
- Code analysis (AST parsing, pattern finding)
- Project management (RFC, plans)
- Communication (mailbox system)
- Web tools (search, fetch)

### 🔧 Development Utilities
Standalone utilities for developers:

#### **Model Capability Tester** (`model_capability_tester/`)
A comprehensive tool for testing and discovering model capabilities on OpenRouter.
- Tests models for multi-tool support, structured output, quirks
- Generates capability configurations
- See `model_capability_tester/README.md` for details

## Adding New Tools

### For Agent Tools:
1. Create a class inheriting from `BaseTool`
2. Implement the required methods
3. Register in `tool_registration.py`

### For Development Utilities:
1. Create a subdirectory with clear naming
2. Include a README.md with usage instructions
3. Make it runnable as a module (`__main__.py`)
4. Consider adding a convenience wrapper in `/tools/`

## Tool Organization

```
ai_whisperer/tools/
├── agent_tools/              # Regular agent-callable tools
│   ├── *_tool.py            # Individual tool implementations
│   └── tool_registry.py     # Tool registration system
│
├── model_capability_tester/  # Standalone utility
│   ├── __init__.py
│   ├── __main__.py
│   ├── test_models.py
│   └── README.md
│
└── README_TOOLS.md          # This file
```