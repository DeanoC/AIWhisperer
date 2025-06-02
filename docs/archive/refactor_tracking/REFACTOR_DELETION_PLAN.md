# AIWhisperer Refactor Deletion Plan

## Critical Discovery
Only **37% of Python files** are actually used! The codebase has 223 unused files out of 352 total.

## Immediate Deletions (Safe)

### 1. Obsolete Code (17 files)
**Old AI Loop**:
- `ai_whisperer/ai_loop/ai_loopy.py` ❌ Replaced by stateless

**Agent E Experimental System**:
- `ai_whisperer/agents/agent_e_handler.py` ❌
- `ai_whisperer/agents/agent_e_exceptions.py` ❌
- `ai_whisperer/agents/external_agent_result.py` ❌

**Old Planning System**:
- `ai_whisperer/agents/planner_handler.py` ❌
- `ai_whisperer/agents/planner_tools.py` ❌
- `ai_whisperer/plan_parser.py` ❌

**Old State Management**:
- `ai_whisperer/state_management.py` ❌
- `ai_whisperer/context_management.py` ❌

**Old Processing**:
- `ai_whisperer/processing.py` ❌
- `ai_whisperer/json_validator.py` ❌

**Obsolete Entry Points**:
- `ai_whisperer/main.py` ❌ Shows deprecation
- `ai_whisperer/batch/__main__.py` ❌ Not used
- `ai_whisperer/interactive_entry.py` ❌ Old entry

**Other**:
- `ai_whisperer/execution_engine.py` ❌ If it exists
- `ai_whisperer/delegate_manager.py` ❌ If it exists
- `ai_whisperer/model_override.py` ❌ Not imported

### 2. Obsolete Directories (Entire Folders)
```
project_dev/           ❌ All prototype/obsolete (146 JSON files)
.WHISPER/              ❌ Test artifacts only
```

### 3. Documentation Cleanup (Based on New Understanding)
**Obsolete Docs**:
- All Agent E execution logs (7 files) ❌
- All delegate system docs ❌
- All runner/execution engine docs ❌
- Project development phase summaries ❌
- Multiple test status summaries ❌

**Keep Only**:
- Current architecture docs
- User guides
- API documentation
- README files

### 4. Temporary Files (119 files)
```
*.txt test outputs     ❌ All test output files
debug_*.txt           ❌ Debug outputs
test_*.txt            ❌ Test scripts
```

## Archive (Move to archive/)

### Development History
```
archive/
├── old_architecture/
│   ├── ai_loopy.py
│   ├── agent_e_system/
│   ├── planner_system/
│   └── state_management/
├── project_dev_history/
│   └── [compressed project_dev]
└── docs_history/
    └── [old execution logs]
```

## Keep But Review

### Suspicious But Possibly Used
- Tools that aren't registered but might be imported
- Command modules that might be dynamically loaded
- Test utilities that might be needed

## Updated Statistics

### Before Refactor
- Python files: 352
- Test files: 157
- Documentation: 239
- Misc files: 265
- **Total: ~1,013 files**

### After Refactor (Estimated)
- Python files: 129 (active only)
- Test files: 157 (keep all)
- Documentation: ~40 (consolidated)
- Misc files: ~50 (configs/scripts)
- **Total: ~376 files (63% reduction!)**

## Deletion Priority

### Phase 1: Immediate Safe Deletions
1. Delete all files marked ❌ above
2. Delete project_dev/ directory
3. Delete .WHISPER/ directory
4. Delete all .txt temporary files

### Phase 2: Archive Old Systems
1. Create archive/ directory structure
2. Move old architecture files
3. Compress and archive historical docs

### Phase 3: Documentation Consolidation
1. Merge redundant status files
2. Archive old execution logs
3. Update remaining docs

### Phase 4: Test and Verify
1. Run full test suite
2. Test both entry points
3. Verify no broken imports

## Commands for Phase 1

```bash
# Create backup first
tar -czf pre_refactor_backup.tar.gz .

# Delete obsolete Python files
rm ai_whisperer/ai_loop/ai_loopy.py
rm ai_whisperer/agents/agent_e_*.py
rm ai_whisperer/agents/planner_*.py
# ... etc

# Delete obsolete directories
rm -rf project_dev/
rm -rf .WHISPER/

# Delete temporary files
rm *.txt
find . -name "debug_*.txt" -delete
```

## Risk Assessment
- **Low Risk**: Deleting clearly obsolete code
- **Medium Risk**: Removing entire directories
- **Mitigation**: Full backup + git tag before starting

---
*Generated: 2025-01-06*