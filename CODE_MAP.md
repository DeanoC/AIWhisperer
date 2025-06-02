# AIWhisperer Code Map

## Overview
AIWhisperer is a Python CLI tool that uses AI models to automate software
development planning and execution. This map provides efficient navigation
for developers and AI assistants working with the codebase.

## Core Systems

### AI Loop System (`ai_whisperer/ai_loop/`)
AI model interaction and response streaming management
- **Key Files**: __init__.py, tool_call_accumulator.py, stateless_ai_loop.py
- **Tests**: 🔴 25.0% coverage
- **Details**: [ai_whisperer/ai_loop/code_map.md](ai_whisperer/ai_loop/code_map.md)

### Agent System (`ai_whisperer/agents/`)
Modular agent handlers with specialized capabilities
- **Key Files**: __init__.py, context_manager.py, session_manager.py
- **Tests**: 🟡 61.1% coverage
- **Details**: [ai_whisperer/agents/code_map.md](ai_whisperer/agents/code_map.md)

### Tool System (`ai_whisperer/tools/`)
Pluggable tools for file operations and command execution
- **Key Files**: __init__.py, tool_registry.py, base_tool.py
- **Tests**: 🔴 22.2% coverage
- **Details**: [ai_whisperer/tools/code_map.md](ai_whisperer/tools/code_map.md)

### Interactive Backend (`interactive_server/`)
FastAPI server with WebSocket support for real-time communication
- **Key Files**: main.py, __init__.py, stateless_session_manager.py
- **Tests**: 🟡 60.0% coverage
- **Details**: [interactive_server/code_map.md](interactive_server/code_map.md)

### Frontend Application (`frontend/`)
React TypeScript application providing chat interface
- **Details**: [frontend/code_map.md](frontend/code_map.md)

## Supporting Systems

### Content Processing (`postprocessing/`)
Content processing pipeline for AI-generated output
- **Key Files**: __init__.py, pipeline.py

### Configuration (`config/`)
Hierarchical configuration management

### Test Suite (`tests/`)
Comprehensive test suite with unit, integration, and performance tests
- **Key Files**: __init__.py, conftest.py

### Development Tools (`scripts/`)
Automation and utility scripts for development
- **Key Files**: analyze_documentation.py, hierarchical_config_loader.py

## Quick Navigation

### By Functionality
- **AI Interaction**: `ai_whisperer/ai_loop/` → `ai_whisperer/agents/`
- **Tool Development**: `ai_whisperer/tools/` → `docs/tool_interface_design.md`
- **Web Interface**: `frontend/src/` → `interactive_server/`
- **Configuration**: `config/` → `ai_whisperer/config.py`
- **Testing**: `tests/unit/` → `tests/integration/`

### By User Type
- **New Developers**: Start with `README.md` → `docs/QUICK_START.md`
- **AI Assistants**: This file → relevant subsystem code_map.md
- **Tool Developers**: `docs/tool_interface_design.md` → `ai_whisperer/tools/`
- **Agent Developers**: `docs/agent_context_tracking_design.md` → `ai_whisperer/agents/`

## Project Statistics
- **Total Code Files**: 415
- **Documentation Files**: 161
- **Code Documentation Coverage**: 222/415 files

## How to Use This Map
1. **Start here** for system overview
2. **Navigate to subsystem** via code_map.md links
3. **Read file headers** for module understanding
4. **Check related docs** for detailed design info
5. **Follow cross-references** for related components