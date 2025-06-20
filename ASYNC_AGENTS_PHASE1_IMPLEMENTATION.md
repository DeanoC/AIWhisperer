# Async Agents Phase 1: Implementation Guide

## Quick Start Implementation

This guide provides copy-paste ready code for Phase 1 of the async agents refactoring.

## Step 1: Create New AsyncAgentSessionManager

Create `ai_whisperer/services/agents/async_session_manager_v2.py`:

```python
"""
Refactored Async Agent Session Manager aligned with current architecture.
"""

import asyncio
import logging
from typing import Dict, Optional, Set, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, Mail, MessagePriority
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
from ai_whisperer.tools.tool_registry import get_tool_registry
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """States an agent can be in."""
    IDLE = "idle"
    ACTIVE = "active"
    SLEEPING = "sleeping"
    WAITING = "waiting"
    STOPPED = "stopped"


@dataclass
class AsyncAgentSession:
    """Represents an async agent session with proper architecture alignment."""
    agent_id: str
    agent: StatelessAgent
    ai_loop: StatelessAILoop
    context: AgentContext
    state: AgentState = AgentState.IDLE
    task_queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=100))
    current_task: Optional[Dict[str, Any]] = None
    wake_events: Set[str] = field(default_factory=set)
    sleep_until: Optional[datetime] = None
    background_task: Optional[asyncio.Task] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AsyncAgentSessionManager:
    """Manages multiple agent sessions running independently - Refactored version."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: Dict[str, AsyncAgentSession] = {}
        self._background_tasks: Set[asyncio.Task] = set()
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Initialize core components matching StatelessSessionManager pattern
        self._init_core_components()
        
    def _init_core_components(self):
        """Initialize components following current architecture."""
        # Path manager
        self.path_manager = PathManager.get_instance()
        
        # Agent registry
        prompts_dir = self.path_manager.project_path / 'prompts' / 'agents'
        self.agent_registry = AgentRegistry(prompts_dir)
        
        # Prompt system
        self.prompt_config = PromptConfiguration(self.config)
        self.tool_registry = get_tool_registry()
        self.prompt_system = PromptSystem(self.prompt_config, self.tool_registry)
        
        # AI loop manager
        self.ai_loop_manager = AILoopManager()
        
        logger.info("Initialized async agent session manager with current architecture")
        
    async def start(self):
        """Start the async agent session manager."""
        if self._running:
            return
            
        self._running = True
        
        # Start event processor
        event_task = asyncio.create_task(self._event_processor())
        self._background_tasks.add(event_task)
        
        logger.info("Async agent session manager started")
        
    async def stop(self):
        """Stop all agents and clean up."""
        self._running = False
        
        # Stop all agents
        for agent_id in list(self.sessions.keys()):
            await self.stop_agent(agent_id)
            
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        logger.info("Async agent session manager stopped")
        
    async def create_agent_session(self, agent_id: str, auto_start: bool = True) -> AsyncAgentSession:
        """Create a new agent session using current patterns."""
        if agent_id in self.sessions:
            raise ValueError(f"Agent session '{agent_id}' already exists")
            
        # Get agent configuration from registry
        agent_info = self.agent_registry.get_agent(agent_id)
        if not agent_info:
            raise ValueError(f"No configuration found for agent '{agent_id}'")
            
        # Load agent prompt using current pattern
        system_prompt = await self._load_agent_prompt(agent_info)
        
        # Create agent context
        context = AgentContext(
            agent_id=agent_id,
            system_prompt=system_prompt
        )
        
        # Get or create AI loop through manager
        ai_loop = self.ai_loop_manager.get_or_create_ai_loop(
            agent_id=agent_id,
            agent_config=agent_info.ai_config,
            fallback_config=self.config
        )
        
        # Create stateless agent
        agent = StatelessAgent(
            agent_id=agent_id,
            system_prompt=system_prompt,
            agent_registry=self.agent_registry
        )
        
        # Initialize agent with AI loop
        agent.ai_loop = ai_loop
        
        # Create async session
        session = AsyncAgentSession(
            agent_id=agent_id,
            agent=agent,
            ai_loop=ai_loop,
            context=context,
            state=AgentState.IDLE
        )
        
        self.sessions[agent_id] = session
        
        # Start background processor if requested
        if auto_start:
            task = asyncio.create_task(self._agent_processor(session))
            session.background_task = task
            self._background_tasks.add(task)
            
        logger.info(f"Created async agent session for '{agent_id}' (auto_start={auto_start})")
        
        # Emit event
        await self._emit_event("agent_created", {
            "agent_id": agent_id,
            "auto_started": auto_start
        })
        
        return session
        
    async def _load_agent_prompt(self, agent_info) -> str:
        """Load agent prompt following current pattern."""
        agent_name = agent_info.prompt_file.replace('.prompt.md', '')
        
        # Get formatted prompt with shared components
        prompt = self.prompt_system.get_formatted_prompt(
            category='agents',
            name=agent_name,
            include_tools=False,  # Tools handled separately
            include_shared=True
        )
        
        return prompt
        
    async def _agent_processor(self, session: AsyncAgentSession):
        """Background processor for an agent - aligned with current patterns."""
        logger.info(f"Starting processor for agent {session.agent_id}")
        
        try:
            while session.state != AgentState.STOPPED:
                session.last_active = datetime.now()
                
                # Handle sleeping state
                if session.state == AgentState.SLEEPING:
                    await self._handle_sleep_state(session)
                    continue
                    
                # Process tasks when idle
                if session.state == AgentState.IDLE:
                    # Try to get a task
                    try:
                        task = await asyncio.wait_for(
                            session.task_queue.get(),
                            timeout=5.0  # Check mail every 5 seconds if no tasks
                        )
                        
                        # Process the task
                        session.state = AgentState.ACTIVE
                        session.current_task = task
                        
                        await self._process_task(session, task)
                        
                        session.current_task = None
                        session.state = AgentState.IDLE
                        
                    except asyncio.TimeoutError:
                        # No tasks, check mail
                        await self._check_mail_async(session)
                        
                await asyncio.sleep(0.1)  # Prevent tight loop
                
        except Exception as e:
            logger.error(f"Fatal error in agent {session.agent_id} processor: {e}")
            session.error_count += 1
            await self._emit_event("agent_error", {
                "agent_id": session.agent_id,
                "error": str(e),
                "error_count": session.error_count
            })
        finally:
            session.state = AgentState.STOPPED
            logger.info(f"Processor stopped for agent {session.agent_id}")
            
    async def _process_task(self, session: AsyncAgentSession, task: Dict[str, Any]):
        """Process a task using the agent's AI loop."""
        logger.info(f"Agent {session.agent_id} processing task: {task.get('type', 'user')}")
        
        try:
            prompt = task.get("prompt", "")
            
            # Create task context
            task_context = {
                "task_id": task.get("id"),
                "task_type": task.get("type"),
                "from_agent": task.get("context", {}).get("from_agent"),
                "priority": task.get("context", {}).get("priority")
            }
            
            # Update agent context
            session.context.update(task_context)
            
            # Process through AI loop (using sync for now, will make async)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                session.agent.process_message,
                prompt
            )
            
            # Handle continuation if needed
            if isinstance(result, dict) and result.get("metadata", {}).get("continue"):
                # Queue continuation
                await session.task_queue.put({
                    "prompt": "Continue with the current task",
                    "context": {
                        "parent_task": task.get("id"),
                        "continuation": True
                    },
                    "type": "continuation"
                })
                
            # Emit completion event
            await self._emit_event("task_completed", {
                "agent_id": session.agent_id,
                "task": task,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Error processing task for agent {session.agent_id}: {e}")
            session.error_count += 1
            
            await self._emit_event("task_error", {
                "agent_id": session.agent_id,
                "task": task,
                "error": str(e)
            })
            
    async def _check_mail_async(self, session: AsyncAgentSession):
        """Check mailbox without blocking."""
        try:
            mailbox = get_mailbox()
            messages = mailbox.check_mail(session.agent_id)
            
            if messages:
                logger.info(f"Agent {session.agent_id} has {len(messages)} new messages")
                
            for message in messages:
                # High priority mail wakes sleeping agents
                if session.state == AgentState.SLEEPING:
                    if message.priority == MessagePriority.HIGH:
                        await self.wake_agent(
                            session.agent_id,
                            f"High priority mail from {message.from_agent}"
                        )
                        
                # Queue mail as task
                await session.task_queue.put({
                    "prompt": f"Process this mail:\nFrom: {message.from_agent}\nSubject: {message.subject}\n\n{message.body}",
                    "context": {
                        "mail_id": message.id,
                        "from_agent": message.from_agent,
                        "priority": message.priority.value,
                        "subject": message.subject
                    },
                    "type": "mail"
                })
                
        except Exception as e:
            logger.error(f"Error checking mail for agent {session.agent_id}: {e}")
            
    async def _handle_sleep_state(self, session: AsyncAgentSession):
        """Handle agent sleep state."""
        # Check if it's time to wake up
        if session.sleep_until and datetime.now() >= session.sleep_until:
            session.state = AgentState.IDLE
            session.sleep_until = None
            logger.info(f"Agent {session.agent_id} woke up (scheduled)")
            
            await self._emit_event("agent_woke", {
                "agent_id": session.agent_id,
                "reason": "scheduled"
            })
        else:
            # Still sleeping
            await asyncio.sleep(1)
            
    async def sleep_agent(self, agent_id: str, duration_seconds: Optional[int] = None,
                         wake_events: Optional[Set[str]] = None):
        """Put an agent to sleep."""
        session = self.sessions.get(agent_id)
        if not session:
            raise ValueError(f"Agent '{agent_id}' not found")
            
        session.state = AgentState.SLEEPING
        
        if duration_seconds:
            session.sleep_until = datetime.now() + timedelta(seconds=duration_seconds)
            
        if wake_events:
            session.wake_events = wake_events
            
        logger.info(f"Agent {agent_id} sleeping until {session.sleep_until}")
        
        await self._emit_event("agent_sleeping", {
            "agent_id": agent_id,
            "until": session.sleep_until,
            "wake_events": list(wake_events) if wake_events else []
        })
        
    async def wake_agent(self, agent_id: str, reason: str = "manual"):
        """Wake a sleeping agent."""
        session = self.sessions.get(agent_id)
        if not session:
            raise ValueError(f"Agent '{agent_id}' not found")
            
        if session.state == AgentState.SLEEPING:
            session.state = AgentState.IDLE
            session.sleep_until = None
            session.wake_events.clear()
            
            logger.info(f"Agent {agent_id} woke up: {reason}")
            
            await self._emit_event("agent_woke", {
                "agent_id": agent_id,
                "reason": reason
            })
            
    async def stop_agent(self, agent_id: str):
        """Stop an agent and clean up resources."""
        session = self.sessions.get(agent_id)
        if not session:
            return
            
        # Set state to stopped
        session.state = AgentState.STOPPED
        
        # Cancel background task
        if session.background_task:
            session.background_task.cancel()
            try:
                await session.background_task
            except asyncio.CancelledError:
                pass
                
        # Clean up AI loop
        if hasattr(session, 'ai_loop'):
            # AI loop cleanup if needed
            pass
            
        # Remove from sessions
        del self.sessions[agent_id]
        
        logger.info(f"Stopped agent {agent_id}")
        
        await self._emit_event("agent_stopped", {
            "agent_id": agent_id
        })
        
    async def send_task_to_agent(self, agent_id: str, prompt: str,
                                context: Optional[Dict[str, Any]] = None):
        """Send a task directly to an agent."""
        session = self.sessions.get(agent_id)
        if not session:
            raise ValueError(f"Agent '{agent_id}' not found")
            
        task = {
            "prompt": prompt,
            "context": context or {},
            "type": "direct",
            "id": f"task_{datetime.now().timestamp()}"
        }
        
        await session.task_queue.put(task)
        
        logger.info(f"Queued task for agent {agent_id}")
        
    async def broadcast_event(self, event: str, data: Dict[str, Any]):
        """Broadcast an event that might wake agents."""
        await self._emit_event(event, data)
        
        # Check if any sleeping agents should wake
        for session in self.sessions.values():
            if session.state == AgentState.SLEEPING and event in session.wake_events:
                await self.wake_agent(session.agent_id, f"Event: {event}")
                
    def get_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get current state of all agents."""
        return {
            agent_id: {
                "state": session.state.value,
                "queue_depth": session.task_queue.qsize(),
                "current_task": session.current_task.get("type") if session.current_task else None,
                "sleep_until": session.sleep_until.isoformat() if session.sleep_until else None,
                "wake_events": list(session.wake_events),
                "error_count": session.error_count,
                "last_active": session.last_active.isoformat()
            }
            for agent_id, session in self.sessions.items()
        }
        
    async def _emit_event(self, event: str, data: Dict[str, Any]):
        """Emit an event to the event queue."""
        await self._event_queue.put({
            "event": event,
            "data": data,
            "timestamp": datetime.now()
        })
        
    async def _event_processor(self):
        """Process events in the background."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                logger.debug(f"Event: {event['event']} - {event['data']}")
                # Future: Add event handlers here
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")


# Import timedelta at the top
from datetime import datetime, timedelta
```

