"""
Module: ai_whisperer/tools/format_for_external_agent_tool.py
Purpose: AI tool implementation for format for external agent

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- FormatForExternalAgentTool: Tool for formatting tasks for specific external agents.

Usage:
    tool = FormatForExternalAgentTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- base_tool
- agents.external_adapters

Related:
- See UNTESTED_MODULES_REPORT.md

"""

from typing import Any, Dict, List

import json
import logging
from ai_whisperer.tools.base_tool import AITool
from ..extensions.agents.decomposed_task import DecomposedTask
from ..extensions.agents.external_adapters import AdapterRegistry
from ..extensions.agents.agent_e_exceptions import ExternalAgentError

logger = logging.getLogger(__name__)

class FormatForExternalAgentTool(AITool):
    """Tool for formatting tasks for specific external agents."""
    
    def __init__(self):
        super().__init__()
        self._registry = AdapterRegistry()
    
    @property
    def name(self) -> str:
        return "format_for_external_agent"
    
    @property
    def description(self) -> str:
        return "Format a task for a specific external AI agent (Claude Code, RooCode, or GitHub Copilot)"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "JSON representation of the task to format"
                },
                "agent": {
                    "type": "string",
                    "description": "Target agent: 'claude_code', 'roocode', or 'github_copilot'",
                    "enum": ["claude_code", "roocode", "github_copilot"]
                },
                "include_instructions": {
                    "type": "boolean",
                    "description": "Include human-readable execution instructions (default: true)"
                }
            },
            "required": ["task", "agent"]
        }
    
    @property
    def tags(self) -> List[str]:
        return ["external_agents", "formatting", "integration"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
Use this tool to format a decomposed task for a specific external AI agent.
The tool will optimize the task presentation for the chosen agent's strengths.

Parameters:
- task: JSON representation of the task to format (required)
- agent: Target agent - must be 'claude_code', 'roocode', or 'github_copilot' (required)
- include_instructions: Include human-readable execution instructions (optional, default: true)

Returns:
A JSON object containing:
- agent: The target agent name
- environment_valid: Whether the agent is available
- validation_message: Environment validation details
- formatted_task: Agent-specific task formatting
- execution_instructions: Human-readable instructions (if requested)
- alternatives: Alternative agents if the target is unavailable
"""
    
    def execute(self, arguments: Dict[str, Any], **kwargs) -> str:
        """Execute the format for external agent tool."""
        task_json = arguments.get("task")
        agent_name = arguments.get("agent")
        include_instructions = arguments.get("include_instructions", True)
        
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
                parent_task_name=task_data.get("parent_task_name", ""),
                context=task_data.get("context", {}),
                acceptance_criteria=task_data.get("acceptance_criteria", []),
                estimated_complexity=task_data.get("complexity", task_data.get("estimated_complexity", "moderate")),
                status=task_data.get("status", "pending"),
                external_agent_prompts=task_data.get("external_agent_prompts", {})
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
