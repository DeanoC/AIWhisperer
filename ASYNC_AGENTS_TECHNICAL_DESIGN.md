# Async Agents Technical Design

## Core Architecture Changes

### 1. Agent Creation Flow

```python
# Current (broken) flow in AsyncAgentSessionManager
agent_info = registry.get_agent(agent_id)
system_prompt = prompt_system.get_formatted_prompt(...)
ai_service = OpenRouterAIService(config)  # Wrong!
ai_loop = AILoopFactory.create_ai_loop(...)  # Missing context

# Proposed flow (aligned with StatelessSessionManager)
class AsyncAgentSessionManager:
    def __init__(self, config, tool_registry, prompt_system):
        self.config = config
        self.tool_registry = tool_registry
        self.prompt_system = prompt_system
        self.ai_loop_manager = AILoopManager()
        
    async def create_agent_session(self, agent_id: str, auto_start: bool = True):
        # 1. Get agent from registry
        agent_info = self.agent_registry.get_agent(agent_id)
        
        # 2. Load prompt using current pattern
        system_prompt = self._load_agent_prompt(agent_info)
        
        # 3. Create context
        context = AgentContext(
            agent_id=agent_id,
            system_prompt=system_prompt
        )
        
        # 4. Get or create AI loop via manager
        ai_loop = self.ai_loop_manager.get_or_create_ai_loop(
            agent_id=agent_id,
            agent_config=agent_info.ai_config,
            fallback_config=self.config
        )
        
        # 5. Create stateless agent
        agent = StatelessAgent(
            agent_id=agent_id,
            system_prompt=system_prompt,
            agent_registry=self.agent_registry
        )
        
        # 6. Wrap in async session
        session = AsyncAgentSession(
            agent_id=agent_id,
            agent=agent,
            ai_loop=ai_loop,
            context=context
        )
```

### 2. Background Task Processor

```python
async def _agent_processor(self, session: AsyncAgentSession):
    """Background processor for an agent."""
    logger.info(f"Starting processor for agent {session.agent_id}")
    
    while session.state != AgentState.STOPPED:
        try:
            # Handle state-specific behavior
            if session.state == AgentState.SLEEPING:
                await self._handle_sleep_state(session)
                continue
                
            if session.state == AgentState.IDLE:
                # Check for tasks
                task = await self._get_next_task(session)
                if task:
                    session.state = AgentState.ACTIVE
                    await self._process_task(session, task)
                    session.state = AgentState.IDLE
                else:
                    # No tasks, check mail
                    await self._check_mail_async(session)
                    await asyncio.sleep(1)  # Prevent busy loop
                    
        except Exception as e:
            logger.error(f"Error in agent {session.agent_id} processor: {e}")
            await self._handle_processor_error(session, e)
```

### 3. Task Processing Integration

```python
async def _process_task(self, session: AsyncAgentSession, task: Dict[str, Any]):
    """Process a task using the agent's AI loop."""
    prompt = task.get("prompt", "")
    context = task.get("context", {})
    
    # Create a temporary session context for this task
    with self._create_task_context(session, task) as task_context:
        # Use the existing AI loop infrastructure
        result = await session.ai_loop.process_message_async(
            message=prompt,
            context=task_context,
            agent=session.agent
        )
        
        # Handle result based on type
        if result.get("needs_continuation"):
            # Queue continuation as new task
            await session.task_queue.put({
                "prompt": result.get("continuation_prompt"),
                "context": result.get("context"),
                "parent_task": task.get("id")
            })
        
        # Notify task completion
        await self._notify_task_complete(session, task, result)
```

### 4. Mailbox Integration

```python
async def _check_mail_async(self, session: AsyncAgentSession):
    """Check mailbox without blocking."""
    from ai_whisperer.extensions.mailbox.mailbox import get_mailbox
    
    mailbox = get_mailbox()
    messages = mailbox.check_mail(session.agent_id)
    
    for message in messages:
        # High priority mail wakes sleeping agents
        if session.state == AgentState.SLEEPING:
            if message.priority == MessagePriority.HIGH:
                await self.wake_agent(session.agent_id, f"High priority mail: {message.subject}")
                
        # Queue mail as task
        await session.task_queue.put({
            "prompt": f"Process mail: {message.subject}\n\n{message.body}",
            "context": {
                "mail_id": message.id,
                "from_agent": message.from_agent,
                "priority": message.priority
            },
            "type": "mail"
        })
```

