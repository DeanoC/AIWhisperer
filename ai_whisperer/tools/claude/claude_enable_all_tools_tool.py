"""
Module: ai_whisperer/tools/claude/claude_enable_all_tools_tool.py
Purpose: Claude CLI tool to enable/disable access to all AIWhisperer tools

This tool provides Claude CLI with emergency access to all tools when
needed (e.g., when Debbie is broken). Part of the hybrid-hybrid system.

The setting persists across sessions to handle recovery scenarios.
"""

import json
import logging
from pathlib import Path
from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class ClaudeEnableAllToolsTool(AITool):
    """Claude CLI's tool for enabling/disabling access to all tools."""
    
    SETTINGS_FILE = Path.home() / ".aiwhisperer" / "claude_tools_settings.json"
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "claude_enable_all_tools"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Enable or disable Claude's access to all AIWhisperer tools (emergency access)"
    
    @property
    def parameters_schema(self) -> dict:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "enable": {
                    "type": "boolean",
                    "description": "True to enable all tools, False to disable"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for enabling/disabling (for audit trail)"
                }
            },
            "required": ["enable"]
        }
    
    @property
    def category(self) -> str:
        """Return the tool category."""
        return "Claude"
    
    @property
    def tags(self) -> list:
        """Return the tool tags."""
        return ["claude", "tools", "emergency", "configuration"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for Claude on how to use this tool."""
        return """Use claude_enable_all_tools for emergency access to all AIWhisperer tools.

This should only be used when:
- Debbie is broken and you need to fix the system
- You need temporary access to tools not in your custom set
- Recovery scenarios where mailbox communication isn't working

Usage:
- Enable: claude_enable_all_tools(enable=true, reason="Debbie not responding, need to debug")
- Disable: claude_enable_all_tools(enable=false, reason="Recovery complete, returning to normal mode")

WARNING: Having all tools enabled uses significant context. Disable when done.
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
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to enable/disable all tools."""
        # Handle both direct kwargs and arguments pattern
        if 'arguments' in kwargs and isinstance(kwargs['arguments'], dict):
            actual_args = kwargs['arguments']
        else:
            actual_args = kwargs
        
        enable = actual_args.get('enable', False)
        reason = actual_args.get('reason', 'No reason provided')
        
        try:
            # Load current settings
            settings = self._load_settings()
            
            # Update settings
            old_state = settings.get('all_tools_enabled', False)
            settings['all_tools_enabled'] = enable
            
            # Add audit trail entry
            from datetime import datetime
            settings.setdefault('audit_trail', []).append({
                'timestamp': datetime.now().isoformat(),
                'action': 'enabled' if enable else 'disabled',
                'reason': reason,
                'changed_from': old_state
            })
            
            # Keep only last 50 audit entries
            settings['audit_trail'] = settings['audit_trail'][-50:]
            
            # Save settings
            self._save_settings(settings)
            
            # Get context to trigger tool registry update
            context = kwargs.get('_context')
            if context and hasattr(context, 'session'):
                # This would trigger a tool registry refresh in a real implementation
                # For now, we'll just log it
                logger.info(f"Claude all tools access {'enabled' if enable else 'disabled'}")
            
            return {
                "success": True,
                "all_tools_enabled": enable,
                "previous_state": old_state,
                "reason": reason,
                "message": f"All tools access {'enabled' if enable else 'disabled'}. "
                          f"{'WARNING: High context usage. Disable when done.' if enable else 'Returned to normal mode.'}"
            }
            
        except Exception as e:
            logger.error(f"Error updating tool access: {e}")
            return {
                "success": False,
                "error": f"Failed to update tool access: {str(e)}"
            }