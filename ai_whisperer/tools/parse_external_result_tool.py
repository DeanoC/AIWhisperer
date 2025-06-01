"""
Tool for parsing results from external agent execution.
"""
import json
import logging
from typing import Dict, Any, List

from .base_tool import AITool
from ..agents.external_adapters import AdapterRegistry

logger = logging.getLogger(__name__)


class ParseExternalResultTool(AITool):
    """Tool for parsing execution results from external agents."""
    
    def __init__(self):
        super().__init__()
        self._registry = AdapterRegistry()
    
    @property
    def name(self) -> str:
        return "parse_external_result"
    
    @property
    def description(self) -> str:
        return "Parse and interpret results from external AI agent execution"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "The external agent that produced the result",
                    "enum": ["claude_code", "roocode", "github_copilot"]
                },
                "output": {
                    "type": "string",
                    "description": "The standard output from the agent execution"
                },
                "error": {
                    "type": "string",
                    "description": "Any error output from the agent execution"
                },
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task that was executed"
                }
            },
            "required": ["agent", "output"]
        }
    
    @property
    def tags(self) -> List[str]:
        return ["external_agents", "parsing", "results"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
Use this tool to parse and interpret results from external AI agent execution.
The tool extracts success status, files changed, and provides recommendations.

Parameters:
- agent: The external agent that produced the result (required)
- output: The standard output from the agent execution (required)
- error: Any error output from the agent execution (optional)
- task_id: The ID of the task that was executed (optional)

Returns:
A JSON object containing:
- agent: The agent name
- success: Whether execution succeeded
- files_changed: List of modified files
- summary: Brief summary of the result
- recommendations: Suggested next actions
- agent_insights: Agent-specific observations
"""
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the parse external result tool."""
        agent_name = arguments.get("agent")
        output = arguments.get("output", "")
        error = arguments.get("error", "")
        task_id = arguments.get("task_id")
        
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