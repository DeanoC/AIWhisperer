# Interactive_Server System Code Map

## Overview
FastAPI server with WebSocket support for real-time communication

## Core Components

### main.py
Main application entry point
- Tests: ⚠️ No tests found

### __init__.py
Package initialization and exports
- Tests: `tests/__init__.py`

### stateless_session_manager.py
Management and coordination logic
- Tests: ⚠️ No tests found

### message_models.py
Implementation for message models
- Tests: `tests/interactive_server/test_interactive_message_models.py`

### debbie_observer.py
Implementation for debbie observer
- Tests: `tests/unit/agents/test_debbie_observer.py`

## Subdirectories

### models/
Data models and schemas for API communication
- **Key Files**: __init__.py, project.py

### handlers/
WebSocket request handlers and routing
- **Key Files**: __init__.py, project_handlers.py, workspace_handler.py

### commands/
Backend server implementation
- **Key Files**: agent.py

### services/
Backend services for project and file management
- **Key Files**: __init__.py, project_manager.py, file_service.py

## Test Coverage
**Coverage**: 🟡 Needs Improvement (60.0%)

**Test Files**:
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/interactive_server/test_interactive_message_models.py`
- `tests/interactive_server/test_message_models.py`

## Related Documentation
- [docs/archive/phase2_consolidation/file_browser_integration_summary.md](../../docs/archive/phase2_consolidation/file_browser_integration_summary.md)
- [PHASE_CONSOLIDATED_SUMMARY.md](../../PHASE_CONSOLIDATED_SUMMARY.md)
- [docs/architecture/architecture.md](../../docs/architecture/architecture.md)
- [docs/archive/legacy/terminal_ui/detail_option_implementation_plan.md](../../docs/archive/legacy/terminal_ui/detail_option_implementation_plan.md)
- [docs/agent-e-execution-consolidated.md](../../docs/agent-e-execution-consolidated.md)

## Navigation
- **Parent**: [Project Root](../../CODE_MAP.md)
- **Subdirectories**: `models/`, `handlers/`, `commands/`, `services/`
