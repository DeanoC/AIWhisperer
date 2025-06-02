"""
Module: ai_whisperer/tools/list_rfcs_tool.py
Purpose: AI tool implementation for list rfcs

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- ListRFCsTool: Tool for listing RFC documents with filtering options.

Usage:
    tool = ListRFCsTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

Related:
- See PHASE_CONSOLIDATED_SUMMARY.md

"""

import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

class ListRFCsTool(AITool):
    """Tool for listing RFC documents with filtering options."""
    
    @property
    def name(self) -> str:
        return "list_rfcs"
    
    @property
    def description(self) -> str:
        return "List RFC documents by status or other criteria."
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by RFC status",
                    "enum": ["in_progress", "archived", "all"],
                    "default": "in_progress"
                },
                "sort_by": {
                    "type": "string",
                    "description": "Sort criteria",
                    "enum": ["created", "updated", "title", "id"],
                    "default": "created"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of RFCs to return",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                }
            }
        }
    
    @property
    def category(self) -> Optional[str]:
        return "RFC Management"
    
    @property
    def tags(self) -> List[str]:
        return ["rfc", "project_management", "planning"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the 'list_rfcs' tool to list RFC documents with filtering options.
        Parameters:
        - status (string, optional): Filter by status ("in_progress", "archived", "all") - defaults to "in_progress"
        - sort_by (string, optional): Sort by "created", "updated", "title", or "id"
        - limit (integer, optional): Maximum RFCs to return (default: 20)
        
        This tool helps browse and find RFC documents.
        Example usage:
        <tool_code>
        list_rfcs()  # List all RFCs
        list_rfcs(status="new")  # List only new RFCs
        list_rfcs(status="in_progress", sort_by="updated")
        </tool_code>
        """
    
    def _get_rfc_metadata(self, rfc_path: Path) -> Dict[str, Any]:
        """Extract metadata from RFC file or metadata JSON."""
        metadata = {
            "rfc_id": rfc_path.stem,
            "filename": rfc_path.name,
            "title": "Unknown",
            "status": rfc_path.parent.name,
            "created": "Unknown",
            "updated": "Unknown",
            "author": "Unknown"
        }
        
        # Try to read metadata JSON first
        metadata_path = rfc_path.with_suffix('.json')
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    json_metadata = json.load(f)
                    metadata.update(json_metadata)
            except Exception as e:
                logger.debug(f"Could not read metadata JSON for {rfc_path}: {e}")
        
        # If no JSON or missing data, parse from markdown
        if metadata["title"] == "Unknown" or metadata["created"] == "Unknown":
            try:
                with open(rfc_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Read first 1000 chars for metadata
                
                # Extract title
                import re
                title_match = re.search(r'^# RFC:\s*(.+)', content, re.MULTILINE)
                if title_match:
                    metadata['title'] = title_match.group(1).strip()
                
                # Extract other metadata
                created_match = re.search(r'\*\*Created\*\*:\s*(.+)', content)
                if created_match:
                    metadata['created'] = created_match.group(1).strip()
                
                updated_match = re.search(r'\*\*Last Updated\*\*:\s*(.+)', content)
                if updated_match:
                    metadata['updated'] = updated_match.group(1).strip()
                
                author_match = re.search(r'\*\*Author\*\*:\s*(.+)', content)
                if author_match:
                    metadata['author'] = author_match.group(1).strip()
                    
            except Exception as e:
                logger.debug(f"Could not parse metadata from {rfc_path}: {e}")
        
        # Get file modification time as fallback
        try:
            stat = rfc_path.stat()
            if metadata['updated'] == "Unknown":
                metadata['updated'] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            if metadata['created'] == "Unknown":
                metadata['created'] = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
        
        return metadata
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string with fallback."""
        if date_str == "Unknown":
            return datetime.min
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # Fallback
        return datetime.min
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute RFC listing."""
        status_filter = arguments.get('status', 'in_progress')
        sort_by = arguments.get('sort_by', 'created')
        limit = arguments.get('limit', 20)
        
        try:
            path_manager = PathManager.get_instance()
            rfc_base_path = Path(path_manager.workspace_path) / ".WHISPER" / "rfc"
            
            # Determine which folders to search
            if status_filter == 'all':
                folders = ['in_progress', 'archived']
            else:
                folders = [status_filter]
            
            # Collect all RFCs
            rfcs = []
            for folder in folders:
                folder_path = rfc_base_path / folder
                if folder_path.exists():
                    for rfc_file in folder_path.glob("*.md"):
                        metadata = self._get_rfc_metadata(rfc_file)
                        rfcs.append(metadata)
            
            # Sort RFCs
            if sort_by == 'created':
                rfcs.sort(key=lambda x: self._parse_datetime(x['created']), reverse=True)
            elif sort_by == 'updated':
                rfcs.sort(key=lambda x: self._parse_datetime(x['updated']), reverse=True)
            elif sort_by == 'title':
                rfcs.sort(key=lambda x: x['title'].lower())
            elif sort_by == 'id':
                rfcs.sort(key=lambda x: x['rfc_id'])
            
            # Apply limit
            rfcs = rfcs[:limit]
            
            # Format response
            if not rfcs:
                return f"No RFCs found with status filter: {status_filter}"
            
            response = f"**RFC List** (Status: {status_filter}, Sort: {sort_by})\n"
            response += f"Found {len(rfcs)} RFC(s)\n\n"
            
            # Group by status for better display
            status_groups = {}
            for rfc in rfcs:
                status = rfc['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(rfc)
            
            # Display by status group
            for status in ['in_progress', 'archived']:
                if status in status_groups:
                    response += f"\n## {status.replace('_', ' ').title()}\n\n"
                    for rfc in status_groups[status]:
                        response += f"**{rfc['filename']}**\n"
                        response += f"  - Title: {rfc['title']}\n"
                        response += f"  - RFC ID: {rfc['rfc_id']}\n"
                        response += f"  - Author: {rfc['author']}\n"
                        response += f"  - Created: {rfc['created']}\n"
                        response += f"  - Updated: {rfc['updated']}\n\n"
            
            response += "\n" + "-" * 50 + "\n"
            response += "Use `read_rfc(rfc_id=\"filename\" or rfc_id=\"RFC-XXXX-XX-XX-XXXX\")` to view details"
            
            return response
            
        except Exception as e:
            logger.error(f"Error listing RFCs: {e}")
            return f"Error listing RFCs: {str(e)}"
