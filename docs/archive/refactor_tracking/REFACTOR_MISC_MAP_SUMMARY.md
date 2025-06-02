# AIWhisperer Miscellaneous Files Summary

## Overview
Beyond code, tests, and documentation, the project contains significant configuration and artifact files that need attention.

## Configuration Files

### Core Configs (16 files)
```
Root Level:
- config.yaml              # Main app config
- pyproject.yaml          # Python project metadata
- pytest.ini              # Test configuration
- requirements.txt        # Python dependencies
- package.json            # Node dependencies

Subsystem Configs:
- agents.yaml             # Agent definitions
- tool_sets.yaml          # Tool configurations
- 3 aiwhisperer_config.yaml files (scattered)

Schemas:
- 7 JSON schema files for validation
```

### Issues with Configs
1. **Multiple aiwhisperer_config.yaml** files in different directories
2. **No config directory** - configs scattered throughout
3. **Mix of formats** - YAML, JSON, INI

## Scripts (23 files)

### Python Scripts (6)
- **Analysis scripts** (3): Created for this refactor
- **Test utilities** (2): check_settings_persistence.py, run_isolated_server.py
- **Tool scripts** (1): test_patricia_structured_plan.py

### Batch Test Scripts (14 JSON files)
- Continuation tests (5 files)
- RFC/Plan tests (4 files)
- Chat/conversation tests (3 files)
- Other tests (2 files)

### Shell Scripts (3)
- `start_server.sh` (executable)
- `setup_worktree_venv.sh` (executable)
- `format_code.bat` (Windows)

## Project Development Artifacts

### project_dev/ Directory
```
Total: 146 JSON files
- Completed tasks: 111 files
- In development: 35 files

Structure per feature:
- Main task JSON
- Overview JSON
- 5-10 subtask JSONs
```

### Major Issues
1. **Historical bloat**: 111 completed task JSONs
2. **No archival**: All completed tasks still active
3. **Excessive granularity**: Each subtask has own JSON

## .WHISPER Directory (Project Workspace)
```
.WHISPER/
├── project.json          # Project configuration
├── plans/               # 4 plan files
│   └── in_progress/     # 2 active plans
└── rfc/                 # 6 RFC files (3 .md + 3 .json)
    └── in_progress/     # 3 active RFCs
```

## Temporary/Test Output Files (119 files)

### Test Output TXT Files (19)
- `test_*.txt` files (output from test runs)
- `debug_*.txt` files (debugging outputs)
- `batch_test_result.txt`
- Large files: `test_with_env.txt` (144KB)

### Log Directories
- `logs/` - Application logs
- `ai_whisperer/logging/` - Logging module
- `.git/logs/` - Git logs

### Build Artifacts
- `frontend/build/` - React build output
- `__pycache__/` directories
- `.pyc` files

## Cleanup Recommendations

### 1. Configuration Consolidation
```
config/
├── app.yaml              # Main configuration
├── agents.yaml           # Agent definitions
├── tools.yaml            # Tool configurations
├── test/                 # Test-specific configs
└── examples/             # Example configurations
```

### 2. Script Organization
```
scripts/
├── analysis/             # Code analysis tools
├── testing/              # Test utilities
├── batch/                # Batch mode test scripts
└── setup/                # Setup and installation
```

### 3. Archive Historical Artifacts
- Move `project_dev/done/` to compressed archive
- Keep only last 30 days of completed tasks
- Consolidate subtask JSONs into single file per feature

### 4. Clean Temporary Files
**Delete immediately**:
- All `*.txt` test output files
- `debug_*.txt` files
- Old batch test results

**Add to .gitignore**:
```
*.txt
debug_*
test_output/
logs/
```

### 5. Standardize Project Structure
```
.WHISPER/             # Active project workspace
archive/              # Historical artifacts (compressed)
config/               # All configuration files
scripts/              # Utility scripts
schemas/              # JSON schemas
```

## Impact Summary
- **Files to move**: ~50 (configs and scripts)
- **Files to archive**: ~146 (project_dev artifacts)
- **Files to delete**: ~119 (temporary outputs)
- **Total reduction**: ~265 files (55% of non-code files)

---
*Generated: 2025-01-06*