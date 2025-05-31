"""
Update Plan from RFC Tool - Updates plans when source RFC changes
"""
import os
import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.json_validator import validate_against_schema

logger = logging.getLogger(__name__)


class UpdatePlanFromRFCTool(AITool):
    """Tool for updating plans when source RFC changes."""
    
    @property
    def name(self) -> str:
        return "update_plan_from_rfc"
    
    @property
    def description(self) -> str:
        return "Update an execution plan when its source RFC has changed."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {
                    "type": "string",
                    "description": "Name of the plan to update"
                },
                "force": {
                    "type": "boolean",
                    "description": "Force update even if RFC hasn't changed",
                    "default": False
                },
                "preserve_progress": {
                    "type": "boolean",
                    "description": "Try to preserve task completion status",
                    "default": True
                }
            },
            "required": ["plan_name"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Plan Management"
    
    @property
    def tags(self) -> List[str]:
        return ["plan", "rfc", "synchronization", "update"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'update_plan_from_rfc' tool to sync plans with RFC changes.
        Parameters:
        - plan_name (string, required): Plan to update
        - force (boolean, optional): Force update regardless of changes (default: false)
        - preserve_progress (boolean, optional): Keep task status (default: true)
        
        Example usage:
        <tool_code>
        update_plan_from_rfc(plan_name="add-caching-plan-2025-05-31")
        update_plan_from_rfc(plan_name="feature-x-plan", force=true)
        </tool_code>
        """
    
    def _find_plan(self, plan_name: str) -> Optional[Path]:
        """Find plan directory by name."""
        path_manager = PathManager.get_instance()
        plans_base = Path(path_manager.workspace_path) / ".WHISPER" / "plans"
        
        for status in ["in_progress", "archived"]:
            plan_dir = plans_base / status / plan_name
            if plan_dir.exists() and plan_dir.is_dir():
                return plan_dir
        
        return None
    
    def _calculate_rfc_hash(self, content: str) -> str:
        """Calculate SHA256 hash of RFC content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _check_rfc_changes(self, plan_dir: Path) -> tuple[bool, Optional[str], Optional[str]]:
        """Check if RFC has changed since last sync."""
        ref_file = plan_dir / "rfc_reference.json"
        if not ref_file.exists():
            return False, None, "No RFC reference found"
        
        try:
            with open(ref_file, 'r') as f:
                ref_data = json.load(f)
            
            # Load current RFC content
            path_manager = PathManager.get_instance()
            rfc_path = Path(path_manager.workspace_path) / ref_data['rfc_path']
            
            if not rfc_path.exists():
                return False, None, f"RFC file not found: {ref_data['rfc_path']}"
            
            with open(rfc_path, 'r', encoding='utf-8') as f:
                rfc_content = f.read()
            
            # Calculate current hash
            current_hash = self._calculate_rfc_hash(rfc_content)
            stored_hash = ref_data.get('rfc_content_hash')
            
            if current_hash != stored_hash:
                return True, rfc_content, None
            
            return False, rfc_content, None
            
        except Exception as e:
            return False, None, str(e)
    
    def _create_update_prompt(self, old_plan: Dict[str, Any], rfc_content: str) -> str:
        """Create prompt for AI to update plan based on RFC changes."""
        return f"""Update the following execution plan based on the updated RFC content.

Current Plan:
{json.dumps(old_plan, indent=2)}

Updated RFC Content:
{rfc_content}

Requirements:
1. Identify what has changed in the RFC
2. Update tasks to reflect new requirements
3. Maintain TDD approach (Red-Green-Refactor)
4. Preserve existing task structure where possible
5. Add new tasks for new requirements
6. Remove tasks for removed requirements
7. Update validation criteria

Generate an updated JSON plan maintaining the same structure as the original.
Ensure all changes follow TDD methodology."""
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute plan update from RFC."""
        plan_name = arguments.get('plan_name')
        force_update = arguments.get('force', False)
        preserve_progress = arguments.get('preserve_progress', True)
        
        if not plan_name:
            return "Error: 'plan_name' is required."
        
        try:
            # Find plan
            plan_dir = self._find_plan(plan_name)
            if not plan_dir:
                return f"Error: Plan '{plan_name}' not found."
            
            # Load current plan
            plan_file = plan_dir / "plan.json"
            with open(plan_file, 'r') as f:
                current_plan = json.load(f)
            
            # Check for RFC changes
            has_changed, rfc_content, error = self._check_rfc_changes(plan_dir)
            
            if error:
                return f"Error checking RFC: {error}"
            
            if not has_changed and not force_update:
                return "Plan is already up to date with the RFC."
            
            # Store task progress if preserving
            task_progress = {}
            if preserve_progress:
                for i, task in enumerate(current_plan.get('tasks', [])):
                    if 'status' in task:
                        task_progress[task['name']] = task['status']
            
            # Generate updated plan using AI
            from ai_whisperer.ai_loop.ai_config import AIConfig
            ai_config = AIConfig(
                api_key=os.environ.get("OPENROUTER_API_KEY", "dummy_key"),
                model_id="anthropic/claude-3-5-sonnet",
                temperature=0.7,
                max_tokens=4000
            )
            ai_service = OpenRouterAIService(config=ai_config)
            
            prompt = self._create_update_prompt(current_plan, rfc_content)
            
            # Use async to sync conversion for the streaming API
            import asyncio
            async def get_completion():
                chunks = []
                async for chunk in ai_service.stream_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                ):
                    if chunk.delta_content:
                        chunks.append(chunk.delta_content)
                return ''.join(chunks)
            
            # Handle both cases: event loop already running or not
            try:
                # Check if an event loop is already running
                loop = asyncio.get_running_loop()
                # Create a task and run it in the existing loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, get_completion())
                    response_content = future.result()
            except RuntimeError:
                # No running event loop, create a new one
                response_content = asyncio.run(get_completion())
            
            # Parse updated plan
            updated_plan = json.loads(response_content)
            
            # Merge with current plan to preserve required fields
            # Start with current plan as base
            merged_plan = current_plan.copy()
            
            # Update fields from AI response
            if "tasks" in updated_plan:
                merged_plan["tasks"] = updated_plan["tasks"]
            if "validation_criteria" in updated_plan:
                merged_plan["validation_criteria"] = updated_plan["validation_criteria"]
            if "description" in updated_plan:
                merged_plan["description"] = updated_plan["description"]
            
            # Update metadata
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            merged_plan["updated"] = now
            
            # Use merged plan as the updated plan
            updated_plan = merged_plan
            
            # Restore task progress if requested
            if preserve_progress and task_progress:
                for task in updated_plan.get('tasks', []):
                    if task['name'] in task_progress:
                        task['status'] = task_progress[task['name']]
            
            # Add to refinement history
            if 'refinement_history' not in updated_plan:
                updated_plan['refinement_history'] = current_plan.get('refinement_history', [])
            
            updated_plan['refinement_history'].append({
                "timestamp": now,
                "action": "Updated from RFC changes",
                "details": "RFC has changed since last sync" if has_changed else "Forced update"
            })
            
            # Validate updated plan
            valid, error = validate_against_schema(updated_plan, "rfc_plan_schema.json")
            if not valid:
                return f"Error: Updated plan failed validation: {error}"
            
            # Save updated plan
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(updated_plan, f, indent=2)
            
            # Update RFC reference
            if has_changed:
                ref_file = plan_dir / "rfc_reference.json"
                with open(ref_file, 'r') as f:
                    ref_data = json.load(f)
                
                # Add to sync history
                if 'sync_history' not in ref_data:
                    ref_data['sync_history'] = []
                
                ref_data['sync_history'].append({
                    "timestamp": now,
                    "previous_hash": ref_data.get('rfc_content_hash'),
                    "new_hash": self._calculate_rfc_hash(rfc_content),
                    "changes_detected": "RFC content modified"
                })
                
                # Update current hash
                ref_data['rfc_content_hash'] = self._calculate_rfc_hash(rfc_content)
                ref_data['last_sync'] = now
                
                with open(ref_file, 'w') as f:
                    json.dump(ref_data, f, indent=2)
            
            # Count changes
            old_tasks = len(current_plan.get('tasks', []))
            new_tasks = len(updated_plan.get('tasks', []))
            
            response = f"""Plan updated successfully!

**Plan**: {plan_name}
**RFC Status**: {"RFC has changed since last sync" if has_changed else "No RFC changes detected (forced update)"}
**Task Changes**: {old_tasks} → {new_tasks} tasks

Updates applied:
- Plan regenerated from current RFC content
- TDD structure maintained
"""
            
            if preserve_progress and task_progress:
                response += f"- Task progress preserved for {len(task_progress)} tasks\n"
            
            response += "\nUse 'read_plan' to review the updated plan."
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating plan from RFC: {e}")
            return f"Error updating plan: {str(e)}"