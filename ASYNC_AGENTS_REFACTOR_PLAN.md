# Async Agents Refactoring Plan

## Executive Summary

The async agent implementation exists but uses outdated patterns. This plan outlines a systematic refactoring to align with the current architecture while preserving the valuable async capabilities.

## Current State Analysis

### What Exists
- `AsyncAgentSessionManager` - Manages multiple agent sessions with background tasks
- `AgentState` enum - IDLE, ACTIVE, SLEEPING, WAITING, STOPPED
- WebSocket endpoints for async control
- Task queues per agent
- Sleep/wake functionality with timers and events
- Event broadcasting system

### Problems
1. Uses old agent creation patterns (AgentFactory instead of current approach)
2. Incorrect imports (OpenRouterService vs OpenRouterAIService)
3. Doesn't leverage AILoopManager
4. Not integrated with current StatelessAgent patterns
5. Missing proper context management

## Refactoring Phases

### Phase 1: Align Agent Creation (2-3 days)

**Goal**: Make async agents use the same creation pattern as StatelessSessionManager

**Tasks**:
1. Study how StatelessSessionManager creates agents:
   ```python
   # Current pattern in StatelessSessionManager
   - Load agent from registry
   - Get prompt via PromptSystem
   - Create AgentContext
   - Use AILoopManager.get_or_create_ai_loop()
   - Create StatelessAgent
   ```

2. Update AsyncAgentSessionManager.create_agent_session():
   - Remove direct OpenRouterAIService creation
   - Use AILoopManager for AI loop creation
   - Ensure proper config propagation
   - Add proper error handling

3. Create `AsyncAgentSession` wrapper:
   ```python
   @dataclass
   class AsyncAgentSession:
       session_id: str
       agent: StatelessAgent
       ai_loop: StatelessAILoop
       state: AgentState
       task_queue: asyncio.Queue
       background_task: Optional[asyncio.Task]
       wake_events: Set[str]
       sleep_until: Optional[datetime]
   ```

**Files to modify**:
- `ai_whisperer/services/agents/async_session_manager.py`

### Phase 2: Integrate with Current Architecture (2-3 days)

**Goal**: Make async agents work seamlessly with existing tools and patterns

**Tasks**:
1. Update background processor to use current patterns:
   - Proper tool registration per agent
   - Context tracking during async execution
   - Channel system compliance
   - Continuation handling

2. Integrate with mailbox system:
   - Async agents check mail periodically
   - Can process mail while sleeping (wake on urgent)
   - Proper mail context preservation

3. Add monitoring hooks:
   - Agent state changes
   - Task queue depths
   - Performance metrics
   - Error tracking

**New files**:
- `ai_whisperer/services/agents/async_agent_monitor.py`
- `ai_whisperer/services/agents/async_task_processor.py`

### Phase 3: Enhanced Sleep/Wake System (1-2 days)

**Goal**: Robust scheduling and event-based agent coordination

**Tasks**:
1. Implement proper sleep scheduling:
   ```python
   class SleepScheduler:
       async def schedule_wake(agent_id: str, wake_time: datetime)
       async def cancel_wake(agent_id: str)
       async def get_next_wake_time(agent_id: str) -> Optional[datetime]
   ```

2. Event system enhancements:
   - Event priorities (urgent wakes immediately)
   - Event filtering per agent
   - Event history tracking
   - Dead letter queue for unhandled events

3. Wake conditions:
   - Time-based (sleep for X seconds)
   - Event-based (wake on specific events)
   - Mailbox-based (wake on mail with priority)
   - Load-based (wake when system load permits)

**Files to create**:
- `ai_whisperer/services/agents/sleep_scheduler.py`
- `ai_whisperer/services/agents/event_manager.py`

### Phase 4: State Persistence (1-2 days)

**Goal**: Async agents survive server restarts

**Tasks**:
1. Persist agent states:
   ```python
   class AsyncAgentStateStore:
       async def save_state(agent_id: str, state: AgentState)
       async def load_state(agent_id: str) -> Optional[AgentState]
       async def list_active_agents() -> List[str]
   ```

2. Task queue persistence:
   - Save pending tasks to disk
   - Restore on startup
   - Handle task expiration

