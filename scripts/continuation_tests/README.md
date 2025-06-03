# Continuation Test Suite

This directory contains regression tests for the AIWhisperer continuation system using Debbie (our AI tester/debugger).

## Test Categories

### 1. Basic Tests
- `test_single_message.json` - Simple one-message interaction
- `test_basic_continuation.json` - Basic continuation with explicit signals

### 2. Model-Specific Tests  
- `test_single_tool_continuation.json` - Tests single-tool model continuation

### 3. Complex Workflows
- `test_complex_rfc_workflow.json` - End-to-end RFC creation, planning, and execution

## Running Tests

### Run all tests:
```bash
python scripts/continuation_tests/run_continuation_tests.py
```

### Run specific test:
```bash
python scripts/continuation_tests/run_continuation_tests.py --test test_single_message.json
```

### Filter tests:
```bash
python scripts/continuation_tests/run_continuation_tests.py --filter basic
```

## Test Structure

Each test file follows this structure:

```json
{
  "name": "test_name",
  "description": "What this test validates",
  "config": {
    "agent": "agent_name",
    "model": "model_id", 
    "max_iterations": 10
  },
  "steps": [
    {
      "name": "step_name",
      "user_message": "The message to send",
      "expected_behavior": {
        "should_continue": true/false,
        "tools_used": ["tool1", "tool2"],
        "continuation_reason": "why it should continue"
      }
    }
  ],
  "validation": {
    "check_continuation_signals": true,
    "check_progress_tracking": true
  }
}
```

## Expected Behaviors

The test runner validates:

1. **Continuation Signals** - Whether the AI properly signals continuation
2. **Tool Usage** - Which tools were called and in what order
3. **Response Patterns** - Expected content in responses
4. **Iteration Counts** - Number of continuation cycles
5. **Agent Transitions** - Proper switching between agents
6. **Artifact Creation** - Files/plans/RFCs created as expected

## Adding New Tests

1. Create a new JSON file starting with `test_`
2. Follow the structure above
3. Define clear expected behaviors
4. Run the test to validate

## Debugging Failed Tests

Test results are saved with timestamps in this directory. Check the detailed output for:

- Exact AI responses
- Tool calls made
- Continuation signals sent
- Validation failures

## Important Notes

- Tests require a valid `config.yaml` with OpenRouter API key
- Some tests may take several minutes due to multiple AI calls
- Complex tests may fail due to non-deterministic AI behavior
- Always verify test failures before assuming a bug