## Step 2: Update AsyncAgentEndpoints

Update `interactive_server/async_agent_endpoints.py` to use the new manager:

```python
# In AsyncAgentEndpoints.__init__
def __init__(self, session_manager):
    self.session_manager = session_manager
    self.async_managers: Dict[str, AsyncAgentSessionManager] = {}
    
# In _get_or_create_manager method
async def _get_or_create_manager(self, session_id: str) -> AsyncAgentSessionManager:
    """Get or create async manager for a session."""
    if session_id not in self.async_managers:
        # Get config from session
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"No session found: {session_id}")
            
        config = session.config if hasattr(session, 'config') else {}
        
        # Use new refactored manager if feature flag is set
        if config.get("use_refactored_async_agents", True):
            from ai_whisperer.services.agents.async_session_manager_v2 import AsyncAgentSessionManager
        else:
            from ai_whisperer.services.agents.async_session_manager import AsyncAgentSessionManager
        
        # Create manager
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        self.async_managers[session_id] = manager
        
    return self.async_managers[session_id]
```

## Step 3: Create Test File

Create `tests/integration/async_agents/test_async_agents_refactored.py`:

```python
"""Test refactored async agent implementation."""

import pytest
import asyncio
import json
from datetime import datetime

from ai_whisperer.services.agents.async_session_manager_v2 import (
    AsyncAgentSessionManager, AgentState
)


class TestAsyncAgentsRefactored:
    """Test the refactored async agent implementation."""
    
    @pytest.mark.asyncio
    async def test_agent_creation_with_current_patterns(self):
        """Test that agents are created using current patterns."""
        config = {
            "use_refactored_async_agents": True,
            "ai_service": {
                "provider": "openrouter",
                "api_key": "test-key"
            }
        }
        
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        
        try:
            # Create agent
            session = await manager.create_agent_session("d", auto_start=False)
            
            # Verify creation
            assert session.agent_id == "d"
            assert session.state == AgentState.IDLE
            assert hasattr(session, 'agent')
            assert hasattr(session, 'ai_loop')
            assert hasattr(session, 'context')
            
            # Verify using StatelessAgent
            assert session.agent.__class__.__name__ == "StatelessAgent"
            
        finally:
            await manager.stop()
            
    @pytest.mark.asyncio
    async def test_task_processing(self):
        """Test task processing through async agent."""
        config = {"use_refactored_async_agents": True}
        
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        
        try:
            # Create agent
            session = await manager.create_agent_session("d")
            
            # Send task
            await manager.send_task_to_agent(
                "d",
                "What is 2 + 2?",
                {"test": True}
            )
            
            # Wait for processing
            await asyncio.sleep(2)
            
            # Check state
            states = manager.get_agent_states()
            assert "d" in states
            
        finally:
            await manager.stop()
```

## Step 4: Enable Feature Flag

In `config/main.yaml`:

```yaml
# Enable refactored async agents
use_refactored_async_agents: true

# Async agent configuration
async_agents:
  max_concurrent_agents: 10
  max_tasks_per_agent: 100
  default_check_mail_interval: 30
```

## Next Steps

1. **Test the basic implementation**:
   ```bash
   pytest tests/integration/async_agents/test_async_agents_refactored.py -v
   ```

2. **Fix any import/initialization issues**

3. **Add more sophisticated task processing** in Phase 2

4. **Implement state persistence** in Phase 3

This implementation provides a solid foundation that aligns with the current architecture while maintaining the async agent capabilities.