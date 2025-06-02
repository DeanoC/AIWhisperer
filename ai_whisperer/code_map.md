# Ai_Whisperer System Code Map

## Overview
Core application logic and AI interaction components

## Core Components

### cli.py
Command-line interface implementation
- Tests: `tests/interactive_server/test_interactive_client_script.py`

### __init__.py
Package initialization and exports
- Tests: `tests/__init__.py`

### __main__.py
Main application entry point
- Tests: ⚠️ No tests found

### exceptions.py
Custom exception types for the AI Whisperer application.
- Tests: ⚠️ No tests found

### json_validator.py
Implementation for json validator
- Tests: ⚠️ No tests found

## Subdirectories

### tools/
Pluggable tools for file operations and command execution
- **Key Files**: __init__.py, tool_registry.py, base_tool.py

### ai_service/
Tool implementations and utilities
- **Key Files**: openrouter_ai_service.py, tool_calling.py, ai_service.py

### batch/
Batch processing and server management
- **Key Files**: __init__.py, server_manager.py, batch_client.py

### commands/
CLI command implementations
- **Key Files**: base.py, registry.py, echo.py

### agents/
Modular agent handlers with specialized capabilities
- **Key Files**: __init__.py, context_manager.py, session_manager.py

### logging/
Logging and monitoring infrastructure
- **Key Files**: __init__.py, log_aggregator.py, debbie_logger.py

### context/
Context tracking and management system
- **Key Files**: __init__.py, context_manager.py, provider.py

### ai_loop/
AI model interaction and response streaming management
- **Key Files**: __init__.py, tool_call_accumulator.py, stateless_ai_loop.py

### agent_handlers/
Implementation module for agent_handlers

## Test Coverage
**Coverage**: 🟡 Needs Improvement (47.4%)

**Test Files**:
- `tests/__init__.py`
- `tests/performance/test_prompt_system_performance.py`
- `tests/uncategorized/test_config.py`
- `tests/uncategorized/test_utils.py`
- `tests/unit/test_workspace_detection_edge_cases.py`

## Related Documentation
- [PHASE_CONSOLIDATED_SUMMARY.md](../../PHASE_CONSOLIDATED_SUMMARY.md)
- [docs/cost_token_storage_design.md](../../docs/cost_token_storage_design.md)
- [docs/archive/phase2_consolidation/agent-continuation-implementation-plan.md](../../docs/archive/phase2_consolidation/agent-continuation-implementation-plan.md)
- [docs/archive/debugging-session-2025-05-30-consolidated.md](../../docs/archive/debugging-session-2025-05-30-consolidated.md)
- [docs/file-browser-consolidated-implementation.md](../../docs/file-browser-consolidated-implementation.md)

## Navigation
- **Parent**: [Project Root](../../CODE_MAP.md)
- **Subdirectories**: `tools/`, `ai_service/`, `batch/`, `commands/`, `agents/`, `logging/`, `context/`, `ai_loop/`, `agent_handlers/`
