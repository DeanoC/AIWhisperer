# Legacy Code Cleanup Summary

## Overview
Removing legacy planning and execution modules that are no longer used in the modern interactive/batch architecture.

## Modules Being Removed

### Core Legacy Modules
- `ai_whisperer/execution_engine.py` - Old execution system
- `ai_whisperer/initial_plan_generator.py` - Legacy plan generation
- `ai_whisperer/plan_runner.py` - Old plan execution runner
- `ai_whisperer/project_plan_generator.py` - Legacy project planning
- `ai_whisperer/subtask_generator.py` - Old subtask generation system

### Agent Handlers (Old Architecture)
- `ai_whisperer/agent_handlers/` - Entire directory of old handlers

### Legacy Tests
- `tests/unit/test_subtask_generator.py` - Tests for removed module
- Various other tests that fail due to missing legacy modules

## Rationale
- The codebase has evolved to use interactive (WebSocket/React) and batch mode architectures
- These legacy modules are from the old CLI-based planning system
- Neither interactive server nor batch mode use any of these modules
- Removing them will:
  - Reduce maintenance burden
  - Eliminate failing tests for unused code
  - Make the codebase cleaner and easier to understand
  - Focus development on the current architecture

## Migration Path
- Interactive mode: Uses stateless agents and WebSocket communication
- Batch mode: Uses script-based execution with monitoring
- Both modes are fully functional without these legacy modules

## Git History
All removed code remains accessible in git history for reference if needed.