"""
Module: ai_whisperer/tools/claude/claude_set_toolset_tool.py
Purpose: Claude CLI tool to manage custom toolset

This tool allows Claude CLI to customize which tools it has direct
access to, building a personalized toolkit over time.

Part of the hybrid-hybrid system that balances context usage with
functionality.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class ClaudeSetToolsetTool(AITool):
    """Claude CLI's tool for managing custom toolset."""
    
    SETTINGS_FILE = Path.home() / ".aiwhisperer" / "claude_tools_settings.json"
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "claude_set_toolset"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Manage Claude's custom toolset - add, remove, or list tools"
    
    @property
    def parameters_schema(self) -> dict:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "remove", "set", "list", "clear"],
                    "description": "Action to perform on toolset"
                },
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tool names to add/remove/set (not needed for list/clear)"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the change (optional)"
                }
            },
            "required": ["action"]
        }
    
    @property
    def category(self) -> str:
        """Return the tool category."""
        return "Claude"
    
    @property
    def tags(self) -> list:
        """Return the tool tags."""
        return ["claude", "tools", "configuration", "customization"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for Claude on how to use this tool."""
        return """Use claude_set_toolset to manage your custom tool collection.

Actions:
- list: Show current custom tools
- add: Add tools to your set
- remove: Remove tools from your set  
- set: Replace entire toolset
- clear: Remove all custom tools

Examples:
- List current: claude_set_toolset(action="list")
- Add tools: claude_set_toolset(action="add", tools=["read_file", "write_file", "execute_command"])
- Remove tool: claude_set_toolset(action="remove", tools=["debug_tool"])
- Set new toolset: claude_set_toolset(action="set", tools=["read_file", "search_files"], reason="Simplified toolset for code review")
- Clear all: claude_set_toolset(action="clear", reason="Starting fresh")

Your custom toolset persists across sessions. Build it based on your common tasks.
"""
    
    def _load_settings(self) -> dict:
        """Load Claude tools settings."""
        if self.SETTINGS_FILE.exists():
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        
        return {
            "all_tools_enabled": False,
            "custom_tools": [],
            "audit_trail": []
        }
    
    def _save_settings(self, settings: dict) -> None:
        """Save Claude tools settings."""
        self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def _get_available_tools(self, context) -> List[str]:
        """Get list of available tools from registry."""
        try:
            if context and hasattr(context, 'tool_registry'):
                return list(context.tool_registry.list_tools().keys())
            else:
                # Fallback - would be populated from actual registry
                return []
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            return []
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to manage custom toolset."""
        # Handle both direct kwargs and arguments pattern
        if 'arguments' in kwargs and isinstance(kwargs['arguments'], dict):
            actual_args = kwargs['arguments']
        else:
            actual_args = kwargs
        
        action = actual_args.get('action', '').lower()
        tools = actual_args.get('tools', [])
        reason = actual_args.get('reason', '')
        
        if not action:
            return {
                "success": False,
                "error": "Action is required (add/remove/set/list/clear)"
            }
        
        try:
            # Load current settings
            settings = self._load_settings()
            current_tools = settings.get('custom_tools', [])
            
            # Get context for available tools
            context = kwargs.get('_context')
            
            if action == 'list':
                return {
                    "success": True,
                    "action": "list",
                    "custom_tools": current_tools,
                    "tool_count": len(current_tools),
                    "all_tools_enabled": settings.get('all_tools_enabled', False)
                }
            
            elif action == 'add':
                if not tools:
                    return {
                        "success": False,
                        "error": "Tools list required for add action"
                    }
                
                # Add new tools (avoid duplicates)
                new_tools = list(set(current_tools + tools))
                added = [t for t in tools if t not in current_tools]
                
                settings['custom_tools'] = new_tools
                
            elif action == 'remove':
                if not tools:
                    return {
                        "success": False,
                        "error": "Tools list required for remove action"
                    }
                
                # Remove specified tools
                new_tools = [t for t in current_tools if t not in tools]
                removed = [t for t in tools if t in current_tools]
                
                settings['custom_tools'] = new_tools
                
            elif action == 'set':
                if not tools:
                    return {
                        "success": False,
                        "error": "Tools list required for set action"
                    }
                
                # Replace entire toolset
                settings['custom_tools'] = list(set(tools))
                
            elif action == 'clear':
                settings['custom_tools'] = []
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
            
            # Add audit trail entry for changes
            if action != 'list':
                from datetime import datetime
                settings.setdefault('audit_trail', []).append({
                    'timestamp': datetime.now().isoformat(),
                    'action': f'toolset_{action}',
                    'tools': tools,
                    'reason': reason,
                    'previous_count': len(current_tools),
                    'new_count': len(settings['custom_tools'])
                })
                
                # Keep only last 50 audit entries
                settings['audit_trail'] = settings['audit_trail'][-50:]
                
                # Save settings
                self._save_settings(settings)
            
            # Prepare response
            result = {
                "success": True,
                "action": action,
                "custom_tools": settings['custom_tools'],
                "tool_count": len(settings['custom_tools']),
                "reason": reason
            }
            
            if action == 'add':
                result['added'] = added
                result['already_present'] = [t for t in tools if t not in added]
            elif action == 'remove':
                result['removed'] = removed
                result['not_found'] = [t for t in tools if t not in removed]
            
            return result
            
        except Exception as e:
            logger.error(f"Error managing toolset: {e}")
            return {
                "success": False,
                "error": f"Failed to manage toolset: {str(e)}"
            }