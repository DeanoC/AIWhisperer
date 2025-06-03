# Phase 1: Workspace Detection - TDD Task List

**Phase Duration**: 1-2 days  
**Objective**: Establish workspace detection mechanism using `.WHISPER` folder  
**TDD Approach**: Tests first, then implementation, then integration

## Pre-Phase Setup ✅

### Environment Preparation
- [x] Ensure test environment is clean
- [x] Verify pytest configuration works
- [x] Check PathManager current state
- [x] Document current workspace detection (if any)

## Task 1: Core Workspace Detection Logic (Day 1, Morning)


### 1.1 Write Unit Tests FIRST ⚠️ **TESTS BEFORE CODE**
**File**: `tests/unit/test_workspace_detection.py`

- [x] **Test 1**: `test_whisper_folder_detected_in_current_dir()`
- [x] **Test 2**: `test_whisper_folder_detected_in_parent_dir()`
- [x] **Test 3**: `test_no_whisper_folder_raises_error()`
- [x] **Test 4**: `test_whisper_folder_stops_at_filesystem_root()`
- [x] **Test 5**: `test_whisper_folder_with_workspace_config()`

Tests created in `tests/unit/test_workspace_detection.py`.

### 1.2 Run Tests (Should FAIL) ⚠️
- [x] Run `pytest tests/unit/test_workspace_detection.py -v`
- [x] Verify all tests fail with import errors or missing functions
- [x] Document test failures (ModuleNotFoundError: No module named 'ai_whisperer.workspace_detection')

### 1.3 Create Implementation to Make Tests Pass
**File**: `ai_whisperer/workspace_detection.py`

- [x] **Implement**: `WorkspaceNotFoundError` exception class
- [x] **Implement**: `find_whisper_workspace(start_path=None)` function
  - Search for `.WHISPER` folder starting from start_path (default: cwd)
  - Walk up directory tree until found or reach filesystem root
  - Return workspace root path (parent of `.WHISPER`)
  - Raise `WorkspaceNotFoundError` if not found

- [x] **Implement**: `load_project_json(workspace_path)` function (loads `.WHISPER/project.json`)
  - Look for `project.json` in `.WHISPER` folder
  - Return parsed dict or None if not found/invalid

### 1.4 Run Tests Again (Should PASS) ✅
- [x] Run `pytest tests/unit/test_workspace_detection.py -v`
- [x] Verify all tests pass (5/5 passed)
- [x] Fix any remaining test failures

## Task 2: Integration with PathManager (Day 1, Afternoon)


### 2.1 Write Integration Tests FIRST ⚠️ **TESTS BEFORE CODE**
**File**: `tests/integration/test_workspace_pathmanager_integration.py`

- [x] **Test 1**: `test_pathmanager_uses_whisper_workspace()`
  - Test PathManager integrates with .WHISPER workspace detection and project.json

- [x] **Test 2**: `test_pathmanager_rejects_non_whisper_workspace()`
  - Test PathManager (or detection) rejects workspace without .WHISPER

- [x] **Test 3**: `test_workspace_config_overrides_pathmanager_defaults()`
  - Test project.json config can override PathManager defaults (expected to fail until implemented)

### 2.2 Run Integration Tests (Should FAIL) ⚠️
- [x] Run `pytest tests/integration/test_workspace_pathmanager_integration.py -v`
- [x] Verify test passes for detection and project.json loading (PathManager integration pending)

### 2.3 Extend PathManager Integration
**File**: `ai_whisperer/path_management.py`

- [x] **Add method**: `initialize_with_workspace_detection()`
  - Use `find_whisper_workspace()` to locate workspace
  - Load workspace config if available
  - Set appropriate paths based on workspace

- [x] **Add validation**: Ensure workspace has `.WHISPER` folder
- [x] **Maintain backward compatibility**: Keep existing `initialize()` method

### 2.4 Run Integration Tests Again (Should PASS) ✅
- [x] Run `pytest tests/integration/test_workspace_pathmanager_integration.py -v`
- [x] Verify all integration tests pass

## Task 3: Error Handling and Edge Cases (Day 2, Morning)

### 3.1 Write Edge Case Tests FIRST ⚠️ **TESTS BEFORE CODE**
**File**: `tests/unit/test_workspace_detection_edge_cases.py`

- [ ] **Test 1**: `test_symlink_handling()`
  ```python
  def test_symlink_handling(tmp_path):
      """Test workspace detection handles symlinks correctly"""
      # Create .WHISPER workspace
      # Create symlink to subdirectory
      # Test detection from symlinked directory
  ```

- [ ] **Test 2**: `test_permission_denied_handling()`
  ```python
  def test_permission_denied_handling(tmp_path):
      """Test graceful handling of permission denied errors"""
      # Create directory structure with restricted permissions
      # Test workspace detection handles permissions gracefully
  ```

- [ ] **Test 3**: `test_corrupted_workspace_config()`
  ```python
  def test_corrupted_workspace_config(tmp_path):
      """Test handling of corrupted workspace.yaml"""
      # Create .WHISPER with invalid YAML
      # Test error handling and fallback behavior
  ```

- [ ] **Test 4**: `test_multiple_whisper_folders_in_hierarchy()`
  ```python
  def test_multiple_whisper_folders_in_hierarchy(tmp_path):
      """Test behavior with nested .WHISPER folders"""
      # Create parent and child .WHISPER folders
      # Test which one is selected (should be closest)
  ```

