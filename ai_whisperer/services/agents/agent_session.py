"""Individual agent session for async multi-agent system."""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ai_whisperer.services.agents.agent_state import AgentState, AgentStateInfo, AgentStateMachine
from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.context.context_manager import ContextManager
from ai_whisperer.core.agent_logger import AgentLogger


logger = logging.getLogger(__name__)


class AgentSession:
    """Represents an individual agent's execution session."""
    
    def __init__(
        self,
        agent_id: str,
        agent_config: Dict[str, Any],
        tool_registry: ToolRegistry,
        context_manager: ContextManager,
        state_change_callback: Optional[Callable] = None
    ):
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.tool_registry = tool_registry
        self.context_manager = context_manager
        self.state_change_callback = state_change_callback
        
        # State management
        self.state_info = AgentStateInfo(
            agent_id=agent_id,
            state=AgentState.IDLE
        )
        
        # AI loop manager
        self.ai_loop_manager = AILoopManager(
            agent_config=agent_config,
            tool_registry=tool_registry,
            context_manager=context_manager
        )
        
        # Agent-specific logger
        self.agent_logger = AgentLogger(agent_id)
        
        # Execution control
        self._task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused by default
        self._stop_event = asyncio.Event()
        
        # Mailbox monitoring
        self._last_mailbox_check = datetime.now()
        
        logger.info(f"Created agent session for {agent_id}")
        self.agent_logger.log_event("session_created", {"config": agent_config})
    
    async def start(self) -> None:
        """Start the agent's AI loop."""
        if self.state_info.state != AgentState.IDLE:
            raise RuntimeError(f"Cannot start agent in state {self.state_info.state.value}")
        
        self._transition_state(AgentState.ACTIVE)
        self._task = asyncio.create_task(self._run_loop())
        
        logger.info(f"Started agent {self.agent_id}")
        self.agent_logger.log_event("session_started", {})
    
    async def pause(self) -> None:
        """Pause the agent's execution."""
        if self.state_info.state != AgentState.ACTIVE:
            raise RuntimeError(f"Cannot pause agent in state {self.state_info.state.value}")
        
        self._transition_state(AgentState.PAUSED)
        self._pause_event.clear()
        
        logger.info(f"Paused agent {self.agent_id}")
        self.agent_logger.log_event("session_paused", {})
    
    async def resume(self) -> None:
        """Resume the agent's execution."""
        if self.state_info.state != AgentState.PAUSED:
            raise RuntimeError(f"Cannot resume agent in state {self.state_info.state.value}")
        
        self._transition_state(AgentState.ACTIVE)
        self._pause_event.set()
        
        logger.info(f"Resumed agent {self.agent_id}")
        self.agent_logger.log_event("session_resumed", {})
    
    async def stop(self) -> None:
        """Stop the agent's execution."""
        if self.state_info.state == AgentState.STOPPED:
            return
        
        self._transition_state(AgentState.STOPPED)
        self._stop_event.set()
        self._pause_event.set()  # Unpause if paused
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Stopped agent {self.agent_id}")
        self.agent_logger.log_event("session_stopped", {})
    
    async def sleep(self, duration: Optional[float] = None) -> None:
        """Put the agent to sleep."""
        if self.state_info.state != AgentState.ACTIVE:
            raise RuntimeError(f"Cannot sleep agent in state {self.state_info.state.value}")
        
        self._transition_state(AgentState.SLEEPING)
        
        if duration:
            # Sleep for specified duration
            await asyncio.sleep(duration)
            if self.state_info.state == AgentState.SLEEPING:
                self._transition_state(AgentState.ACTIVE)
        
        logger.info(f"Agent {self.agent_id} sleeping")
        self.agent_logger.log_event("session_sleeping", {"duration": duration})
    
    async def wake(self) -> None:
        """Wake the agent from sleep."""
        if self.state_info.state != AgentState.SLEEPING:
            return
        
        self._transition_state(AgentState.ACTIVE)
        
        logger.info(f"Woke agent {self.agent_id}")
        self.agent_logger.log_event("session_woken", {})
    
    def get_state(self) -> AgentStateInfo:
        """Get current agent state."""
        return self.state_info
    
    async def _run_loop(self) -> None:
        """Main execution loop for the agent."""
        try:
            while not self._stop_event.is_set():
                # Check if paused
                await self._pause_event.wait()
                
                # Check mailbox for new messages
                await self._check_mailbox()
                
                # Process any pending tasks
                # This is where the AI loop would process tasks
                # For now, just sleep to simulate work
                await asyncio.sleep(1)
                
                # Update last activity
                self.state_info.last_activity = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in agent {self.agent_id} loop: {e}")
            self.agent_logger.log_error("session_error", str(e))
            self.state_info.error_message = str(e)
            self._transition_state(AgentState.ERROR)
            raise
    
    async def _check_mailbox(self) -> None:
        """Check mailbox for new messages."""
        # TODO: Implement mailbox checking
        # This will integrate with the existing mailbox system
        pass
    
    def _transition_state(self, new_state: AgentState) -> None:
        """Transition to a new state."""
        old_state = self.state_info.state
        self.state_info = AgentStateMachine.transition(self.state_info, new_state)
        
        # Notify callback if registered
        if self.state_change_callback:
            self.state_change_callback(self.agent_id, old_state, new_state)
        
        self.agent_logger.log_event("state_changed", {
            "from": old_state.value,
            "to": new_state.value
        })