"""
Module: ai_whisperer/tools/delete_plan_tool.py
Purpose: AI tool implementation for delete plan

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- DeletePlanTool: Tool for deleting plan documents and their directories.

Usage:
    tool = DeletePlanTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- shutil

"""

import json
import logging
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

class DeletePlanTool(AITool):
    """Tool for deleting plan documents and their directories."""
    
    @property
    def name(self) -> str:
        return "delete_plan"
    
    @property
    def description(self) -> str:
        return "Delete a plan permanently, including all associated files."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {
                    "type": "string",
                    "description": "The plan directory name to delete (e.g., dark-mode-plan-2025-05-31)"
                },
                "confirm_delete": {
                    "type": "boolean",
                    "description": "Confirmation flag - must be true to delete",
                    "default": False
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for deletion",
                    "nullable": True
                }
            },
            "required": ["plan_name", "confirm_delete"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Plan Management"
    
    @property
    def tags(self) -> List[str]:
        return ["plan", "project_management", "dangerous"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'delete_plan' tool to permanently delete plan directories.
        
        IMPORTANT: This action is PERMANENT and cannot be undone!
        
        Parameters:
        - plan_name (string, required): Plan directory name to delete
        - confirm_delete (boolean, required): Must be true to proceed with deletion
        - reason (string, optional): Reason for deletion
        
        Before using this tool:
        1. ALWAYS ask the user to confirm they want to delete the plan
        2. Explain that this action is permanent
        3. Consider if archiving might be more appropriate
        4. Check if the plan has any important information that should be saved
        
        Example usage:
        <tool_code>
        delete_plan(
            plan_name="dark-mode-plan-2025-05-31",
            confirm_delete=true,
            reason="Plan completed and no longer needed"
        )
        </tool_code>
        """
    
    def _find_plan(self, plan_name: str) -> Optional[Path]:
        """Find plan directory in any status folder."""
        path_manager = PathManager.get_instance()
        plan_base_path = Path(path_manager.workspace_path) / ".WHISPER" / "plans"
        
        # Check each folder
        for folder in ["in_progress", "archived"]:
            folder_path = plan_base_path / folder
            if not folder_path.exists():
                continue
                
            plan_dir = folder_path / plan_name
            if plan_dir.exists() and plan_dir.is_dir():
                return plan_dir
        
        return None
    
    def _update_rfc_reference(self, plan_dir: Path, plan_name: str) -> Optional[str]:
        """Remove plan reference from the source RFC metadata."""
        try:
            # Read RFC reference to find the source RFC
            ref_path = plan_dir / "rfc_reference.json"
            if not ref_path.exists():
                return None
                
            with open(ref_path, 'r', encoding='utf-8') as f:
                ref_data = json.load(f)
            
            rfc_id = ref_data.get('rfc_id')
            if not rfc_id:
                return None
            
            # Find and update RFC metadata
            path_manager = PathManager.get_instance()
            rfc_base = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
            
            for status in ["in_progress", "archived"]:
                status_dir = rfc_base / status
                if not status_dir.exists():
                    continue
                
                # Look for RFC metadata file by checking all JSON files
                for json_file in status_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            rfc_metadata = json.load(f)
                        
                        # Check if this is the right RFC
                        if rfc_metadata.get("rfc_id") == rfc_id:
                            # Remove plan reference
                            if "derived_plans" in rfc_metadata:
                                rfc_metadata["derived_plans"] = [
                                    p for p in rfc_metadata["derived_plans"]
                                    if p.get("plan_name") != plan_name
                                ]
                            
                            # Save updated metadata
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(rfc_metadata, f, indent=2)
                            
                            return rfc_id
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Error updating RFC reference: {e}")
        
        return None
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute plan deletion."""
        plan_name = arguments.get('plan_name')
        confirm_delete = arguments.get('confirm_delete', False)
        reason = arguments.get('reason', 'No reason provided')
        
        if not plan_name:
            return "Error: 'plan_name' is required."
        
        if not confirm_delete:
            return f"""Delete operation cancelled.

To delete plan {plan_name}, you must:
1. Get user confirmation
2. Set confirm_delete=true

This action is PERMANENT and cannot be undone."""
        
        try:
            # Find the plan
            plan_dir = self._find_plan(plan_name)
            if not plan_dir:
                return f"Error: Plan {plan_name} not found in any folder."
            
            # Store some info before deletion
            folder_name = plan_dir.parent.name
            
            # Check what files exist in the plan
            files_found = []
            if (plan_dir / "plan.json").exists():
                files_found.append("plan.json")
            if (plan_dir / "rfc_reference.json").exists():
                files_found.append("rfc_reference.json")
            # Check for any task files
            for task_file in plan_dir.glob("subtask_*.json"):
                files_found.append(task_file.name)
            
            # Update RFC reference before deletion
            updated_rfc = self._update_rfc_reference(plan_dir, plan_name)
            
            # Delete the entire plan directory
            shutil.rmtree(plan_dir)
            
            logger.info(f"Deleted plan {plan_name}: {reason}")
            
            result = f"""Plan deleted successfully!

**Plan Name**: {plan_name}
**Status**: Was in '{folder_name}'
**Files Deleted**: {len(files_found)} files in directory
**Reason**: {reason}"""

            if updated_rfc:
                result += f"\n**RFC Updated**: Removed reference from {updated_rfc}"
            
            result += "\n\nThis action is permanent and cannot be undone."
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting plan {plan_name}: {e}")
            return f"Error deleting plan: {str(e)}"
