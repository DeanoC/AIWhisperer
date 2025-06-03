"""
Switch Agent Tool - Allows agents to hand off conversations to other agents.

This is a transitional tool that bridges the current single-active-agent model
with the future multi-agent communication model.
"""

import logging
from typing import Dict, Any, Optional

from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)


class SwitchAgentTool(AITool):
    """Tool for switching the active agent in a session."""
    
    def __init__(self):
        """Initialize the switch agent tool."""
        super().__init__()
        self._requires_context = True
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "switch_agent"
    
    @property
    def description(self) -> str:
        """Tool description."""
        return "Switch the active agent to handle the current conversation"
    
    @property
    def category(self) -> str:
        """Tool category."""
        return "agent_switching"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "The ID of the agent to switch to (e.g., 'p' for Patricia, 't' for Tessa)",
                    "enum": ["p", "a", "t", "d", "e"]
                },
                "reason": {
                    "type": "string",
                    "description": "Brief explanation of why switching to this agent"
                },
                "context_summary": {
                    "type": "string",
                    "description": "Summary of the conversation context for the new agent"
                }
            },
            "required": ["agent_id", "reason"]
        }
    
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for the AI on how to use this tool."""
        return self.get_ai_instructions()
    
    def _get_session_from_context(self, context: Any) -> Optional[Any]:
        """
        Extract session from various context formats.
        
        Args:
            context: The context object that may contain the session
            
        Returns:
            The session object if found, None otherwise
        """
        # Import here to avoid circular imports
        from interactive_server.stateless_session_manager import StatelessInteractiveSession
        
        # Method 1: Direct access if context is the session
        if isinstance(context, StatelessInteractiveSession):
            return context
            
        # Method 2: Session as attribute
        if hasattr(context, 'session'):
            return context.session
            
        # Method 3: Session in dict
        if isinstance(context, dict) and 'session' in context:
            return context['session']
            
        # Method 4: Through ai_context (how tools are called)
        if hasattr(context, 'ai_context'):
            ai_context = context.ai_context
            if hasattr(ai_context, 'session'):
                return ai_context.session
                
        return None
    
    async def execute(self, agent_id: str, reason: str, context_summary: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Switch to a different agent.
        
        Args:
            agent_id: ID of the agent to switch to
            reason: Why we're switching
            context_summary: Optional context for the new agent
            
        Returns:
            Result of the switch operation
        """
        try:
            # Get the context object which should contain the session
            context = kwargs.get('context', {})
            
            # Extract session using helper method
            session = self._get_session_from_context(context)
            
            if not session:
                logger.error(f"Could not find session in context. Context type: {type(context)}, keys: {context.keys() if isinstance(context, dict) else 'N/A'}")
                return {
                    "success": False,
                    "error": "No active session found for agent switching. This tool requires an active interactive session."
                }
            
            # Normalize agent ID to lowercase
            agent_id = agent_id.lower()
            
            # Get agent info from registry
            agent_registry = getattr(session, 'agent_registry', None)
            if agent_registry:
                agent_info = agent_registry.get_agent(agent_id.upper())
                if not agent_info:
                    return {
                        "success": False,
                        "error": f"Unknown agent ID: {agent_id}"
                    }
                agent_name = agent_info.name
            else:
                # Fallback agent names
                agent_names = {
                    'p': 'Patricia the Planner',
                    'a': 'Alice the Assistant',
                    't': 'Tessa the Tester',
                    'd': 'Debbie the Debugger',
                    'e': 'Eamonn the Executioner'
                }
                agent_name = agent_names.get(agent_id, f"Agent {agent_id.upper()}")
            
            # Perform the switch
            try:
                await session.switch_agent(agent_id)
                
                result = {
                    "success": True,
                    "switched_to": agent_id,
                    "agent_name": agent_name,
                    "reason": reason,
                    "message": f"Successfully switched to {agent_name}"
                }
                
                # Add handoff message if context provided
                if context_summary:
                    result["handoff_message"] = (
                        f"You've been handed this conversation from another agent. "
                        f"Context: {context_summary}"
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to switch agent: {e}")
                return {
                    "success": False,
                    "error": f"Failed to switch to {agent_name}: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Error in switch_agent tool: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_ai_instructions(self) -> str:
        """Get instructions for the AI on how to use this tool."""
        return """
## Switch Agent Tool

Use this tool to hand off the conversation to a more specialized agent.

### Available Agents:
- **p** (Patricia): RFC creation and planning specialist
- **a** (Alice): General assistant (that's you!)
- **t** (Tessa): Testing specialist
- **d** (Debbie): Debugging and troubleshooting expert
- **e** (Eamonn): Task decomposition specialist

### Usage Examples:

1. **Switching to Patricia for RFC creation:**
   ```
   switch_agent(
       agent_id="p",
       reason="User wants to create RFCs",
       context_summary="User needs to create RFCs for terminal and file browser features"
   )
   ```

2. **Switching to Debbie for debugging:**
   ```
   switch_agent(
       agent_id="d",
       reason="User experiencing technical issues",
       context_summary="System health check requested"
   )
   ```

### Important Notes:
- Always provide a clear reason for the switch
- Include a context summary to help the new agent understand the situation
- The new agent will take over the conversation completely
- You won't be active again until someone switches back to you
"""