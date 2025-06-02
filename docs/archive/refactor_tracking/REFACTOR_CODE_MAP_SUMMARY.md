# AIWhisperer Code Map Summary

## Core Modules Overview

### 1. Main Package Structure (`ai_whisperer/`)
```
ai_whisperer/
├── __init__.py           # Package initialization
├── __main__.py           # Entry point
├── cli.py                # CLI main entry (102 lines)
├── config.py             # Configuration loader (204 lines)
├── main.py               # Main orchestration
└── [utility modules]     # Various utilities
```

### 2. Core Systems

#### AI Loop (`ai_loop/`) - 5 files
- `ai_loopy.py` - Main AI interaction loop
- `stateless_ai_loop.py` - Stateless implementation
- `ai_config.py` - AI configuration
- `tool_call_accumulator.py` - Tool call handling

#### Agents (`agents/`) - 24 files
- `agent.py` - Base agent class
- `stateless_agent.py` - Stateless agent implementation
- `planner_handler.py` - Planning agent
- `agent_e_handler.py` - Agent E (external agent)
- `factory.py` - Agent factory
- `registry.py` - Agent registry
- `mailbox.py`, `mailbox_tools.py` - Inter-agent communication
- Various agent-specific handlers and tools

#### Tools (`tools/`) - 54 files
**Categories:**
- **File Operations**: read_file, write_file, get_file_content, list_directory
- **Project Analysis**: analyze_dependencies, analyze_languages, workspace_stats
- **RFC/Plan Management**: create_rfc, read_rfc, create_plan_from_rfc, etc.
- **Development Tools**: python_executor, execute_command, find_pattern
- **Agent Communication**: check_mail, send_mail, reply_mail
- **Specialized**: web_search, fetch_url, session_analysis

#### AI Service (`ai_service/`) - 3 files
- `ai_service.py` - Base AI service interface
- `openrouter_ai_service.py` - OpenRouter implementation
- `tool_calling.py` - Tool calling utilities

#### Batch Mode (`batch/`) - 10 files
- `batch_client.py` - Batch mode client
- `script_processor.py` - Script processing
- `websocket_client.py` - WebSocket communication
- `monitoring.py` - Batch monitoring
- `debbie_integration.py` - Debbie agent integration

#### Commands (`commands/`) - 11 files
- Command implementations for CLI
- Agent-specific commands
- Session management commands

### 3. Support Systems

#### Context Management (`context/`) - 5 files
- Context tracking and management for agents

#### Logging (`logging/`) - 3 files
- Custom logging implementations
- Log aggregation

#### Postprocessing (`postprocessing/`)
- Pipeline for processing AI outputs
- Scripted transformation steps

### 4. Interactive Server (`interactive_server/`)
- FastAPI-based WebSocket server
- Stateless session management
- JSON-RPC message handling

### 5. Frontend (`frontend/`)
- React TypeScript application
- WebSocket client
- UI components for chat and agent interaction

## Key Findings

### Orphaned Code (Safe to Delete)
1. **execution_engine** - 0 imports, completely unused
2. **delegates** - 1 import only, legacy system

### Problematic Patterns
1. **Circular Dependencies**: tools ↔ agents.mailbox
2. **Duplicate Functionality**: 
   - `read_file_tool.py` vs `get_file_content_tool.py`
   - Multiple context management files
3. **Inconsistent Naming**:
   - `agent_e_*` files vs standard naming
   - `ai_loopy.py` vs snake_case convention

### Tool Registration Issues
- 5 tools not in main registry:
  - `python_ast_json_tool.py` (tested but not registered)
  - `create_plan_from_rfc_tool.py` (only in tests)
  - Mail tools (registered separately)

### Architecture Transition
- Mix of stateless and old delegate patterns
- Some modules still reference old architecture
- Tests still use runner concepts

## Recommendations for Refactoring

1. **Immediate Deletions**:
   - Remove execution_engine
   - Archive delegate references
   - Clean up unused imports

2. **Consolidations**:
   - Merge duplicate file reading tools
   - Unify context management
   - Centralize tool registration

3. **Naming Standardization**:
   - Rename `ai_loopy.py` → `ai_loop_legacy.py`
   - Standardize agent_e file naming
   - Apply consistent snake_case

4. **Architecture Cleanup**:
   - Complete transition to stateless
   - Remove circular dependencies
   - Update tests to new patterns

---
*Generated: 2025-01-06*