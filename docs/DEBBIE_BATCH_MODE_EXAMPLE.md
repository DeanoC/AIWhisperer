# Using Debbie with Batch Mode - Example Guide

This guide demonstrates how to use AIWhisperer's batch mode to run automated tasks with Debbie, the debugging agent.

## Overview

Batch mode allows you to run pre-scripted AI sessions without interactive input. This is perfect for:
- Automated testing and health checks
- Scheduled maintenance tasks
- Reproducible debugging sessions
- CI/CD integration

## Example: System Health Check with Debbie

### Method 1: Command Line Interface

The simplest way to run a batch script:

```bash
# Run the health check script
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml batch scripts/debbie_health_check_working.json
```

### Method 2: Python Script (Recommended for Integration)

For more control and integration into larger systems, use the Python API:

```python
#!/usr/bin/env python3
# See scripts/run_debbie_health_check.py for the complete example

import asyncio
from ai_whisperer.extensions.batch.client import BatchClient
from ai_whisperer.extensions.batch.server_manager import ServerManager

async def run_health_check():
    # Start server
    server_manager = ServerManager()
    port = server_manager.find_available_port()
    server_url = await server_manager.start_server(port)
    
    try:
        # Create client and run script
        client = BatchClient(server_url)
        await client.wait_for_ready()
        result = await client.run_script("scripts/debbie_health_check_working.json")
        
        # Process results
        if result.get('success'):
            print("✅ Health check completed!")
        else:
            print(f"❌ Failed: {result.get('error')}")
            
    finally:
        await server_manager.stop_server()

# Run it
asyncio.run(run_health_check())
```

### Method 3: Direct Script Formats

Batch scripts can be written in multiple formats:

#### JSON Format (Recommended)
```json
{
  "name": "Debbie System Health Check",
  "description": "Comprehensive system analysis",
  "steps": [
    {
      "action": "switch_agent",
      "agent": "d"
    },
    {
      "command": "Please run a system health check with verbose output"
    }
  ]
}
```

#### YAML Format
```yaml
name: Debbie System Health Check
description: Comprehensive system analysis
steps:
  - action: switch_agent
    agent: d
  - command: Please run a system health check with verbose output
```

#### Text Format (Natural Language)
```text
# Debbie System Health Check
switch to agent d
Please run a system health check with verbose output
```

## Supported Actions

The batch script parser supports these actions:

- `switch_agent` - Switch to a different agent (a, p, t, d, e)
- `read_file` - Read file contents
- `write_file` - Write to a file
- `create_file` - Create a new file
- `list_files` - List directory contents
- `execute_command` - Run shell commands
- `search_files` - Search for patterns in files
- `list_rfcs` - List RFC documents
- `create_rfc` - Create new RFC
- `update_rfc` - Update existing RFC

## Debbie-Specific Commands

When switched to Debbie (agent d), you can use these debugging commands:

```json
{
  "command": "Run system health check"
}
```

```json
{
  "command": "Check workspace validation"
}
```

```json
{
  "command": "Analyze session health for the last hour"
}
```

```json
{
  "command": "Monitor current session with active intervention"
}
```

## Error Handling

The batch runner provides detailed error information:

```python
result = await client.run_script("script.json")

if not result['success']:
    print(f"Error: {result['error']}")
    
    # Check individual step results
    for step in result.get('results', []):
        if step['status'] == 'error':
            print(f"Step {step['step_id']} failed: {step['error']}")
```

## Best Practices

1. **Always specify the agent first** - Start scripts by switching to the appropriate agent
2. **Use descriptive step IDs** - Makes debugging easier
3. **Handle errors gracefully** - Check success status and handle failures
4. **Save results** - Store output for analysis and debugging
5. **Use appropriate timeouts** - Health checks may take time

## Complete Example

See these files for working examples:
- `/scripts/debbie_health_check_working.json` - The batch script
- `/scripts/run_debbie_health_check.py` - Python runner with full error handling
- `/scripts/debbie_health_check.txt` - Natural language format example

## Running the Example

```bash
# Method 1: Direct CLI
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml batch scripts/debbie_health_check_working.json

# Method 2: Python script
python scripts/run_debbie_health_check.py

# Method 3: From any Python code
import subprocess
subprocess.run([
    "python", "-m", "ai_whisperer.interfaces.cli.main",
    "--config", "config/main.yaml",
    "batch", "scripts/debbie_health_check_working.json"
])
```

## Integration with CI/CD

Batch mode is perfect for CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run AIWhisperer Health Check
  run: |
    python -m ai_whisperer.interfaces.cli.main \
      --config config/main.yaml \
      batch scripts/debbie_health_check_working.json
    
- name: Check Results
  run: |
    python -c "
    import json
    with open('health_check_results.json') as f:
        result = json.load(f)
        if not result['success']:
            raise Exception('Health check failed')
    "
```

## Troubleshooting

Common issues and solutions:

1. **"Tool registry not set"** - Make sure you're using the latest code with tool registry fixes
2. **"Action not allowed"** - Check the ALLOWED_ACTIONS list in script_parser_tool.py
3. **"Agent not found"** - Ensure agents are loaded from config/agents/agents.yaml
4. **WebSocket connection errors** - Check that the server started successfully

For more information, see:
- [Batch Mode Documentation](./batch-mode/USER_GUIDE.md)
- [Agent Documentation](./AGENT_P_RFC_IMPLEMENTATION_CHECKLIST.md)
- [System Architecture](./architecture/architecture.md)