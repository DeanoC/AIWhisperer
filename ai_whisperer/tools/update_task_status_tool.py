"""
Module: ai_whisperer/tools/update_task_status_tool.py
Purpose: AI tool implementation for update task status

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- UpdateTaskStatusTool: Tool for updating task execution status.

Usage:
    tool = UpdateTaskStatusTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- base_tool

Related:
- See UNTESTED_MODULES_REPORT.md

"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ai_whisperer.tools.base_tool import AITool
from ..extensions.agents.decomposed_task import TaskStatus

logger = logging.getLogger(__name__)


class UpdateTaskStatusTool(AITool):
    """Tool for updating task execution status."""
    
    def __init__(self):
        super().__init__()
        # In a real implementation, this would connect to a task storage system
        self._task_store = {}
    
    @property
    def name(self) -> str:
        return "update_task_status"
    
    @property
    def description(self) -> str:
        return "Update the status of a decomposed task after external agent execution"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task to update"
                },
                "status": {
                    "type": "string",
                    "description": "New status: 'pending', 'assigned', 'in_progress', 'completed', 'failed', 'blocked'",
                    "enum": ["pending", "assigned", "in_progress", "completed", "failed", "blocked"]
                },
                "assigned_agent": {
                    "type": "string",
                    "description": "The external agent assigned to this task"
                },
                "execution_result": {
                    "type": "string",
                    "description": "Result from external agent execution (JSON)"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes or comments about the status update"
                }
            },
            "required": ["task_id", "status"]
        }
    
    @property
    def tags(self) -> List[str]:
        return ["task_management", "status", "tracking"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
Use this tool to update the status of a decomposed task after external agent execution.
The tool tracks task history, execution results, and provides guidance on next steps.

Parameters:
- task_id: The ID of the task to update (required)
- status: New status - must be one of: 'pending', 'assigned', 'in_progress', 'completed', 'failed', 'blocked' (required)
- assigned_agent: The external agent assigned to this task (optional)
- execution_result: Result from external agent execution as JSON (optional)
- notes: Additional notes or comments about the status update (optional)

Returns:
A JSON object containing:
- task_id: The updated task ID
- updated_status: The new status
- previous_status: The previous status (if any)
- warnings: Any warnings about the status transition
- next_steps: Suggested next actions
"""
    
    def execute(self, arguments: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute the update task status tool."""
        task_id = arguments.get("task_id")
        status_str = arguments.get("status")
        assigned_agent = arguments.get("assigned_agent")
        execution_result = arguments.get("execution_result")
        notes = arguments.get("notes")
        
        if not task_id:
            return {
                "error": "task_id is required",
                "task_id": None,
                "updated": False
            }
        if not status_str:
            return {
                "error": "status is required",
                "task_id": task_id,
                "updated": False
            }
        
        try:
            # Validate status
            try:
                status = TaskStatus(status_str)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                return {
                    "error": f"Invalid status '{status_str}'. Valid statuses: {', '.join(valid_statuses)}",
                    "task_id": task_id,
                    "valid_statuses": valid_statuses,
                    "updated": False
                }
            
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
            
            response["updated"] = True
            return response
            
        except Exception as e:
            logger.error(f"Unexpected error in update_task_status: {e}", exc_info=True)
            return {
                "error": f"Unexpected error - {str(e)}",
                "task_id": task_id,
                "updated": False
            }
    
    def get_task_record(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task record by ID (for internal use)."""
        return self._task_store.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all task records (for internal use)."""
        return self._task_store.copy()