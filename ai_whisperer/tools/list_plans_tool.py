"""
Module: ai_whisperer/tools/list_plans_tool.py
Purpose: AI tool implementation for list plans

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- ListPlansTool: Tool for listing execution plans.

Usage:
    tool = ListPlansTool()
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

class ListPlansTool(AITool):
    """Tool for listing execution plans."""
    
    @property
    def name(self) -> str:
        return "list_plans"
    
    @property
    def description(self) -> str:
        return "List execution plans with filtering options."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["in_progress", "archived", "all"],
                    "description": "Filter by plan status",
                    "default": "all"
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["created", "updated", "name"],
                    "description": "Sort plans by field",
                    "default": "created"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of plans to return",
                    "nullable": True
                },
                "format": {
                    "type": "string",
                    "description": "Output format: 'markdown' (default) or 'json'",
                    "enum": ["markdown", "json"],
                    "default": "markdown"
                }
            }
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Plan Management"
    
    @property
    def tags(self) -> List[str]:
        return ["plan", "project_management", "listing"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'list_plans' tool to view available execution plans.
        Parameters:
        - status (string, optional): 'in_progress', 'archived', or 'all' (default: all)
        - sort_by (string, optional): 'created', 'updated', or 'name' (default: created)
        - limit (integer, optional): Maximum number of results
        - format (string, optional): Output format - 'markdown' (default) or 'json'
        
        Example usage:
        <tool_code>
        list_plans()
        list_plans(status="in_progress")
        list_plans(sort_by="updated", limit=5)
        list_plans(format="json")
        </tool_code>
        
        Use format="json" when you need structured data for UI components or other tools.
        """
    
    def _load_plan_info(self, plan_dir: Path) -> Optional[Dict[str, Any]]:
        """Load plan information from directory."""
        plan_file = plan_dir / "plan.json"
        if not plan_file.exists():
            return None
        
        try:
            with open(plan_file, 'r') as f:
                plan_data = json.load(f)
                
            # Add directory name for reference
            plan_data["_plan_name"] = plan_dir.name
            plan_data["_status_dir"] = plan_dir.parent.name
            
            return plan_data
        except Exception as e:
            logger.error(f"Error loading plan from {plan_dir}: {e}")
            return None
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan listing."""
        status_filter = arguments.get('status', 'all')
        sort_by = arguments.get('sort_by', 'created')
        limit = arguments.get('limit')
        output_format = arguments.get('format', 'markdown')
        
        try:
            path_manager = PathManager.get_instance()
            # Handle potential None workspace_path
            workspace_path = path_manager.workspace_path
            if workspace_path is None:
                return {
                    "error": "Workspace path not initialized.",
                    "plans": [],
                    "count": 0
                }
            
            plans_base = Path(workspace_path) / ".WHISPER" / "plans"
            
            # Determine which directories to search
            if status_filter == 'all':
                search_dirs = ['in_progress', 'archived']
            else:
                search_dirs = [status_filter]
            
            # Collect all plans
            all_plans = []
            
            for status_dir in search_dirs:
                status_path = plans_base / status_dir
                if not status_path.exists():
                    continue
                
                # List all plan directories
                for plan_dir in status_path.iterdir():
                    if plan_dir.is_dir():
                        plan_info = self._load_plan_info(plan_dir)
                        if plan_info:
                            all_plans.append(plan_info)
            
            # Sort plans
            if sort_by == 'created':
                all_plans.sort(key=lambda x: x.get('created', ''), reverse=True)
            elif sort_by == 'updated':
                all_plans.sort(key=lambda x: x.get('updated', ''), reverse=True)
            elif sort_by == 'name':
                all_plans.sort(key=lambda x: x.get('_plan_name', ''))
            
            # Apply limit
            if limit and limit > 0:
                all_plans = all_plans[:limit]
            
            # Create simplified plan summaries
            plan_summaries = []
            for plan in all_plans:
                summary = {
                    'plan_name': plan.get('_plan_name', ''),
                    'title': plan.get('title', 'Untitled'),
                    'plan_type': plan.get('plan_type', 'unknown'),
                    'status': plan.get('_status_dir', 'unknown'),
                    'source_rfc': plan.get('source_rfc', {}).get('rfc_id', 'None'),
                    'task_count': len(plan.get('tasks', [])),
                    'created_at': plan.get('created', 'Unknown'),
                    'updated_at': plan.get('updated', 'Unknown')
                }
                plan_summaries.append(summary)
            
            # Group by status
            by_status = {}
            for plan in all_plans:
                status = plan.get('_status_dir', 'unknown')
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(plan)
            
            return {
                "plans": plan_summaries,
                "count": len(plan_summaries),
                "status_filter": status_filter,
                "sort_by": sort_by,
                "by_status": {
                    "in_progress": len(by_status.get('in_progress', [])),
                    "archived": len(by_status.get('archived', []))
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing plans: {e}")
            return {
                "error": f"Error listing plans: {str(e)}",
                "plans": [],
                "count": 0
            }
