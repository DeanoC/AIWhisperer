# Fix for is_continuation Design Flaw

## The Problem

The `is_continuation` flag disables tool processing when `True`, which is fundamentally wrong because:
- Tools are part of the AI's capabilities ("body")
- Continuations often need tools to complete multi-step tasks
- It causes silent failures and confusing behavior
- There's no logical reason to restrict tools during continuations

## Current Problematic Code

```python
# Line 991 in stateless_session_manager.py
if result.get('finish_reason') == 'tool_calls' and result.get('tool_calls') and not is_continuation:
    # Tool processing ONLY happens when NOT a continuation!
```

## Recommended Fix

Remove the `not is_continuation` check:

```python
# Fixed version
if result.get('finish_reason') == 'tool_calls' and result.get('tool_calls'):
    # Always process tools, regardless of continuation status
```

## Other uses of is_continuation (these are OK)

1. **Continuation tracking** - Just bookkeeping, no functionality removed
2. **Message optimization** - Minor performance optimization
3. **Loop prevention** - Prevents infinite continuation loops

## Why This Matters

- The agent switch handler bug was caused by this
- Any multi-step task that needs tools will fail silently
- The AI gets confused when tools don't work as expected
- It's an architectural flaw that will cause more bugs

## Alternative (if tool restrictions are ever needed)

If there's ever a legitimate need to restrict tools, it should be explicit:
- Remove tools from the tool list
- Use a specific `disable_tools=True` parameter
- Document WHY tools are being disabled

But honestly, I can't think of any good reason to do this. If you don't want the AI to use tools, don't give it tools!