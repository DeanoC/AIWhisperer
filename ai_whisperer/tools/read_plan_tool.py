"""
Read Plan Tool - Reads and displays execution plan details
"""
import os
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class ReadPlanTool(AITool):
    """Tool for reading execution plan details."""
    
    @property
    def name(self) -> str:
        return "read_plan"
    
    @property
    def description(self) -> str:
        return "Read and display details of an execution plan."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {
                    "type": "string",
                    "description": "Name of the plan directory (e.g., 'add-caching-plan-2025-05-31')"
                },
                "include_tasks": {
                    "type": "boolean",
                    "description": "Include detailed task list",
                    "default": True
                },
                "format": {
                    "type": "string",
                    "description": "Output format: 'markdown' (default) or 'json'",
                    "enum": ["markdown", "json"],
                    "default": "markdown"
                }
            },
            "required": ["plan_name"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Plan Management"
    
    @property
    def tags(self) -> List[str]:
        return ["plan", "project_management", "reading"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'read_plan' tool to view details of an execution plan.
        Parameters:
        - plan_name (string, required): Plan directory name
        - include_tasks (boolean, optional): Show task details (default: true)
        - format (string, optional): Output format - 'markdown' (default) or 'json'
        
        Example usage:
        <tool_code>
        read_plan(plan_name="add-caching-plan-2025-05-31")
        read_plan(plan_name="feature-x-plan-2025-05-30", include_tasks=false)
        read_plan(plan_name="dark-mode-plan-2025-05-31", format="json")
        </tool_code>
        
        Use format="json" when you need to pass the plan to another tool like decompose_plan.
        """
    
    def _find_plan(self, plan_name: str) -> Optional[Path]:
        """Find plan directory by name."""
        path_manager = PathManager.get_instance()
        plans_base = Path(path_manager.workspace_path) / ".WHISPER" / "plans"
        
        # Check both in_progress and archived
        for status in ["in_progress", "archived"]:
            plan_dir = plans_base / status / plan_name
            if plan_dir.exists() and plan_dir.is_dir():
                return plan_dir
        
        return None
    
    def _format_task(self, task: Dict[str, Any], index: int) -> str:
        """Format a single task for display."""
        result = f"{index}. **{task.get('name', 'Unnamed Task')}**\n"
        result += f"   - Description: {task.get('description', 'No description')}\n"
        result += f"   - Agent Type: {task.get('agent_type', 'unspecified')}\n"
        
        if task.get('tdd_phase'):
            result += f"   - TDD Phase: {task['tdd_phase'].upper()}\n"
        
        deps = task.get('dependencies', [])
        if deps:
            result += f"   - Dependencies: {', '.join(deps)}\n"
        
        criteria = task.get('validation_criteria', [])
        if criteria:
            result += f"   - Validation: {', '.join(criteria)}\n"
        
        return result
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute plan reading."""
        plan_name = arguments.get('plan_name')
        include_tasks = arguments.get('include_tasks', True)
        output_format = arguments.get('format', 'markdown')
        
        if not plan_name:
            error_response = {"error": "'plan_name' is required."}
            return json.dumps(error_response) if output_format == 'json' else "Error: 'plan_name' is required."
        
        try:
            # Find plan directory
            plan_dir = self._find_plan(plan_name)
            if not plan_dir:
                error_response = {"error": f"Plan '{plan_name}' not found."}
                return json.dumps(error_response) if output_format == 'json' else f"Error: Plan '{plan_name}' not found."
            
            # Load plan data
            plan_file = plan_dir / "plan.json"
            with open(plan_file, 'r') as f:
                plan_data = json.load(f)
            
            # Load RFC reference if exists
            ref_file = plan_dir / "rfc_reference.json"
            ref_data = None
            if ref_file.exists():
                with open(ref_file, 'r') as f:
                    ref_data = json.load(f)
            
            # Return JSON format if requested
            if output_format == 'json':
                return json.dumps(plan_data, indent=2)
            
            # Format response as markdown
            response = f"**Plan Found**: {plan_name}\n\n"
            
            # Basic information
            response += f"**Title**: {plan_data.get('title', 'Untitled')}\n"
            
            if plan_data.get('description'):
                response += f"**Description**: {plan_data['description']}\n"
            
            response += f"**Type**: {plan_data.get('plan_type', 'unknown')}\n"
            response += f"**Status**: {plan_data.get('status', 'unknown')}\n"
            
            # Source RFC info
            source_rfc = plan_data.get('source_rfc', {})
            response += f"**Source RFC**: {source_rfc.get('rfc_id', 'None')} - {source_rfc.get('title', 'Unknown')}\n"
            
            # Timestamps
            response += f"**Created**: {plan_data.get('created', 'Unknown')}\n"
            response += f"**Updated**: {plan_data.get('updated', 'Unknown')}\n"
            
            # Task summary
            tasks = plan_data.get('tasks', [])
            response += f"\n**Total Tasks**: {len(tasks)}\n"
            
            # TDD phase breakdown
            tdd_phases = {'red': 0, 'green': 0, 'refactor': 0}
            for task in tasks:
                phase = task.get('tdd_phase', '').lower()
                if phase in tdd_phases:
                    tdd_phases[phase] += 1
            
            if any(tdd_phases.values()):
                response += f"**TDD Breakdown**: RED ({tdd_phases['red']}), GREEN ({tdd_phases['green']}), REFACTOR ({tdd_phases['refactor']})\n"
            
            # Validation criteria
            criteria = plan_data.get('validation_criteria', [])
            if criteria:
                response += f"\n**Validation Criteria**:\n"
                for criterion in criteria:
                    response += f"- {criterion}\n"
            
            # RFC sync status
            if ref_data:
                response += f"\n**RFC Sync Status**:\n"
                response += f"- Last Sync: {ref_data.get('last_sync', 'Unknown')}\n"
                response += f"- RFC Path: {ref_data.get('rfc_path', 'Unknown')}\n"
            
            # Detailed task list
            if include_tasks and tasks:
                response += f"\n## Tasks\n\n"
                for i, task in enumerate(tasks, 1):
                    response += self._format_task(task, i)
                    response += "\n"
            
            # Refinement history
            history = plan_data.get('refinement_history', [])
            if history:
                response += f"\n## Refinement History\n\n"
                for entry in history[-5:]:  # Show last 5 entries
                    response += f"- {entry.get('timestamp', 'Unknown')}: {entry.get('action', 'Unknown action')}\n"
                    if entry.get('details'):
                        response += f"  Details: {entry['details']}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error reading plan: {e}")
            error_response = {"error": f"Error reading plan: {str(e)}"}
            return json.dumps(error_response) if output_format == 'json' else f"Error reading plan: {str(e)}"