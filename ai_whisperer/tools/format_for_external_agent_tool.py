"""
Tool for formatting tasks for external AI coding assistants.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from .base_tool import AITool
from ..agents.decomposed_task import DecomposedTask
from ..agents.external_adapters import AdapterRegistry
from ..agents.agent_e_exceptions import ExternalAgentError

logger = logging.getLogger(__name__)


class FormatForExternalAgentTool(AITool):
    """Tool for formatting tasks for specific external agents."""
    
    def __init__(self):
        super().__init__(
            name="format_for_external_agent",
            description="Format a task for a specific external AI agent (Claude Code, RooCode, or GitHub Copilot)",
            parameters={
                "task": {
                    "type": "string",
                    "description": "JSON representation of the task to format",
                    "required": True
                },
                "agent": {
                    "type": "string",
                    "description": "Target agent: 'claude_code', 'roocode', or 'github_copilot'",
                    "required": True
                },
                "include_instructions": {
                    "type": "boolean",
                    "description": "Include human-readable execution instructions (default: true)",
                    "required": False
                }
            },
            tags=["external_agents", "formatting", "integration"]
        )
        self._registry = AdapterRegistry()
    
    def execute(self, **kwargs) -> str:
        """Execute the format for external agent tool."""
        task_json = kwargs.get("task")
        agent_name = kwargs.get("agent")
        include_instructions = kwargs.get("include_instructions", True)
        
        if not task_json:
            return "Error: task parameter is required"
        if not agent_name:
            return "Error: agent parameter is required"
        
        try:
            # Parse the task
            if isinstance(task_json, str):
                task_data = json.loads(task_json)
            else:
                task_data = task_json
            
            # Convert to DecomposedTask object
            task = DecomposedTask(
                task_id=task_data.get("id", task_data.get("task_id", "unknown")),
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                parent_task_id=task_data.get("parent", task_data.get("parent_task_id")),
                parent_task_name=task_data.get("parent_task_name", ""),
                dependencies=task_data.get("dependencies", []),
                estimated_complexity=task_data.get("complexity", task_data.get("estimated_complexity", "moderate")),
                tdd_phase=task_data.get("tdd_phase", "RED"),
                acceptance_criteria=task_data.get("acceptance_criteria", []),
                external_agent_prompts=task_data.get("external_agent_prompts", {}),
                context=task_data.get("context", {})
            )
            
            # Get the adapter
            adapter = self._registry.get_adapter(agent_name.lower())
            if not adapter:
                available = self._registry.list_adapters()
                return f"Error: Unknown agent '{agent_name}'. Available agents: {', '.join(available)}"
            
            # Validate the environment
            is_valid, validation_msg = adapter.validate_environment()
            
            # Format the task
            formatted = adapter.format_task(task)
            
            # Build the result
            result = {
                "agent": agent_name,
                "environment_valid": is_valid,
                "validation_message": validation_msg,
                "formatted_task": formatted
            }
            
            # Add instructions if requested
            if include_instructions:
                instructions = adapter.get_execution_instructions(task)
                result["execution_instructions"] = instructions
            
            # Add recommendations if environment is not valid
            if not is_valid:
                # Get alternative recommendations
                recommendations = self._registry.recommend_adapters(task)
                alternative_agents = []
                for alt_agent, score in recommendations:
                    if alt_agent != agent_name and score > 0.5:
                        alt_adapter = self._registry.get_adapter(alt_agent)
                        alt_valid, _ = alt_adapter.validate_environment()
                        if alt_valid:
                            alternative_agents.append({
                                "agent": alt_agent,
                                "score": score
                            })
                
                if alternative_agents:
                    result["alternatives"] = alternative_agents
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task JSON: {e}")
            return f"Error: Invalid JSON format - {str(e)}"
        except ExternalAgentError as e:
            logger.error(f"External agent error: {e}")
            return f"Error: External agent error - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in format_for_external_agent: {e}", exc_info=True)
            return f"Error: Unexpected error - {str(e)}"
    
    def get_openrouter_tool_definition(self) -> Dict[str, Any]:
        """Get the OpenRouter tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": self.parameters["task"]["description"]
                        },
                        "agent": {
                            "type": "string",
                            "description": self.parameters["agent"]["description"],
                            "enum": ["claude_code", "roocode", "github_copilot"]
                        },
                        "include_instructions": {
                            "type": "boolean",
                            "description": self.parameters["include_instructions"]["description"]
                        }
                    },
                    "required": ["task", "agent"]
                }
            }
        }