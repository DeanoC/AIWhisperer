# Reasoning Token Implementation

## Problem
The model `anthropic/claude-sonnet-4` was returning empty responses with only 3 chunks when processing certain message sequences. Investigation revealed this was due to the model outputting reasoning tokens that weren't being captured.

## Root Cause
OpenRouter supports reasoning tokens for certain models. When a model outputs reasoning tokens but the code doesn't handle them, the response appears empty because:
- Reasoning tokens appear in `delta.reasoning` not `delta.content`
- Our code was only looking at `delta.content`
- The 3-chunk pattern was: initialization, reasoning output, finish

## Solution Architecture

### 1. Extended AIStreamChunk
Added `delta_reasoning` field to capture reasoning tokens:
```python
class AIStreamChunk:
    def __init__(self, delta_content=None, delta_tool_call_part=None, 
                 finish_reason=None, delta_reasoning=None):
        self.delta_reasoning = delta_reasoning  # New field
```

### 2. Updated OpenRouter Service
Extract reasoning from the delta:
```python
delta_reasoning = delta.get("reasoning")  # Extract reasoning tokens
yield AIStreamChunk(
    delta_content=delta_content,
    delta_reasoning=delta_reasoning,
    ...
)
```

### 3. Enhanced AI Loop
- Accumulate reasoning tokens separately: `full_reasoning = ""`
- Stream reasoning tokens to maintain backward compatibility
- Return reasoning in the result dict
- Handle reasoning-only responses (no content but has reasoning)

### 4. Context Storage
Store reasoning in assistant messages:
```python
if response_data.get('reasoning'):
    assistant_message['reasoning'] = response_data['reasoning']
```

## Behavior

### When Model Outputs Reasoning Only
- Reasoning is accumulated and returned in the `reasoning` field
- For backward compatibility, reasoning is also used as `content` 
- Context stores both fields to preserve full information

### Empty Response Handling
- Empty means no content AND no reasoning
- If we have reasoning but no content, that's valid
- Retry logic only triggers for truly empty responses

## Benefits
1. **Proper Model Support**: Works with all OpenRouter reasoning models
2. **Backward Compatible**: Existing code continues to work
3. **Transparent**: Reasoning is available for debugging/analysis
4. **Flexible**: Can later add UI to show/hide reasoning

## Future Enhancements
1. Add UI toggle to show/hide reasoning tokens
2. Support reasoning configuration (effort levels, token limits)
3. Separate reasoning from content in the UI
4. Add reasoning-specific formatting

## Testing
Run `test_reasoning_tokens.py` to verify:
- Reasoning tokens are captured
- Context integrity is maintained
- No more empty responses for reasoning models
- Backward compatibility with non-reasoning models