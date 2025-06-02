# BATCH MODE USAGE FOR AI ASSISTANTS

**CRITICAL: READ THIS ENTIRE DOCUMENT BEFORE USING BATCH MODE**

## Overview

AIWhisperer's batch mode is designed for automated testing and scripted interactions. It automatically manages its own server lifecycle on a random port.

## IMPORTANT: How Batch Mode Works

1. **Batch mode starts its own server automatically** on a random port
2. **DO NOT start a server manually** before running batch mode
3. **DO NOT use port 8000** - batch mode picks its own port
4. **The batch client handles everything** - server startup, execution, and cleanup

## Correct Usage

### ✅ CORRECT Way to Run Batch Mode:

```bash
# Just run the batch client directly - it handles everything!
python -m ai_whisperer.batch.batch_client scripts/your_test_script.json
```

### ❌ INCORRECT Ways (DO NOT DO THESE):

```bash
# WRONG - Don't start server first
python -m interactive_server.main &
python -m ai_whisperer.batch.batch_client scripts/test.json

# WRONG - Don't specify ports
python -m interactive_server.main --port 8000 &
python -m ai_whisperer.batch.batch_client scripts/test.json

# WRONG - Don't use complex shell commands
timeout 60 python -m ai_whisperer.batch.batch_client scripts/test.json
```

## How It Works Internally

1. **Automatic Server Management**:
   - Batch client starts a server on a random available port
   - Server runs in a subprocess
   - Client connects via WebSocket to the random port
   - Everything is cleaned up automatically when done

2. **Port Selection**:
   - Uses `get_random_port()` to find an available port
   - Typically uses ports in range 49152-65535
   - Never conflicts with existing servers

3. **Lifecycle**:
   ```
   Start batch_client → Find free port → Start server subprocess → 
   Connect WebSocket → Run script → Close connection → Shutdown server
   ```

## Example Test Scripts

### Simple Test
```json
{
  "metadata": {
    "title": "Simple Batch Test",
    "description": "Basic test of batch functionality"
  },
  "messages": [
    {
      "role": "user",
      "content": "Hello, this is a test"
    }
  ]
}
```

### Multi-Agent Test
```json
{
  "metadata": {
    "title": "Multi-Agent Test",
    "agent": "debbie"
  },
  "messages": [
    {
      "role": "user", 
      "content": "@debbie Can you check the system health?"
    },
    {
      "role": "user",
      "content": "@alice Can you list the files in the current directory?"
    }
  ]
}
```

## Common Issues and Solutions

### Issue: "Address already in use"
**Cause**: You started a server manually before running batch mode
**Solution**: Kill any running servers and just run the batch client

### Issue: "Connection refused"
**Cause**: Batch client couldn't start its server
**Solution**: Check permissions and available ports

### Issue: "RuntimeWarning about sys.modules"
**Cause**: Normal Python module loading behavior
**Solution**: This is just a warning and can be ignored

## Debugging Batch Mode

1. **Check the batch test report**:
   ```bash
   cat batch_test_report.json
   ```

2. **Look for server logs** (includes port number):
   ```bash
   ls -la logs/aiwhisperer_server_port*.log
   ```

3. **Enable debug logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   python -m ai_whisperer.batch.batch_client scripts/test.json
   ```

## Best Practices

1. **Keep test scripts simple** - One purpose per script
2. **Use descriptive metadata** - Helps identify tests in reports
3. **Don't mix interactive and batch modes** - They use different ports
4. **Let batch mode manage everything** - Don't try to control the server

## For AI Assistants Using This System

When a user asks you to run batch mode tests:

1. **ALWAYS** just run: `python -m ai_whisperer.batch.batch_client <script>`
2. **NEVER** start a server first
3. **NEVER** try to specify ports
4. **NEVER** use complex shell commands or background processes
5. **TRUST** the batch client to handle everything

Remember: The batch client is self-contained and manages its own server lifecycle. Your job is just to run it with the script file.

## Example Session for AI Assistants

```bash
# User: "Run the batch test for conversation persistence"
cd /home/deano/projects/AIWhisperer
python -m ai_whisperer.batch.batch_client scripts/test_conversation_persistence.json

# That's it! Don't do anything else!
```

## Current Status & Known Issues

⚠️ **IMPORTANT**: The batch mode implementation currently has some issues with server startup. The `python -m ai_whisperer.batch.batch_client` command exists but may not work reliably.

### Working Alternative

For now, use the test runner approach:

```bash
cd /home/deano/projects/AIWhisperer
PYTHONPATH=/home/deano/projects/AIWhisperer python tests/debugging-tools/run_batch_test.py scripts/your_script.json
```

This uses the same BatchClient but with a working entry point.

### Known Issues

1. **Server Manager**: The batch mode server manager tries to start uvicorn directly, but the interactive server needs its own initialization
2. **Module Loading**: The batch client module has import issues when run directly
3. **Port Management**: Server port selection works but startup logic needs fixing

## Summary

**Current Working Rule**: Use `PYTHONPATH=/home/deano/projects/AIWhisperer python tests/debugging-tools/run_batch_test.py <script>` until the main batch client is fixed.

The batch mode concept is sound and the core functionality works, but the entry point needs some fixes.