"""
Module: ai_whisperer/tools/save_generated_plan_tool.py
Purpose: AI tool implementation for save generated plan

Tool to save a plan that was generated by the agent.
This complements prepare_plan_from_rfc by saving the agent-generated plan.

Key Components:
- SaveGeneratedPlanTool: 

Usage:
    tool = SaveGeneratedPlanTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- base_tool

"""


import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager
from ai_whisperer.utils.validation import validate_against_schema

logger = logging.getLogger(__name__)


class SaveGeneratedPlanTool(AITool):
    """
    Saves a plan that was generated by the agent through the AI loop.
    Handles validation, directory creation, and RFC linkage.
    """
    
    @property
    def name(self) -> str:
        return "save_generated_plan"
    
    @property
    def description(self) -> str:
        return "Save a generated plan to the filesystem with proper structure"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {
                    "type": "string",
                    "description": "Name for the plan directory (e.g., 'feature-x-plan-2025-05-31')"
                },
                "plan_content": {
                    "type": "object",
                    "description": "The generated plan JSON object"
                },
                "rfc_id": {
                    "type": "string",
                    "description": "Source RFC ID for linking"
                },
                "rfc_hash": {
                    "type": "string",
                    "description": "RFC content hash for change detection"
                }
            },
            "required": ["plan_name", "plan_content", "rfc_id"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Plan Management"
    
    @property
    def tags(self) -> List[str]:
        return ["plan", "file_write", "project_management"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'save_generated_plan' tool to save a plan after generating it.
        Parameters:
        - plan_name (string, required): Directory name for the plan
        - plan_content (object, required): The complete plan JSON
        - rfc_id (string, required): Source RFC identifier
        - rfc_hash (string, optional): RFC content hash from prepare_plan_from_rfc
        
        The plan_content should include:
        - plan_type: "initial" or "overview"
        - title: Plan title
        - description: Brief description
        - tdd_phases: Object with red, green, refactor arrays
        - tasks: Array of all tasks with dependencies
        - validation_criteria: Array of acceptance criteria
        
        Example usage:
        <tool_code>
        save_generated_plan(
            plan_name="feature-x-plan-2025-05-31",
            plan_content={
                "plan_type": "initial",
                "title": "Feature X Implementation",
                "tdd_phases": {...},
                "tasks": [...],
                "validation_criteria": [...]
            },
            rfc_id="RFC-2025-05-31-0001",
            rfc_hash="abc123..."
        )
        </tool_code>
        """
    
    def _find_rfc_metadata(self, rfc_id: str) -> Optional[tuple[Path, Dict[str, Any]]]:
        """Find RFC metadata file."""
        path_manager = PathManager.get_instance()
        rfc_base = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        
        for status in ["in_progress", "archived"]:
            status_dir = rfc_base / status
            if not status_dir.exists():
                continue
            
            for json_file in status_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                    
                    if metadata.get("rfc_id") == rfc_id:
                        return json_file, metadata
                except Exception:
                    continue
        
        return None
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Save the generated plan."""
        plan_name = arguments.get('plan_name')
        plan_content = arguments.get('plan_content')
        rfc_id = arguments.get('rfc_id')
        rfc_hash = arguments.get('rfc_hash')
        
        if not all([plan_name, plan_content, rfc_id]):
            return {
                "error": "'plan_name', 'plan_content', and 'rfc_id' are required.",
                "saved": False,
                "plan_name": plan_name
            }
        
        try:
            # Add metadata to plan
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plan_content["created"] = now
            plan_content["updated"] = now
            plan_content["status"] = "in_progress"
            
            # Find RFC metadata
            rfc_result = self._find_rfc_metadata(rfc_id)
            if not rfc_result:
                return {
                    "error": f"RFC '{rfc_id}' metadata not found.",
                    "saved": False,
                    "plan_name": plan_name,
                    "rfc_id": rfc_id
                }
            
            rfc_path, rfc_metadata = rfc_result
            
            # Add source RFC info
            plan_content["source_rfc"] = {
                "rfc_id": rfc_id,
                "title": rfc_metadata.get("title"),
                "filename": rfc_metadata.get("filename"),
                "version_hash": rfc_hash or "unknown"
            }
            
            # Validate plan against schema
            valid, error = validate_against_schema(plan_content, "rfc_plan_schema.json")
            if not valid:
                return {
                    "error": f"Generated plan failed validation: {error}",
                    "saved": False,
                    "plan_name": plan_name,
                    "validation_error": error
                }
            
            # Create plan directory
            path_manager = PathManager.get_instance()
            plan_dir = Path(path_manager.workspace_path) / ".WHISPER" / "plans" / "in_progress" / plan_name
            plan_dir.mkdir(parents=True, exist_ok=True)
            
            # Save plan.json
            plan_path = plan_dir / "plan.json"
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(plan_content, f, indent=2)
            
            # Create RFC reference
            ref_data = {
                "rfc_id": rfc_id,
                "rfc_path": str(rfc_path.relative_to(path_manager.workspace_path)),
                "rfc_content_hash": rfc_hash or "unknown",
                "last_sync": now
            }
            
            ref_path = plan_dir / "rfc_reference.json"
            with open(ref_path, 'w', encoding='utf-8') as f:
                json.dump(ref_data, f, indent=2)
            
            # Update RFC metadata with plan reference
            if "derived_plans" not in rfc_metadata:
                rfc_metadata["derived_plans"] = []
            
            # Check if plan already referenced (avoid duplicates)
            plan_refs = [p["plan_name"] for p in rfc_metadata["derived_plans"]]
            if plan_name not in plan_refs:
                rfc_metadata["derived_plans"].append({
                    "plan_name": plan_name,
                    "status": "in_progress",
                    "location": f".WHISPER/plans/in_progress/{plan_name}",
                    "created": now
                })
                
                # Save updated RFC metadata
                with open(rfc_path, 'w', encoding='utf-8') as f:
                    json.dump(rfc_metadata, f, indent=2)
            
            logger.info(f"Saved plan {plan_name} from RFC {rfc_id}")
            
            # Count tasks by phase
            tdd_phases = plan_content.get("tdd_phases", {})
            red_count = len(tdd_phases.get("red", []))
            green_count = len(tdd_phases.get("green", []))
            refactor_count = len(tdd_phases.get("refactor", []))
            total_tasks = len(plan_content.get("tasks", []))
            
            return {
                "saved": True,
                "plan_name": plan_name,
                "plan_path": f".WHISPER/plans/in_progress/{plan_name}/",
                "absolute_path": str(plan_path),
                "rfc_id": rfc_id,
                "rfc_linked": True,
                "total_tasks": total_tasks,
                "tdd_breakdown": {
                    "red": red_count,
                    "green": green_count,
                    "refactor": refactor_count
                },
                "created": now,
                "status": "in_progress"
            }
            
        except Exception as e:
            logger.error(f"Error saving generated plan: {e}")
            return {
                "error": f"Error saving plan: {str(e)}",
                "saved": False,
                "plan_name": plan_name
            }