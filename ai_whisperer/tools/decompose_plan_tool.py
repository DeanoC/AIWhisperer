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
        super().__init__(
            name="decompose_plan",
            description="Decompose an Agent P plan into executable tasks for external agents",
            parameters={
                "plan_content": {
                    "type": "string",
                    "description": "The JSON plan content to decompose",
                    "required": True
                },
                "max_depth": {
                    "type": "integer", 
                    "description": "Maximum depth for task decomposition (default: 3)",
                    "required": False
                }
            },
            tags=["planning", "task_management", "decomposition"]
        )
        self._decomposer = TaskDecomposer()
    
    def execute(self, **kwargs) -> str:
        """Execute the decompose plan tool."""
        plan_content = kwargs.get("plan_content")
        max_depth = kwargs.get("max_depth", 3)
        
        if not plan_content:
            return "Error: plan_content is required"
        
        try:
            # Parse the plan
            if isinstance(plan_content, str):
                plan_data = json.loads(plan_content)
            else:
                plan_data = plan_content
            
            # Decompose the plan
            tasks = self._decomposer.decompose_plan(plan_data, max_depth=max_depth)
            
            # Format the output
            result = {
                "total_tasks": len(tasks),
                "technology_stack": self._decomposer._detect_technology_stack(plan_data),
                "tasks": []
            }
            
            for task in tasks:
                task_info = {
                    "id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "parent": task.parent_task_id,
                    "dependencies": task.dependencies,
                    "complexity": task.estimated_complexity,
                    "tdd_phase": task.tdd_phase,
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
                        "plan_content": {
                            "type": "string",
                            "description": self.parameters["plan_content"]["description"]
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": self.parameters["max_depth"]["description"]
                        }
                    },
                    "required": ["plan_content"]
                }
            }
        }