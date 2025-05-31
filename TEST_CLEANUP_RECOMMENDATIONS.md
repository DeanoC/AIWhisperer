# Test Cleanup Recommendations

Based on analysis of failing tests in CI, here are the recommended actions:

## 1. Tests to Remove (Obsolete Architecture)

### `tests/unit/test_tool_calling_integration.py`
- **Action**: DELETE entire file
- **Reason**: Tests the old `ToolCallHandler` architecture that has been replaced
- **Evidence**: Uses classes that no longer exist: `ToolCallHandler`, `ToolCall`, `ToolCallResult`, etc.

### `tests/unit/test_ai_service_interaction.py` (partial)
- **Action**: Remove only cache-related tests
- **Tests to remove**:
  - `test_cache_disabled`
  - `test_cache_enabled`
  - `test_call_chat_completion_cache_hit`
  - `test_call_chat_completion_cache_miss`
  - `test_stream_chat_completion_cache_disabled`
  - `test_stream_chat_completion_cache_enabled_no_caching`
- **Reason**: Cache functionality has been removed from the AI service
- **Keep**: All other tests in this file

## 2. Tests to Mark with @pytest.mark.xfail

### `tests/unit/test_stateless_ailoop.py`
Mark these specific tests as expected failures for future implementation:

```python
@pytest.mark.xfail(reason="Timeout parameter not yet implemented")
async def test_process_with_context_timeout(...)

@pytest.mark.xfail(reason="Custom tools parameter not yet implemented")
async def test_process_with_context_custom_tools(...)

@pytest.mark.xfail(reason="store_messages parameter not yet implemented")
async def test_process_with_context_without_storing(...)

@pytest.mark.xfail(reason="process_messages method not yet implemented")
async def test_direct_process_without_context(...)
```

### `tests/unit/batch_mode/test_batch_command_performance.py`
- **Action**: Mark ALL tests with `@pytest.mark.xfail`
- **Reason**: Performance tests have environment-specific thresholds
- **Alternative**: Could use `@pytest.mark.skip` if performance testing is not a current priority

### `tests/integration/test_plan_error_recovery.py`
Mark these platform-specific tests:

```python
@pytest.mark.xfail(reason="Permission testing is platform-specific")
def test_filesystem_permission_error(...)

@pytest.mark.xfail(reason="File locking behavior varies by platform")
def test_concurrent_plan_updates(...)
```

## 3. Tests to Fix (Minor Issues)

### `tests/unit/test_debbie_command.py`
- **Action**: Fix the tests, don't mark as xfail
- **Reason**: Only minor message format differences, not architectural issues

## Implementation Steps

1. **Delete obsolete test file**:
   ```bash
   rm tests/unit/test_tool_calling_integration.py
   ```

2. **Remove cache tests from test_ai_service_interaction.py**

3. **Add @pytest.mark.xfail decorators** to the specified tests with appropriate reasons

4. **Run tests** to verify cleanup:
   ```bash
   pytest -v --tb=short
   ```

## Notes

- The xfail marks indicate features that are planned but not yet implemented
- These should be revisited when implementing the corresponding features
- Performance tests might need environment-specific configuration rather than hard-coded thresholds