### 5. State Persistence Schema

```python
@dataclass
class PersistedAgentState:
    """State that survives restarts."""
    agent_id: str
    state: AgentState
    sleep_until: Optional[datetime]
    wake_events: List[str]
    pending_tasks: List[Dict[str, Any]]
    last_checkpoint: datetime
    metadata: Dict[str, Any]
    
class AsyncStateStore:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        
    async def save_state(self, session: AsyncAgentSession):
        state = PersistedAgentState(
            agent_id=session.agent_id,
            state=session.state,
            sleep_until=session.sleep_until,
            wake_events=list(session.wake_events),
            pending_tasks=await self._drain_queue_to_list(session.task_queue),
            last_checkpoint=datetime.now(),
            metadata=session.metadata
        )
        
        state_file = self.storage_path / f"agent_{session.agent_id}.json"
        async with aiofiles.open(state_file, 'w') as f:
            await f.write(json.dumps(asdict(state), default=str))
```

### 6. Event System Design

```python
class EventBus:
    """Central event bus for agent coordination."""
    
    def __init__(self):
        self._subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
    async def publish(self, event: str, data: Any):
        await self._event_queue.put({
            "event": event,
            "data": data,
            "timestamp": datetime.now()
        })
        
    async def subscribe(self, event_pattern: str, callback: Callable):
        self._subscribers[event_pattern].add(callback)
        
    async def process_events(self):
        """Background task to process events."""
        while True:
            event_data = await self._event_queue.get()
            event = event_data["event"]
            
            # Find matching subscribers
            for pattern, callbacks in self._subscribers.items():
                if self._matches_pattern(event, pattern):
                    for callback in callbacks:
                        asyncio.create_task(callback(event_data))
```

## Critical Integration Points

### 1. Tool System Integration

```python
# Ensure async agents have proper tool access
async def _setup_agent_tools(self, session: AsyncAgentSession):
    """Setup tools for async agent."""
    # Get tools based on agent configuration
    agent_info = self.agent_registry.get_agent(session.agent_id)
    
    # Register tools for this session
    session.tool_registry = ToolRegistry()
    
    # Add tools based on agent's permissions
    if agent_info.tool_sets:
        for tool_set in agent_info.tool_sets:
            tools = self.tool_registry.get_tools_by_set(tool_set)
            for tool in tools:
                session.tool_registry.register(tool)
```

### 2. Context Preservation

```python
class AsyncContextManager:
    """Manages context across async agent tasks."""
    
    def __init__(self):
        self._contexts: Dict[str, AgentContext] = {}
        
    async def create_task_context(self, session: AsyncAgentSession, task: Dict) -> AgentContext:
        """Create isolated context for task execution."""
        base_context = self._contexts.get(session.agent_id, session.context)
        
        # Create child context for task
        task_context = base_context.create_child()
        task_context.set("task_id", task.get("id"))
        task_context.set("task_type", task.get("type"))
        
        return task_context
```

### 3. Resource Management

```python
class AsyncResourceManager:
    """Manages resources for async agents."""
    
    def __init__(self, config: Dict):
        self.max_concurrent_agents = config.get("max_concurrent_agents", 10)
        self.max_tasks_per_agent = config.get("max_tasks_per_agent", 100)
        self.max_memory_per_agent = config.get("max_memory_mb", 512)
        
        self._agent_resources: Dict[str, AgentResources] = {}
        
    async def can_create_agent(self) -> bool:
        active_agents = sum(1 for r in self._agent_resources.values() if r.is_active)
        return active_agents < self.max_concurrent_agents
        
    async def monitor_resources(self):
        """Background task to monitor and enforce limits."""
        while True:
            for agent_id, resources in self._agent_resources.items():
                if resources.memory_usage > self.max_memory_per_agent:
                    await self._handle_memory_pressure(agent_id)
            await asyncio.sleep(10)
```

## Migration Strategy

