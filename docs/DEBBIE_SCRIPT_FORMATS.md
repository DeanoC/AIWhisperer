# Debbie's Script Format Support

This document describes the different script formats that Debbie the Debugger supports for batch processing.

## Supported Formats

Debbie supports three script formats for batch execution:

### 1. JSON Format (.json)
Structured scripts with metadata and parameterized commands.

**Structure:**
```json
{
  "name": "Script Name",
  "description": "Description of what the script does",
  "steps": [
    {"command": "command_name"},
    {"command": "command_with_params", "param1": "value1", "param2": "value2"}
  ]
}
```

**Example:**
```json
{
  "name": "Project Settings End-to-End Flow",
  "description": "Test that project settings persist from UI to backend and disk",
  "steps": [
    { "command": "open_settings_ui" },
    { "command": "set_project_setting", "field": "default_agent", "value": "alice" },
    { "command": "save_settings" }
  ]
}
```

### 2. YAML Format (.yaml, .yml)
Human-readable configuration format, similar structure to JSON.

**Example:**
```yaml
name: "Create RFC Workflow"
description: "Automated RFC creation process"
steps:
  - command: "switch_agent"
    agent: "p"
  - command: "list_rfcs"
  - command: "create_rfc"
    params:
      title: "New Feature Design"
      description: "Design document for feature X"
```

### 3. Plain Text Format (.txt, .script)
Simple line-by-line commands, most basic format.

**Example:**
```
# This is a comment
switch to agent p
list all RFCs
create new RFC with title "Test RFC"
# Another comment
validate the RFC
```

## Tools Available in Batch Mode

When running in batch mode, Debbie has access to these tools:

### Core Debugging Tools
- `session_health` - Check health status of sessions
- `session_analysis` - Analyze session patterns and performance  
- `monitoring_control` - Control monitoring settings
- `session_inspector` - Inspect session details
- `message_injector` - Inject messages for testing
- `workspace_validator` - Validate workspace setup

### Script Processing Tools
- `script_parser` - Parse batch scripts (JSON, YAML, or text)
- `batch_command` - Execute batch commands
- `python_executor` - Execute Python scripts

## Usage

### Command Line Interface
```bash
# Basic execution
python -m ai_whisperer.cli --config config.yaml script.json

# Dry run (echo commands without execution)
python -m ai_whisperer.cli --config config.yaml --dry-run script.txt

# Examples
python -m ai_whisperer.cli --config config.yaml scripts/test_settings.json
python -m ai_whisperer.cli --config config.yaml --dry-run scripts/debug_session.txt
```

### Batch Server Architecture
When running batch scripts, Debbie:

1. **Starts Dedicated Server**: Launches a new interactive server on a random port (20000-40000)
2. **Port-Specific Logging**: Creates log files with port suffix (e.g., `aiwhisperer_server_batch_25432.log`)
3. **WebSocket Connection**: Connects to the batch server via WebSocket
4. **Session Management**: Starts a dedicated session for batch execution
5. **Sequential Execution**: Processes commands one by one as if typed by a user
6. **Cleanup**: Stops session and server when complete

### Log Files
- **Main server logs**: `logs/aiwhisperer_server.log`
- **Batch server logs**: `logs/aiwhisperer_server_batch_[PORT].log`
- **Debug logs**: `logs/aiwhisperer_debug_batch_[PORT].log`
- **Test logs**: `logs/aiwhisperer_test_batch_[PORT].log`

## Current Status

### ✅ Working Features
- ✅ JSON script parsing with `script_parser` tool
- ✅ Dry-run mode for testing scripts
- ✅ Port-specific logging for batch servers
- ✅ Console output with emojis and progress indicators
- ✅ Workspace validation before execution
- ✅ Error handling and cleanup

### ⚠️ Known Issues
- ⚠️ Batch server startup may hang in some cases
- ⚠️ WebSocket connection timing issues
- ⚠️ Tool parameter passing needs investigation

### 🔧 Improvements Made
- 🔧 Added port-specific log files to avoid conflicts
- 🔧 Enhanced console output for better debugging
- 🔧 Fixed CLI import issues
- 🔧 Added proper error handling and cleanup messages

## Testing

### Backend Integration Test
```bash
cd /home/deano/projects/feature-settings
python -m pytest tests/integration/test_project_settings_persistence.py -v
```

### Batch Script Testing
```bash
# Test script parsing
python -c "
from ai_whisperer.tools.script_parser_tool import ScriptParserTool
tool = ScriptParserTool()
result = tool.execute(file_path='scripts/test_project_settings_flow.json')
print('Result:', result)
"

# Test dry-run execution
python -m ai_whisperer.cli --config config.yaml --dry-run scripts/test_script_parser.txt
```

## Example Scripts

### Project Settings Test (JSON)
Location: `scripts/test_project_settings_flow.json`
Purpose: Test project settings persistence through UI workflow

### Script Parser Test (Text)
Location: `scripts/test_script_parser.txt`
Purpose: Test script_parser tool functionality

## Next Steps

1. **Debug Batch Server Startup**: Investigate why batch server hangs during startup
2. **Tool Parameter Investigation**: Ensure proper parameter passing to tools
3. **End-to-End Testing**: Complete settings flow testing once batch mode is stable
4. **Documentation**: Expand examples and troubleshooting guides
