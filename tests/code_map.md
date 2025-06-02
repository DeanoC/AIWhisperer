# Tests System Code Map

## Overview
Comprehensive test suite with unit, integration, and performance tests

## Core Components

### __init__.py
Package initialization and exports
- Tests: `tests/__init__.py`

### conftest.py
Implementation for conftest
- Tests: `tests/conftest.py`

### test_runner_directory_access.py
Implementation for test runner directory access
- Tests: `tests/test_runner_directory_access.py`

## Subdirectories

### performance/
Test suite for functionality validation
- **Key Files**: test_ai_service_timeout.py, test_long_running_session.py, test_prompt_system_performance.py

### uncategorized/
Test suite for functionality validation
- **Key Files**: test_processing.py, test_config.py, test_utils.py

### debugging-tools/
Test suite for functionality validation
- **Key Files**: test_run_batch_test.py, test_batch_test_runner.py, test_run_batch_test_existing_server.py

### unit/
Unit tests organized by module
- **Key Files**: __init__.py, test_session_manager_refactor.py, test_session_manager.py

### temp_output/
Test suite for functionality validation

### examples/
Test suite for functionality validation
- **Key Files**: debbie_practical_example.py, debbie_demo.py

### integration/
Integration tests for end-to-end workflows
- **Key Files**: __init__.py, test_workspace_pathmanager_integration.py, test_project_pathmanager_integration.py

### interactive_server/
Tests for WebSocket and API functionality
- **Key Files**: test_session_manager.py, conftest.py, test_interactive_message_models.py

### fixtures/
Test suite for functionality validation

## Test Coverage
**Coverage**: 🟢 Good (100.0%)

**Test Files**:
- `tests/conftest.py`
- `tests/test_runner_directory_access.py`
- `tests/__init__.py`
- `tests/unit/conftest.py`
- `tests/unit/__init__.py`

## Navigation
- **Parent**: [Project Root](../../CODE_MAP.md)
- **Subdirectories**: `performance/`, `uncategorized/`, `debugging-tools/`, `unit/`, `temp_output/`, `examples/`, `integration/`, `interactive_server/`, `fixtures/`
