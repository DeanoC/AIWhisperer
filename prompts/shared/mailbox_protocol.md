# Mailbox Communication Protocol

The mailbox system enables asynchronous communication between agents during collaborative tasks. This protocol defines how agents should send, receive, and process messages.

## Mailbox Overview

Each agent has access to mailbox tools for inter-agent communication:
- `send_mail`: Send messages to other agents
- `check_mail`: Check for new messages
- `reply_mail`: Reply to received messages

## Message Format

When sending messages, use this structured format:

```json
{
  "to": "agent_name",
  "subject": "Clear, descriptive subject line",
  "body": {
    "purpose": "Brief statement of why you're sending this message",
    "content": "Main message content",
    "context": {
      "task": "Current task description",
      "dependencies": ["list", "of", "dependencies"],
      "related_files": ["file1.py", "file2.md"]
    },
    "requested_action": "What you need the recipient to do",
    "priority": "high|medium|low",
    "deadline": "Optional deadline or timeframe"
  }
}
```

## Communication Guidelines

### When to Use Mailbox

Use mailbox communication when:
- You need another agent's specialized expertise
- Coordinating on shared tasks
- Requesting code review or validation
- Sharing important updates or findings
- Delegating subtasks to specialized agents

### Message Etiquette

1. **Clear Subject Lines**: Make the purpose immediately obvious
2. **Concise Content**: Be brief but include all necessary context
3. **Actionable Requests**: Clearly state what you need
4. **Priority Levels**: Use appropriately (most messages are medium)
5. **Timely Responses**: Check mail regularly during collaborative tasks

### Example Communications

#### Requesting Code Review
```json
{
  "to": "alice",
  "subject": "Code review needed: Authentication module",
  "body": {
    "purpose": "Need review of new authentication implementation",
    "content": "I've implemented JWT authentication in auth.py. Could you review for security best practices?",
    "context": {
      "task": "Implement user authentication",
      "related_files": ["auth.py", "tests/test_auth.py"]
    },
    "requested_action": "Review code and provide feedback on security",
    "priority": "high"
  }
}
```

#### Delegating Task
```json
{
  "to": "patricia",
  "subject": "RFC needed: API versioning strategy",
  "body": {
    "purpose": "Need RFC for API versioning approach",
    "content": "We need to implement API versioning. Could you create an RFC outlining the strategy?",
    "context": {
      "task": "Design API versioning system",
      "dependencies": ["Current API structure", "Client compatibility requirements"]
    },
    "requested_action": "Create comprehensive RFC for API versioning",
    "priority": "medium",
    "deadline": "By end of week"
  }
}
```

## Checking and Processing Mail

When checking mail:
1. Check at the start of your session
2. Check periodically during long tasks
3. Check before marking complex tasks complete
4. Process high-priority messages first
5. Always acknowledge receipt of important messages

## Response Protocol

When replying to messages:
1. Reference the original subject
2. Acknowledge the request
3. Provide requested information or explain why you cannot
4. Suggest alternatives if unable to fulfill request
5. Include any relevant findings or outputs

## Important Notes

- Messages are asynchronous - don't expect immediate responses
- Include enough context for the recipient to understand without extensive history
- Use for coordination, not for real-time conversation
- Keep sensitive information secure
- Archive important communications for future reference