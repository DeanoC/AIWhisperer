# Stateless Architecture Overview

## Introduction

This document describes the new stateless architecture implemented in AIWhisperer, which replaces the delegate-based event system with direct communication patterns.

## Key Components

### 1. StatelessAILoop

The `StatelessAILoop` class provides a clean interface for AI interactions without delegates:

- **Location**: `ai_whisperer/ai_loop/stateless_ai_loop.py`
- **Purpose**: Process messages directly and return results
- **Key Methods**:
  - `process_with_context()`: Process a message using a context provider
  - `process_messages()`: Process messages directly without context

### 2. StatelessAgent

The `StatelessAgent` manages AI interactions without session state:

- **Location**: `ai_whisperer/agents/stateless_agent.py`
- **Purpose**: Encapsulate agent behavior with owned context
- **Features**:
  - Owns its own context and AILoop instance
  - Supports custom generation parameters
  - Direct message processing without delegates

### 3. StreamingSession

Handles WebSocket streaming without delegate bridges:

- **Location**: `interactive_server/streaming_session.py`
- **Purpose**: Direct WebSocket communication with token streaming
- **Features**:
  - Real-time token streaming
  - Multi-agent support
  - Direct error handling

### 4. StatelessSessionManager

Manages sessions without delegate dependencies:

- **Location**: `interactive_server/stateless_session_manager.py`
- **Purpose**: Session lifecycle management
- **Features**:
  - Session persistence
  - WebSocket management
  - Agent creation and routing

## Architecture Benefits

1. **Simplicity**: Direct function calls replace complex event routing
2. **Performance**: 747+ chunks/second streaming throughput
3. **Maintainability**: Clear data flow and ownership
4. **Testability**: Easier to test without event indirection

## Migration Guide

### For Agent Development

Old pattern with delegates:
```python
# Old: Agent using delegates
agent = Agent(config, context, ai_loop, delegate_manager)
agent.start()
delegate_manager.invoke_notification("user_message", message)
```

New pattern with stateless components:
```python
# New: Direct agent usage
agent = StatelessAgent(config, context, ai_loop)
result = await agent.process_message(message)
```

### For Session Management

Old pattern:
```python
# Old: Session with delegates
session_manager = InteractiveSessionManager(config, delegate_manager)
session = session_manager.create_session()
delegate_bridge = DelegateBridge(session, websocket)
```

New pattern:
```python
# New: Direct streaming
session_manager = StatelessSessionManager(config)
session_id = await session_manager.create_session(websocket)
result = await session_manager.send_message(session_id, message)
```

## Testing

The stateless architecture includes comprehensive test coverage:

- `tests/integration/test_no_delegates.py`: Verifies no delegate usage
- `tests/integration/test_stateless_session_manager.py`: Session management tests
- `tests/unit/test_agent_stateless.py`: Agent functionality tests

All 21 tests pass, confirming the architecture works correctly.

## Future Considerations

While the legacy codebase still uses delegates in some areas, all new development should use the stateless architecture. The two systems can coexist during migration.