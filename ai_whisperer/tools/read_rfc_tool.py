"""
Read RFC Tool - Reads RFC documents and extracts information
"""
import os
import logging
import re
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class ReadRFCTool(AITool):
    """Tool for reading RFC documents and extracting structured information."""
    
    @property
    def name(self) -> str:
        return "read_rfc"
    
    @property
    def description(self) -> str:
        return "Read RFC document content and extract structured information."
    
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
                    "description": "Specific section to extract (optional)",
                    "enum": ["summary", "background", "requirements", "technical", "questions", "all"],
                    "nullable": True
                }
            },
            "required": ["rfc_id"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "RFC Management"
    
    @property
    def tags(self) -> List[str]:
        return ["rfc", "project_management", "planning"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'read_rfc' tool to read RFC documents and extract information.
        Parameters:
        - rfc_id (string, required): RFC identifier (e.g., RFC-2025-05-29-0001)
        - section (string, optional): Specific section to extract
          Options: "summary", "background", "requirements", "technical", "questions", "all"
        
        This tool reads and parses RFC documents for review and refinement.
        Example usage:
        <tool_code>
        read_rfc(rfc_id="RFC-2025-05-29-0001")
        read_rfc(rfc_id="RFC-2025-05-29-0001", section="requirements")
        </tool_code>
        """
    
    def _find_rfc_file(self, rfc_id: str) -> Optional[Path]:
        """Find RFC file by RFC ID or filename."""
        path_manager = PathManager.get_instance()
        rfc_base_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        
        # Check each folder
        for folder in ["in_progress", "archived"]:
            folder_path = rfc_base_path / folder
            if not folder_path.exists():
                continue
                
            # First try direct filename match
            if rfc_id.endswith('.md'):
                rfc_path = folder_path / rfc_id
                if rfc_path.exists():
                    return rfc_path
            else:
                # Try with .md extension
                rfc_path = folder_path / f"{rfc_id}.md"
                if rfc_path.exists():
                    return rfc_path
            
            # Search for files containing the RFC ID in metadata
            for file_path in folder_path.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        metadata = json.load(f)
                        if metadata.get('rfc_id') == rfc_id:
                            return file_path.with_suffix('.md')
                except:
                    continue
        
        return None
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a specific section from RFC content."""
        # Define section headers
        section_headers = {
            "summary": "## Summary",
            "background": "## Background",
            "requirements": "## Requirements",
            "technical": "## Technical Considerations",
            "questions": "## Open Questions",
            "approach": "## Implementation Approach",
            "criteria": "## Acceptance Criteria",
            "history": "## Refinement History"
        }
        
        # Map requested section to header
        if section_name == "technical":
            header = section_headers["technical"]
        elif section_name == "questions":
            header = section_headers["questions"]
        else:
            header = section_headers.get(section_name, f"## {section_name.title()}")
        
        # Find section start
        pattern = re.compile(rf'^{re.escape(header)}$', re.MULTILINE | re.IGNORECASE)
        match = pattern.search(content)
        
        if not match:
            return f"*Section '{section_name}' not found*"
        
        start_pos = match.end()
        
        # Find next section (any line starting with ##)
        next_section_pattern = re.compile(r'^##\s+', re.MULTILINE)
        next_match = next_section_pattern.search(content, start_pos)
        
        if next_match:
            end_pos = next_match.start()
        else:
            # Look for the footer marker
            footer_pattern = re.compile(r'^---', re.MULTILINE)
            footer_match = footer_pattern.search(content, start_pos)
            if footer_match:
                end_pos = footer_match.start()
            else:
                end_pos = len(content)
        
        section_content = content[start_pos:end_pos].strip()
        return section_content if section_content else "*Section is empty*"
    
    def _parse_metadata(self, content: str) -> Dict[str, str]:
        """Extract metadata from RFC header."""
        metadata = {}
        
        # Extract RFC ID
        rfc_id_match = re.search(r'\*\*RFC ID\*\*:\s*(.+)', content)
        if rfc_id_match:
            metadata['rfc_id'] = rfc_id_match.group(1).strip()
        
        # Extract Status
        status_match = re.search(r'\*\*Status\*\*:\s*(.+)', content)
        if status_match:
            metadata['status'] = status_match.group(1).strip()
        
        # Extract dates
        created_match = re.search(r'\*\*Created\*\*:\s*(.+)', content)
        if created_match:
            metadata['created'] = created_match.group(1).strip()
        
        updated_match = re.search(r'\*\*Last Updated\*\*:\s*(.+)', content)
        if updated_match:
            metadata['updated'] = updated_match.group(1).strip()
        
        # Extract author
        author_match = re.search(r'\*\*Author\*\*:\s*(.+)', content)
        if author_match:
            metadata['author'] = author_match.group(1).strip()
        
        # Extract title
        title_match = re.search(r'^# RFC:\s*(.+)', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        return metadata
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute RFC reading."""
        rfc_id = arguments.get('rfc_id')
        section = arguments.get('section')
        
        if not rfc_id:
            return "Error: 'rfc_id' is required."
        
        try:
            # Find RFC file
            rfc_path = self._find_rfc_file(rfc_id)
            
            if not rfc_path:
                return f"Error: RFC '{rfc_id}' not found in any RFC folder (new, in_progress, archived)."
            
            # Read content
            with open(rfc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse metadata
            metadata = self._parse_metadata(content)
            
            # Check for metadata JSON file
            metadata_path = rfc_path.with_suffix('.json')
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    json_metadata = json.load(f)
                    metadata.update(json_metadata)
            
            # Determine folder location
            folder = rfc_path.parent.name
            
            # Build response
            response = f"**RFC Found**: {rfc_id}\n"
            response += f"**Location**: .WHISPER/rfc/{folder}/{rfc_id}.md\n"
            response += f"**Title**: {metadata.get('title', 'Unknown')}\n"
            response += f"**Status**: {metadata.get('status', 'Unknown')}\n"
            response += f"**Author**: {metadata.get('author', 'Unknown')}\n"
            response += f"**Created**: {metadata.get('created', 'Unknown')}\n"
            response += f"**Last Updated**: {metadata.get('updated', 'Unknown')}\n"
            response += "\n" + "-" * 50 + "\n\n"
            
            # Extract requested section or full content
            if section and section != "all":
                response += f"## {section.title()} Section\n\n"
                response += self._extract_section(content, section)
            else:
                # Return full content
                response += content
            
            return response
            
        except Exception as e:
            logger.error(f"Error reading RFC {rfc_id}: {e}")
            return f"Error reading RFC: {str(e)}"