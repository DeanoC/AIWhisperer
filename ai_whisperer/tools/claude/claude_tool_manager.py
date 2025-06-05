"""
Module: ai_whisperer/tools/claude/claude_tool_manager.py
Purpose: Manager for Claude CLI tool access

This module manages which tools are available to Claude CLI based on
the persistent settings. It implements the hybrid-hybrid system.

Core tools (always available):
- claude_mailbox
- claude_check_mail  
- claude_user_message
- claude_enable_all_tools
- claude_set_toolset

Additional tools available based on settings:
- All tools (when enabled)
- Custom toolset (user-defined)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ClaudeToolManager:
    """Manages Claude CLI's tool access based on settings."""
    
    SETTINGS_FILE = Path.home() / ".aiwhisperer" / "claude_tools_settings.json"
    
    # Core tools always available to Claude
    CORE_TOOLS = [
        "claude_mailbox",
        "claude_check_mail",
        "claude_user_message", 
        "claude_enable_all_tools",
        "claude_set_toolset"
    ]
    
    def __init__(self):
        """Initialize the Claude tool manager."""
        self._ensure_settings_exist()
    
    def _ensure_settings_exist(self) -> None:
        """Ensure settings file exists with defaults."""
        if not self.SETTINGS_FILE.exists():
            self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            default_settings = {
                "all_tools_enabled": False,
                "custom_tools": [],
                "audit_trail": []
            }
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(default_settings, f, indent=2)
    
    def load_settings(self) -> dict:
        """Load Claude tools settings."""
        try:
            with open(self.SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading Claude settings: {e}")
            return {
                "all_tools_enabled": False,
                "custom_tools": [],
                "audit_trail": []
            }
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of tools that should be available to Claude."""
        settings = self.load_settings()
        
        # Always include core tools
        enabled_tools = self.CORE_TOOLS.copy()
        
        # If all tools enabled, return None (signals to include all)
        if settings.get('all_tools_enabled', False):
            return None  # Special value meaning "all tools"
        
        # Otherwise, add custom tools
        custom_tools = settings.get('custom_tools', [])
        enabled_tools.extend(custom_tools)
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for tool in enabled_tools:
            if tool not in seen:
                seen.add(tool)
                result.append(tool)
        
        return result
    
    def should_include_tool(self, tool_name: str) -> bool:
        """Check if a specific tool should be available to Claude."""
        enabled_tools = self.get_enabled_tools()
        
        # None means all tools enabled
        if enabled_tools is None:
            return True
        
        return tool_name in enabled_tools
    
    def get_claude_tools(self) -> Dict[str, Any]:
        """Get Claude-specific tool instances."""
        tools = {}
        
        # Import Claude tools
        try:
            from ai_whisperer.tools.claude.claude_mailbox_tool import ClaudeMailboxTool
            from ai_whisperer.tools.claude.claude_check_mail_tool import ClaudeCheckMailTool
            from ai_whisperer.tools.claude.claude_user_message_tool import ClaudeUserMessageTool
            from ai_whisperer.tools.claude.claude_enable_all_tools_tool import ClaudeEnableAllToolsTool
            from ai_whisperer.tools.claude.claude_set_toolset_tool import ClaudeSetToolsetTool
            
            # Create instances
            tools['claude_mailbox'] = ClaudeMailboxTool()
            tools['claude_check_mail'] = ClaudeCheckMailTool()
            tools['claude_user_message'] = ClaudeUserMessageTool()
            tools['claude_enable_all_tools'] = ClaudeEnableAllToolsTool()
            tools['claude_set_toolset'] = ClaudeSetToolsetTool()
            
        except Exception as e:
            logger.error(f"Error loading Claude tools: {e}")
        
        return tools
    
    def filter_tools_for_claude(self, all_tools: Dict[str, Any]) -> Dict[str, Any]:
        """Filter tools based on Claude's current settings."""
        # Get Claude-specific tools
        claude_tools = self.get_claude_tools()
        
        # Get enabled tools list
        enabled_tools = self.get_enabled_tools()
        
        # If all tools enabled, return everything plus Claude tools
        if enabled_tools is None:
            result = all_tools.copy()
            result.update(claude_tools)
            return result
        
        # Otherwise, filter to only enabled tools
        result = {}
        
        # Add Claude core tools
        for tool_name, tool in claude_tools.items():
            if tool_name in self.CORE_TOOLS:
                result[tool_name] = tool
        
        # Add enabled custom tools from all_tools
        for tool_name in enabled_tools:
            if tool_name in all_tools:
                result[tool_name] = all_tools[tool_name]
        
        return result


# Global instance
_claude_tool_manager = None

def get_claude_tool_manager() -> ClaudeToolManager:
    """Get the global Claude tool manager instance."""
    global _claude_tool_manager
    if _claude_tool_manager is None:
        _claude_tool_manager = ClaudeToolManager()
    return _claude_tool_manager