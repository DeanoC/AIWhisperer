# AIWhisperer Current State Snapshot

## Baseline Metrics (2025-01-06)

### File Counts (Excluding Dependencies)
- **Python files**: 345
- **Test files**: 156 (45% of Python files)
- **Documentation files**: 231
- **JSON files**: 197 (mostly in project_dev/)
- **YAML configs**: ~15-20 (estimated)

### Directory Structure
```
AIWhisperer/
├── ai_whisperer/           # Main package (345 Python files)
│   ├── agents/             # Agent system
│   ├── ai_loop/           # Core AI interaction
│   ├── ai_service/        # AI service interfaces
│   ├── batch/             # Batch mode
│   ├── commands/          # CLI commands
│   ├── context/           # Context management
│   ├── logging/           # Logging system
│   └── tools/             # Tool registry (54 files)
├── interactive_server/     # WebSocket server
├── frontend/              # React TypeScript UI
├── tests/                 # Test suite (156 test files)
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── interactive_server/# Server tests
├── docs/                  # Documentation (231 files)
├── project_dev/           # Development artifacts
├── prompts/               # AI prompts
├── schemas/               # JSON schemas
├── templates/             # Templates
└── postprocessing/        # Output processing
```

### Configuration Files
- Root: `config.yaml`, `pytest.ini`, `pyproject.yaml`
- Agent configs: `ai_whisperer/agents/config/agents.yaml`
- Tool configs: `ai_whisperer/tools/tool_sets.yaml`
- Multiple test configs scattered

### Active Components
1. **CLI Batch Mode**: Working, used for automation
2. **Interactive Server**: FastAPI + WebSocket
3. **React Frontend**: TypeScript UI
4. **Agent System**: Alice, Patricia, Tessa, Debbie, Planner
5. **Tool System**: 54 tools for various operations

### Known Issues
1. **Orphaned Code**: Delegate system, old runner
2. **Documentation Overload**: 231 .md files
3. **Test Organization**: Mixed types, demos with tests
4. **Naming Inconsistencies**: agent_e_*, various patterns
5. **Configuration Scatter**: Configs in multiple locations
6. **Development Artifacts**: 197 JSON files in project_dev

### Git State
- Branch: `refactor-proto-to-prod`
- Tag: `before-refactor-proto-to-prod`
- Clean working tree (only new refactor docs untracked)

---

*Snapshot taken: 2025-01-06*  
*Purpose: Baseline for refactor comparison*