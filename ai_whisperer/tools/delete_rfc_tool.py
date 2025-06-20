"""
Module: ai_whisperer/tools/delete_rfc_tool.py
Purpose: AI tool implementation for delete rfc

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- DeleteRFCTool: Tool for deleting RFC documents.

Usage:
    tool = DeleteRFCTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)


class DeleteRFCTool(AITool):
    """Tool for deleting RFC documents."""
    
    @property
    def name(self) -> str:
        return "delete_rfc"
    
    @property
    def description(self) -> str:
        return "Delete an RFC document permanently."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rfc_id": {
                    "type": "string",
                    "description": "The RFC ID to delete (e.g., RFC-2025-05-29-0001)"
                },
                "confirm_delete": {
                    "type": "boolean",
                    "description": "Confirmation flag - must be true to delete",
                    "default": False
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for deletion",
                    "nullable": True
                }
            },
            "required": ["rfc_id", "confirm_delete"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "RFC Management"
    
    @property
    def tags(self) -> List[str]:
        return ["rfc", "project_management", "planning", "dangerous"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'delete_rfc' tool to permanently delete RFC documents.
        
        IMPORTANT: This action is PERMANENT and cannot be undone!
        
        Parameters:
        - rfc_id (string, required): RFC identifier to delete
        - confirm_delete (boolean, required): Must be true to proceed with deletion
        - reason (string, optional): Reason for deletion
        
        Before using this tool:
        1. ALWAYS ask the user to confirm they want to delete the RFC
        2. Explain that this action is permanent
        3. Consider if archiving might be more appropriate
        
        Example usage:
        <tool_code>
        delete_rfc(
            rfc_id="RFC-2025-05-29-0001",
            confirm_delete=true,
            reason="Duplicate RFC, content merged into RFC-2025-05-29-0002"
        )
        </tool_code>
        """
    
    def _find_rfc(self, rfc_id: str) -> Optional[Path]:
        """Find RFC file in any status folder.
        
        Supports:
        1. Direct filename (e.g., RFC-2025-05-31-0001.md)
        2. RFC ID without extension (e.g., RFC-2025-05-31-0001)
        3. Search by rfc_id in JSON metadata files
        """
        path_manager = PathManager.get_instance()
        rfc_base_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
        
        # Check each folder
        for folder in ["in_progress", "archived"]:
            folder_path = rfc_base_path / folder
            if not folder_path.exists():
                continue
                
            # Method 1: Direct filename or with .md extension
            if rfc_id.endswith('.md'):
                rfc_path = folder_path / rfc_id
            else:
                rfc_path = folder_path / f"{rfc_id}.md"
            
            if rfc_path.exists():
                return rfc_path
            
            # Method 2: Search through JSON metadata files
            for json_file in folder_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        if metadata.get('rfc_id') == rfc_id:
                            # Found matching RFC ID in metadata
                            md_file = json_file.with_suffix('.md')
                            if md_file.exists():
                                return md_file
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return None
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RFC deletion."""
        rfc_id = arguments.get('rfc_id')
        confirm_delete = arguments.get('confirm_delete', False)
        reason = arguments.get('reason', 'No reason provided')
        
        if not rfc_id:
            return {
                "error": "'rfc_id' is required.",
                "rfc_id": None,
                "deleted": False
            }
        
        if not confirm_delete:
            return {
                "error": "Delete operation cancelled. Must set confirm_delete=true after user confirmation.",
                "rfc_id": rfc_id,
                "deleted": False,
                "message": "This action is PERMANENT and cannot be undone.",
                "requirements": [
                    "Get user confirmation",
                    "Set confirm_delete=true"
                ]
            }
        
        try:
            # Find the RFC
            rfc_path = self._find_rfc(rfc_id)
            if not rfc_path:
                return {
                    "error": f"RFC {rfc_id} not found in any folder.",
                    "rfc_id": rfc_id,
                    "deleted": False
                }
            
            # Also find metadata file
            metadata_path = rfc_path.with_suffix('.json')
            
            # Store some info before deletion
            folder_name = rfc_path.parent.name
            
            # Delete the files
            files_deleted = []
            
            if rfc_path.exists():
                os.remove(rfc_path)
                files_deleted.append(f"{folder_name}/{rfc_id}.md")
            
            if metadata_path.exists():
                os.remove(metadata_path)
                files_deleted.append(f"{folder_name}/{rfc_id}.json")
            
            logger.info(f"Deleted RFC {rfc_id}: {reason}")
            
            return {
                "deleted": True,
                "rfc_id": rfc_id,
                "previous_status": folder_name,
                "files_deleted": files_deleted,
                "file_count": len(files_deleted),
                "reason": reason,
                "message": "This action is permanent and cannot be undone.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error deleting RFC {rfc_id}: {e}")
            return {
                "error": f"Error deleting RFC: {str(e)}",
                "rfc_id": rfc_id,
                "deleted": False
            }