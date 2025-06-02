# Agents System Code Map

## Overview
Modular agent handlers with specialized capabilities

## Core Components

### __init__.py
Package initialization and exports
- Tests: `tests/__init__.py`

### context_manager.py
Management and coordination logic
- Tests: `tests/unit/agents/test_agent_context_manager.py`

### session_manager.py
Management and coordination logic
- Tests: `tests/unit/test_session_manager_refactor.py`

### base_handler.py
Request/event handler implementation
- Tests: ⚠️ No tests found

### registry.py
Implementation for registry
- Tests: `tests/unit/agents/test_agent_registry.py`

## Subdirectories

### config/
Configuration files and settings

## Test Coverage
**Coverage**: 🟡 Needs Improvement (61.1%)

**Test Files**:
- `tests/__init__.py`
- `tests/uncategorized/test_config.py`
- `tests/unit/test_session_manager_refactor.py`
- `tests/unit/__init__.py`
- `tests/unit/test_session_manager.py`

## Related Documentation
- [docs/feature/agent-continuation-consolidated-implementation.md](../../docs/feature/agent-continuation-consolidated-implementation.md)
- [PHASE_CONSOLIDATED_SUMMARY.md](../../PHASE_CONSOLIDATED_SUMMARY.md)
- [docs/archive/phase2_consolidation/agent-continuation-implementation-plan.md](../../docs/archive/phase2_consolidation/agent-continuation-implementation-plan.md)
- [docs/archive/consolidated_phase2/docs/architecture/stateless_architecture.md](../../docs/archive/consolidated_phase2/docs/architecture/stateless_architecture.md)
- [docs/archive/legacy/analysis/path_manager_analysis.md](../../docs/archive/legacy/analysis/path_manager_analysis.md)

## Navigation
- **Parent**: [Project Root](../../CODE_MAP.md)
- **Subdirectories**: `config/`
