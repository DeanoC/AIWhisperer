# AI Whisperer Development Plan

## Current State Analysis

### Working Components

- **Frontend**: React-based chat interface at `frontend/`
- **Backend**: FastAPI server with WebSocket support in `interactive_server/`
- **AI Integration**: OpenRouter API integration for AI responses
- **Core Systems**:
  - AI loop in `src/ai_whisperer/ai_loop.py`
  - Tool registry and management
  - Context management system
  - Execution engine
  - State management

### Identified Issues

1. **Double Display Bug**: The frontend appears to display AI responses twice. This is likely in the WebSocket message handling in `frontend/src/App.js`.

2. **Missing Command System**: No command processing functionality exists yet.

## Development Plan

### Phase 1: Bug Fixes and Command System

#### 1.1 Fix Double Display Issue

- [x] Debug WebSocket message handling in frontend
- [x] Check if backend is sending duplicate messages
- [x] Ensure proper state management in React component

#### 1.2 Implement Command System

- [ ] Add command detection logic (messages starting with `*COMMAND*`)
- [ ] Create command router in backend
- [ ] Add command feedback to frontend
- [ ] Initial commands to implement:
  - `*COMMAND* help` - List available commands
  - `*COMMAND* clear` - Clear chat history
  - `*COMMAND* status` - Show system status

### Phase 2: Integration of Existing Functionality

#### 2.1 Initial Plan Generation

- [ ] Integrate `prompts/core/initial_plan.prompt.md` with interactive flow
- [ ] Adapt `src/ai_whisperer/orchestrator.py` for interactive use
- [ ] Add command: `*COMMAND* plan <requirements>`
- [ ] Implement interactive plan refinement using chat
- [ ] Connect postprocessing pipeline from `src/ai_whisperer/postprocessing/`

#### 2.2 Tool System Integration

- [ ] Expose tool registry to interactive system
- [ ] Add command: `*COMMAND* tools list` - Show available tools
- [ ] Add command: `*COMMAND* tools enable/disable <tool_name>`
- [ ] Ensure tools work properly in chat context

#### 2.3 Execution Engine Integration

- [ ] Adapt execution engine for interactive mode
- [ ] Add command: `*COMMAND* execute <plan_file>`
- [ ] Implement real-time execution status updates via WebSocket
- [ ] Add pause/resume/stop functionality

### Phase 3: Refactoring and Cleanup

#### 3.1 Code to Remove/Update

Based on the codebase analysis, these components need attention:

**To Remove:**

- [ ] Old CLI-only functionality that's been superseded
- [ ] Duplicate or dead code in agent handlers
- [ ] Test files for removed functionality

**To Update:**

- [ ] `src/ai_whisperer/main.py` - Add interactive mode as primary interface
- [ ] `src/ai_whisperer/execution_engine.py` - Support for interactive execution
- [ ] Agent handlers - Ensure they work with new interactive context
- [ ] Tests - Update to reflect new interactive architecture

#### 3.2 Architecture Improvements

- [ ] Unify AI loop usage across all components
- [ ] Standardize delegate/notification system
- [ ] Improve error handling for interactive mode
- [ ] Add session management for multiple users

### Phase 4: Enhanced Features

#### 4.1 Advanced Commands

- [ ] `*COMMAND* load <project>` - Load existing project
- [ ] `*COMMAND* save <name>` - Save current session
- [ ] `*COMMAND* config <setting> <value>` - Runtime configuration
- [ ] `*COMMAND* model <model_name>` - Switch AI model

#### 4.2 UI Improvements

- [ ] Add syntax highlighting for code blocks
- [ ] Implement file tree viewer
- [ ] Add execution progress visualization
- [ ] Improve error display

## Implementation Checklist

### Immediate Tasks (Week 1)

- [ ] Fix double display bug
- [ ] Implement basic command detection
- [ ] Add help command
- [ ] Create command router infrastructure

### Short Term (Week 2-3)

- [ ] Integrate initial plan generation
- [ ] Hook up prompt system to interactive flow
- [ ] Implement plan refinement chat flow
- [ ] Add basic execution commands

### Medium Term (Week 4-6)

- [ ] Full tool integration
- [ ] Complete execution engine adaptation
- [ ] Remove deprecated code
- [ ] Update test suite

### Long Term (Week 7+)

- [ ] Advanced command system
- [ ] Multi-user support
- [ ] UI enhancements
- [ ] Performance optimizations

## Technical Considerations

1. **State Management**: Consider using a proper state management solution (Redux/Zustand) for the frontend as complexity grows.

2. **WebSocket Protocol**: Define a clear message protocol for different types of communications (chat, commands, status updates).

3. **Security**: Add authentication and authorization for production use.

4. **Persistence**: Implement proper session saving/loading.

5. **Testing**: Ensure interactive features have appropriate test coverage.

This plan provides a structured approach to evolving your AI Whisperer from a prototype to a fully interactive development tool while maintaining the existing functionality
