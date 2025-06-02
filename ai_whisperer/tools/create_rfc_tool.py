"""
Module: ai_whisperer/tools/create_rfc_tool.py
Purpose: AI tool implementation for create rfc

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- CreateRFCTool: Tool for creating new RFC documents from ideas.

Usage:
    tool = CreateRFCTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

Related:
- See PHASE_CONSOLIDATED_SUMMARY.md

"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import re

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager
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
                "short_name": {
                    "type": "string",
                    "description": "Short descriptive name for the RFC filename (e.g., 'dark-mode', 'api-auth', 'user-profiles'). Should be lowercase with hyphens, 2-4 words max.",
                    "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"
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
            "required": ["title", "summary", "short_name"]
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
            short_name="code-formatting",
            background="Developers want consistent code style",
            initial_requirements=["Support Python", "Support JavaScript", "Configurable"]
        )
        </tool_code>
        """
    
    def _generate_rfc_filename(self, short_name: str) -> tuple[str, str]:
        """Generate unique RFC filename and ID.
        
        Returns:
            tuple: (filename, rfc_id) where filename is like 'dark-mode-2025-05-31.md'
                   and rfc_id is like 'RFC-2025-05-31-0001'
        """
        now = datetime.now()
        date_part = now.strftime("%Y-%m-%d")
        
        # Clean the short name
        short_name = short_name.lower().strip()
        short_name = re.sub(r'[^a-z0-9-]', '-', short_name)
        short_name = re.sub(r'-+', '-', short_name).strip('-')
        
        # Find next available filename
        path_manager = PathManager.get_instance()
        rfc_base_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        
        counter = 1
        while True:
            if counter == 1:
                filename = f"{short_name}-{date_part}.md"
            else:
                filename = f"{short_name}-{date_part}-{counter}.md"
            
            rfc_id = f"RFC-{date_part}-{counter:04d}"
            
            # Check if this filename exists in any RFC folder
            exists = False
            for folder in ["in_progress", "archived"]:
                if (rfc_base_path / folder / filename).exists():
                    exists = True
                    break
            
            if not exists:
                return filename, rfc_id
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
        short_name = arguments.get('short_name')
        background = arguments.get('background', '*To be defined during refinement*')
        initial_requirements = arguments.get('initial_requirements', [])
        author = arguments.get('author', 'User')
        
        if not title:
            return "Error: 'title' is required."
        
        if not summary:
            return "Error: 'summary' is required."
        
        if not short_name:
            return "Error: 'short_name' is required."
        
        try:
            # Generate RFC filename and ID
            filename, rfc_id = self._generate_rfc_filename(short_name)
            
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
                status="in_progress",
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
            
            # Remove HTML comments from the content
            rfc_content = re.sub(r'<!--.*?-->', '', rfc_content, flags=re.DOTALL)
            # Clean up any extra blank lines left by comment removal
            rfc_content = re.sub(r'\n{3,}', '\n\n', rfc_content)
            
            # Save RFC file
            path_manager = PathManager.get_instance()
            rfc_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc" / "in_progress" / filename
            
            # Ensure directory exists
            rfc_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(rfc_path, 'w', encoding='utf-8') as f:
                f.write(rfc_content)
            
            # Create metadata file for easier querying
            metadata = {
                "rfc_id": rfc_id,
                "filename": filename,
                "short_name": short_name,
                "title": title,
                "status": "in_progress",
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
**Status**: in_progress
**Filename**: {filename}
**Location**: .WHISPER/rfc/in_progress/{filename}

The RFC has been created and is ready for refinement. You can now:
1. Add more requirements through discussion
2. Answer clarifying questions to improve the RFC
3. Research technical approaches
4. Archive with 'move_rfc' when refinement is complete

Next step: Use Agent P to refine this RFC through conversation."""
            
        except Exception as e:
            logger.error(f"Error creating RFC: {e}")
            return f"Error creating RFC: {str(e)}"
