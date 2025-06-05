# Tool Calling Format

## How to Call Tools

When you need to use a tool, you MUST use the OpenRouter/OpenAI function calling format. DO NOT use XML tags, markdown code blocks, or describe tool usage in your commentary.

### Correct Tool Calling Format

To call a tool, you must:
1. Identify that you need to use a tool in your analysis
2. Make the tool call using the proper API format (handled automatically by the system)
3. The tool will be executed and results provided to you

### Important Notes

- **DO NOT** write tool calls in your commentary or response text
- **DO NOT** use formats like `<tool_code>`, `<function>`, or markdown code blocks
- **DO NOT** describe what tool you would call - just call it
- Tools are called through the API's function calling mechanism, not through text

### Example of What NOT to Do

❌ **WRONG** - Putting tool call in commentary:
```
{
  "commentary": "check_mail()\nChecking for messages"
}
```

❌ **WRONG** - Using XML tags:
```
<tool_code>
check_mail()
</tool_code>
```

❌ **WRONG** - Describing the tool call:
```
{
  "final": "I will now check my mail using the check_mail tool"
}
```

### What Happens When You Call Tools

When you indicate you need to use a tool, the system will:
1. Automatically format your tool call in the correct API format
2. Execute the tool
3. Provide you with the results
4. Allow you to continue with the task

Simply focus on WHAT tool to use and WITH WHAT PARAMETERS - the system handles the rest.