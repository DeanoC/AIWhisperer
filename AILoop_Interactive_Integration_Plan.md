# AILoop Interactive Integration Plan & Checklist

## Overview

This document outlines the plan for the **third phase** of interactive mode development: integrating the real AILoop with the scaffolded interactive server backend. This follows the completion of:

1. **Phase 1: AILoop Stabilization** ✅ - Session lifecycle, streaming, tools, delegate system
2. **Phase 2: Interactive Mode Scaffolding** ✅ - FastAPI WebSocket server, Pydantic models, mocked AILoop integration, comprehensive tests

**Phase 3 Goal**: Replace mocked AILoop responses with real AILoop integration while maintaining all existing API contracts and test coverage.

---

## Current State Analysis

### Completed Components

#### AILoop (Stabilized)

- ✅ **Session Lifecycle**: `start_session()`, `stop_session()`, `pause_session()`, `resume_session()`
- ✅ **User Message Handling**: Async `send_user_message()` with streaming notifications  
- ✅ **AI Streaming**: Real-time chunk delivery via `ai_loop.message.ai_chunk_received` events
- ✅ **Tool Integration**: Tool call/result handling with delegate notifications
- ✅ **Delegate System**: Event-driven notifications for all session state changes
- ✅ **Error Handling**: Comprehensive error management and recovery
- ✅ **Async Architecture**: Full async/await support with proper task management

#### Interactive Server (Scaffolded)

- ✅ **FastAPI WebSocket**: JSON-RPC 2.0 protocol implementation
- ✅ **Pydantic Models**: Type-safe message validation for all API messages
- ✅ **Mocked AILoop**: Simulated responses, streaming, and tool calls
- ✅ **Server Notifications**: Async streaming to clients via WebSocket
- ✅ **Test Coverage**: End-to-end integration tests with message ordering
- ✅ **API Documentation**: Complete frontend developer documentation
- ✅ **Manual Testing**: Python WebSocket client for development testing

#### Interactive AI Wrapper

- ✅ **AILoop Bridge**: `InteractiveAI` class wrapping AILoop for simpler usage
- ✅ **Configuration**: AI service and delegate manager setup
- ✅ **Session Management**: Start session and message sending methods

### Integration Challenge

The interactive server currently uses **mocked AILoop responses** in the handler functions (`interactive_server/main.py`). The real integration requires:

1. **Replace mocked handlers** with real AILoop instance management
2. **Bridge delegate events** to WebSocket notifications  
3. **Manage session state** across WebSocket connections
4. **Handle async streaming** from AILoop to WebSocket clients
5. **Preserve API contracts** so existing tests continue to pass

---

## Implementation Plan

### 1. Architecture Design

#### Session Management Strategy

```
WebSocket Connection → Interactive Session → AILoop Instance
     ↓                        ↓                   ↓
 Session State         AILoop Bridge      AI Service + Context
```

**Key Design Decisions:**

- **One AILoop per WebSocket connection**: Each client gets dedicated AILoop instance
- **Session state isolation**: No shared state between different client sessions  
- **Delegate bridge**: Route AILoop delegate events to appropriate WebSocket clients
- **Resource cleanup**: Proper cleanup when WebSocket disconnects

#### Event Flow Integration

```
Client Request → JSON-RPC Handler → AILoop Method → Delegate Event → WebSocket Notification
```

### 2. Core Integration Components

#### A. Session Manager Class

**Purpose**: Manage AILoop instances per WebSocket connection

**Responsibilities:**

- Create/destroy AILoop instances per session
- Route delegate events to correct WebSocket
- Handle session cleanup on disconnect
- Manage session state and metadata

#### B. Delegate Bridge

**Purpose**: Convert AILoop delegate events to WebSocket notifications

**Event Mappings:**

- `ai_loop.session_started` → `SessionStatusNotification`
- `ai_loop.message.ai_chunk_received` → `AIMessageChunkNotification`  
- `ai_loop.tool.call_generated` → `ToolCallNotification`
- `ai_loop.session_ended` → `SessionStatusNotification`
- `ai_loop.error` → Error handling and notifications

#### C. Enhanced Message Handlers

**Purpose**: Replace mocked handlers with real AILoop integration

**Handler Updates:**

- `startSession`: Create AILoop, start session, return session ID
- `sendUserMessage`: Route message to AILoop, handle streaming responses
- `provideToolResult`: Pass tool results to AILoop for processing
- `stopSession`: Clean stop AILoop and cleanup resources

### 3. Detailed Implementation Steps

#### Step 1: Create Session Manager Infrastructure

- [ ] **1.1** Create `InteractiveSessionManager` class
  - [ ] Session creation/destruction methods
  - [ ] WebSocket-to-session mapping
  - [ ] Resource cleanup utilities
  - [ ] Session state tracking

- [ ] **1.2** Create `DelegateBridge` class  
  - [ ] Event-to-notification mapping
  - [ ] WebSocket routing for notifications
  - [ ] Async notification sending
  - [ ] Error handling for send failures

