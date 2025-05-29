# Batch Mode Implementation Plan

> **TDD Policy (applies to all phases):**
> All new features and modules must be developed using strict Test-Driven Development (TDD). This means:
> - Tests must be fully implemented first, and must fail (RED) before any production code is written.
> - Test names and logic should reflect the intended feature/behavior, not the absence of it (e.g., use `test_server_starts_on_valid_port` instead of `test_server_does_not_fail_to_start`).
> - Only after confirming failing tests should implementation proceed to make them pass (GREEN).
> - This policy applies to all phases and all batch mode components.

**Date**: May 29, 2025  
**Status**: Planning Phase  
**Objective**: Replace current CLI mode with batch mode that drives interactive mode via JSON-RPC

## Overview

The batch mode feature will replace the existing CLI with a system that:
1. Reads batch scripts specified via command line
2. Creates a local interactive server on a random port
3. Connects via WebSocket using JSON-RPC 2.0
4. Uses a new agent "Billy the Batcher" to interpret scripts
5. Converts script commands into AIWhisperer actions
6. Requires workspace detection via `.WHISPER` folder

## High-Level Architecture

```
[CLI] → [Workspace Detection] → [Batch Client] → [Local Server] → [Billy Agent] → [AIWhisperer Actions]
  ↓              ↓                    ↓              ↓              ↓              ↓
Script File → .WHISPER Check → WebSocket Client → JSON-RPC → Script Analysis → Commands
```

## Key Components

### 1. Workspace Detection
- **Purpose**: Validate AIWhisperer project before batch execution
- **Implementation**: Look for `.WHISPER/` folder in current and parent directories
- **Error Handling**: Exit with error if no workspace found

### 2. Billy the Batcher Agent
- **Agent ID**: B
- **Role**: batch_processor
- **Capabilities**: Script interpretation, command generation, batch automation
- **Tools**: Script parsing, command validation, batch execution

### 3. Batch Client
- **Components**: Server manager, WebSocket client, script processor
- **Functionality**: Start server, establish connection, process scripts
- **Error Handling**: Cleanup on interrupts, proper error propagation

### 4. CLI Integration
- **Entry Point**: Modified `ai_whisperer/main.py`
- **Command**: `python -m ai_whisperer.main batch script.txt`
- **Validation**: Script file existence, workspace detection

## Detailed Implementation Phases

### Phase 1: Workspace Detection Foundation (1-2 days)
**Objective**: Establish workspace detection mechanism using `.WHISPER` folder

#### Backend Changes
- `ai_whisperer/workspace_detection.py` - Core detection logic
- Integration with existing PathManager
- Error handling for missing workspace

#### Test Strategy
- Unit tests for detection logic
- Integration tests for various folder structures
- Error scenario testing

### Phase 2: Billy the Batcher Agent (4 days)
**Objective**: Create new agent specialized in batch script interpretation

#### Backend Changes
- Add Billy to `agents.yaml` configuration
- Create `prompts/agents/billy_batcher.prompt.md`
- Implement Billy-specific tools:
  - `ai_whisperer/tools/script_parser_tool.py`
  - `ai_whisperer/tools/batch_command_tool.py`

#### Agent Configuration
```yaml
b:
  name: "Billy the Batcher"
  role: "batch_processor"
  description: "Processes batch scripts and converts them to AIWhisperer commands"
  tool_tags: ["batch", "script", "automation"]
  prompt_file: "billy_batcher"
  context_sources: ["workspace_structure", "batch_history"]
  color: "#FF9800"
  icon: "⚡"
```

#### Test Strategy
- Agent registration tests
- Prompt loading tests
- Tool functionality tests
- Script interpretation tests

### Phase 3: Batch Client Core (6 days)
**Objective**: Create the Python client that drives the interactive mode

#### Backend Changes
- `ai_whisperer/batch/server_manager.py` - Server lifecycle management
- `ai_whisperer/batch/websocket_client.py` - JSON-RPC client
- `ai_whisperer/batch/script_processor.py` - Script handling

#### Key Features
- Random port allocation with retry logic
- WebSocket connection with reconnect capability
- JSON-RPC 2.0 protocol implementation
- Session management and agent switching
- Stream processing for real-time feedback

#### Test Strategy
- Server startup/shutdown tests
- WebSocket connection tests
- JSON-RPC protocol tests
- Script processing tests
- Error handling tests

### Phase 4: CLI Integration (3 days)
**Objective**: Replace current CLI with batch mode

#### Backend Changes
- Modify `ai_whisperer/main.py` for batch entry point
- Update `ai_whisperer/cli.py` with batch command parsing
- Create `ai_whisperer/cli_commands.py::BatchCliCommand`

#### CLI Interface

```bash
# New batch mode command (config is required)
python -m ai_whisperer.cli SCRIPT --config config.yaml [--dry-run]

# Options
--config     Configuration file (required)
--dry-run    Echo commands only, do not start server or connect
```

