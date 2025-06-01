"""
Tool for decomposing Agent P plans into executable tasks.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from .base_tool import AITool
from ..agents.task_decomposer import TaskDecomposer
from ..agents.decomposed_task import DecomposedTask
from ..agents.agent_e_exceptions import (
    InvalidPlanError,
    TaskDecompositionError
)

logger = logging.getLogger(__name__)


class DecomposePlanTool(AITool):
    """Tool for decomposing plans into executable tasks."""
    
    def __init__(self):
        super().__init__()
        self._decomposer = TaskDecomposer()
    
    @property
    def name(self) -> str:
        return "decompose_plan"
    
    @property
    def description(self) -> str:
        return "Decompose an Agent P plan into executable tasks for external agents"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_content": {
                    "type": "string",
                    "description": "The JSON plan content to decompose"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for task decomposition (default: 3)"
                }
            },
            "required": ["plan_content"]
        }
    
    @property
    def tags(self) -> List[str]:
        return ["planning", "task_management", "decomposition"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
Use this tool to decompose an Agent P plan into executable tasks for external agents.
The tool will analyze the plan structure, detect the technology stack, and create
tasks with proper dependencies and complexity estimates.

Parameters:
- plan_content: The JSON plan content to decompose (required)
- max_depth: Maximum depth for task decomposition (optional, default: 3)

Returns:
A JSON object containing:
- total_tasks: Number of tasks created
- technology_stack: Detected languages, frameworks, and tools
- tasks: Array of decomposed tasks with dependencies and metadata
"""
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the decompose plan tool."""
        plan_content = arguments.get("plan_content")
        max_depth = arguments.get("max_depth", 3)
        
        if not plan_content:
            return "Error: plan_content is required"
        
        try:
            # Parse the plan
            if isinstance(plan_content, str):
                plan_data = json.loads(plan_content)
            else:
                plan_data = plan_content
            
            # Decompose the plan
            tasks = self._decomposer.decompose_plan(plan_data)
            
            # Format the output
            result = {
                "total_tasks": len(tasks),
                "technology_stack": {},  # Technology stack is detected per task
                "tasks": []
            }
            
            for task in tasks:
                task_info = {
                    "id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "parent_task_name": task.parent_task_name,
                    "dependencies": task.get_dependencies(),
                    "complexity": task.estimated_complexity,
                    "status": task.status,
                    "acceptance_criteria": task.acceptance_criteria,
                    "context": task.context
                }
                result["tasks"].append(task_info)
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            return f"Error: Invalid JSON format - {str(e)}"
        except InvalidPlanError as e:
            logger.error(f"Invalid plan: {e}")
            return f"Error: Invalid plan - {str(e)}"
        except TaskDecompositionError as e:
            logger.error(f"Decomposition failed: {e}")
            return f"Error: Failed to decompose plan - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in decompose_plan: {e}", exc_info=True)
            return f"Error: Unexpected error - {str(e)}"