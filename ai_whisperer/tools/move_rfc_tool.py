"""
Module: ai_whisperer/tools/move_rfc_tool.py
Purpose: AI tool implementation for move rfc

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- MoveRFCTool: Tool for moving RFC documents between status folders.

Usage:
    tool = MoveRFCTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- shutil

Related:
- See PHASE_CONSOLIDATED_SUMMARY.md

"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

class MoveRFCTool(AITool):
    """Tool for moving RFC documents between status folders."""
    
    @property
    def name(self) -> str:
        return "move_rfc"
    
    @property
    def description(self) -> str:
        return "Move an RFC document to a different status folder."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rfc_id": {
                    "type": "string",
                    "description": "The RFC ID (e.g., RFC-2025-05-29-0001)"
                },
                "target_status": {
                    "type": "string",
                    "description": "Target status folder",
                    "enum": ["new", "in_progress", "archived"]
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the status change",
                    "nullable": True
                }
            },
            "required": ["rfc_id", "target_status"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "RFC Management"
    
    @property
    def tags(self) -> List[str]:
        return ["rfc", "project_management", "planning", "workflow"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'move_rfc' tool to move RFC documents between status folders.
        Parameters:
        - rfc_id (string, required): RFC identifier
        - target_status (string, required): "in_progress" or "archived"
        - reason (string, optional): Reason for the move
        
        This tool manages RFC workflow transitions.
        Example usage:
        <tool_code>
        move_rfc(rfc_id="RFC-2025-05-29-0001", target_status="in_progress", reason="Starting refinement")
        move_rfc(rfc_id="RFC-2025-05-29-0001", target_status="archived", reason="Completed")
        </tool_code>
        """
    
    def _find_rfc_file(self, rfc_id: str) -> Optional[tuple[Path, str]]:
        """Find RFC file and return path and current status.
        
        Supports:
        1. Direct filename (e.g., RFC-2025-05-31-0001.md)
        2. RFC ID without extension (e.g., RFC-2025-05-31-0001)
        3. Search by rfc_id in JSON metadata files
        """
        path_manager = PathManager.get_instance()
        rfc_base_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        
        # Check each folder
        for folder in ["new", "in_progress", "archived"]:
            folder_path = rfc_base_path / folder
            if not folder_path.exists():
                continue
                
            # Method 1: Direct filename or with .md extension
            if rfc_id.endswith('.md'):
                rfc_path = folder_path / rfc_id
            else:
                rfc_path = folder_path / f"{rfc_id}.md"
            
            if rfc_path.exists():
                return rfc_path, folder
            
            # Method 2: Search through JSON metadata files
            for json_file in folder_path.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                        if metadata.get('rfc_id') == rfc_id:
                            # Found matching RFC ID in metadata
                            md_file = json_file.with_suffix('.md')
                            if md_file.exists():
                                return md_file, folder
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return None, None
    
    def _update_rfc_status(self, content: str, new_status: str) -> str:
        """Update status in RFC content."""
        import re
        
        # Update status field
        content = re.sub(
            r'(\*\*Status\*\*:\s*)([^\n]+)',
            f'\\1{new_status}',
            content
        )
        
        # Update last updated timestamp
        content = re.sub(
            r'(\*\*Last Updated\*\*:\s*)([^\n]+)',
            f'\\1{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            content
        )
        
        return content
    
    def _add_history_entry(self, content: str, old_status: str, new_status: str, reason: str) -> str:
        """Add status change to refinement history."""
        import re
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"- {timestamp}: Status changed from '{old_status}' to '{new_status}'"
        if reason:
            entry += f" - {reason}"
        
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
        """Execute RFC move."""
        rfc_id = arguments.get('rfc_id')
        target_status = arguments.get('target_status')
        reason = arguments.get('reason', '')
        
        if not rfc_id:
            return "Error: 'rfc_id' is required."
        if not target_status:
            return "Error: 'target_status' is required."
        
        try:
            # Find current RFC location
            current_path, current_status = self._find_rfc_file(rfc_id)
            if not current_path:
                return f"Error: RFC '{rfc_id}' not found."
            
            # Check if already in target status
            if current_status == target_status:
                return f"RFC '{rfc_id}' is already in '{target_status}' status."
            
            # Validate status transition
            valid_transitions = {
                'new': ['in_progress', 'archived'],
                'in_progress': ['archived', 'new'],  # Can move back to new if needed
                'archived': ['in_progress', 'new']   # Can reactivate
            }
            
            if target_status not in valid_transitions.get(current_status, []):
                return f"Error: Invalid transition from '{current_status}' to '{target_status}'."
            
            # Read RFC content
            with open(current_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update status in content
            content = self._update_rfc_status(content, target_status)
            
            # Add history entry
            content = self._add_history_entry(content, current_status, target_status, reason)
            
            # Determine target path
            path_manager = PathManager.get_instance()
            target_dir = Path(path_manager.workspace_path) / ".WHISPER" / "rfc" / target_status
            
            # Use the same filename as the source
            target_path = target_dir / current_path.name
            
            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Write updated content to new location
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Move metadata file if exists
            metadata_path = current_path.with_suffix('.json')
            if metadata_path.exists():
                target_metadata_path = target_path.with_suffix('.json')
                
                # Read metadata
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Update metadata
                metadata['status'] = target_status
                metadata['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                metadata['status_history'] = metadata.get('status_history', [])
                metadata['status_history'].append({
                    'from': current_status,
                    'to': target_status,
                    'timestamp': metadata['updated'],
                    'reason': reason
                })
                
                # Write to new location
                with open(target_metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Remove old metadata file
                metadata_path.unlink()
            
            # Remove old RFC file
            current_path.unlink()
            
            logger.info(f"Moved RFC {rfc_id} from '{current_status}' to '{target_status}'")
            
            # Generate appropriate message based on transition
            messages = {
                ('new', 'in_progress'): "The RFC is now in active refinement. Continue asking questions and updating sections.",
                ('new', 'archived'): "The RFC has been archived without refinement.",
                ('in_progress', 'archived'): "The RFC refinement is complete and has been archived.",
                ('in_progress', 'new'): "The RFC has been moved back to new status for reconsideration.",
                ('archived', 'in_progress'): "The RFC has been reactivated for further refinement.",
                ('archived', 'new'): "The RFC has been moved back to new status."
            }
            
            transition_msg = messages.get((current_status, target_status), "Status transition complete.")
            
            return f"""RFC moved successfully!

**RFC ID**: {rfc_id}
**Previous Status**: {current_status}
**New Status**: {target_status}
**New Location**: .WHISPER/rfc/{target_status}/{rfc_id}.md
{f'**Reason**: {reason}' if reason else ''}

{transition_msg}"""
            
        except Exception as e:
            logger.error(f"Error moving RFC {rfc_id}: {e}")
            return f"Error moving RFC: {str(e)}"
