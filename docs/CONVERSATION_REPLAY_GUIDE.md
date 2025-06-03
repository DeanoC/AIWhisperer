# Conversation Replay Mode Guide

## What is Conversation Replay Mode?

Conversation Replay Mode (formerly "batch mode") allows you to replay pre-recorded conversations with AI agents. Think of it like playing back a movie script - it sends a sequence of messages to agents automatically.

## Key Concepts

### Conversations vs Scripts

**🎬 Conversations** (what this mode uses):
- Sequences of messages sent to AI agents
- Like dialogue in a movie script
- Files with `.conv.json`, `.dialogue.json` extensions
- Located in `scripts/conversations/`

**⚙️ Scripts** (what agents like Debbie execute):
- Actual executable test/command scripts
- Contain actions, validations, system commands
- Files with `.json`, `.yaml`, `.txt` extensions
- Located in `tests/` directories

## How It Works

1. **Load a conversation file** containing messages
2. **Start a server** automatically on a random port
3. **Connect via WebSocket** to the server
4. **Replay messages** one by one to the agent
5. **Collect responses** and handle any tool executions
6. **Clean up** when done

## Conversation File Format

Conversations are simple text files where:
- Each line is sent as a message to the AI
- Empty lines are skipped
- Lines starting with `#` are comments
- The AI interprets the messages naturally

### Example Conversation File
```text
# Debbie Health Check Conversation
# Each line below is sent as a message

Please switch to agent D (Debbie)

Hi Debbie! Can you run a system health check?

Use the system_health_check tool with verbose output please

What do you recommend we fix first?
```

### How It Works

1. The conversation processor reads the file line by line
2. Skips comments (lines starting with #) and empty lines  
3. Sends each remaining line as a message to the current agent
4. The agent interprets the message naturally

### Common Messages

**Switching Agents:**
```text
Please switch to agent D (Debbie)
Switch to Patricia (agent P)
Can you hand this off to agent E?
```

**Asking for Actions:**
```text
Run a system health check
Create an RFC for a logging system
List all available tools
Check the workspace validation
```

**Natural Conversation:**
```text
Hi! How are you doing?
Can you help me debug this issue?
What do you think about the test results?
Thanks for your help!
```

## Running Conversations

### Method 1: Command Line
```bash
# Replay a conversation
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay scripts/conversations/debbie_health_check.conv.json

# With custom timeout
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay scripts/conversations/long_test.conv.json --timeout 300
```

### Method 2: Python API
```python
import asyncio
from ai_whisperer.extensions.conversation import ConversationClient, ConversationManager

async def replay_conversation():
    # Start server
    manager = ConversationManager()
    server_url = await manager.start_server()
    
    try:
        # Create client
        client = ConversationClient(server_url)
        await client.connect()
        
        # Replay conversation
        results = await client.replay_conversation(
            "scripts/conversations/health_check.conv.json"
        )
        
        # Process results
        for message_result in results:
            print(f"Message: {message_result['message'][:50]}...")
            print(f"Response: {message_result['response'][:100]}...")
            
    finally:
        await manager.stop_server()

# Run it
asyncio.run(replay_conversation())
```

## Example Conversations

### 1. Simple Health Check
`health_check.txt`:
```text
# Quick health check
Switch to agent D
Run a quick system health check
```

### 2. Multi-Agent Workflow  
`rfc_workflow.txt`:
```text
# RFC to Plan Workflow

# Start with Patricia for RFC
Please switch to agent P (Patricia)
Create an RFC for a user authentication system

# Get Patricia to convert it to a plan
Convert the RFC to a detailed plan

# Switch to Eamonn for task breakdown
Now switch to agent E (Eamonn)
Break down the plan into executable tasks for external agents
```

### 3. Debugging Session
`debug_session.txt`:
```text
# Debug conversation
Switch to Debbie (agent D)

Check the last session for any errors

What monitoring alerts do you see?

Can you validate the workspace configuration?

Run the system_health_check tool
```

## Best Practices

1. **Start with agent switch**: Always begin by switching to the right agent
2. **Use descriptive names**: Make conversation purpose clear in the name
3. **Add waits when needed**: Some operations take time
4. **Keep messages natural**: Write as you would in interactive mode
5. **Save responses**: Store results for analysis

## Common Use Cases

1. **Automated Testing**: Replay test conversations to verify functionality
2. **Debugging**: Reproduce issues by replaying problem conversations  
3. **Demos**: Show consistent functionality with pre-recorded conversations
4. **CI/CD**: Include conversation replays in build pipelines
5. **Performance Testing**: Measure response times across conversations

## Troubleshooting

### "Conversation file not found"
- Check file exists in `scripts/conversations/`
- Ensure `.conv.json` extension
- Use full path if needed

### "Invalid conversation format"
- Validate JSON syntax
- Check message types are correct
- Ensure required fields present

### "Agent not responding"
- Verify agent is available
- Check previous messages completed
- Add wait time between messages

### "Tool execution failed"
- This usually means the agent tried to run something that failed
- Check the agent's response for error details
- The conversation replay continues despite tool failures

## Migration from Old Batch Mode

If you have old batch "scripts", convert them:

1. Rename `.json` to `.conv.json`
2. Move to `scripts/conversations/`
3. Update format if needed:
   ```json
   // Old format
   {
     "steps": [
       {"action": "switch_agent", "agent": "d"},
       {"command": "check health"}
     ]
   }
   
   // New format
   {
     "messages": [
       {"type": "switch_agent", "agent": "d"},
       {"type": "user_message", "content": "check health"}
     ]
   }
   ```

## Related Documentation

- [Debbie Conversation Examples](./DEBBIE_CONVERSATION_EXAMPLE.md)
- [Conversation File Format Reference](./conversation-replay/format-reference.md)
- [Python API Reference](./api/conversation-client.md)