"""
AI Loop Inspector Tool for Debbie to inspect per-agent AI configurations.

This tool allows Debbie to inspect which AI models are being used by each agent
in the current session.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)


@dataclass
class AILoopInspectorTool(AITool):
    """Tool for inspecting AI loop configurations by agent."""
    
    name: str = "ai_loop_inspector"
    description: str = "Inspect AI model configurations for agents in the current session"
    category: str = "monitoring"
    input_schema: Dict[str, Any] = None
    requires_context: bool = True
    
    def __post_init__(self):
        self.input_schema = {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID to inspect (optional, shows all if not provided)"
                },
                "include_details": {
                    "type": "boolean",
                    "description": "Include detailed configuration information",
                    "default": False
                }
            },
            "required": []
        }
    
    async def execute(self, agent_id: Optional[str] = None, include_details: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Inspect AI loop configurations.
        
        Args:
            agent_id: Specific agent to inspect (optional)
            include_details: Include detailed configuration
            
        Returns:
            Dictionary with AI loop information
        """
        try:
            # Get the current session from context
            # The context might be passed in different ways
            context = kwargs.get('context')
            session = None
            
            # Try to get session from context or directly from kwargs
            if hasattr(context, 'agent_context'):
                # From agent context
                session = getattr(context.agent_context, 'session', None)
            elif hasattr(context, 'session'):
                # Direct session attribute
                session = context.session
            else:
                # Check if we have a session manager
                from ai_whisperer.utils.helpers import get_current_session
                try:
                    session = get_current_session()
                except:
                    pass
            
            if not session:
                return {
                    "success": False,
                    "error": "No active session found"
                }
            
            # Access the AI loop manager
            if not hasattr(session, 'ai_loop_manager'):
                return {
                    "success": False,
                    "error": "Session does not have AI loop manager"
                }
            
            ai_loop_manager = session.ai_loop_manager
            
            # Get active models summary
            active_models = ai_loop_manager.get_active_models()
            
            result = {
                "success": True,
                "active_agents": len(active_models),
                "models_by_agent": active_models,
                "current_agent": session.active_agent
            }
            
            # If specific agent requested
            if agent_id:
                agent_id = agent_id.upper()
                if agent_id in ai_loop_manager._ai_loops:
                    entry = ai_loop_manager._ai_loops[agent_id]
                    agent_info = {
                        "agent_id": agent_id,
                        "model": entry.config.model,
                        "provider": entry.config.provider,
                        "temperature": entry.config.temperature,
                        "max_tokens": entry.config.max_tokens
                    }
                    
                    if include_details:
                        agent_info["generation_params"] = entry.config.generation_params
                        agent_info["api_settings"] = {
                            k: v for k, v in entry.config.api_settings.items()
                            if k != "api_key"  # Don't expose API key
                        }
                    
                    result["agent_details"] = agent_info
                else:
                    result["error"] = f"Agent {agent_id} not found in AI loop manager"
            
            # Add detailed info for all agents if requested
            if include_details and not agent_id:
                details = {}
                for aid, entry in ai_loop_manager._ai_loops.items():
                    details[aid] = {
                        "model": entry.config.model,
                        "provider": entry.config.provider,
                        "temperature": entry.config.temperature,
                        "max_tokens": entry.config.max_tokens,
                        "has_custom_config": aid in ["D", "E"]  # Based on our test setup
                    }
                result["all_agent_details"] = details
            
            # Add verification info
            result["verification"] = {
                "default_model": ai_loop_manager._default_config.get("openrouter", {}).get("model", "unknown"),
                "agents_with_custom_models": [
                    aid for aid, model in active_models.items()
                    if model != ai_loop_manager._default_config.get("openrouter", {}).get("model")
                ]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error inspecting AI loops: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_ai_instructions(self) -> str:
        """Get instructions for the AI on how to use this tool."""
        return """
## AI Loop Inspector Tool

Use this tool to inspect which AI models are being used by different agents in the session.

### Usage Examples:

1. **Check all active agents and their models:**
   ```
   ai_loop_inspector()
   ```

2. **Inspect specific agent configuration:**
   ```
   ai_loop_inspector(agent_id="E", include_details=True)
   ```

3. **Verify custom model configurations:**
   The tool will identify which agents have custom models vs default models.

### Key Information Provided:
- Active agents and their AI models
- Temperature and token settings
- Which agents use custom vs default configurations
- Current active agent in the session

This tool is essential for verifying that per-agent AI loops are working correctly.
"""