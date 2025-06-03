# CONVERSATION REPLAY MODE USAGE FOR AI ASSISTANTS

**CRITICAL: This is NOT batch processing! Read [NOT_BATCH_PROCESSING.md](./NOT_BATCH_PROCESSING.md) first!**

## What is Conversation Replay Mode?

Conversation Replay Mode (formerly misnamed "batch mode") replays recorded conversations with AI agents. It reads a text file and sends each line as a message, just like a human typing in interactive mode.

## Quick Start

```bash
# Replay a conversation
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay conversations/health_check.txt

# Or use aliases
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml conversation conversations/test.txt
```

## Conversation File Format

**Simple text files** where each line is a message:

```text
# health_check.txt
# Comments start with #

Switch to agent D (Debbie)

Hi Debbie! Please run a system health check

Use the system_health_check tool with verbose output

What should we fix first?
```

That's it! No JSON, no special syntax, just messages.

## How It Works

1. **Reads** the conversation file line by line
2. **Skips** comments (lines starting with #) and empty lines
3. **Sends** each line as a message to the current agent
4. **Waits** for the response before sending the next line
5. **Collects** all responses for review

## Complete Example

### 1. Create a conversation file

`conversations/test_agents.txt`:
```text
# Test multiple agents
Hi! What agent are you?

Please list all available agents

Switch to Patricia (agent P)

Hi Patricia! Can you create a simple RFC for a calculator?

Now switch to Debbie (agent D)

Debbie, can you check if the RFC was created?
```

### 2. Run the conversation

```bash
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay conversations/test_agents.txt
```

### 3. What happens

- Starts with default agent (Alice)
- Alice responds to greeting and lists agents
- Switches to Patricia
- Patricia creates an RFC
- Switches to Debbie
- Debbie checks the RFC

## Common Patterns

### Agent Switching
```text
Switch to agent D
Switch to Debbie (agent D)
Please change to agent P
Can you hand this off to Eamonn?
```

### Tool Usage
```text
Run the system_health_check tool
Please use workspace_validator
Can you execute the list_rfcs tool?
Check the session health
```

### Natural Conversation
```text
Hi! How are you?
Can you help me with this?
What do you think?
Thanks for your help!
```

## What NOT to Put in Conversation Files

❌ **Shell commands** - Won't execute
```text
ls -la  # ❌ This just sends "ls -la" as a message
```

❌ **Scripts** - Won't run
```text
#!/bin/bash  # ❌ This is just sent as text
echo "test"
```

❌ **Special syntax** - Not needed
```text
{"action": "switch_agent"}  # ❌ Just say "switch to agent X"
```

✅ **Natural messages** - This works!
```text
Please list the files in the current directory
Can you show me what's in this folder?
```

## Advanced Usage

### With Timeout
```bash
# 10 minute timeout for long conversations
ai_whisperer replay long_conversation.txt --timeout 600
```

### Dry Run
```bash
# See what would be sent without running
ai_whisperer replay test.txt --dry-run
```

### Save Transcript
```bash
# Save the conversation to a file
ai_whisperer replay test.txt --output transcript.txt
```

### Verbose Mode
```bash
# See detailed server output
ai_whisperer replay test.txt --verbose
```

## Python API

```python
from ai_whisperer.extensions.conversation_replay import ConversationReplayClient, ServerManager

async def replay():
    # Start server
    manager = ServerManager()
    server_url = await manager.start_server()
    
    try:
        # Connect and replay
        client = ConversationReplayClient(server_url)
        await client.connect()
        
        results = await client.replay_conversation("conversations/test.txt")
        
        # Process results
        for msg in results:
            print(f"Sent: {msg['message']}")
            print(f"Got: {msg['response']}")
            
    finally:
        await manager.stop_server()
```

## Troubleshooting

### "Is this batch processing?"
NO! See [NOT_BATCH_PROCESSING.md](./NOT_BATCH_PROCESSING.md)

### "Can it run my shell script?"
NO! It sends messages to AI agents, not execute scripts.

### "Why isn't my JSON working?"
Conversation files are plain text, not JSON. Each line is a message.

### "How do I execute commands?"
Ask the AI agent naturally: "Please run the Python tests"

## Best Practices

1. **Use descriptive filenames**: `test_rfc_creation.txt`, not `script1.txt`
2. **Add comments**: Explain what each section does
3. **Keep it natural**: Write like you're chatting
4. **Test incrementally**: Start with short conversations
5. **Use the right tool**: This is for AI conversations only

## Migration from Old "Batch Mode"

If you have old "batch scripts":

1. **Rename files**: `*.json` → `*.txt` 
2. **Convert format**: Remove JSON, keep just the messages
3. **Update commands**: `batch` → `replay`
4. **Move location**: `scripts/` → `conversations/`

Old:
```json
{
  "steps": [
    {"action": "switch_agent", "agent": "d"},
    {"command": "check health"}
  ]
}
```

New:
```text
Switch to agent D
check health
```

## Remember

- 🎬 **Replays conversations** - Not batch processing
- 💬 **Sends messages** - Not executing scripts  
- 📝 **Plain text files** - Not JSON or code
- 🤖 **AI interprets** - Natural language understanding