"""
Refactored Async Agent Session Manager aligned with current architecture.
"""

import asyncio
import logging
from typing import Dict, Optional, Set, Any
from datetime import datetime, timedelta
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
from ai_whisperer.services.agents.state_persistence import StatePersistenceManager

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
    
    def __init__(self, config: Dict[str, Any], notification_callback=None):
        self.config = config
        self.sessions: Dict[str, AsyncAgentSession] = {}
        self._background_tasks: Set[asyncio.Task] = set()
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Notification callback for WebSocket events
        self._notification_callback = notification_callback
        
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
        
        # State persistence manager
        state_dir = self.path_manager.output_path / 'state'
        self.state_manager = StatePersistenceManager(state_dir)
        
        logger.info("Initialized async agent session manager with current architecture and state persistence")
        
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
        
        # Inject async session manager reference for tools
        context.async_session_manager = self
        
        # Get or create AI loop through manager
        # Note: agent_info.ai_config is a dict, not an AgentConfig object
        ai_loop = self.ai_loop_manager.get_or_create_ai_loop(
            agent_id=agent_id,
            agent_config=None,  # Don't pass the AgentConfig
            fallback_config=agent_info.ai_config or self.config  # Use ai_config dict as fallback
        )
        
        # Create a proper AgentConfig for StatelessAgent
        from ai_whisperer.services.agents.config import AgentConfig
        
        # Extract generation params from ai_config if available
        generation_params = {}
        if agent_info.ai_config:
            generation_params = agent_info.ai_config.get('generation_params', {})
        
        # Create agent config with required fields
        agent_config = AgentConfig(
            name=agent_id,
            description=agent_info.description,
            system_prompt=system_prompt,
            model_name=ai_loop.config.model_id,
            provider="openrouter",
            generation_params=generation_params,
            api_settings={}
        )
        
        # Create stateless agent with correct signature
        agent = StatelessAgent(
            config=agent_config,
            context=context,
            ai_loop=ai_loop,
            agent_registry_info=agent_info
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
            task_id = task.get("id", f"task_{datetime.now().timestamp()}")
            
            # Send task started notification
            logger.info(f"About to send task.started notification for task {task_id}")
            await self._send_notification("async.task.started", {
                "agent_id": session.agent_id,
                "task_id": task_id,
                "task_type": task.get("type", "user"),
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
            })
            
            # Create task context
            task_context = {
                "task_id": task_id,
                "task_type": task.get("type"),
                "from_agent": task.get("context", {}).get("from_agent"),
                "priority": task.get("context", {}).get("priority")
            }
            
            # Update agent context
            if hasattr(session.context, 'update'):
                session.context.update(task_context)
            else:
                # AgentContext doesn't have update method, set attributes directly
                for key, value in task_context.items():
                    if value is not None:
                        setattr(session.context, key, value)
            
            # Process through AI loop (already async)
            result = await session.agent.process_message(prompt)
            
            # Parse result to extract channel responses
            channel_response = self._extract_channel_response(result)
            
            # Send task completed notification with channel response
            await self._send_notification("async.task.completed", {
                "agent_id": session.agent_id,
                "task_id": task_id,
                "result": channel_response,
                "raw_result": result  # Include raw result for debugging
            })
            
            # Handle continuation if needed
            if isinstance(result, dict) and result.get("metadata", {}).get("continue"):
                # Queue continuation
                await session.task_queue.put({
                    "prompt": "Continue with the current task",
                    "context": {
                        "parent_task": task_id,
                        "continuation": True
                    },
                    "type": "continuation"
                })
                
                await self._send_notification("async.task.continuation", {
                    "agent_id": session.agent_id,
                    "task_id": task_id,
                    "parent_task": task_id
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
            
            # Send error notification
            await self._send_notification("async.task.error", {
                "agent_id": session.agent_id,
                "task_id": task.get("id"),
                "error": str(e),
                "error_count": session.error_count
            })
            
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
                # Wake sleeping agents based on their wake events and message priority
                if session.state == AgentState.SLEEPING:
                    should_wake = False
                    wake_reason = None
                    
                    # Check if agent should wake based on configured wake events
                    if "mail_received" in session.wake_events:
                        should_wake = True
                        wake_reason = f"Mail received from {message.from_agent}"
                    elif "high_priority_mail" in session.wake_events and message.priority == MessagePriority.HIGH:
                        should_wake = True
                        wake_reason = f"High priority mail from {message.from_agent}"
                    
                    if should_wake:
                        await self.wake_agent(session.agent_id, wake_reason)
                        
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
        """Handle agent sleep state with optimized monitoring."""
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
            # Still sleeping - check mail less frequently and sleep longer
            # Check mail every 10 seconds when sleeping (vs 5 seconds when active)
            await self._check_mail_async(session)
            
            # Sleep for longer periods when sleeping to reduce CPU usage
            # Calculate sleep time based on remaining sleep duration
            if session.sleep_until:
                time_remaining = (session.sleep_until - datetime.now()).total_seconds()
                # Sleep for up to 5 seconds, but not longer than remaining time
                sleep_duration = min(5.0, max(1.0, time_remaining))
            else:
                # Indefinite sleep - check every 5 seconds
                sleep_duration = 5.0
                
            await asyncio.sleep(sleep_duration)
            
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
    
    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a notification via the callback if available."""
        logger.info(f"Attempting to send notification: {method}")
        if self._notification_callback:
            try:
                logger.info(f"Calling notification callback for {method}")
                await self._notification_callback(method, params)
                logger.info(f"Successfully sent notification: {method}")
            except Exception as e:
                logger.error(f"Error sending notification {method}: {e}")
        else:
            # Log notification for debugging
            logger.warning(f"No notification callback available for: {method} - {params}")
    
    def _extract_channel_response(self, result: Any) -> Dict[str, Any]:
        """Extract channel response from AI result."""
        if not isinstance(result, dict):
            # Convert string result to channel format
            return {
                "analysis": "",
                "commentary": "",
                "final": str(result)
            }
        
        # Check if already in channel format
        if all(key in result for key in ['analysis', 'commentary', 'final']):
            return {
                "analysis": result.get("analysis", ""),
                "commentary": result.get("commentary", ""),
                "final": result.get("final", "")
            }
        
        # Extract from other formats
        if "response" in result:
            return {
                "analysis": "",
                "commentary": "",
                "final": result["response"]
            }
        
        # Default format
        return {
            "analysis": "",
            "commentary": "",
            "final": str(result)
        }
    
    # === STATE PERSISTENCE METHODS ===
    
    def _session_to_state_dict(self, session: AsyncAgentSession) -> Dict[str, Any]:
        """Convert AsyncAgentSession to serializable dictionary."""
        # Extract task queue items (convert to list for serialization)
        pending_tasks = []
        try:
            # Get tasks from queue without blocking
            while not session.task_queue.empty():
                task = session.task_queue.get_nowait()
                pending_tasks.append(task)
                # Put it back in the queue
                session.task_queue.put_nowait(task)
        except asyncio.QueueEmpty:
            pass
        
        return {
            "agent_id": session.agent_id,
            "agent_name": getattr(session.agent, 'name', session.agent_id),
            "status": session.state.value,
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat(),
            "configuration": {
                "model": getattr(session.ai_loop.config, 'model_id', 'unknown'),
                "provider": getattr(session.ai_loop.config, 'provider', 'openrouter'),
                "generation_params": getattr(session.agent.config, 'generation_params', {})
            },
            "context": {
                "system_prompt": session.agent.config.system_prompt,
                "conversation_history": getattr(session.context, 'conversation_history', []),
                "working_memory": getattr(session.context, 'metadata', {})
            },
            "tool_sets": getattr(session.agent.config, 'tool_sets', []),
            "sleep_state": {
                "is_sleeping": session.state == AgentState.SLEEPING,
                "sleep_until": session.sleep_until.isoformat() if session.sleep_until else None,
                "wake_events": list(session.wake_events)
            },
            "task_queue": {
                "pending_tasks": pending_tasks,
                "current_task": session.current_task
            },
            "metadata": {
                "error_count": session.error_count,
                "custom_metadata": session.metadata
            }
        }
    
    async def save_session_state(self, agent_id: str) -> bool:
        """Save agent session state to persistence layer."""
        session = self.sessions.get(agent_id)
        if not session:
            logger.warning(f"Cannot save state for non-existent agent: {agent_id}")
            return False
        
        try:
            # Convert session to serializable dict
            state_dict = self._session_to_state_dict(session)
            
            # Save agent state
            agent_success = self.state_manager.save_agent_state(agent_id, state_dict)
            
            # Save task queue state separately
            task_queue_state = state_dict["task_queue"]
            task_queue_state["agent_id"] = agent_id
            task_success = self.state_manager.save_task_queue_state(agent_id, task_queue_state)
            
            # Save sleep state separately
            sleep_state = state_dict["sleep_state"]
            sleep_state["agent_id"] = agent_id
            sleep_success = self.state_manager.save_sleep_state(agent_id, sleep_state)
            
            success = agent_success and task_success and sleep_success
            if success:
                logger.info(f"Successfully saved state for agent {agent_id}")
            else:
                logger.error(f"Failed to save complete state for agent {agent_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving state for agent {agent_id}: {e}")
            return False
    
    async def save_all_session_states(self) -> int:
        """Save state for all active sessions."""
        saved_count = 0
        for agent_id in list(self.sessions.keys()):
            if await self.save_session_state(agent_id):
                saved_count += 1
        
        logger.info(f"Saved state for {saved_count}/{len(self.sessions)} agents")
        return saved_count
    
    async def restore_session_state(self, agent_id: str) -> bool:
        """Restore agent session from persistence layer."""
        try:
            # Load agent state
            agent_state = self.state_manager.load_agent_state(agent_id)
            if not agent_state:
                logger.debug(f"No persisted state found for agent {agent_id}")
                return False
            
            # Create agent session from saved state
            session = await self.create_agent_session(agent_id, auto_start=False)
            
            # Restore session properties
            session.state = AgentState(agent_state.get("status", "idle"))
            session.last_active = datetime.fromisoformat(agent_state.get("last_active", datetime.now().isoformat()))
            session.error_count = agent_state.get("metadata", {}).get("error_count", 0)
            session.metadata = agent_state.get("metadata", {}).get("custom_metadata", {})
            
            # Restore sleep state
            sleep_state = self.state_manager.load_sleep_state(agent_id)
            if sleep_state and sleep_state.get("is_sleeping"):
                session.state = AgentState.SLEEPING
                if sleep_state.get("sleep_until"):
                    session.sleep_until = datetime.fromisoformat(sleep_state["sleep_until"])
                session.wake_events = set(sleep_state.get("wake_events", []))
            
            # Restore task queue
            task_queue_state = self.state_manager.load_task_queue_state(agent_id)
            if task_queue_state:
                # Add pending tasks back to queue
                for task in task_queue_state.get("pending_tasks", []):
                    await session.task_queue.put(task)
                session.current_task = task_queue_state.get("current_task")
            
            logger.info(f"Successfully restored state for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring state for agent {agent_id}: {e}")
            return False
    
    async def restore_all_session_states(self) -> int:
        """Restore all persisted agent sessions."""
        try:
            persisted_agents = self.state_manager.list_persisted_agents()
            restored_count = 0
            
            for agent_id in persisted_agents:
                if await self.restore_session_state(agent_id):
                    restored_count += 1
            
            logger.info(f"Restored {restored_count}/{len(persisted_agents)} persisted agents")
            return restored_count
            
        except Exception as e:
            logger.error(f"Error restoring session states: {e}")
            return 0
    
    async def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """Clean up old persisted state files."""
        try:
            cleanup_count = self.state_manager.cleanup_old_states(max_age_hours)
            logger.info(f"Cleaned up {cleanup_count} old state files")
            return cleanup_count
        except Exception as e:
            logger.error(f"Error cleaning up old states: {e}")
            return 0