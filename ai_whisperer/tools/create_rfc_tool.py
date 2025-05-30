"""
Create RFC Tool - Creates new RFC documents for feature refinement
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager
from ai_whisperer.exceptions import FileRestrictionError

logger = logging.getLogger(__name__)


class CreateRFCTool(AITool):
    """Tool for creating new RFC documents from ideas."""
    
    @property
    def name(self) -> str:
        return "create_rfc"
    
    @property
    def description(self) -> str:
        return "Create a new RFC document for feature refinement."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the RFC"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief overview of the feature/idea"
                },
                "background": {
                    "type": "string",
                    "description": "Context and motivation for this feature",
                    "nullable": True
                },
                "initial_requirements": {
                    "type": "array",
                    "description": "List of initial requirements",
                    "items": {"type": "string"},
                    "nullable": True
                },
                "author": {
                    "type": "string",
                    "description": "Author of the RFC",
                    "default": "User"
                }
            },
            "required": ["title", "summary"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "RFC Management"
    
    @property
    def tags(self) -> List[str]:
        return ["rfc", "project_management", "planning"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'create_rfc' tool to create new RFC documents for feature ideas.
        Parameters:
        - title (string, required): RFC title
        - summary (string, required): Brief overview
        - background (string, optional): Context and motivation
        - initial_requirements (array, optional): List of requirements
        - author (string, optional): Defaults to "User"
        
        This tool creates structured RFC documents for requirement refinement.
        Example usage:
        <tool_code>
        create_rfc(
            title="Add Code Formatting Feature",
            summary="Automatically format code files on save",
            background="Developers want consistent code style",
            initial_requirements=["Support Python", "Support JavaScript", "Configurable"]
        )
        </tool_code>
        """
    
    def _generate_rfc_id(self) -> str:
        """Generate unique RFC ID with format RFC-YYYY-MM-DD-XXXX."""
        now = datetime.now()
        date_part = now.strftime("%Y-%m-%d")
        
        # Find next available ID for today
        path_manager = PathManager.get_instance()
        rfc_base_path = Path(path_manager.workspace_path) / "rfc"
        
        counter = 1
        while True:
            rfc_id = f"RFC-{date_part}-{counter:04d}"
            # Check if this ID exists in any RFC folder
            exists = False
            for folder in ["new", "in_progress", "archived"]:
                if (rfc_base_path / folder / f"{rfc_id}.md").exists():
                    exists = True
                    break
            
            if not exists:
                return rfc_id
            counter += 1
    
    def _format_requirements(self, requirements: List[str]) -> str:
        """Format requirements as markdown checkboxes."""
        if not requirements:
            return "- [ ] *To be defined during refinement*"
        
        return "\n".join(f"- [ ] {req}" for req in requirements)
    
    def _load_template(self) -> str:
        """Load RFC template."""
        path_manager = PathManager.get_instance()
        template_path = Path(path_manager.workspace_path) / "templates" / "rfc_template.md"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Fallback template if file doesn't exist
            return """# RFC: {title}

**RFC ID**: {rfc_id}
**Status**: {status}
**Created**: {created_date}
**Last Updated**: {updated_date}
**Author**: {author}

## Summary
{summary}

## Background
{background}

## Requirements
{requirements}

## Technical Considerations
{technical_considerations}

## Implementation Approach
{implementation_approach}

## Open Questions
{open_questions}

## Acceptance Criteria
{acceptance_criteria}

## Related RFCs
{related_rfcs}

## Refinement History
{refinement_history}

---
*This RFC was created by AIWhisperer's Agent P (Patricia)*"""
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute RFC creation."""
        title = arguments.get('title')
        summary = arguments.get('summary')
        background = arguments.get('background', '*To be defined during refinement*')
        initial_requirements = arguments.get('initial_requirements', [])
        author = arguments.get('author', 'User')
        
        if not title:
            return "Error: 'title' is required."
        
        if not summary:
            return "Error: 'summary' is required."
        
        try:
            # Generate RFC ID
            rfc_id = self._generate_rfc_id()
            
            # Create timestamps
            now = datetime.now()
            created_date = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Format data
            requirements_formatted = self._format_requirements(initial_requirements)
            
            # Initial refinement history
            refinement_history = f"- {created_date}: RFC created with initial idea"
            
            # Load and populate template
            template = self._load_template()
            rfc_content = template.format(
                title=title,
                rfc_id=rfc_id,
                status="new",
                created_date=created_date,
                updated_date=created_date,
                author=author,
                summary=summary,
                background=background,
                requirements=requirements_formatted,
                technical_considerations="*To be defined during refinement*",
                implementation_approach="*To be defined during refinement*",
                open_questions="- [ ] *Questions will be added during refinement*",
                acceptance_criteria="*To be defined during refinement*",
                related_rfcs="*None identified yet*",
                refinement_history=refinement_history
            )
            
            # Save RFC file
            path_manager = PathManager.get_instance()
            rfc_path = Path(path_manager.workspace_path) / "rfc" / "new" / f"{rfc_id}.md"
            
            # Ensure directory exists
            rfc_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(rfc_path, 'w', encoding='utf-8') as f:
                f.write(rfc_content)
            
            # Create metadata file for easier querying
            metadata = {
                "rfc_id": rfc_id,
                "title": title,
                "status": "new",
                "created": created_date,
                "updated": created_date,
                "author": author
            }
            
            metadata_path = rfc_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Created RFC {rfc_id}: {title}")
            
            return f"""RFC created successfully!

**RFC ID**: {rfc_id}
**Title**: {title}
**Status**: new
**Location**: rfc/new/{rfc_id}.md

The RFC has been created and is ready for refinement. You can now:
1. Add more requirements through discussion
2. Answer clarifying questions to improve the RFC
3. Research technical approaches
4. Move to 'in_progress' when refinement begins

Next step: Use Agent P to refine this RFC through conversation."""
            
        except Exception as e:
            logger.error(f"Error creating RFC: {e}")
            return f"Error creating RFC: {str(e)}"