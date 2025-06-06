"""
Module: examples/async_agents/utils/base_workflow.py
Purpose: Base class for async agent workflows

Provides common functionality for multi-agent workflows including:
- Result tracking
- Error handling
- State management
- Performance metrics
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

from ai_whisperer.services.agents.async_session_manager_v2 import (
    AsyncAgentSessionManager, AgentState
)
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, Mail, MessagePriority

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Base class for workflow results."""
    status: str = "pending"
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_runtime(self) -> float:
        """Calculate total runtime in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == "completed" and not self.errors
    
    def add_error(self, error_type: str, error_msg: str, **kwargs) -> None:
        """Add an error to the result."""
        error = {
            "type": error_type,
            "message": error_msg,
            "timestamp": datetime.now(),
            **kwargs
        }
        self.errors.append(error)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status,
            "errors": self.errors,
            "total_runtime": self.total_runtime,
            "metadata": self.metadata
        }


class BaseWorkflow(ABC):
    """
    Abstract base class for async agent workflows.
    
    Provides common functionality for:
    - Agent session management
    - Error handling and recovery
    - Performance tracking
    - State persistence support
    """
    
    def __init__(self, workspace_path: Path, output_path: Path):
        """Initialize base workflow."""
        self.workspace_path = Path(workspace_path)
        self.output_path = Path(output_path)
        self.mailbox = get_mailbox()
        self._active_agents: Set[str] = set()
        self._checkpoint_data: Optional[Dict[str, Any]] = None
        
    async def create_agents(
        self, 
        agent_ids: List[str], 
        session_manager: AsyncAgentSessionManager,
        auto_start: bool = True
    ) -> Dict[str, Any]:
        """
        Create agent sessions with error handling.
        
        Args:
            agent_ids: List of agent IDs to create
            session_manager: Session manager instance
            auto_start: Whether to auto-start agents
            
        Returns:
            Dictionary with created agents and any errors
        """
        created = {}
        errors = []
        
        for agent_id in agent_ids:
            try:
                session = await session_manager.create_agent_session(
                    agent_id, 
                    auto_start=auto_start
                )
                created[agent_id] = session
                self._active_agents.add(agent_id)
                logger.info(f"Created agent session for {agent_id}")
            except Exception as e:
                logger.error(f"Failed to create agent {agent_id}: {e}")
                errors.append({
                    "agent": agent_id,
                    "error": str(e),
                    "type": "creation_error"
                })
        
        return {"created": created, "errors": errors}
    
    async def send_task_to_agent(
        self,
        from_agent: str,
        to_agent: str,
        subject: str,
        body: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send task to agent via mailbox.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            subject: Mail subject
            body: Mail body
            priority: Message priority
            metadata: Optional metadata
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            mail = Mail(
                from_agent=from_agent,
                to_agent=to_agent,
                subject=subject,
                body=body,
                metadata=metadata or {},
                priority=priority
            )
            self.mailbox.send_mail(mail)
            return True
        except Exception as e:
            logger.error(f"Failed to send mail from {from_agent} to {to_agent}: {e}")
            return False
    
    async def wait_with_monitoring(
        self,
        duration: float,
        monitor_interval: float = 0.5,
        monitor_callback: Optional[callable] = None
    ) -> None:
        """
        Wait for specified duration with optional monitoring.
        
        Args:
            duration: Total wait duration in seconds
            monitor_interval: Interval between monitor calls
            monitor_callback: Optional callback to run during wait
        """
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < duration:
            if monitor_callback:
                await monitor_callback()
            await asyncio.sleep(monitor_interval)
    
    async def cleanup_agents(
        self, 
        session_manager: AsyncAgentSessionManager
    ) -> None:
        """Clean up active agent sessions."""
        for agent_id in self._active_agents:
            try:
                if hasattr(session_manager, 'stop_agent_session'):
                    await session_manager.stop_agent_session(agent_id)
            except Exception as e:
                logger.warning(f"Failed to stop agent {agent_id}: {e}")
        
        self._active_agents.clear()
    
    @abstractmethod
    async def run(
        self, 
        config: Dict[str, Any], 
        session_manager: AsyncAgentSessionManager
    ) -> Dict[str, Any]:
        """
        Run the workflow.
        
        Must be implemented by subclasses.
        
        Args:
            config: Workflow configuration
            session_manager: Async agent session manager
            
        Returns:
            Dictionary with workflow results
        """
        pass
    
    async def resume(
        self, 
        session_manager: AsyncAgentSessionManager
    ) -> Dict[str, Any]:
        """
        Resume workflow from checkpoint.
        
        Can be overridden by subclasses for custom resume logic.
        
        Args:
            session_manager: New session manager with restored state
            
        Returns:
            Dictionary with workflow results
        """
        if not self._checkpoint_data:
            raise ValueError("No checkpoint data available for resume")
            
        # Default implementation - subclasses should override
        return {
            "status": "resumed",
            "message": "Resume not fully implemented for this workflow"
        }
    
    def save_checkpoint(self, data: Dict[str, Any]) -> None:
        """Save checkpoint data for potential resume."""
        self._checkpoint_data = {
            "timestamp": datetime.now(),
            "data": data
        }
    
    def get_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Get saved checkpoint data."""
        return self._checkpoint_data