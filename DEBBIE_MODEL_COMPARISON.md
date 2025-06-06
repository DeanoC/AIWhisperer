# Debbie Agent Model Comparison

This document summarizes the behavior of different AI models when used with the Debbie debugging agent.

## Issue Summary

When Debbie receives mail asking her to execute tools (e.g., "Please use the list_directory tool"), different models exhibit different behaviors and issues.

## Model Comparison

### 1. Gemini (google/gemini-2.5-flash-preview-05-20:thinking)
- **Issue**: Response truncation with `finish_reason: error`
- **Cause**: Wraps JSON responses in markdown code blocks (```json)
- **Example**: ````json\n{\n  "analysis": "The user has activated me...` (truncated)
- **Tool Calls**: Sometimes works (when not truncated)
- **Response Length**: 127-154 chars when truncated

### 2. Claude (anthropic/claude-3-5-sonnet-20241022)
- **Issue**: Doesn't make tool calls even when intending to
- **Cause**: Unknown - may be tool calling format incompatibility
- **Example**: Says "Executing check_mail" in commentary but doesn't actually call it
- **Tool Calls**: 0 (finish_reason: stop)
- **Response Length**: 330 chars (complete response, proper JSON)

### 3. GPT-4 (openai/gpt-4-turbo-preview)
- **Issue**: None - works correctly
- **Cause**: N/A
- **Example**: Successfully calls `check_mail({"unread_only":true,"limit":5})`
- **Tool Calls**: Works properly
- **Response Length**: 0 (may use different response format)

## Technical Details

### Postprocessing Pipeline
- A regex cleanup exists in `_postprocess_response()` to strip markdown wrappers
- Pattern: `re.sub(r"^```[a-zA-Z]*\n?(.*)\n?```$", r"\1", response.strip(), flags=re.DOTALL)`
- But this only works if the full response is received (not truncated)

### Root Causes
1. **Gemini**: Adds markdown wrappers despite instructions, causing streaming errors
2. **Claude**: Possible incompatibility with OpenRouter tool calling format
3. **GPT-4**: Works as expected with proper tool calling

## Recommendations
1. Use GPT-4 for Debbie when reliable tool execution is needed
2. Implement more robust streaming error handling for Gemini responses
3. Investigate Claude's tool calling compatibility with OpenRouter
4. Consider using the proper postprocessing pipeline instead of inline regex