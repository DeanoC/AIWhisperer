# Continuation Protocol

## Overview
This protocol allows agents to signal when they need to continue with additional steps after tool execution. The continuation signal is detected by the system through the response structure.

## When to Signal Continuation

**Signal CONTINUE when:**
- You need to use additional tools to complete the task
- The task requires multiple steps and you haven't finished all steps
- You need to verify or refine your work
- Tool execution results require further processing
- You're in the middle of a complex operation that needs more steps

**Signal TERMINATE when:**
- The task is fully complete
- You've provided a comprehensive answer
- No further actions would improve the response
- The user's request has been fully addressed

## How It Works

When you use tools during your response, the system checks if you need to continue afterward. You signal this by including a `continuation` field in your response structure alongside your natural language response.

**IMPORTANT**: Your response to the user should ALWAYS be in natural language. The continuation signal is a separate field that the system reads but doesn't show to the user.

## Response Structure

When responding with tool calls, your response object can include:
- `response`: Your natural language message to the user
- `tool_calls`: The tools you're calling
- `continuation`: (Optional) Signal for the system about next steps

The continuation field structure:
```
continuation: {
  status: "CONTINUE" or "TERMINATE"
  reason: "Why you need to continue or why you're done"
  progress: {
    current_step: number
    total_steps: number (if known)
    steps_completed: ["what you've done"]
    steps_remaining: ["what's left to do"]
  }
}
```

## Examples

### Example 1: Continuing after listing RFCs
Your response object would include:
- response: "I've found 3 existing RFCs. Now I'll create the new RFC for the dark mode feature as requested."
- tool_calls: [create_rfc tool call]
- continuation: {status: "CONTINUE", reason: "Need to create RFC after listing"}

### Example 2: Task complete
Your response object would include:
- response: "I've successfully created the RFC for the dark mode feature. It has been saved as 'dark-mode-rfc-2025-01-06.md' in the .WHISPER/rfcs/in_progress directory."
- continuation: {status: "TERMINATE", reason: "RFC creation completed"}

## Important Notes

- Always respond to users in natural, conversational language
- The continuation field is separate from your user-facing response
- If you're not using tools, you don't need to include continuation signals
- When in doubt, let the system handle continuation automatically