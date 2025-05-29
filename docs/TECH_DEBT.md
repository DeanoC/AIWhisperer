# Technical Debt

This document tracks known technical debt and areas that need refactoring.

## CLI Mode Deprecation

**Status**: CLI mode being phased out
**Priority**: Low
**Impact**: Batch processing commands will need replacement

### Current State:
- Monitor folder and terminal UI removed (2025-05-29)
- Textual framework references removed
- CLI commands simplified but still present
- Created `UserMessageLevel` enum to replace monitor dependency

### Removed Components:
- `/monitor/` directory and all files
- Terminal-based UI (Textual framework)
- ANSI console message handlers
- Monitor-related test files

### Remaining Work:
- CLI commands in `ai_whisperer/cli_commands.py` need complete refactoring
- Consider replacing batch commands with API endpoints
- Document migration path for users of CLI commands

## Legacy AI Loop and Agent Handlers

**Status**: Deprecated but still referenced
**Priority**: Medium
**Impact**: Old delegate-based AI loop still exists

### Components to Remove:
- `ai_whisperer/ai_loop/ai_loopy.py` - Old delegate-based AI loop
- `ai_whisperer/agent_handlers/` - Old handler system
- `ai_whisperer/execution_engine.py` - Uses old handlers

### Migration:
- Use `StatelessAILoop` instead of old `AILoop`
- Use agent system in `ai_whisperer/agents/` instead of handlers
- Interactive mode already uses the new stateless architecture

## Other Technical Debt

### 1. Test Cleanup
- Old runner tests in `/tests/1st_runner_test/` need removal
- Some integration tests may reference delegates

### 2. Documentation Updates
- Some docs may still reference the old architecture
- API documentation needs updating for stateless design

### 3. Performance Optimization
- WebSocket streaming could be further optimized
- Session persistence could be improved

## Migration Plan

1. **Phase 1** (Completed): Migrate interactive mode to stateless
2. **Phase 2** (Current): Clean up obsolete code and documentation
3. **Phase 3** (Future): Refactor CLI commands to stateless
4. **Phase 4** (Future): Full removal of delegate system