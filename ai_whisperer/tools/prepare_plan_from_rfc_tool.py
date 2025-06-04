"""
Module: ai_whisperer/tools/prepare_plan_from_rfc_tool.py
Purpose: AI tool implementation for prepare plan from rfc

Tool to prepare RFC content and context for plan generation.
This tool doesn't generate the plan itself - it prepares the information
for the agent to generate the plan through the normal AI loop.

Key Components:
- PreparePlanFromRFCTool: 

Usage:
    tool = PreparePlanFromRFCTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- base_tool
- hashlib

"""


import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import hashlib

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)


class PreparePlanFromRFCTool(AITool):
    """
    Prepares RFC content and metadata for plan generation.
    Returns structured information that the agent can use to generate a plan.
    """
    
    @property
    def name(self) -> str:
        return "prepare_plan_from_rfc"
    
    @property
    def description(self) -> str:
        return "Prepare RFC content and context for plan generation"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rfc_id": {
                    "type": "string",
                    "description": "RFC ID, short name, or filename to convert"
                },
                "plan_type": {
                    "type": "string",
                    "enum": ["initial", "overview"],
                    "description": "Type of plan to generate",
                    "default": "initial"
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
        Use the 'prepare_plan_from_rfc' tool to prepare RFC content for plan generation.
        Parameters:
        - rfc_id (string, required): RFC ID, short name, or filename
        - plan_type (string, optional): 'initial' or 'overview' (default: initial)
        
        This tool prepares the RFC content and context. After using this tool,
        generate a structured plan following TDD principles (Red-Green-Refactor).
        
        Example workflow:
        1. Use prepare_plan_from_rfc to get RFC content
        2. Generate a JSON plan with the following structure:
           {
             "plan_type": "initial",
             "title": "Plan title from RFC",
             "description": "Brief description",
             "tdd_phases": {
               "red": [/* test tasks */],
               "green": [/* implementation tasks */],
               "refactor": [/* improvement tasks */]
             },
             "tasks": [/* all tasks with dependencies */],
             "validation_criteria": [/* acceptance criteria */]
           }
        3. Use save_generated_plan to save the plan
        """
    
    def _find_rfc(self, rfc_id: str) -> Optional[tuple[Path, Dict[str, Any]]]:
        """Find RFC by ID, short name, or filename."""
        logger.info(f"_find_rfc called with rfc_id: '{rfc_id}'")
        path_manager = PathManager.get_instance()
        rfc_base = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        logger.info(f"RFC base path: {rfc_base}")
        
        # Strip common file extensions if present
        rfc_id_clean = rfc_id
        if rfc_id.endswith('.md'):
            rfc_id_clean = rfc_id[:-3]
        elif rfc_id.endswith('.json'):
            rfc_id_clean = rfc_id[:-5]
        logger.info(f"Cleaned RFC ID: '{rfc_id_clean}'")
        
        for status in ["in_progress", "archived"]:
            status_dir = rfc_base / status
            if not status_dir.exists():
                continue
            
            # Check all JSON metadata files
            for json_file in status_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                        
                    # Check if RFC ID, short name, or filename matches
                    filename_without_ext = json_file.stem
                    if (metadata.get("rfc_id") == rfc_id or 
                        metadata.get("rfc_id") == rfc_id_clean or
                        metadata.get("short_name") == rfc_id or
                        metadata.get("short_name") == rfc_id_clean or
                        filename_without_ext == rfc_id or
                        filename_without_ext == rfc_id_clean or
                        metadata.get("filename", "").replace(".md", "") == rfc_id or
                        metadata.get("filename", "").replace(".md", "") == rfc_id_clean):
                        
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
    
    def _load_prompt_guidelines(self) -> str:
        """Load plan generation guidelines."""
        try:
            prompt_path = Path(__file__).parent.parent.parent / "prompts" / "agents" / "rfc_to_plan.prompt.md"
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        
        # Fallback guidelines
        return """
## Plan Generation Guidelines

1. **Follow TDD Methodology**: Structure tasks in Red-Green-Refactor phases
2. **Task Granularity**: Each task should be 1-4 hours of work
3. **Clear Dependencies**: Specify which tasks depend on others
4. **Validation Criteria**: Include specific acceptance criteria from RFC
5. **Testing First**: Always start with test tasks before implementation
"""
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare RFC content for plan generation."""
        logger.info(f"prepare_plan_from_rfc called with arguments: {arguments}")
        rfc_id = arguments.get('rfc_id')
        plan_type = arguments.get('plan_type', 'initial')
        logger.info(f"Extracted rfc_id: '{rfc_id}', plan_type: '{plan_type}'")
        
        if not rfc_id:
            logger.error(f"RFC ID validation failed. rfc_id value: '{rfc_id}', type: {type(rfc_id)}")
            return {
                "error": "'rfc_id' is required.",
                "rfc_id": None,
                "prepared": False
            }
        
        try:
            # Find RFC
            logger.info(f"Calling _find_rfc with rfc_id: '{rfc_id}'")
            rfc_result = self._find_rfc(rfc_id)
            logger.info(f"_find_rfc returned: {rfc_result}")
            if not rfc_result:
                return {
                    "error": f"RFC '{rfc_id}' not found.",
                    "rfc_id": rfc_id,
                    "prepared": False
                }
            
            rfc_path, rfc_metadata = rfc_result
            
            # Read RFC content
            with open(rfc_path, 'r', encoding='utf-8') as f:
                rfc_content = f.read()
            
            # Calculate RFC hash for future change detection
            rfc_hash = self._calculate_rfc_hash(rfc_content)
            
            # Generate plan name
            plan_name = self._generate_plan_name(rfc_metadata)
            
            # Load guidelines
            guidelines = self._load_prompt_guidelines()
            
            # Prepare context information
            context = {
                "rfc_content": rfc_content,
                "rfc_metadata": rfc_metadata,
                "plan_name": plan_name,
                "plan_type": plan_type,
                "rfc_hash": rfc_hash,
                "guidelines": guidelines
            }
            
            # Create metadata for the agent to use when saving
            save_metadata = {
                "plan_name": plan_name,
                "rfc_id": rfc_metadata.get('rfc_id'),
                "rfc_hash": rfc_hash,
                "plan_type": plan_type
            }
            
            # Return structured information for the agent
            return {
                "prepared": True,
                "rfc_id": rfc_metadata.get('rfc_id'),
                "rfc_title": rfc_metadata.get('title', 'Unknown'),
                "rfc_short_name": rfc_metadata.get('short_name'),
                "rfc_content": rfc_content,
                "rfc_metadata": rfc_metadata,
                "rfc_hash": rfc_hash,
                "plan_name": plan_name,
                "plan_type": plan_type,
                "guidelines": guidelines,
                "save_metadata": save_metadata,
                "plan_schema": {
                    "plan_type": plan_type,
                    "title": "<from RFC>",
                    "description": "<from RFC>",
                    "agent_type": "planning",
                    "tdd_phases": {
                        "red": ["<test tasks>"],
                        "green": ["<implementation tasks>"],
                        "refactor": ["<improvement tasks>"]
                    },
                    "tasks": [
                        {
                            "name": "<task name>",
                            "description": "<task description>",
                            "agent_type": "<type>",
                            "dependencies": [],
                            "tdd_phase": "<phase>",
                            "validation_criteria": []
                        }
                    ],
                    "validation_criteria": ["<criteria>"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error preparing RFC for plan generation: {e}", exc_info=True)
            return {
                "error": f"Error preparing RFC: {str(e)}",
                "rfc_id": rfc_id,
                "prepared": False
            }