- [ ] **1.3** Update project structure
  - [ ] Add session management module
  - [ ] Update imports in main.py
  - [ ] Add configuration for session management

#### Step 2: Implement Real AILoop Integration

- [ ] **2.1** Replace `start_session_handler`
  - [ ] Create AILoop instance using `InteractiveAI`
  - [ ] Set up delegate bridge for session
  - [ ] Start AILoop with system prompt
  - [ ] Return real session ID
  - [ ] Handle initialization errors

- [ ] **2.2** Replace `send_user_message_handler`
  - [ ] Route message to appropriate AILoop instance
  - [ ] Handle streaming AI responses via delegates
  - [ ] Manage message state and acknowledgments
  - [ ] Handle AILoop communication errors

- [ ] **2.3** Implement `provide_tool_result_handler`
  - [ ] Route tool results to correct AILoop
  - [ ] Handle tool result processing
  - [ ] Manage tool call state transitions
  - [ ] Error handling for invalid tool results

- [ ] **2.4** Replace `stop_session_handler`
  - [ ] Gracefully stop AILoop session
  - [ ] Clean up session resources
  - [ ] Remove session from manager
  - [ ] Send final status notifications

#### Step 3: Delegate Event Integration

- [ ] **3.1** Implement delegate event handlers
  - [ ] `ai_loop.session_started` → Session status notifications
  - [ ] `ai_loop.message.ai_chunk_received` → AI chunk notifications
  - [ ] `ai_loop.tool.call_generated` → Tool call notifications
  - [ ] `ai_loop.session_ended` → Session cleanup and status

- [ ] **3.2** Handle streaming AI responses
  - [ ] Real-time chunk delivery to WebSocket
  - [ ] Proper message ordering and sequencing
  - [ ] Handle connection drops during streaming
  - [ ] Final message indicators

- [ ] **3.3** Implement error event handling
  - [ ] AILoop errors → Client error notifications  
  - [ ] Network/service errors → Appropriate error responses
  - [ ] Session timeout handling
  - [ ] Resource exhaustion scenarios

#### Step 4: Configuration and Lifecycle Management

- [ ] **4.1** Configuration integration
  - [ ] Load AI configuration from `config.yaml`
  - [ ] Set up OpenRouter API service
  - [ ] Configure delegate manager
  - [ ] Set up context manager per session

- [ ] **4.2** Resource management
  - [ ] Proper cleanup on WebSocket disconnect
  - [ ] Session timeout handling
  - [ ] Memory management for long-running sessions
  - [ ] Graceful shutdown procedures

- [ ] **4.3** Error handling and recovery
  - [ ] Handle AILoop initialization failures
  - [ ] Recover from temporary AI service outages
  - [ ] Manage delegate manager errors
  - [ ] WebSocket connection error handling

#### Step 5: Testing and Validation

- [ ] **5.1** Update existing tests
  - [ ] Modify tests to work with real AILoop (where appropriate)
  - [ ] Add integration test variants with real AI service mocking
  - [ ] Ensure message ordering still works correctly
  - [ ] Validate all error scenarios still covered

- [ ] **5.2** Add new integration tests
  - [ ] End-to-end tests with real AILoop integration
  - [ ] Multi-session concurrency tests
  - [ ] Resource cleanup verification tests
  - [ ] Delegate event flow validation tests

- [ ] **5.3** Performance and stress testing
  - [ ] Multiple concurrent WebSocket connections
  - [ ] Long-running session stability
  - [ ] Memory usage under load
  - [ ] AI service timeout handling

- [ ] **5.4** Manual testing updates
  - [ ] Update manual test client for real scenarios
  - [ ] Add test cases for tool calls with real tools
  - [ ] Test streaming with real AI responses
  - [ ] Verify error handling in real scenarios

#### Step 6: Documentation and Finalization

- [ ] **6.1** Update API documentation
  - [ ] Note any behavioral changes from mocked version
  - [ ] Document real-world response times and patterns
  - [ ] Update error code documentation
  - [ ] Add troubleshooting section

- [ ] **6.2** Developer documentation
  - [ ] Architecture documentation for new components
  - [ ] Session management guidelines
  - [ ] Deployment considerations
  - [ ] Performance tuning recommendations

- [ ] **6.3** Configuration documentation  
  - [ ] Required configuration for AI service
  - [ ] Session management settings
  - [ ] Resource limit recommendations
  - [ ] Security considerations

---

## Implementation Details

### Session Manager Implementation

```python
class InteractiveSessionManager:
    def __init__(self, config: dict):
        self.sessions: Dict[str, InteractiveSession] = {}
        self.websocket_sessions: Dict[WebSocket, str] = {}
        self.config = config
        
    async def create_session(self, websocket: WebSocket, session_params: SessionParams) -> str:
        session_id = str(uuid.uuid4())
        session = InteractiveSession(session_id, websocket, self.config)
        self.sessions[session_id] = session
        self.websocket_sessions[websocket] = session_id
        return session_id
        
    async def cleanup_session(self, session_id: str):
        if session_id in self.sessions:
            await self.sessions[session_id].cleanup()
            del self.sessions[session_id]
```

