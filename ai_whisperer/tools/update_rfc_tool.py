"""
Update RFC Tool - Updates existing RFC documents
"""
import os
import logging
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class UpdateRFCTool(AITool):
    """Tool for updating existing RFC documents during refinement."""
    
    @property
    def name(self) -> str:
        return "update_rfc"
    
    @property
    def description(self) -> str:
        return "Update an existing RFC document with new information."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rfc_id": {
                    "type": "string",
                    "description": "The RFC ID (e.g., RFC-2025-05-29-0001)"
                },
                "section": {
                    "type": "string",
                    "description": "Section to update",
                    "enum": ["summary", "background", "requirements", "technical_considerations", 
                            "implementation_approach", "open_questions", "acceptance_criteria", 
                            "related_rfcs", "title"]
                },
                "content": {
                    "type": "string",
                    "description": "New content for the section"
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to existing content instead of replacing",
                    "default": False
                },
                "history_note": {
                    "type": "string",
                    "description": "Note to add to refinement history",
                    "nullable": True
                }
            },
            "required": ["rfc_id", "section", "content"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "RFC Management"
    
    @property
    def tags(self) -> List[str]:
        return ["rfc", "project_management", "planning"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'update_rfc' tool to update sections of existing RFC documents.
        Parameters:
        - rfc_id (string, required): RFC identifier
        - section (string, required): Section to update
        - content (string, required): New content
        - append (boolean, optional): Append instead of replace (default: false)
        - history_note (string, optional): Note for refinement history
        
        Sections: summary, background, requirements, technical_considerations,
        implementation_approach, open_questions, acceptance_criteria, related_rfcs, title
        
        Example usage:
        <tool_code>
        update_rfc(
            rfc_id="RFC-2025-05-29-0001",
            section="requirements",
            content="- [ ] Support Python 3.8+\\n- [ ] Add type hints",
            append=True
        )
        </tool_code>
        """
    
    def _find_rfc_file(self, rfc_id: str) -> Optional[Path]:
        """Find RFC file in any of the RFC folders."""
        path_manager = PathManager.get_instance()
        rfc_base_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        
        # Check each folder
        for folder in ["in_progress", "archived"]:
            rfc_path = rfc_base_path / folder / f"{rfc_id}.md"
            if rfc_path.exists():
                return rfc_path
        
        return None
    
    def _read_rfc_content(self, rfc_path: Path) -> str:
        """Read RFC content."""
        with open(rfc_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _write_rfc_content(self, rfc_path: Path, content: str):
        """Write RFC content."""
        with open(rfc_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _update_metadata(self, rfc_path: Path, updates: Dict[str, Any]):
        """Update RFC metadata JSON file."""
        metadata_path = rfc_path.with_suffix('.json')
        
        # Read existing metadata
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Update
        metadata.update(updates)
        metadata['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write back
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _update_section(self, content: str, section: str, new_content: str, append: bool) -> str:
        """Update a specific section in the RFC content."""
        section_headers = {
            'summary': '## Summary',
            'background': '## Background',
            'requirements': '## Requirements',
            'technical_considerations': '## Technical Considerations',
            'implementation_approach': '## Implementation Approach',
            'open_questions': '## Open Questions',
            'acceptance_criteria': '## Acceptance Criteria',
            'related_rfcs': '## Related RFCs',
            'title': '# RFC:'
        }
        
        header = section_headers.get(section)
        if not header:
            raise ValueError(f"Unknown section: {section}")
        
        # Special handling for title
        if section == 'title':
            # Update title in header
            title_pattern = r'^# RFC:\s*(.+)$'
            if re.search(title_pattern, content, re.MULTILINE):
                return re.sub(title_pattern, f'# RFC: {new_content}', content, flags=re.MULTILINE)
            else:
                return content  # Title not found
        
        # Find section boundaries
        header_pattern = re.compile(rf'^{re.escape(header)}$', re.MULTILINE)
        match = header_pattern.search(content)
        
        if not match:
            # Section doesn't exist, add it before refinement history
            history_pattern = re.compile(r'^## Refinement History$', re.MULTILINE)
            history_match = history_pattern.search(content)
            
            if history_match:
                insert_pos = history_match.start()
                new_section = f"\n{header}\n{new_content}\n"
                return content[:insert_pos] + new_section + content[insert_pos:]
            else:
                # Add at end
                return content + f"\n\n{header}\n{new_content}\n"
        
        # Find next section
        start_pos = match.end()
        next_section_pattern = re.compile(r'^##\s+', re.MULTILINE)
        next_match = next_section_pattern.search(content, start_pos)
        
        if next_match:
            end_pos = next_match.start()
        else:
            # Check for footer
            footer_pattern = re.compile(r'^---', re.MULTILINE)
            footer_match = footer_pattern.search(content, start_pos)
            if footer_match:
                end_pos = footer_match.start()
            else:
                end_pos = len(content)
        
        # Extract current section content
        current_content = content[start_pos:end_pos].strip()
        
        # Update content
        if append and current_content:
            # Remove placeholder text if present
            if "*To be defined during refinement*" in current_content:
                current_content = current_content.replace("*To be defined during refinement*", "").strip()
            
            # Append with proper formatting
            if current_content and not current_content.endswith('\n'):
                updated_content = current_content + '\n' + new_content
            else:
                updated_content = current_content + new_content
        else:
            # When replacing, just use new content
            updated_content = new_content
        
        # Rebuild content
        return content[:match.end()] + '\n' + updated_content + '\n' + content[end_pos:]
    
    def _add_history_entry(self, content: str, note: str) -> str:
        """Add entry to refinement history."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"- {timestamp}: {note}"
        
        # Find history section
        history_pattern = re.compile(r'^## Refinement History$', re.MULTILINE)
        match = history_pattern.search(content)
        
        if match:
            # Find position to insert (after header)
            insert_pos = content.find('\n', match.end()) + 1
            return content[:insert_pos] + entry + '\n' + content[insert_pos:]
        else:
            # No history section, add it
            return content + f"\n\n## Refinement History\n{entry}\n"
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute RFC update."""
        rfc_id = arguments.get('rfc_id')
        section = arguments.get('section')
        new_content = arguments.get('content')
        append = arguments.get('append', False)
        history_note = arguments.get('history_note')
        
        if not rfc_id:
            return "Error: 'rfc_id' is required."
        if not section:
            return "Error: 'section' is required."
        if not new_content:
            return "Error: 'content' is required."
        
        try:
            # Find RFC file
            rfc_path = self._find_rfc_file(rfc_id)
            if not rfc_path:
                return f"Error: RFC '{rfc_id}' not found."
            
            # Read current content
            content = self._read_rfc_content(rfc_path)
            
            # Update section
            updated_content = self._update_section(content, section, new_content, append)
            
            # Update timestamp in header
            updated_content = re.sub(
                r'(\*\*Last Updated\*\*:\s*)([^\n]+)',
                f'\\1{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                updated_content
            )
            
            # Add history entry
            if not history_note:
                if section == 'title':
                    history_note = "Updated RFC title"
                else:
                    action = "Added to" if append else "Updated"
                    history_note = f"{action} {section.replace('_', ' ')} section"
            
            updated_content = self._add_history_entry(updated_content, history_note)
            
            # Write back
            self._write_rfc_content(rfc_path, updated_content)
            
            # Update metadata
            metadata_updates = {
                'last_updated_section': section,
                'last_updated_by': 'Agent P'
            }
            if section == 'title':
                metadata_updates['title'] = new_content
            
            self._update_metadata(rfc_path, metadata_updates)
            
            logger.info(f"Updated RFC {rfc_id} section '{section}'")
            
            return f"""RFC updated successfully!

**RFC ID**: {rfc_id}
**Section**: {section.replace('_', ' ').title()}
**Action**: {'Appended to' if append else 'Replaced'} content
**Location**: {rfc_path.parent.name}/{rfc_id}.md

The RFC has been updated. You can:
1. Continue refining other sections
2. Review the changes with `read_rfc`
3. Move to 'in_progress' when ready"""
            
        except Exception as e:
            logger.error(f"Error updating RFC {rfc_id}: {e}")
            return f"Error updating RFC: {str(e)}"