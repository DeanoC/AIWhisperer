# AIWhisperer Test Map Summary

## Test Suite Overview

### Test Statistics
- **Total Test Files**: 157
- **Total Tests**: 1,204 (812 methods + 392 functions)
- **Test Classes**: 158
- **Python Modules**: 139 (only 89 have tests)
- **Coverage Gap**: 50 modules (36%) without any tests

### Test Distribution by Type
```
Unit Tests:        103 files (66%)
Integration Tests:  27 files (17%)
Server Tests:       21 files (13%)
Performance Tests:   1 file  (1%)
Other Tests:         5 files (3%)
```

### Test Markers Used
- `@pytest.mark.asyncio`: 29 files (async tests)
- `@pytest.mark.xfail`: 13 files (expected failures)
- `@pytest.mark.skipif`: 13 files (conditional skips)
- `@pytest.mark.parametrize`: 8 files (parameterized tests)
- `@pytest.mark.performance`: 6 files
- `@pytest.mark.skip`: 5 files
- `@pytest.mark.integration`: 4 files
- `@pytest.mark.flaky`: 3 files

## Critical Coverage Gaps

### 1. Completely Untested Core Modules (50 files)
**Entry Points & CLI**:
- `main.py`, `__main__.py`, `cli.py`
- `cli_commands.py`, `cli_commands_batch_mode.py`
- `interactive_entry.py`

**Agent System**:
- `base_handler.py`
- `debbie_tools.py`
- `mail_notification.py`
- `mailbox_tools.py`

**Batch Mode**:
- `intervention.py`
- `server_manager.py`
- `websocket_interceptor.py`

**Tools** (13 untested):
- `batch_command_tool.py`
- `system_health_check_tool.py`
- `message_injector_tool.py`
- `monitoring_control_tool.py`
- `script_parser_tool.py`
- Agent-E specific tools

**Core Infrastructure**:
- `ai_loopy.py` (main AI loop!)
- `logging_custom.py`
- `model_capabilities.py`
- `processing.py`
- `task_selector.py`

### 2. Test Organization Issues

**Non-standard Test Files**:
- `debbie_demo.py` - Demo mixed with tests
- `debbie_practical_example.py` - Example mixed with tests
- `runner_directory_access_tests.py` - Not following naming convention
- Debugging tools in `tests/debugging-tools/`

**Mixed Test Types**:
- Unit tests importing integration dependencies
- Performance tests mixed with regular tests
- Server tests requiring live connections

### 3. Test Quality Concerns

**High Skip/Fail Rate**:
- 13 files with `@xfail` markers
- 13 files with conditional skips
- 5 files completely skipped

**Flaky Tests**:
- 3 files marked as flaky
- WebSocket and async tests prone to timing issues

## Recommendations for Test Refactoring

### 1. Immediate Actions
- **Add tests for critical untested modules**:
  - CLI entry points (`main.py`, `cli.py`)
  - Core AI loop (`ai_loopy.py`)
  - Batch mode components
  
- **Reorganize test structure**:
  ```
  tests/
  ├── unit/          # Pure unit tests, no external deps
  ├── integration/   # System integration tests
  ├── e2e/           # End-to-end scenarios
  ├── performance/   # Performance benchmarks
  ├── fixtures/      # Shared test data
  └── examples/      # Demo files (not tests)
  ```

### 2. Test Cleanup
- Remove `.skip` and `.bak` files
- Move demos to `examples/` directory
- Standardize test file naming
- Consolidate test utilities

### 3. Coverage Improvements
- Target 80% coverage for core modules
- Add tests for all registered tools
- Test all CLI commands
- Cover error handling paths

### 4. Test Performance
- Separate slow tests with markers
- Use fixtures to reduce setup time
- Mock external services consistently
- Parallelize test execution

## Test-to-Code Mapping

### Well-Tested Modules
1. **Agent System**: Factory, registry, stateless agents
2. **Tools**: File operations, RFC/plan tools
3. **Context Management**: Agent context, providers
4. **AI Service**: OpenRouter integration

### Under-Tested Areas
1. **Batch Mode**: Only basic integration tests
2. **CLI Commands**: No direct command tests
3. **Error Handling**: Limited exception testing
4. **Tool Registration**: Dynamic registration untested

---
*Generated: 2025-01-06*