"""
Create Plan from RFC Tool - Converts RFCs into structured execution plans
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
from ai_whisperer.exceptions import FileRestrictionError
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.config import load_config
from ai_whisperer.json_validator import validate_against_schema

logger = logging.getLogger(__name__)


class CreatePlanFromRFCTool(AITool):
    """Tool for converting RFCs into structured execution plans."""
    
    @property
    def name(self) -> str:
        return "create_plan_from_rfc"
    
    @property
    def description(self) -> str:
        return "Convert an RFC into a structured execution plan with TDD approach."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rfc_id": {
                    "type": "string",
                    "description": "RFC ID (e.g., 'RFC-2025-05-31-0001') or short name (e.g., 'add-caching')"
                },
                "plan_type": {
                    "type": "string",
                    "enum": ["initial", "overview"],
                    "description": "Type of plan to generate",
                    "default": "initial"
                },
                "model": {
                    "type": "string",
                    "description": "AI model to use for plan generation",
                    "nullable": True
                }
            },
            "required": ["rfc_id"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Plan Management"
    
    @property
    def tags(self) -> List[str]:
        return ["plan", "rfc", "project_management", "planning"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'create_plan_from_rfc' tool to convert RFCs into structured plans.
        Parameters:
        - rfc_id (string, required): RFC ID or short name
        - plan_type (string, optional): 'initial' or 'overview' (default: initial)
        - model (string, optional): Specific AI model to use
        
        This tool creates executable plans from RFCs with TDD structure.
        Example usage:
        <tool_code>
        create_plan_from_rfc(rfc_id="RFC-2025-05-31-0001")
        create_plan_from_rfc(rfc_id="add-caching", plan_type="overview")
        </tool_code>
        """
    
    def _find_rfc(self, rfc_id: str) -> Optional[tuple[Path, Dict[str, Any]]]:
        """Find RFC by ID or short name."""
        path_manager = PathManager.get_instance()
        rfc_base = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        
        for status in ["in_progress", "archived"]:
            status_dir = rfc_base / status
            if not status_dir.exists():
                continue
            
            # Check all JSON metadata files
            for json_file in status_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                        
                    # Check if RFC ID or short name matches
                    if (metadata.get("rfc_id") == rfc_id or 
                        metadata.get("short_name") == rfc_id):
                        
                        # Find corresponding markdown file
                        md_file = json_file.with_suffix('.md')
                        if md_file.exists():
                            return md_file, metadata
                except Exception:
                    continue
        
        return None
    
    def _calculate_rfc_hash(self, content: str) -> str:
        """Calculate SHA256 hash of RFC content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_plan_name(self, rfc_metadata: Dict[str, Any]) -> str:
        """Generate plan directory name from RFC metadata."""
        short_name = rfc_metadata.get("short_name", "unknown")
        date = datetime.now().strftime("%Y-%m-%d")
        return f"{short_name}-plan-{date}"
    
    def _create_plan_prompt(self, rfc_content: str, rfc_metadata: Dict[str, Any], plan_type: str) -> str:
        """Create prompt for AI to generate plan from RFC."""
        return f"""Convert the following RFC into a structured {plan_type} plan following TDD principles.

RFC Content:
{rfc_content}

Requirements:
1. Extract all requirements from the RFC
2. Create tasks that follow Red-Green-Refactor TDD cycle
3. For each feature:
   - First create test writing tasks (RED phase)
   - Then implementation tasks (GREEN phase)
   - Finally refactoring tasks if needed (REFACTOR phase)
4. Set appropriate agent types for each task
5. Define clear validation criteria
6. Establish task dependencies

Generate a JSON plan with this structure:
{{
  "plan_type": "{plan_type}",
  "title": "Implementation plan title",
  "description": "Brief description",
  "agent_type": "primary agent type",
  "tasks": [
    {{
      "name": "Task name",
      "description": "Task description",
      "agent_type": "agent_type",
      "dependencies": ["dependency1"],
      "tdd_phase": "red|green|refactor"
    }}
  ],
  "validation_criteria": ["criteria1", "criteria2"]
}}

