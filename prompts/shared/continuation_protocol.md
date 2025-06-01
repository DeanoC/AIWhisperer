# Continuation Protocol

When responding, you MUST include a "continuation" field in your response to indicate whether you need to perform additional actions.

## Continuation Decision Criteria

Use "CONTINUE" when:
- You need to use additional tools to complete the task
- The task requires multiple steps and you haven't finished all steps
- You need to verify or refine your work
- You're following a multi-step plan
- Tool execution results require further processing
- You're in the middle of a complex operation
- You've identified dependencies that need to be handled
- You need to gather more information before providing a complete answer

Use "TERMINATE" when:
- The task is fully complete
- You've provided a comprehensive answer
- No further actions would improve the response
- You've reached a natural stopping point
- An error prevents further progress
- The user's request has been fully addressed
- All subtasks have been completed

## Response Format

Include the following in your response when continuation is needed:

```json
{
  "response": "Your response text explaining what you've done and what's next",
  "continuation": {
    "status": "CONTINUE" or "TERMINATE",
    "reason": "Brief explanation of why continuing or terminating",
    "next_action": {
      "type": "tool_call",
      "tool": "tool_name",
      "description": "What this action will accomplish"
    },
    "progress": {
      "current_step": 3,
      "total_steps": 5,
      "completion_percentage": 60,
      "steps_completed": ["Step 1 description", "Step 2 description"],
      "steps_remaining": ["Step 4 description", "Step 5 description"]
    }
  }
}
```

## Important Notes

- Always be explicit about continuation status
- Provide clear reasons for your decision
- Include progress information when possible
- Consider user experience - avoid unnecessary continuations
- Respect iteration limits to prevent infinite loops
- If uncertain whether to continue, prefer TERMINATE
- Each continuation should make meaningful progress

## Examples

### Example 1: Multi-step task requiring continuation
```json
{
  "response": "I've successfully listed all RFCs. Now I need to create the new RFC as requested.",
  "continuation": {
    "status": "CONTINUE",
    "reason": "Need to create RFC after listing existing ones",
    "next_action": {
      "type": "tool_call",
      "tool": "create_rfc",
      "description": "Create new RFC for dark mode feature"
    },
    "progress": {
      "current_step": 1,
      "total_steps": 2,
      "completion_percentage": 50,
      "steps_completed": ["Listed existing RFCs"],
      "steps_remaining": ["Create new RFC"]
    }
  }
}
```

### Example 2: Task complete, no continuation needed
```json
{
  "response": "I've successfully created the RFC for the dark mode feature. The RFC has been saved as 'dark-mode-rfc-2025-01-06.md' in the .WHISPER/rfcs/in_progress directory.",
  "continuation": {
    "status": "TERMINATE",
    "reason": "RFC creation completed successfully",
    "progress": {
      "current_step": 2,
      "total_steps": 2,
      "completion_percentage": 100,
      "steps_completed": ["Listed existing RFCs", "Created new RFC"],
      "steps_remaining": []
    }
  }
}
```