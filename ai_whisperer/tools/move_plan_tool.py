"""
Module: ai_whisperer/tools/move_plan_tool.py
Purpose: AI tool implementation for move plan

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- MovePlanTool: Tool for moving plans between status directories.

Usage:
    tool = MovePlanTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- shutil

"""

import logging
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

class MovePlanTool(AITool):
    """Tool for moving plans between status directories."""
    
    @property
    def name(self) -> str:
        return "move_plan"
    
    @property
    def description(self) -> str:
        return "Move a plan between in_progress and archived status."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {
                    "type": "string",
                    "description": "Name of the plan to move"
                },
                "to_status": {
                    "type": "string",
                    "enum": ["in_progress", "archived"],
                    "description": "Target status"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for moving the plan",
                    "nullable": True
                }
            },
            "required": ["plan_name", "to_status"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Plan Management"
    
    @property
    def tags(self) -> List[str]:
        return ["plan", "project_management", "archival"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'move_plan' tool to change plan status.
        Parameters:
        - plan_name (string, required): Plan to move
        - to_status (string, required): 'in_progress' or 'archived'
        - reason (string, optional): Reason for the move
        
        Example usage:
        <tool_code>
        move_plan(plan_name="add-caching-plan-2025-05-31", to_status="archived")
        move_plan(plan_name="old-plan", to_status="archived", reason="Completed successfully")
        </tool_code>
        """
    
    def _find_plan(self, plan_name: str) -> Optional[tuple[Path, str]]:
        """Find plan directory and current status."""
        path_manager = PathManager.get_instance()
        plans_base = Path(path_manager.workspace_path) / ".WHISPER" / "plans"
        
        for status in ["in_progress", "archived"]:
            plan_dir = plans_base / status / plan_name
            if plan_dir.exists() and plan_dir.is_dir():
                return plan_dir, status
        
        return None
    
    def _update_rfc_metadata(self, plan_name: str, old_status: str, new_status: str) -> None:
        """Update RFC metadata to reflect plan move."""
        path_manager = PathManager.get_instance()
        
        # Load plan to get RFC reference
        plan_path = Path(path_manager.workspace_path) / ".WHISPER" / "plans" / new_status / plan_name / "plan.json"
        
        try:
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
            
            source_rfc = plan_data.get('source_rfc', {})
            rfc_id = source_rfc.get('rfc_id')
            
            if not rfc_id:
                return
            
            # Find RFC metadata file
            rfc_base = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
            
            for rfc_status in ["in_progress", "archived"]:
                for json_file in (rfc_base / rfc_status).glob("*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            metadata = json.load(f)
                        
                        if metadata.get('rfc_id') == rfc_id:
                            # Update derived plans
                            if 'derived_plans' in metadata:
                                for plan_ref in metadata['derived_plans']:
                                    if plan_ref.get('plan_name') == plan_name:
                                        plan_ref['status'] = new_status
                                        plan_ref['location'] = f".WHISPER/plans/{new_status}/{plan_name}"
                                
                                # Save updated metadata
                                with open(json_file, 'w') as f:
                                    json.dump(metadata, f, indent=2)
                            
                            return
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.error(f"Error updating RFC metadata: {e}")
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan move."""
        plan_name = arguments.get('plan_name')
        to_status = arguments.get('to_status')
        reason = arguments.get('reason', 'Status change requested')
        
        if not plan_name:
            return {
                "error": "'plan_name' is required.",
                "plan_name": None,
                "moved": False
            }
        
        if not to_status:
            return {
                "error": "'to_status' is required.",
                "plan_name": plan_name,
                "moved": False
            }
        
        try:
            # Find current plan location
            result = self._find_plan(plan_name)
            if not result:
                return {
                    "error": f"Plan '{plan_name}' not found.",
                    "plan_name": plan_name,
                    "moved": False
                }
            
            current_path, current_status = result
            
            # Check if already in target status
            if current_status == to_status:
                return {
                    "error": f"Plan is already in '{to_status}' status.",
                    "plan_name": plan_name,
                    "current_status": current_status,
                    "target_status": to_status,
                    "moved": False
                }
            
            # Prepare target directory
            path_manager = PathManager.get_instance()
            target_dir = Path(path_manager.workspace_path) / ".WHISPER" / "plans" / to_status / plan_name
            
            # Ensure target status directory exists
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Update plan metadata before moving
            plan_file = current_path / "plan.json"
            if plan_file.exists():
                with open(plan_file, 'r') as f:
                    plan_data = json.load(f)
                
                # Update status and history
                plan_data['status'] = to_status
                plan_data['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if 'refinement_history' not in plan_data:
                    plan_data['refinement_history'] = []
                
                plan_data['refinement_history'].append({
                    "timestamp": plan_data['updated'],
                    "action": f"Moved from {current_status} to {to_status}",
                    "details": reason
                })
                
                # Save updated plan data
                with open(plan_file, 'w') as f:
                    json.dump(plan_data, f, indent=2)
            
            # Move the directory
            shutil.move(str(current_path), str(target_dir))
            
            # Update RFC metadata
            self._update_rfc_metadata(plan_name, current_status, to_status)
            
            logger.info(f"Moved plan {plan_name} from {current_status} to {to_status}")
            
            return {
                "moved": True,
                "plan_name": plan_name,
                "from_status": current_status,
                "to_status": to_status,
                "reason": reason,
                "new_location": f".WHISPER/plans/{to_status}/{plan_name}",
                "absolute_path": str(target_dir),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rfc_metadata_updated": True
            }
            
        except Exception as e:
            logger.error(f"Error moving plan: {e}")
            return {
                "error": f"Error moving plan: {str(e)}",
                "plan_name": plan_name,
                "moved": False
            }