3. Recovery mechanism:
   - Detect crashed agents
   - Restore from last checkpoint
   - Replay failed tasks

**Files to create**:
- `ai_whisperer/services/agents/async_state_store.py`
- `ai_whisperer/services/agents/task_persistence.py`

### Phase 5: Testing & Documentation (2-3 days)

**Goal**: Comprehensive test coverage and usage documentation

**Tasks**:
1. Unit tests:
   - Agent creation/destruction
   - Sleep/wake cycles
   - Event handling
   - State persistence

2. Integration tests:
   - Multi-agent scenarios
   - Sync/async agent interaction
   - Failure recovery
   - Load testing

3. Documentation:
   - Architecture overview
   - Usage patterns
   - API reference
   - Troubleshooting guide

**Files to create**:
- `tests/unit/agents/test_async_session_manager_refactored.py`
- `tests/integration/async_agents/test_refactored_async_agents.py`
- `docs/ASYNC_AGENTS_ARCHITECTURE.md`
- `docs/ASYNC_AGENTS_PATTERNS.md`

## Implementation Strategy

### Week 1: Foundation
- Phase 1: Align agent creation
- Phase 2 (partial): Basic integration

### Week 2: Core Features  
- Phase 2 (complete): Full integration
- Phase 3: Sleep/wake system
- Phase 4: State persistence

### Week 3: Polish & Release
- Phase 5: Testing & documentation
- Performance optimization
- Beta testing with real workflows

## Key Design Decisions

### 1. Reuse Existing Components
- Use StatelessAgent as base
- Leverage AILoopManager
- Integrate with current tool system
- Maintain compatibility with sync agents

### 2. Async-First Patterns
```python
# Bad: Blocking in async context
result = agent.process_task(task)  # Blocks event loop

# Good: Proper async handling  
result = await agent.process_task_async(task)
```

### 3. Resource Management
- Limit concurrent agents (configurable)
- Task queue size limits
- Automatic cleanup of idle agents
- Memory usage monitoring

### 4. Error Handling
- Graceful degradation
- Task retry logic
- Dead letter queues
- Health check endpoints

## Success Criteria

1. **Compatibility**: Async agents work with all existing tools
2. **Performance**: Can run 10+ agents concurrently without degradation
3. **Reliability**: Survives crashes and restarts
4. **Observability**: Full visibility into agent states and tasks
5. **Usability**: Simple API for common patterns

## Example Usage After Refactoring

```python
# Create async agent
response = await websocket.send({
    "method": "async.createAgent",
    "params": {
        "agentId": "d",
        "config": {
            "checkMailInterval": 30,  # Check mail every 30 seconds
            "maxConcurrentTasks": 5,
            "wakeOnPriority": "high"
        }
    }
})

# Schedule periodic task
await websocket.send({
    "method": "async.scheduleTask",
    "params": {
        "agentId": "d",
        "task": "Check system health and report issues",
        "schedule": "*/15 * * * *"  # Every 15 minutes
    }
})

# Sleep with wake conditions
await websocket.send({
    "method": "async.sleepAgent",
    "params": {
        "agentId": "d",
        "untilTime": "2024-01-01T09:00:00Z",
        "wakeEvents": ["urgent_mail", "system_alert"],
        "wakeOnMailPriority": "high"
    }
})
```

## Risk Mitigation

### Technical Risks
- **Risk**: Breaking existing functionality
- **Mitigation**: Feature flag for async agents, extensive testing

### Performance Risks
- **Risk**: Too many agents overwhelming system
- **Mitigation**: Resource limits, monitoring, circuit breakers

### Complexity Risks
- **Risk**: Difficult to debug async issues
- **Mitigation**: Comprehensive logging, visualization tools, replay capability

## Rollout Plan

1. **Alpha**: Internal testing with simple workflows
2. **Beta**: Limited release to power users
3. **GA**: Full release with migration guide

## Estimated Timeline

- **Total Duration**: 3 weeks
- **Developer Resources**: 1-2 developers
- **Review Checkpoints**: End of each phase

## Next Steps

1. Review and approve this plan
2. Create feature branch `feature/async-agents-refactor`
3. Begin Phase 1 implementation
4. Daily progress updates
5. Weekly architecture reviews