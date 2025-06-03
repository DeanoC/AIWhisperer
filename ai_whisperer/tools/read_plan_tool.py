"""
Module: ai_whisperer/tools/read_plan_tool.py
Purpose: AI tool implementation for read plan

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- ReadPlanTool: Tool for reading execution plan details.

Usage:
    tool = ReadPlanTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

Related:
- See UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md

"""

import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

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
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan reading."""
        plan_name = arguments.get('plan_name')
        include_tasks = arguments.get('include_tasks', True)
        output_format = arguments.get('format', 'markdown')
        
        if not plan_name:
            return {
                "error": "'plan_name' is required.",
                "plan_name": None,
                "found": False
            }
        
        try:
            # Find plan directory
            plan_dir = self._find_plan(plan_name)
            if not plan_dir:
                return {
                    "error": f"Plan '{plan_name}' not found.",
                    "plan_name": plan_name,
                    "found": False
                }
            
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
            
            # Add metadata to plan data
            plan_data["_metadata"] = {
                "plan_name": plan_name,
                "plan_directory": str(plan_dir),
                "status_folder": plan_dir.parent.name,
                "found": True,
                "include_tasks": include_tasks,
                "rfc_reference_exists": ref_data is not None
            }
            
            if ref_data:
                plan_data["_metadata"]["rfc_sync"] = ref_data
            
            return plan_data
            
        except Exception as e:
            logger.error(f"Error reading plan: {e}")
            return {
                "error": f"Error reading plan: {str(e)}",
                "plan_name": plan_name,
                "found": False
            }
