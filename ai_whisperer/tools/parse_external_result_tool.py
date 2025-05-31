"""
Tool for parsing results from external agent execution.
"""
import json
import logging
from typing import Dict, Any

from .base_tool import AITool
from ..agents.external_adapters import AdapterRegistry

logger = logging.getLogger(__name__)


class ParseExternalResultTool(AITool):
    """Tool for parsing execution results from external agents."""
    
    def __init__(self):
        super().__init__(
            name="parse_external_result",
            description="Parse and interpret results from external AI agent execution",
            parameters={
                "agent": {
                    "type": "string",
                    "description": "The external agent that produced the result",
                    "required": True
                },
                "output": {
                    "type": "string",
                    "description": "The standard output from the agent execution",
                    "required": True
                },
                "error": {
                    "type": "string",
                    "description": "Any error output from the agent execution",
                    "required": False
                },
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task that was executed",
                    "required": False
                }
            },
            tags=["external_agents", "parsing", "results"]
        )
        self._registry = AdapterRegistry()
    
    def execute(self, **kwargs) -> str:
        """Execute the parse external result tool."""
        agent_name = kwargs.get("agent")
        output = kwargs.get("output", "")
        error = kwargs.get("error", "")
        task_id = kwargs.get("task_id")
        
        if not agent_name:
            return "Error: agent parameter is required"
        if not output and not error:
            return "Error: either output or error must be provided"
        
        try:
            # Get the adapter
            adapter = self._registry.get_adapter(agent_name.lower())
            if not adapter:
                available = self._registry.list_adapters()
                return f"Error: Unknown agent '{agent_name}'. Available agents: {', '.join(available)}"
            
            # Parse the result
            result = adapter.parse_result(output, error)
            
            # Build parsed response
            parsed = {
                "agent": agent_name,
                "success": result.success,
                "files_changed": result.files_changed,
                "files_changed_count": len(result.files_changed),
                "has_error": bool(result.error),
                "task_id": task_id
            }
            
            # Add summary
            if result.success:
                if result.files_changed:
                    parsed["summary"] = f"Task completed successfully. Modified {len(result.files_changed)} file(s)."
                else:
                    parsed["summary"] = "Task completed successfully with no file changes."
            else:
                parsed["summary"] = f"Task failed: {result.error or 'Unknown error'}"
            
            # Add output preview (first 500 chars)
            if result.output:
                preview_length = 500
                if len(result.output) > preview_length:
                    parsed["output_preview"] = result.output[:preview_length] + "..."
                    parsed["output_truncated"] = True
                else:
                    parsed["output_preview"] = result.output
                    parsed["output_truncated"] = False
            
            # Add error details if present
            if result.error:
                parsed["error_details"] = result.error
            
            # Add metadata if available
            if result.metadata:
                parsed["metadata"] = result.metadata
            
            # Add recommendations based on result
            recommendations = []
            
            if result.success:
                recommendations.append("Update task status to 'completed' using update_task_status")
                if result.files_changed:
                    recommendations.append("Review changed files before proceeding")
                    recommendations.append("Run tests to verify changes")
            else:
                recommendations.append("Update task status to 'failed' using update_task_status")
                recommendations.append("Review error details to understand failure")
                recommendations.append("Consider reformatting task or trying different agent")
            
            parsed["recommendations"] = recommendations
            
            # Agent-specific insights
            agent_insights = []
            
            if agent_name.lower() == "claude_code" and result.metadata:
                if result.metadata.get("iterations"):
                    agent_insights.append(f"Claude performed {result.metadata['iterations']} iterations")
            
            elif agent_name.lower() == "github_copilot" and result.metadata:
                if result.metadata.get("iterations"):
                    agent_insights.append(f"Copilot agent mode used {result.metadata['iterations']} iterations")
                if result.metadata.get("agent_mode"):
                    agent_insights.append("Executed in agent mode with autonomous refinement")
            
            elif agent_name.lower() == "roocode":
                if len(result.files_changed) > 3:
                    agent_insights.append("RooCode handled multi-file edit successfully")
            
            if agent_insights:
                parsed["agent_insights"] = agent_insights
            
            return json.dumps(parsed, indent=2)
            
        except Exception as e:
            logger.error(f"Unexpected error in parse_external_result: {e}", exc_info=True)
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
                        "agent": {
                            "type": "string",
                            "description": self.parameters["agent"]["description"],
                            "enum": ["claude_code", "roocode", "github_copilot"]
                        },
                        "output": {
                            "type": "string",
                            "description": self.parameters["output"]["description"]
                        },
                        "error": {
                            "type": "string",
                            "description": self.parameters["error"]["description"]
                        },
                        "task_id": {
                            "type": "string",
                            "description": self.parameters["task_id"]["description"]
                        }
                    },
                    "required": ["agent", "output"]
                }
            }
        }