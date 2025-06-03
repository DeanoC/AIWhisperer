# Batch Mode to Conversation Mode Refactoring Plan

## Overview
Rename "Batch Mode" to "Conversation Replay Mode" to clearly distinguish between:
- **Conversations/Dialogues**: Message sequences sent to agents (what batch mode does)
- **Scripts**: Executable test/command files that agents like Debbie run

## Phase 1: Core Module Renames

### 1.1 File Renames
```bash
# Core processor - THIS IS THE KEY RENAME
ai_whisperer/extensions/batch/script_processor.py → ai_whisperer/extensions/batch/conversation_processor.py

# Update class names in these files
ScriptProcessor → ConversationProcessor
ScriptFileNotFoundError → ConversationFileNotFoundError
self.commands → self.messages
get_next_command() → get_next_message()
load_script() → load_conversation()
```

### 1.2 Directory Structure
```bash
# Create new structure
scripts/conversations/  # For conversation files
scripts/examples/       # For Python examples

# Move existing "scripts" to conversations
scripts/debbie_health_check.json → scripts/conversations/debbie_health_check.conv.json
scripts/test_*.json → scripts/conversations/test_*.conv.json
```

### 1.3 File Extension Convention
- Conversations: `.conv.json`, `.conversation.json`, `.dialogue.json`
- Scripts (Debbie executable): Keep `.json`, `.yaml`, `.txt`

## Phase 2: Code Changes

### 2.1 Method/Variable Renames
```python
# In conversation_processor.py
script_path → conversation_path
load_script() → load_conversation()
get_next_command() → get_next_message()
commands → messages

# In batch_client.py  
run_script() → replay_conversation()
script_runner → conversation_replayer

# In CLI commands
batch → conversation or replay
--script → --conversation
```

### 2.2 Class Renames
- `BatchClient` → `ConversationClient`
- `BatchCommandTool` → Keep as is (it executes actual scripts)
- `ScriptParserTool` → Keep as is (it parses actual scripts)

### 2.3 Configuration Updates
```yaml
# In config files
batch_mode:
  enabled: true
  scripts_dir: "scripts/"

# Becomes
conversation_replay:
  enabled: true
  conversations_dir: "scripts/conversations/"
```

## Phase 3: Documentation Updates

### 3.1 Rename Documentation Files
- `BATCH_MODE_USAGE_FOR_AI.md` → `CONVERSATION_REPLAY_USAGE_FOR_AI.md`
- `DEBBIE_BATCH_MODE_EXAMPLE.md` → `DEBBIE_CONVERSATION_EXAMPLE.md`
- `docs/batch-mode/` → `docs/conversation-replay/`

### 3.2 Update Content
Replace terminology throughout:
- "batch script" → "conversation sequence"
- "run script" → "replay conversation"
- "script file" → "conversation file"
- "batch mode" → "conversation replay mode"

### 3.3 Add Clear Distinction Section
Add to all relevant docs:
```markdown
## Important Distinction

**Conversations** (for replay mode):
- Sequences of messages sent to agents
- Like a movie script - just dialogue
- Files: `.conv.json`, `.dialogue.json`
- Used by conversation replay mode

**Scripts** (executable by agents):
- Actual executable test/command scripts
- Parsed and run by tools like Debbie's batch_command_tool
- Files: `.json`, `.yaml`, `.txt` in test directories
- Contain actions, validations, commands
```

## Phase 4: Command Updates

### 4.1 CLI Interface
```bash
# Old
python -m ai_whisperer.cli batch scripts/test.json

# New (support both during transition)
python -m ai_whisperer.cli replay conversations/test.conv.json
python -m ai_whisperer.cli conversation conversations/test.conv.json
```

### 4.2 Error Messages
Update all error messages:
- "Script not found" → "Conversation file not found"
- "Invalid script format" → "Invalid conversation format"
- "Script execution failed" → "Conversation replay failed"

## Phase 5: Testing Updates

### 5.1 Test File Renames
```bash
test_batch_mode.py → test_conversation_replay.py
test_script_processor.py → test_conversation_processor.py
```

### 5.2 Test Data
Move test conversations to proper location:
```bash
tests/fixtures/scripts/ → tests/fixtures/conversations/
```

## Phase 6: Migration Support

### 6.1 Backwards Compatibility
- Keep old command names as aliases for 2 versions
- Auto-detect old format and suggest migration
- Provide migration script for user files

### 6.2 Migration Script
Create `scripts/migrate_to_conversations.py`:
- Rename user's .json files to .conv.json
- Update format if needed
- Move to conversations/ directory

## Implementation Order

1. **Week 1**: Core renames (Phase 1-2)
   - File/class renames
   - Method updates
   - Basic functionality working

2. **Week 2**: Documentation (Phase 3)
   - Update all docs
   - Add examples
   - Clear distinction guides

3. **Week 3**: Polish (Phase 4-6)
   - CLI updates
   - Testing updates
   - Migration support

## Benefits

1. **Clarity**: No more confusion between conversation replay and script execution
2. **Debugging**: Easier to understand what's happening
3. **Documentation**: Clearer for new users and AI assistants
4. **Maintenance**: Better code organization

## Risks & Mitigation

1. **Breaking Changes**: Mitigate with backwards compatibility
2. **User Confusion**: Clear migration guide and examples
3. **Test Failures**: Update tests incrementally

## Success Metrics

- Zero confusion in issues/discussions about "scripts" vs "conversations"
- Improved debugging efficiency
- Clearer documentation
- Better AI assistant understanding