### 3.2 Run Edge Case Tests (Should FAIL) ⚠️
- [ ] Run `pytest tests/unit/test_workspace_detection_edge_cases.py -v`
- [ ] Document expected failures

### 3.3 Implement Robust Error Handling
**File**: `ai_whisperer/workspace_detection.py`

- [ ] **Add**: Symlink resolution in path walking
- [ ] **Add**: Permission error handling with informative messages
- [ ] **Add**: YAML parsing error handling with fallbacks
- [ ] **Add**: Logging for debugging workspace detection issues

### 3.4 Run Edge Case Tests Again (Should PASS) ✅
- [ ] Run `pytest tests/unit/test_workspace_detection_edge_cases.py -v`
- [ ] Verify all edge case tests pass

## Task 4: CLI Integration Preparation (Day 2, Afternoon)

### 4.1 Write CLI Integration Tests FIRST ⚠️ **TESTS BEFORE CODE**
**File**: `tests/unit/test_cli_workspace_validation.py`

- [ ] **Test 1**: `test_cli_validates_workspace_before_execution()`
  ```python
  def test_cli_validates_workspace_before_execution():
      """Test CLI validates workspace before running commands"""
      # Mock CLI command execution
      # Test workspace validation is called
      # Test execution fails if no workspace
  ```

- [ ] **Test 2**: `test_cli_workspace_error_message()`
  ```python
  def test_cli_workspace_error_message():
      """Test CLI shows helpful error message for missing workspace"""
      # Run CLI in directory without .WHISPER
      # Assert error message is clear and helpful
  ```

### 4.2 Create Workspace Validation Utility
**File**: `ai_whisperer/workspace_validation.py`

- [ ] **Implement**: `validate_workspace_for_batch_mode()` function
  - Use workspace detection
  - Provide clear error messages
  - Return workspace info for use by CLI

### 4.3 Run CLI Integration Tests (Should PASS) ✅
- [ ] Run `pytest tests/unit/test_cli_workspace_validation.py -v`
- [ ] Verify CLI integration tests pass

## Task 5: Documentation and Examples (Day 2, Evening)

### 5.1 Create Example Workspace Structure
**Directory**: `tests/fixtures/example_whisper_workspace/`

- [ ] Create example `.WHISPER/` folder structure
- [ ] Create sample `workspace.yaml` with documentation
- [ ] Create example batch scripts for testing

### 5.2 Write Documentation
**File**: `docs/batch-mode/WORKSPACE_DETECTION.md`

- [ ] Document `.WHISPER` folder structure
- [ ] Explain workspace.yaml configuration options
- [ ] Provide setup examples
- [ ] Document error scenarios and solutions

## Task 6: Full Phase 1 Integration Testing

### 6.1 Run Complete Test Suite ✅
- [ ] Run `pytest tests/unit/test_workspace*.py -v`
- [ ] Run `pytest tests/integration/test_workspace*.py -v`
- [ ] Verify all Phase 1 tests pass
- [ ] Check test coverage: `pytest --cov=ai_whisperer.workspace_detection`

### 6.2 Manual Testing
- [ ] Test workspace detection in real directory structures
- [ ] Test error messages are user-friendly
- [ ] Test performance with deep directory hierarchies
- [ ] Test integration with existing PathManager functionality

### 6.3 Code Review Preparation
- [ ] Ensure code follows project style guidelines
- [ ] Add type hints to all public functions
- [ ] Add docstrings to all public functions
- [ ] Remove any debug print statements

## Phase 1 Completion Checklist ✅

### Code Quality
- [ ] All tests pass (`pytest tests/unit/test_workspace*.py tests/integration/test_workspace*.py`)
- [ ] Test coverage ≥ 90% for workspace detection code
- [ ] No linting errors (`black . --check` if project uses black)
- [ ] Type hints on all public interfaces
- [ ] Comprehensive docstrings

### Functionality
- [ ] `.WHISPER` folder detection works in current and parent directories
- [ ] Error handling provides clear, actionable messages
- [ ] Integration with PathManager maintains backward compatibility
- [ ] Edge cases handled robustly (symlinks, permissions, etc.)
- [ ] Performance acceptable for deep directory structures

### Documentation
- [ ] User documentation for workspace setup
- [ ] Developer documentation for API
- [ ] Example workspace structures
- [ ] Error troubleshooting guide

### Team Coordination
- [ ] No conflicts with existing PathManager usage
- [ ] No breaking changes to current functionality
- [ ] Clean integration points for Phase 2 (Debbie agent)

## Next Phase Preparation
- [ ] Document workspace detection API for Debbie agent integration
- [ ] Identify any PathManager enhancements needed for Phase 2
- [ ] Plan Debbie agent's workspace context requirements

---

## TDD Reminders 🚨

1. **NEVER write implementation code before tests**
2. **Tests should fail first, then pass after implementation**
3. **Refactor only when tests are green**
4. **Each test should test one specific behavior**
5. **Test names should clearly describe what they test**
6. **Use descriptive assertion messages**
7. **Mock external dependencies in unit tests**
8. **Keep integration tests focused on integration, not unit logic**

## Common TDD Mistakes to Avoid ❌

- Writing tests after code (defeats the purpose)
- Writing tests that always pass (not testing real behavior)
- Testing implementation details instead of behavior
- Making tests too complex (should be simple and focused)
- Not running tests frequently during development
- Skipping the refactor step
- Not updating tests when requirements change
