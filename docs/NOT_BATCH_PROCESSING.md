# This is NOT Batch Processing!

## Common Misconception

When you see "batch mode" in AIWhisperer, you might think it does traditional batch processing like:
- ❌ Running shell scripts in batch
- ❌ Processing multiple files at once
- ❌ Executing background jobs
- ❌ Bulk data operations
- ❌ Scheduled task execution

**None of these are what it does!**

## What It Actually Does

**Conversation Replay Mode** (formerly "batch mode") simply:
- ✅ Reads a text file line by line
- ✅ Sends each line as a message to an AI agent
- ✅ Like playing back a recorded conversation
- ✅ Automates interactive AI sessions

## Visual Comparison

### Traditional Batch Processing (NOT what we do)
```bash
# Process 1000 files
for file in *.csv; do
    process_data "$file"
done

# Run multiple jobs
job1 &
job2 &
job3 &
wait
```

### Conversation Replay (what we ACTUALLY do)
```text
# conversation.txt
Hi Alice!
Can you help me debug this issue?
Please check the error logs
What do you think is wrong?
```

Each line is sent as if you typed it in the interactive mode.

## Why The Confusion?

The original name "batch mode" was misleading because:
1. It sounds like batch processing
2. People expect it to run scripts
3. The documentation wasn't clear

## The Solution: Renamed to Conversation Replay

Now it's clear:
- **Name**: Conversation Replay Mode
- **Purpose**: Replay recorded conversations
- **Files**: `.conversation.txt` files
- **Command**: `replay` (not `batch`)

## Examples

### WRONG Expectation (doesn't work)
```bash
# This is NOT what it does
echo "CREATE DATABASE test;" > batch.sql
ai_whisperer batch batch.sql  # ❌ Won't execute SQL
```

### RIGHT Usage (this works)
```text
# conversation.txt
Switch to agent D (Debbie)
Please check the database status
Can you validate the schema?
```

```bash
# This replays the conversation
ai_whisperer replay conversation.txt  # ✅ Sends messages to AI
```

## Key Takeaways

1. **It's NOT batch processing** - It's conversation replay
2. **Files are conversations** - Not scripts to execute
3. **Each line is a message** - Like typing in chat
4. **AI interprets naturally** - No special commands

## If You Need Actual Batch Processing

If you need traditional batch processing:
- Use your shell directly (bash, PowerShell, etc.)
- Use Python scripts
- Use cron jobs or task schedulers
- This tool is for AI conversations only

## TL;DR

- ❌ **NOT**: Script execution, bulk operations, background jobs
- ✅ **IS**: Automated AI conversations, message replay, testing interactions