### Phase 1: Side-by-side Testing
```python
# Feature flag to enable new implementation
if config.get("use_refactored_async_agents", False):
    from .async_session_manager_v2 import AsyncAgentSessionManager
else:
    from .async_session_manager import AsyncAgentSessionManager
```

### Phase 2: Gradual Rollout
1. Start with read-only agents (monitoring, reporting)
2. Move to low-risk agents (testing, validation)
3. Finally enable for production agents

### Phase 3: Deprecation
1. Log warnings for old API usage
2. Provide migration guide
3. Remove old implementation

## Performance Considerations

### 1. Task Queue Optimization
```python
class PriorityTaskQueue:
    """Priority queue for agent tasks."""
    
    def __init__(self, maxsize: int = 1000):
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
        self._counter = 0  # For FIFO ordering of same priority
        
    async def put(self, task: Dict, priority: int = 5):
        self._counter += 1
        # Lower number = higher priority
        await self._queue.put((priority, self._counter, task))
```

### 2. Batch Processing
```python
async def _process_mail_batch(self, session: AsyncAgentSession, messages: List[Mail]):
    """Process multiple mail messages efficiently."""
    # Group by sender for context
    by_sender = defaultdict(list)
    for msg in messages:
        by_sender[msg.from_agent].append(msg)
    
    # Process each sender's messages together
    for sender, sender_messages in by_sender.items():
        context = {"mail_from": sender, "message_count": len(sender_messages)}
        combined_prompt = self._combine_mail_messages(sender_messages)
        
        await session.task_queue.put({
            "prompt": combined_prompt,
            "context": context,
            "type": "mail_batch"
        })
```

## Monitoring & Observability

### 1. Metrics Collection
```python
class AsyncAgentMetrics:
    """Collects metrics for async agents."""
    
    def __init__(self):
        self.task_processing_time = Histogram("async_agent_task_duration_seconds")
        self.queue_depth = Gauge("async_agent_queue_depth")
        self.agent_state = Gauge("async_agent_state")
        
    async def record_task_duration(self, agent_id: str, duration: float):
        self.task_processing_time.labels(agent_id=agent_id).observe(duration)
```

### 2. Health Checks
```python
async def get_agent_health(self, agent_id: str) -> Dict:
    """Get health status of an async agent."""
    session = self.sessions.get(agent_id)
    if not session:
        return {"status": "not_found"}
        
    return {
        "status": "healthy" if session.state != AgentState.STOPPED else "stopped",
        "state": session.state.value,
        "queue_depth": session.task_queue.qsize(),
        "last_active": session.last_active,
        "errors": session.error_count,
        "uptime": (datetime.now() - session.created_at).total_seconds()
    }
```

## Security Considerations

### 1. Task Validation
```python
async def _validate_task(self, task: Dict) -> bool:
    """Validate task before processing."""
    # Check required fields
    if not task.get("prompt"):
        return False
        
    # Validate prompt length
    if len(task["prompt"]) > 10000:
        return False
        
    # Check for injection attempts
    if self._contains_injection(task["prompt"]):
        return False
        
    return True
```

### 2. Resource Isolation
```python
async def _create_sandboxed_context(self, session: AsyncAgentSession) -> SandboxedContext:
    """Create isolated execution context."""
    return SandboxedContext(
        agent_id=session.agent_id,
        max_execution_time=300,  # 5 minutes
        max_memory_mb=512,
        allowed_tools=session.allowed_tools,
        workspace_path=session.workspace_path
    )
```

## Testing Strategy

### 1. Unit Test Structure
```python
class TestAsyncAgentSessionManager:
    @pytest.mark.asyncio
    async def test_create_agent_aligned_with_current_pattern(self):
        """Test agent creation uses current patterns."""
        manager = AsyncAgentSessionManager(config, tool_registry, prompt_system)
        
        session = await manager.create_agent_session("d")
        
        assert isinstance(session.agent, StatelessAgent)
        assert isinstance(session.ai_loop, StatelessAILoop)
        assert session.state == AgentState.IDLE
```

### 2. Integration Test Scenarios
- Multi-agent coordination with mix of sync/async
- Recovery from crashes
- Resource limit enforcement
- Performance under load
- Event propagation accuracy

This technical design provides the detailed implementation guidance needed to refactor the async agents to work with the current architecture while maintaining their unique capabilities.