### Delegate Bridge Implementation

```python
class DelegateBridge:
    def __init__(self, session_manager: InteractiveSessionManager):
        self.session_manager = session_manager
        
    async def handle_ai_chunk(self, sender: AILoop, event_data: str, **kwargs):
        session = self.session_manager.get_session_by_ailoop(sender)
        if session and session.websocket:
            notification = AIMessageChunkNotification(
                sessionId=session.session_id,
                chunk=event_data,
                isFinal=False
            )
            await session.send_notification("AIMessageChunkNotification", notification)
```

### Integration Points

1. **Replace handlers in main.py** with session manager calls
2. **Set up delegate bridges** in session creation
3. **Route all events** through the delegate system
4. **Handle WebSocket lifecycle** through session manager

---

## Testing Strategy

### Test Categories

#### 1. Unit Tests

- Session manager functionality
- Delegate bridge event routing  
- Individual handler logic
- Error handling scenarios

#### 2. Integration Tests  

- End-to-end message flow with real AILoop
- Multi-session isolation testing
- Resource cleanup verification
- Delegate event flow validation

#### 3. Performance Tests

- Concurrent session handling
- Memory usage under load
- Response time measurements
- Resource leak detection

#### 4. Manual Testing

- Real AI service integration
- Tool call workflows
- Streaming response handling
- Error scenario validation

---

## Risk Assessment & Mitigation

### High Risk Areas

#### 1. **State Management Complexity**

- **Risk**: Session state getting out of sync between WebSocket and AILoop
- **Mitigation**: Clear state ownership rules, comprehensive state validation

#### 2. **Resource Leaks**  

- **Risk**: AILoop instances not properly cleaned up on WebSocket disconnect
- **Mitigation**: Robust cleanup procedures, resource monitoring, timeout handling

#### 3. **Performance Under Load**

- **Risk**: Too many concurrent AILoop instances degrading performance
- **Mitigation**: Connection limits, resource pooling, performance monitoring

#### 4. **Error Propagation**

- **Risk**: AILoop errors not properly handled/communicated to clients
- **Mitigation**: Comprehensive error mapping, graceful degradation, retry logic

### Medium Risk Areas

#### 1. **API Contract Changes**

- **Risk**: Real AILoop behavior differs from mocked behavior, breaking tests
- **Mitigation**: Careful behavior analysis, gradual migration, compatibility testing

#### 2. **Delegate Event Ordering**

- **Risk**: Events arriving out of order causing client confusion
- **Mitigation**: Event sequencing, message ordering validation, idempotent handling

---

## Success Criteria

### Functional Requirements

- [ ] All existing interactive server tests pass with real AILoop integration
- [ ] Real AI responses stream correctly to WebSocket clients
- [ ] Tool calls work end-to-end with actual tool execution
- [ ] Session lifecycle management works reliably
- [ ] Error handling provides appropriate client feedback

### Performance Requirements  

- [ ] Support at least 10 concurrent WebSocket sessions
- [ ] AI response streaming latency under 200ms for first chunk
- [ ] Memory usage grows linearly with active sessions
- [ ] Graceful handling of AI service timeouts/errors

### Quality Requirements

- [ ] No memory leaks in long-running sessions  
- [ ] Comprehensive error logging for debugging
- [ ] Clean resource cleanup on all disconnect scenarios
- [ ] Maintains backwards compatibility with existing API

---

## Timeline Estimate

### Phase 3A: Core Integration (1-2 weeks)

- Session manager implementation
- Basic AILoop integration  
- Replace core handlers
- Basic delegate bridge

### Phase 3B: Complete Integration (1 week)

- Full delegate event handling
- Tool call integration
- Error handling completion
- Resource management

### Phase 3C: Testing & Polish (1 week)  

- Update all tests
- Performance testing
- Documentation updates
- Manual testing validation

**Total Estimated Duration: 3-4 weeks**

---

## Dependencies

### External Dependencies

- AILoop stabilization (✅ Complete)
- Interactive server scaffolding (✅ Complete)
- OpenRouter AI service integration (✅ Complete)
- Delegate manager system (✅ Complete)

### Internal Dependencies

- Configuration management for AI service setup
- Error handling standards and patterns
- Logging and monitoring infrastructure
- Development/testing AI service credentials

---

## Next Steps

1. **Review and approve this plan** with development team
2. **Set up development environment** with AI service credentials
3. **Create development branch** for Phase 3 implementation  
4. **Begin with Step 1**: Session Manager Infrastructure implementation
5. **Implement in phases** with testing after each major component

This plan provides a clear roadmap for integrating real AILoop functionality while maintaining the robust foundation established in the previous phases.
