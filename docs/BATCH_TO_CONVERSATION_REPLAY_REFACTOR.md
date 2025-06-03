# Comprehensive Refactor: Batch Mode → Conversation Replay Mode

## Overview
Rename "Batch Mode" to "Conversation Replay Mode" throughout the entire codebase to make it clear this is NOT traditional batch processing, but rather replaying recorded conversations with AI agents.

## Phase 1: Directory Structure Changes

### Current Structure:
```
ai_whisperer/extensions/batch/
├── __init__.py
├── client.py
├── debbie_integration.py
├── intervention.py
├── monitoring.py
├── script_processor.py
├── server_manager.py
├── websocket_client.py
└── websocket_interceptor.py
```

### New Structure:
```
ai_whisperer/extensions/conversation_replay/
├── __init__.py
├── client.py → conversation_client.py
├── debbie_integration.py
├── intervention.py
├── monitoring.py
├── script_processor.py → conversation_processor.py
├── server_manager.py
├── websocket_client.py
└── websocket_interceptor.py
```

## Phase 2: File Renames and Class Changes

### 2.1 Core Renames
```bash
# Directory rename
ai_whisperer/extensions/batch/ → ai_whisperer/extensions/conversation_replay/

# File renames
batch/client.py → conversation_replay/conversation_client.py
batch/script_processor.py → conversation_replay/conversation_processor.py

# Class renames
BatchClient → ConversationReplayClient
ScriptProcessor → ConversationProcessor
BatchMode → ConversationReplayMode
```

### 2.2 Import Updates
All imports need to change:
```python
# Old
from ai_whisperer.extensions.batch.client import BatchClient
from ai_whisperer.extensions.batch.script_processor import ScriptProcessor

# New
from ai_whisperer.extensions.conversation_replay.conversation_client import ConversationReplayClient
from ai_whisperer.extensions.conversation_replay.conversation_processor import ConversationProcessor
```

## Phase 3: CLI Changes

### 3.1 Command Name Change
```bash
# Old
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml batch script.txt

# New (support multiple aliases)
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay conversation.txt
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml conversation conversation.txt
python -m ai_whisperer.interfaces.cli.main --config config/main.yaml converse conversation.txt
```

### 3.2 CLI File Updates
`ai_whisperer/interfaces/cli/batch.py` → `ai_whisperer/interfaces/cli/conversation_replay.py`

Update the command registration:
```python
# Old
@register_command("batch")
class BatchCommand(BaseCommand):
    """Execute batch scripts"""

# New
@register_command("replay", aliases=["conversation", "converse"])
class ConversationReplayCommand(BaseCommand):
    """Replay recorded conversations with AI agents"""
```

## Phase 4: Documentation Updates

### 4.1 File Renames
```
docs/batch-mode/ → docs/conversation-replay/
docs/BATCH_MODE_USAGE_FOR_AI.md → docs/CONVERSATION_REPLAY_USAGE_FOR_AI.md
docs/DEBBIE_BATCH_MODE_EXAMPLE.md → docs/DEBBIE_CONVERSATION_REPLAY_EXAMPLE.md
```

### 4.2 Content Updates
Replace all instances of:
- "batch mode" → "conversation replay mode"
- "batch script" → "conversation file"
- "batch processing" → "conversation replay"
- "run batch" → "replay conversation"
- "batch client" → "conversation replay client"

### 4.3 Add Clarification Headers
Add to all relevant docs:
```markdown
## What This Is NOT

**This is NOT traditional batch processing!**

Conversation Replay Mode does NOT:
- Execute shell scripts in batch
- Process data files in batches
- Run background jobs
- Perform bulk operations

## What This IS

**This is conversation automation!**

Conversation Replay Mode DOES:
- Replay recorded conversations with AI agents
- Send messages line by line from a text file
- Automate interactive sessions
- Enable reproducible AI interactions
```

## Phase 5: Test Updates

### 5.1 Test Directory Renames
```
tests/integration/batch_mode/ → tests/integration/conversation_replay/
tests/unit/batch/ → tests/unit/conversation_replay/
```

### 5.2 Test File Updates
```
test_batch_mode_e2e.py → test_conversation_replay_e2e.py
test_batch_script_execution.py → test_conversation_replay.py
test_batch_command_tool.py → test_conversation_command_tool.py
```

## Phase 6: Configuration Updates

### 6.1 Config Schema
```yaml
# Old
batch_mode:
  enabled: true
  timeout: 300
  scripts_dir: "scripts/"

# New
conversation_replay:
  enabled: true
  timeout: 300
  conversations_dir: "scripts/conversations/"
```

### 6.2 Environment Variables
```bash
# Old
AIWHISPERER_BATCH_MODE_ENABLED=true
AIWHISPERER_BATCH_TIMEOUT=300

# New
AIWHISPERER_CONVERSATION_REPLAY_ENABLED=true
AIWHISPERER_CONVERSATION_TIMEOUT=300
```

## Phase 7: Logging Updates

Update all log messages:
```python
# Old
logger.info("Starting batch mode server")
logger.debug("Loading batch script")

# New
logger.info("Starting conversation replay server")
logger.debug("Loading conversation file")
```

## Phase 8: Error Messages

Update all error messages:
```python
# Old
raise ValueError("Invalid batch script format")
raise RuntimeError("Batch mode not enabled")

# New
raise ValueError("Invalid conversation file format")
raise RuntimeError("Conversation replay mode not enabled")
```

## Implementation Order

1. **Week 1: Core Renames**
   - Rename directories and files
   - Update imports
   - Fix immediate breaks

2. **Week 2: Functionality Updates**
   - Update CLI commands
   - Update class names
   - Update method names

3. **Week 3: Documentation**
   - Update all docs
   - Add clarification sections
   - Create migration guide

4. **Week 4: Polish**
   - Update tests
   - Update configs
   - Update logging

## Backwards Compatibility

### Transition Period (2 versions)
1. Keep `batch` as an alias for `replay` command
2. Show deprecation warning when `batch` is used
3. Auto-detect old format and suggest migration

### Migration Helper
```python
# Show helpful message
if command == "batch":
    print("⚠️  'batch' command is deprecated. Use 'replay' instead.")
    print("📝 This feature replays conversations, it doesn't do batch processing.")
    print("🔄 Your command still works, but please update to: ... replay conversation.txt")
```

## Benefits

1. **Clarity**: No confusion with traditional batch processing
2. **Accuracy**: Name describes what it actually does
3. **Discoverability**: Users understand the feature immediately
4. **Debugging**: Clearer error messages and logs

## Success Metrics

- Zero confusion about "batch processing" in issues
- New users understand the feature immediately
- AI assistants don't suggest batch processing solutions
- Documentation is self-explanatory