Ensure all tasks follow TDD methodology with tests written before implementation."""
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute plan creation from RFC."""
        rfc_id = arguments.get('rfc_id')
        plan_type = arguments.get('plan_type', 'initial')
        model_override = arguments.get('model')
        
        if not rfc_id:
            return "Error: 'rfc_id' is required."
        
        try:
            # Find RFC
            rfc_result = self._find_rfc(rfc_id)
            if not rfc_result:
                return f"Error: RFC '{rfc_id}' not found."
            
            rfc_path, rfc_metadata = rfc_result
            
            # Read RFC content
            with open(rfc_path, 'r', encoding='utf-8') as f:
                rfc_content = f.read()
            
            # Calculate RFC hash
            rfc_hash = self._calculate_rfc_hash(rfc_content)
            
            # Generate plan using AI
            # In production, config would be loaded from file
            # For now, using minimal config for the tool
            ai_config = {
                "api_key": os.environ.get("OPENROUTER_API_KEY", "dummy_key"),
                "base_url": "https://openrouter.ai/api/v1",
                "model": model_override or "anthropic/claude-3-5-sonnet",
                "temperature": 0.7,
                "max_tokens": 4000
            }
            ai_service = OpenRouterAIService(ai_config)
            
            prompt = self._create_plan_prompt(rfc_content, rfc_metadata, plan_type)
            
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
            
            response_content = asyncio.run(get_completion())
            
            # Parse AI response
            plan_data = json.loads(response_content)
            
            # Add metadata
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plan_data["created"] = now
            plan_data["updated"] = now
            plan_data["status"] = "in_progress"
            plan_data["source_rfc"] = {
                "rfc_id": rfc_metadata.get("rfc_id"),
                "title": rfc_metadata.get("title"),
                "filename": rfc_path.name,
                "version_hash": rfc_hash
            }
            
            # Validate plan against schema
            valid, error = validate_against_schema(plan_data, "rfc_plan_schema.json")
            if not valid:
                return f"Error: Generated plan failed validation: {error}"
            
            # Create plan directory
            plan_name = self._generate_plan_name(rfc_metadata)
            path_manager = PathManager.get_instance()
            plan_dir = Path(path_manager.workspace_path) / ".WHISPER" / "plans" / "in_progress" / plan_name
            plan_dir.mkdir(parents=True, exist_ok=True)
            
            # Save plan.json
            plan_path = plan_dir / "plan.json"
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2)
            
            # Create RFC reference
            ref_data = {
                "rfc_id": rfc_metadata.get("rfc_id"),
                "rfc_path": str(rfc_path.relative_to(path_manager.workspace_path)),
                "rfc_content_hash": rfc_hash,
                "last_sync": now
            }
            
            ref_path = plan_dir / "rfc_reference.json"
            with open(ref_path, 'w', encoding='utf-8') as f:
                json.dump(ref_data, f, indent=2)
            
            # Update RFC metadata with plan reference
            if "derived_plans" not in rfc_metadata:
                rfc_metadata["derived_plans"] = []
            
            rfc_metadata["derived_plans"].append({
                "plan_name": plan_name,
                "status": "in_progress",
                "location": f".WHISPER/plans/in_progress/{plan_name}",
                "created": now
            })
            
            # Save updated RFC metadata
            metadata_path = rfc_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(rfc_metadata, f, indent=2)
            
            logger.info(f"Created plan {plan_name} from RFC {rfc_id}")
            
            return f"""Plan created successfully!

**Plan Name**: {plan_name}
**Type**: {plan_type}
**Source RFC**: {rfc_metadata.get('rfc_id')}
**Location**: .WHISPER/plans/in_progress/{plan_name}

The plan has been created with {len(plan_data.get('tasks', []))} tasks following TDD principles.

Next steps:
1. Review the generated plan with 'read_plan'
2. Execute tasks in order
3. Update plan if RFC changes with 'update_plan_from_rfc'
4. Archive when complete with 'move_plan'"""
            
        except Exception as e:
            logger.error(f"Error creating plan from RFC: {e}")
            return f"Error creating plan from RFC: {str(e)}"