#### Test Strategy
- CLI argument parsing tests
- Command execution tests
- Integration with batch client tests
- Error handling and cleanup tests


### Phase 5: Integration & Testing (3 days)
**Objective**: End-to-end integration and validation

#### Comprehensive Testing
- **End-to-end batch mode test:**
    - Launch CLI with a real batch script and connect to a real AI (OpenRouter API key from `.env`).
    - Validate full workflow: script → CLI → server → AI → response → output.
    - Ensure test fails if API key is missing or output is not as expected.
- Multiple script format tests
- Concurrent execution safety tests
- Performance and memory usage tests
- Error recovery scenario tests

#### Documentation
- User guide with examples
- Troubleshooting documentation
- Performance guidelines
- Migration guide from old CLI

#### Checklist (Phase 5)
- [ ] Integration test runs CLI with real server and OpenRouter AI
- [ ] Test fails if API key is missing or output is not as expected
- [ ] Output and error logs are captured for debugging
- [ ] Documentation updated with integration test instructions

See `tests/integration/test_batch_mode_e2e.py` for the new end-to-end test.

## Technical Specifications

### JSON-RPC Protocol Usage
The batch mode will use existing JSON-RPC methods:
- `startSession` - Initialize batch session
- `session.switch_agent` - Switch to Billy agent
- `sendUserMessage` - Send script content to Billy
- `stopSession` - Clean up session

### Workspace Detection Rules
1. Look for `.WHISPER/` folder in current directory
2. If not found, check parent directories up to filesystem root
3. `.WHISPER/` folder should contain:
   - `workspace.yaml` (optional configuration)
   - `batch_history/` (optional execution history)

### Error Handling Strategy
- **Workspace Errors**: Exit immediately with clear message
- **Server Errors**: Retry with different port, fallback options
- **Connection Errors**: Retry with exponential backoff
- **Script Errors**: Continue processing, log errors, report at end
- **Interrupt Handling**: Graceful cleanup of server and connections

## Coordination Requirements

### With Interactive Team
1. **Agent Registry**: Confirm Billy agent integration approach
2. **JSON-RPC Extensions**: Verify existing methods are sufficient
3. **Session Management**: Ensure batch sessions don't conflict
4. **Tool Registry**: Coordinate batch tool registration
5. **Error Formats**: Align error handling between modes

### Backend Changes Summary
**Minimal backend changes as requested:**
- New agent configuration (Billy)
- New tools for batch processing
- New workspace detection utility
- No changes to existing interactive server
- No changes to existing JSON-RPC protocol
- No changes to existing session management

## Testing Strategy

### Test-Driven Development Approach
Each phase follows strict TDD methodology:
1. **Write tests first** - Define expected behavior
2. **Implement functionality** - Make tests pass
3. **Refactor** - Improve code while keeping tests green
4. **Integration** - Test component interactions

### Test Categories
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Full workflow validation
- **Performance Tests**: Memory, speed, concurrent safety
- **Error Tests**: Failure scenarios and recovery

### Coverage Requirements
- Minimum 90% code coverage for new components
- 100% coverage for critical paths (workspace detection, error handling)
- All public APIs must have comprehensive tests

## Risk Mitigation

### Technical Risks
- **Port Conflicts**: Random port allocation with retry logic
- **Connection Issues**: Robust reconnection with timeouts
- **Script Parsing**: Extensive validation and error recovery
- **Memory Leaks**: Proper cleanup in all error paths

### Process Risks
- **Team Coordination**: Regular sync meetings with interactive team
- **Backward Compatibility**: Keep existing CLI during transition
- **Rollback Plan**: Each phase independently deployable/reversible
- **Documentation**: Comprehensive user and developer docs

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | 1-2 days | Workspace detection with tests |
| Phase 2 | 4 days | Billy agent with tools and tests |
| Phase 3 | 6 days | Batch client with full test suite |
| Phase 4 | 3 days | CLI integration with tests |
| Phase 5 | 3 days | Integration testing and docs |

**Total Estimated Time**: 17-18 days

## Success Criteria

### Functional Requirements
- ✅ Batch scripts execute successfully via Billy agent
- ✅ Workspace detection prevents execution outside AIWhisperer projects
- ✅ Server starts on random port without conflicts
- ✅ JSON-RPC communication works reliably
- ✅ Error handling provides clear user feedback
- ✅ Cleanup happens properly on interrupts

### Quality Requirements
- ✅ 90%+ test coverage on new components
- ✅ No performance degradation in interactive mode
- ✅ Memory usage stays within reasonable bounds
- ✅ Documentation covers all user scenarios
- ✅ Backward compatibility maintained during transition

### Team Coordination
- ✅ No breaking changes to interactive server
- ✅ New agent integrates smoothly
- ✅ Tool registry additions don't conflict
- ✅ Error handling aligns with existing patterns
