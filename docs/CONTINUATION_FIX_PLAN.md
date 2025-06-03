# Continuation Fix and Testing Plan

## Overview
This plan addresses the continuation and conversation issues in AIWhisperer by fixing critical bugs and creating a comprehensive test suite using Debbie (our AI tester/debugger).

## Phase 1: Fix Critical Continuation Bug

### Issue
The continuation check order in `stateless_session_manager.py` prevents single-tool models from continuing even with explicit continuation signals.

### Fix
```python
# Current (incorrect) order at line 886-914:
if not model_info.supports_multiple_tool_calls:
    # This blocks continuation for single-tool models
    return False

if self._has_explicit_continuation(response):
    # This never gets checked for single-tool models
    return True
```

### Solution
Reverse the check order to prioritize explicit continuation signals over model capabilities.

## Phase 2: Create Debbie Test Suite

### Test Categories

#### 1. Basic Conversation Tests
- **test_single_message.json**: Simple one-message chat with immediate response
- **test_multi_message_no_continue.json**: Multiple messages without continuation needs
- **test_basic_continuation.json**: Simple continuation with explicit signal

#### 2. Tool Usage Tests
- **test_single_tool_use.json**: Single tool call and response
- **test_multi_tool_batch.json**: Multiple tools in one response (for capable models)
- **test_multi_tool_continuation.json**: Multiple tools requiring continuation

#### 3. Model-Specific Tests
- **test_reasoning_models.json**: Tests for models with reasoning support
- **test_single_tool_models.json**: Specific tests for single-tool models
- **test_continuation_limits.json**: Test max iterations and timeouts

#### 4. Complex Integration Test
- **test_rfc_to_plan_execution.json**: Complete workflow:
  1. Create RFC with Agent Patricia
  2. Convert RFC to plan
  3. Execute plan with Agent Eamonn
  4. Handle multiple continuations
  5. Complete all tasks

### Test Structure
```json
{
  "test_name": "Test Description",
  "config": {
    "agent": "agent_name",
    "model": "model_id",
    "max_iterations": 10,
    "timeout": 300
  },
  "conversation": [
    {
      "role": "user",
      "content": "User message",
      "expected_behavior": {
        "should_continue": true/false,
        "tools_used": ["tool1", "tool2"],
        "continuation_reason": "reason if continuing"
      }
    }
  ],
  "validation": {
    "check_continuation_signals": true,
    "check_progress_tracking": true,
    "check_completion": true
  }
}
```

## Phase 3: Enhanced Continuation Features

### 1. Smarter Continuation Messages
Instead of generic "Please continue", generate context-aware messages:
- "Please continue with the file analysis"
- "Please proceed with the next test case"
- "Please complete the remaining 3 tasks"

### 2. Progress Tracking Enhancement
```json
{
  "continuation": {
    "status": "CONTINUE",
    "reason": "3 more files to analyze",
    "progress": {
      "current_step": 2,
      "total_steps": 5,
      "completed": ["file1.py", "file2.py"],
      "remaining": ["file3.py", "file4.py", "file5.py"]
    }
  }
}
```

### 3. Model-Specific Prompts
Research and adapt prompts from the AI system prompts repository for:
- Claude (our primary model)
- GPT-4
- Gemini
- Other models we support

## Phase 4: Implementation Steps

1. **Create feature branch**
   ```bash
   git checkout -b feature-continues
   ```

2. **Fix continuation check order**
   - Modify `stateless_session_manager.py`
   - Update unit tests

3. **Create Debbie test scripts**
   - Start with simple tests
   - Progress to complex scenarios
   - Include edge cases

4. **Run regression tests**
   - Execute all test scripts with Debbie
   - Document results
   - Fix any issues found

5. **Enhance continuation features**
   - Implement context-aware messages
   - Improve progress tracking
   - Add model-specific optimizations

## Success Criteria

1. All test scripts pass consistently
2. Single-tool models can continue with explicit signals
3. No false positive continuations
4. Progress tracking works accurately
5. Complex workflows complete successfully
6. Performance remains acceptable (no excessive API calls)

## Risk Mitigation

1. **Backward Compatibility**: Ensure existing conversations still work
2. **Model Differences**: Test across multiple models
3. **Edge Cases**: Include timeout and error scenarios
4. **Performance**: Monitor API usage and response times

## Next Steps

1. Create the feature branch
2. Fix the critical continuation bug
3. Create the first basic test script
4. Iterate and expand the test suite
5. Document findings and best practices