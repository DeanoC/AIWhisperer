"""
Module: ai_whisperer/tools/claude/claude_user_message_tool.py
Purpose: Claude CLI user message tool for direct interaction

This tool provides Claude CLI with the ability to send messages as if
typed in the UI, including markdown, @files, and /commands.

Part of the hybrid-hybrid system that gives Claude intervention
capabilities when needed.
"""

import logging
from typing import Optional
from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class ClaudeUserMessageTool(AITool):
    """Claude CLI's user message tool for direct UI-like interaction."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "claude_user_message"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Send a message as if typed in the UI - supports markdown, @files, and /commands"
    
    @property
    def parameters_schema(self) -> dict:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to send (supports markdown, @files, /commands)"
                },
                "agent": {
                    "type": "string",
                    "description": "Optional: Target agent (if not specified, uses current agent)",
                    "default": None
                }
            },
            "required": ["message"]
        }
    
    @property
    def category(self) -> str:
        """Return the tool category."""
        return "Claude"
    
    @property
    def tags(self) -> list:
        """Return the tool tags."""
        return ["claude", "user-message", "intervention", "commands"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for Claude on how to use this tool."""
        return """Use claude_user_message to send messages as if you were the user typing in the UI.

This gives you full access to:
- Markdown formatting
- @file references (e.g., @README.md)
- /commands (e.g., /clear, /agent Patricia, /help)
- Complex multi-line messages

Examples:
- Send a command: claude_user_message(message="/agent Debbie")
- Reference files: claude_user_message(message="Please review @src/main.py and @tests/test_main.py")
- Complex message: claude_user_message(message="```python\\ncode here\\n```\\n\\nPlease fix this code.")

This is your intervention tool when you need direct control or when mailbox communication isn't sufficient.
"""
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to send a user message."""
        # Handle both direct kwargs and arguments pattern
        if 'arguments' in kwargs and isinstance(kwargs['arguments'], dict):
            actual_args = kwargs['arguments']
        else:
            actual_args = kwargs
        
        message = actual_args.get('message', '')
        target_agent = actual_args.get('agent')
        
        if not message:
            return {
                "error": "Message content is required",
                "sent": False
            }
        
        # Get the context to access the session
        context = kwargs.get('_context')
        if not context:
            return {
                "error": "No context available for message sending",
                "sent": False
            }
        
        try:
            # Get the current session
            session = getattr(context, 'session', None)
            if not session:
                return {
                    "error": "No active session found",
                    "sent": False
                }
            
            # Switch agent if specified
            if target_agent:
                # Check if we need to switch agents
                current_agent = getattr(session, 'current_agent_id', None)
                if current_agent != target_agent:
                    # Send agent switch command first
                    session.process_user_message(f"/agent {target_agent}")
            
            # Send the actual message
            # This will process markdown, @files, /commands, etc.
            response = session.process_user_message(message)
            
            return {
                "sent": True,
                "message": message,
                "agent": target_agent or "current",
                "response_preview": str(response)[:200] if response else "Message sent",
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error sending user message: {e}")
            return {
                "error": f"Failed to send message: {str(e)}",
                "sent": False
            }