"""Tool for agents to wake other sleeping agents."""

import logging
from typing import Dict, Any
from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)


class AgentWakeTool(AITool):
    """Tool that allows an agent to wake another sleeping agent."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "agent_wake"
    
    @property    
    def description(self) -> str:
        """Return the tool description."""
        return "Wake a sleeping agent"
        
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "target_agent_id": {
                    "type": "string",
                    "description": "ID of the agent to wake up (e.g., 'd', 'p', 'e')",
                    "pattern": "^[a-z]$"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for waking the agent",
                    "default": "Manual wake by another agent"
                }
            },
            "required": ["target_agent_id"]
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
        return """Use the agent_wake tool to wake another sleeping agent.
        
Parameters:
- target_agent_id: The ID of the agent to wake up (single letter like 'd', 'p', 'e')
- reason: Optional reason for waking the agent

Example usage:
- Wake agent 'd': agent_wake(target_agent_id='d')
- Wake agent 'p' with reason: agent_wake(target_agent_id='p', reason='Urgent task needs attention')
"""
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the agent wake operation."""
        try:
            agent_context = kwargs.get('agent_context')
            if not agent_context:
                return {
                    "success": False,
                    "error": "No agent context available - this tool can only be used by async agents"
                }
                
            # Get current agent ID
            current_agent_id = getattr(agent_context, 'agent_id', 'unknown')
            
            # Get parameters
            target_agent_id = kwargs.get('target_agent_id')
            reason = kwargs.get('reason', f'Manual wake by agent {current_agent_id}')
            
            if not target_agent_id:
                return {
                    "success": False,
                    "error": "target_agent_id is required"
                }
            
            # Validate target agent ID format
            if not target_agent_id.isalpha() or len(target_agent_id) != 1:
                return {
                    "success": False,
                    "error": "target_agent_id must be a single letter (e.g., 'd', 'p', 'e')"
                }
            
            # Get the async session manager
            async_manager = self._get_async_session_manager(agent_context)
            if not async_manager:
                return {
                    "success": False,
                    "error": "No async session manager available - this tool requires async agent execution"
                }
            
            # Check if target agent exists
            if target_agent_id not in async_manager.sessions:
                return {
                    "success": False,
                    "error": f"Agent '{target_agent_id}' not found in current session"
                }
            
            # Wake the target agent using asyncio
            import asyncio
            try:
                # If we're already in an async context, use create_task
                loop = asyncio.get_running_loop()
                task = loop.create_task(async_manager.wake_agent(
                    agent_id=target_agent_id,
                    reason=reason
                ))
                # Note: The task will run in the background
            except RuntimeError:
                # No running loop
                return {
                    "success": False,
                    "error": "This tool can only be used within an async agent context"
                }
            
            logger.info(f"Agent {current_agent_id} woke agent {target_agent_id}: {reason}")
            
            return {
                "success": True,
                "woken_agent_id": target_agent_id,
                "reason": reason,
                "message": f"Successfully woke agent {target_agent_id}"
            }
            
        except Exception as e:
            logger.error(f"Error in agent_wake tool: {e}")
            return {
                "success": False,
                "error": f"Failed to wake agent: {str(e)}"
            }
    
    def _get_async_session_manager(self, agent_context):
        """Get the async session manager for the current agent context."""
        # The async session manager is injected into the agent context during creation
        if hasattr(agent_context, 'async_session_manager'):
            return agent_context.async_session_manager
            
        return None


# Register the tool
def get_tool():
    """Get an instance of the AgentWakeTool."""
    return AgentWakeTool()