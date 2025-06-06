"""Tool for agents to put themselves to sleep."""

import logging
from typing import Dict, Any, Optional, Set
from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)


class AgentSleepTool(AITool):
    """Tool that allows an agent to put itself to sleep for a specified duration."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "agent_sleep"
    
    @property    
    def description(self) -> str:
        """Return the tool description."""
        return "Put the current agent to sleep for a specified duration or until woken by events"
        
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "duration_seconds": {
                    "type": "integer",
                    "description": "How long to sleep in seconds (optional - if not provided, sleep indefinitely until woken)",
                    "minimum": 1,
                    "maximum": 3600  # Max 1 hour
                },
                "wake_events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of events that should wake the agent (e.g., ['mail_received', 'high_priority_mail'])",
                    "default": ["mail_received"]
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for sleeping (for logging/debugging)",
                    "default": "Agent-requested sleep"
                }
            },
            "required": []
        }
    
    @property
    def category(self) -> str:
        """Return the tool category."""
        return "Agent Management"
    
    @property
    def tags(self) -> list:
        """Return the tool tags."""
        return ["async_agents", "sleep_wake", "agent_management"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for the AI on how to use this tool."""
        return """Use the agent_sleep tool to put yourself to sleep for a specified duration.
        
Parameters:
- duration_seconds: How long to sleep (1-3600 seconds). Optional - if not provided, sleep indefinitely.
- wake_events: List of events that should wake you up. Defaults to ['mail_received'].
- reason: Optional reason for sleeping (for logging).

Wake events:
- 'mail_received': Wake up when any mail arrives
- 'high_priority_mail': Wake up only for high priority mail
- 'manual_wake': Wake up when another agent uses agent_wake
- 'system_event': Wake up for system events

Example usage:
- Sleep for 5 seconds: agent_sleep(duration_seconds=5)
- Sleep until mail: agent_sleep(wake_events=['mail_received'])
- Sleep for 10 seconds or until high priority mail: agent_sleep(duration_seconds=10, wake_events=['high_priority_mail'])
"""
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the agent sleep operation."""
        try:
            agent_context = kwargs.get('agent_context')
            if not agent_context:
                return {
                    "success": False,
                    "error": "No agent context available - this tool can only be used by async agents"
                }
                
            # Get agent ID from context
            agent_id = getattr(agent_context, 'agent_id', None)
            if not agent_id:
                return {
                    "success": False,
                    "error": "Could not determine agent ID from context"
                }
            
            # Get parameters
            duration_seconds = kwargs.get('duration_seconds')
            wake_events = kwargs.get('wake_events', ['mail_received'])
            reason = kwargs.get('reason', 'Agent-requested sleep')
            
            # Validate wake_events
            valid_events = {'mail_received', 'high_priority_mail', 'system_event', 'manual_wake'}
            if isinstance(wake_events, list):
                wake_events_set = set(wake_events)
                invalid_events = wake_events_set - valid_events
                if invalid_events:
                    return {
                        "success": False,
                        "error": f"Invalid wake events: {invalid_events}. Valid events: {valid_events}"
                    }
            else:
                wake_events_set = {'mail_received'}  # Default
                
            # Get the async session manager 
            async_manager = self._get_async_session_manager(agent_context)
            if not async_manager:
                return {
                    "success": False,
                    "error": "No async session manager available - this tool requires async agent execution"
                }
            
            # Put the agent to sleep using asyncio.run_coroutine_threadsafe
            import asyncio
            try:
                # If we're already in an async context, use create_task
                loop = asyncio.get_running_loop()
                task = loop.create_task(async_manager.sleep_agent(
                    agent_id=agent_id,
                    duration_seconds=duration_seconds,
                    wake_events=wake_events_set
                ))
                # Note: The task will run in the background, we don't await it here
                # since this is a synchronous method
            except RuntimeError:
                # No running loop, tool is being called outside async context
                return {
                    "success": False,
                    "error": "This tool can only be used within an async agent context"
                }
            
            logger.info(f"Agent {agent_id} put itself to sleep for {duration_seconds}s, wake events: {wake_events_set}")
            
            sleep_msg = f"Sleeping for {duration_seconds} seconds" if duration_seconds else "Sleeping indefinitely"
            
            return {
                "success": True,
                "agent_id": agent_id,
                "duration_seconds": duration_seconds,
                "wake_events": list(wake_events_set),
                "reason": reason,
                "message": f"{sleep_msg}. Wake events: {', '.join(wake_events_set)}"
            }
            
        except Exception as e:
            logger.error(f"Error in agent_sleep tool: {e}")
            return {
                "success": False,
                "error": f"Failed to put agent to sleep: {str(e)}"
            }
    
    def _get_async_session_manager(self, agent_context):
        """Get the async session manager for the current agent context."""
        # The async session manager is injected into the agent context during creation
        if hasattr(agent_context, 'async_session_manager'):
            return agent_context.async_session_manager
            
        return None


# Register the tool
def get_tool():
    """Get an instance of the AgentSleepTool."""
    return AgentSleepTool()