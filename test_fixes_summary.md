# Test Fixes Summary

## Fixed Issues

### 1. test_ai_tool_usage.py
- Fixed `call_chat_completion` calls to use `messages` parameter instead of `prompt_text` and `messages_history`
- The new API expects messages as a list of role/content dictionaries as the first parameter
- Updated all 5 instances in the file

### 2. test_ai_interaction_history.py
- Fixed `call_chat_completion` calls to use `messages` parameter
- When using conversation history, combine the history with the current prompt into a single messages list
- Updated test assertions to expect the full message list (history + current prompt) in API calls

### 3. test_patricia_rfc_plan_integration.py
- Removed invalid `process_script` method call on ScriptProcessor
- ScriptProcessor is designed for text-based command scripts, not JSON conversation scripts
- Refactored test to simulate the conversation flow directly without relying on non-existent methods
- Test now properly validates the RFC-to-plan conversion workflow

### 4. test_ai_service_interaction.py
- Fixed all `call_chat_completion` calls to use `messages` parameter
- Fixed all `stream_chat_completion` calls to use `messages` parameter
- Updated test assertions to match the new API expectations
- Fixed approximately 15 instances of outdated API usage

## Key API Changes

The OpenRouterAIService API has been updated:
- `call_chat_completion(messages, model, params, tools, response_format)` - messages is now the first parameter
- `stream_chat_completion(messages, tools, **kwargs)` - messages is the first parameter
- No more `prompt_text` or `messages_history` parameters
- All messages (including history and current prompt) should be combined into a single list

## Next Steps

The test_plan_error_recovery.py file appears to be correctly importing all required tools. If there are still failures, they may be due to:
1. Missing tool implementations
2. Path/workspace initialization issues
3. Actual bugs in the error handling logic being tested

Run the tests again to see if these fixes resolve the integration test failures.