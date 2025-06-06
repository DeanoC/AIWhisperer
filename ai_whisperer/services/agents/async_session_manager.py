"""
Async Agent Session Manager for managing multiple independent AI loops.

This module enables true parallel agent execution with each agent running
its own AI loop independently, coordinating through the mailbox system.
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional, Set, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, Mail, MessagePriority
from ai_whisperer.context.agent_context import AgentContext

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """States an agent can be in."""
    IDLE = "idle"           # Not doing anything
    ACTIVE = "active"       # Processing a task
    SLEEPING = "sleeping"   # Sleeping until wake event
    WAITING = "waiting"     # Waiting for response
    STOPPED = "stopped"     # Stopped/terminated


@dataclass 
class AgentSession:
    """Represents an independent agent session."""
    agent_id: str
    agent: StatelessAgent
    ai_loop: StatelessAILoop
    state: AgentState = AgentState.IDLE
    task_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    current_task: Optional[Dict[str, Any]] = None
    wake_events: Set[str] = field(default_factory=set)  # Events that can wake this agent
    sleep_until: Optional[datetime] = None
    background_task: Optional[asyncio.Task] = None


class AsyncAgentSessionManager:
    """Manages multiple agent sessions running independently."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: Dict[str, AgentSession] = {}
        self.mailbox = get_mailbox()
        self._running = False
        self._background_tasks: Set[asyncio.Task] = set()
        self._wake_timers: Dict[str, asyncio.Task] = {}
        
    async def create_agent_session(
        self, 
        agent_id: str,
        auto_start: bool = True
    ) -> AgentSession:
        """Create a new agent session with its own AI loop."""
        if agent_id in self.sessions:
            raise ValueError(f"Agent session '{agent_id}' already exists")
            
        # Get agent configuration from registry
        from ai_whisperer.services.agents.registry import AgentRegistry
        from ai_whisperer.utils.path import PathManager
        
        path_manager = PathManager.get_instance()
        prompts_dir = path_manager.project_path / 'prompts' / 'agents'
        registry = AgentRegistry(prompts_dir)
        
        agent_info = registry.get_agent(agent_id)
        if not agent_info:
            raise ValueError(f"No configuration found for agent '{agent_id}'")
            
        # Load agent's prompt
        from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
        from ai_whisperer.tools.tool_registry import get_tool_registry
        
        prompt_config = PromptConfiguration(self.config)
        tool_registry = get_tool_registry()
        prompt_system = PromptSystem(prompt_config, tool_registry)
        
        agent_name = agent_info.prompt_file.replace('.prompt.md', '')
        system_prompt = prompt_system.get_formatted_prompt(
            category='agents',
            name=agent_name,
            include_tools=False,
            include_shared=True
        )
        
        # Create context and AI loop
        context = AgentContext(
            agent_id=agent_id,
            system_prompt=system_prompt
        )
        
        # Create AI loop for this agent
        from ai_whisperer.services.execution.ai_loop_factory import AILoopFactory
        from ai_whisperer.services.ai.openrouter import OpenRouterAIService
        
        # Use agent's AI config or fallback to default
        ai_config = agent_info.ai_config or self.config.get('ai_service', {})
        
        # Create AI service
        ai_service = OpenRouterAIService(ai_config)
        
        # Create AI loop
        ai_loop = AILoopFactory.create_ai_loop(
            ai_service=ai_service,
            config=self.config
        )
        
        # Create agent using StatelessAgent
        agent = StatelessAgent(
            agent_id=agent_id,
            system_prompt=system_prompt,
            agent_registry=registry
        )
        
        # Create session
        session = AgentSession(
            agent_id=agent_id,
            agent=agent,
            ai_loop=ai_loop,
            state=AgentState.IDLE
        )
        
        self.sessions[agent_id] = session
        
        if auto_start:
            # Start background processor for this agent
            task = asyncio.create_task(self._agent_processor(session))
            session.background_task = task
            self._background_tasks.add(task)
            
        logger.info(f"Created agent session for {agent_id}")
        return session
        
    async def _agent_processor(self, session: AgentSession):
        """Background processor for an agent session."""
        logger.info(f"Starting processor for agent {session.agent_id}")
        
        while self._running:
            try:
                # Check if sleeping
                if session.state == AgentState.SLEEPING:
                    if session.sleep_until and datetime.now() < session.sleep_until:
                        await asyncio.sleep(1)  # Check every second
                        continue
                    else:
                        # Wake up
                        session.state = AgentState.IDLE
                        session.sleep_until = None
                        logger.info(f"Agent {session.agent_id} woke up")
                
                # Check mailbox for new messages
                await self._check_agent_mailbox(session)
                
                # Process task queue
                if not session.task_queue.empty():
                    task = await session.task_queue.get()
                    await self._process_agent_task(session, task)
                else:
                    # No tasks, idle
                    session.state = AgentState.IDLE
                    await asyncio.sleep(0.5)  # Brief idle
                    
            except Exception as e:
                logger.error(f"Error in agent {session.agent_id} processor: {e}")
                await asyncio.sleep(1)
                
    async def _check_agent_mailbox(self, session: AgentSession):
        """Check agent's mailbox for new messages."""
        messages = self.mailbox.get_mail(session.agent_id)
        
        for mail in messages:
            # Convert mail to task
            task = {
                "type": "mailbox_message",
                "mail": mail,
                "from_agent": mail.from_agent,
                "subject": mail.subject,
                "body": mail.body,
                "priority": mail.priority
            }
            
            # Add to task queue
            await session.task_queue.put(task)
            logger.info(f"Agent {session.agent_id} received mail from {mail.from_agent}")
            
            # Mark as read
            self.mailbox.mark_as_read(session.agent_id, mail.message_id)
            
    async def _process_agent_task(self, session: AgentSession, task: Dict[str, Any]):
        """Process a task for an agent."""
        session.state = AgentState.ACTIVE
        session.current_task = task
        
        try:
            if task["type"] == "mailbox_message":
                # Process mail message
                mail = task["mail"]
                
                # Construct prompt for agent
                prompt = f"""You have received a message:
From: {mail.from_agent}
Subject: {mail.subject}
Body: {mail.body}

Please process this request and respond appropriately."""
                
                # Send to AI loop
                response = await session.ai_loop.process_message(
                    prompt,
                    agent_context=session.agent.context
                )
                
                # Send response back
                if mail.from_agent:  # Don't reply to broadcast messages
                    reply = Mail(
                        from_agent=session.agent_id,
                        to_agent=mail.from_agent,
                        subject=f"Re: {mail.subject}",
                        body=response.get("response", "Task completed"),
                        priority=MessagePriority.NORMAL
                    )
                    self.mailbox.send_mail(reply)
                    
            elif task["type"] == "timer_wake":
                # Timer-based wake up
                logger.info(f"Agent {session.agent_id} woke up from timer")
                
            elif task["type"] == "direct_task":
                # Direct task execution
                response = await session.ai_loop.process_message(
                    task["prompt"],
                    agent_context=session.agent.context
                )
                
                # Store result if callback provided
                if "callback" in task:
                    await task["callback"](response)
                    
        except Exception as e:
            logger.error(f"Agent {session.agent_id} task processing error: {e}")
        finally:
            session.state = AgentState.IDLE
            session.current_task = None
            
    async def send_task_to_agent(
        self,
        agent_id: str,
        prompt: str,
        callback: Optional[callable] = None
    ):
        """Send a direct task to an agent."""
        if agent_id not in self.sessions:
            raise ValueError(f"No session for agent '{agent_id}'")
            
        task = {
            "type": "direct_task",
            "prompt": prompt,
            "callback": callback
        }
        
        await self.sessions[agent_id].task_queue.put(task)
        
    async def sleep_agent(
        self,
        agent_id: str,
        duration_seconds: Optional[float] = None,
        until: Optional[datetime] = None,
        wake_events: Optional[Set[str]] = None
    ):
        """Put an agent to sleep."""
        if agent_id not in self.sessions:
            raise ValueError(f"No session for agent '{agent_id}'")
            
        session = self.sessions[agent_id]
        session.state = AgentState.SLEEPING
        
        if duration_seconds:
            session.sleep_until = datetime.now().timestamp() + duration_seconds
        elif until:
            session.sleep_until = until
            
        if wake_events:
            session.wake_events = wake_events
            
        logger.info(f"Agent {agent_id} going to sleep")
        
    async def wake_agent(self, agent_id: str, reason: str = "manual"):
        """Wake a sleeping agent."""
        if agent_id not in self.sessions:
            return
            
        session = self.sessions[agent_id]
        if session.state == AgentState.SLEEPING:
            session.state = AgentState.IDLE
            session.sleep_until = None
            
            # Add wake event to task queue
            await session.task_queue.put({
                "type": "wake_event",
                "reason": reason
            })
            
            logger.info(f"Agent {agent_id} woken up: {reason}")
            
    async def broadcast_event(self, event: str, data: Dict[str, Any]):
        """Broadcast an event to all agents listening for it."""
        for agent_id, session in self.sessions.items():
            if event in session.wake_events:
                await self.wake_agent(agent_id, f"Event: {event}")
                
    async def start(self):
        """Start the session manager."""
        self._running = True
        logger.info("Async agent session manager started")
        
    async def stop(self):
        """Stop all agent sessions."""
        self._running = False
        
        # Cancel all background tasks
        for task in self._background_tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
        self.sessions.clear()
        
        logger.info("Async agent session manager stopped")
        
    def get_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get current state of all agents."""
        states = {}
        for agent_id, session in self.sessions.items():
            states[agent_id] = {
                "state": session.state.value,
                "current_task": session.current_task.get("type") if session.current_task else None,
                "queue_size": session.task_queue.qsize(),
                "sleeping_until": session.sleep_until.isoformat() if session.sleep_until else None
            }
        return states