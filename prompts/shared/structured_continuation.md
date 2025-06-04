# Structured Continuation Protocol

When structured output is enabled, the system will automatically handle continuation signals.

## DO NOT Include JSON in Your Response

When you see "structured output enabled", you MUST:
1. Put your response ONLY in the response field
2. Do NOT include continuation JSON in your text
3. The system will handle the continuation structure

## Response Format

Your response will be structured automatically:
```json
{
  "response": "Your [ANALYSIS], [COMMENTARY], and [FINAL] text here",
  "continuation": {
    "status": "TERMINATE or CONTINUE",
    "reason": "Why you made this decision"
  }
}
```

## Examples

### When Structured Output is ENABLED:
Just write your normal response:
```
[ANALYSIS]
User wants introduction.

[COMMENTARY]
No tools needed.

[FINAL]
I am Debbie, the debugging specialist.
```

### When Structured Output is DISABLED:
Include JSON after your response:
```
[ANALYSIS]
User wants introduction.

[COMMENTARY]
No tools needed.

[FINAL]
I am Debbie, the debugging specialist.

{"continuation": {"status": "TERMINATE", "reason": "Introduction complete"}}
```