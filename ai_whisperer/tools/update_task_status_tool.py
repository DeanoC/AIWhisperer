"""
Tool for updating the status of decomposed tasks.
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_tool import AITool
from ..agents.decomposed_task import TaskStatus

logger = logging.getLogger(__name__)


class UpdateTaskStatusTool(AITool):
    """Tool for updating task execution status."""
    
    def __init__(self):
        super().__init__(
            name="update_task_status",
            description="Update the status of a decomposed task after external agent execution",
            parameters={
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task to update",
                    "required": True
                },
                "status": {
                    "type": "string",
                    "description": "New status: 'pending', 'assigned', 'in_progress', 'completed', 'failed', 'blocked'",
                    "required": True
                },
                "assigned_agent": {
                    "type": "string",
                    "description": "The external agent assigned to this task",
                    "required": False
                },
                "execution_result": {
                    "type": "string",
                    "description": "Result from external agent execution (JSON)",
                    "required": False
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes or comments about the status update",
                    "required": False
                }
            },
            tags=["task_management", "status", "tracking"]
        )
        # In a real implementation, this would connect to a task storage system
        self._task_store = {}
    
    def execute(self, **kwargs) -> str:
        """Execute the update task status tool."""
        task_id = kwargs.get("task_id")
        status_str = kwargs.get("status")
        assigned_agent = kwargs.get("assigned_agent")
        execution_result = kwargs.get("execution_result")
        notes = kwargs.get("notes")
        
        if not task_id:
            return "Error: task_id is required"
        if not status_str:
            return "Error: status is required"
        
        try:
            # Validate status
            try:
                status = TaskStatus(status_str.upper())
            except ValueError:
                valid_statuses = [s.value.lower() for s in TaskStatus]
                return f"Error: Invalid status '{status_str}'. Valid statuses: {', '.join(valid_statuses)}"
            
            # Get or create task record
            if task_id not in self._task_store:
                self._task_store[task_id] = {
                    "id": task_id,
                    "status_history": [],
                    "current_status": None,
                    "assigned_agent": None,
                    "execution_results": []
                }
            
            task_record = self._task_store[task_id]
            
            # Record the status change
            status_update = {
                "status": status.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "notes": notes
            }
            
            # Update assigned agent if provided
            if assigned_agent:
                task_record["assigned_agent"] = assigned_agent
                status_update["assigned_agent"] = assigned_agent
            
            # Add execution result if provided
            if execution_result:
                try:
                    # Parse execution result if it's JSON
                    if isinstance(execution_result, str):
                        result_data = json.loads(execution_result)
                    else:
                        result_data = execution_result
                    
                    task_record["execution_results"].append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent": assigned_agent or task_record.get("assigned_agent", "unknown"),
                        "result": result_data
                    })
                    status_update["has_execution_result"] = True
                except json.JSONDecodeError:
                    # Store as plain text if not JSON
                    task_record["execution_results"].append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent": assigned_agent or task_record.get("assigned_agent", "unknown"),
                        "result": execution_result
                    })
                    status_update["has_execution_result"] = True
            
            # Update current status and history
            task_record["current_status"] = status.value
            task_record["status_history"].append(status_update)
            
            # Build response
            response = {
                "task_id": task_id,
                "updated_status": status.value,
                "previous_status": task_record["status_history"][-2]["status"] if len(task_record["status_history"]) > 1 else None,
                "assigned_agent": task_record["assigned_agent"],
                "total_updates": len(task_record["status_history"]),
                "execution_results_count": len(task_record["execution_results"])
            }
            
            # Add transition warnings
            warnings = []
            if status == TaskStatus.IN_PROGRESS and not task_record["assigned_agent"]:
                warnings.append("Task marked as IN_PROGRESS but no agent assigned")
            if status == TaskStatus.COMPLETED and len(task_record["execution_results"]) == 0:
                warnings.append("Task marked as COMPLETED but no execution results recorded")
            if status == TaskStatus.BLOCKED:
                warnings.append("Task is BLOCKED - ensure dependencies are resolved")
            
            if warnings:
                response["warnings"] = warnings
            
            # Add next steps suggestions
            next_steps = []
            if status == TaskStatus.PENDING:
                next_steps.append("Assign an external agent using format_for_external_agent")
            elif status == TaskStatus.ASSIGNED:
                next_steps.append("Execute with the assigned external agent")
            elif status == TaskStatus.FAILED:
                next_steps.append("Review failure reason and consider reassigning")
            elif status == TaskStatus.BLOCKED:
                next_steps.append("Check and resolve blocking dependencies")
            
            if next_steps:
                response["next_steps"] = next_steps
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(f"Unexpected error in update_task_status: {e}", exc_info=True)
            return f"Error: Unexpected error - {str(e)}"
    
    def get_task_record(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task record by ID (for internal use)."""
        return self._task_store.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all task records (for internal use)."""
        return self._task_store.copy()
    
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
                        "task_id": {
                            "type": "string",
                            "description": self.parameters["task_id"]["description"]
                        },
                        "status": {
                            "type": "string",
                            "description": self.parameters["status"]["description"],
                            "enum": ["pending", "assigned", "in_progress", "completed", "failed", "blocked"]
                        },
                        "assigned_agent": {
                            "type": "string",
                            "description": self.parameters["assigned_agent"]["description"]
                        },
                        "execution_result": {
                            "type": "string",
                            "description": self.parameters["execution_result"]["description"]
                        },
                        "notes": {
                            "type": "string",
                            "description": self.parameters["notes"]["description"]
                        }
                    },
                    "required": ["task_id", "status"]
                }
            }
        }