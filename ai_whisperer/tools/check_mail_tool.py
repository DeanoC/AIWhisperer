"""
Module: ai_whisperer/tools/check_mail_tool.py
Purpose: AI tool implementation for checking mail

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- CheckMailTool: Tool for checking mail messages in the mailbox.

Usage:
    tool = CheckMailTool()
    result = tool.execute(**parameters)

Related:
- See docs/agent-e-consolidated-implementation.md

"""

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, MessageStatus

class CheckMailTool(AITool):
    """Tool for checking mail messages in the mailbox."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "check_mail"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Check your mailbox for new messages"
    
    @property
    def parameters_schema(self) -> dict:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "unread_only": {
                    "type": "boolean",
                    "description": "Whether to show only unread messages",
                    "default": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to retrieve",
                    "default": 10
                }
            },
            "required": []
        }
    
    @property
    def category(self) -> str:
        """Return the tool category."""
        return "Communication"
    
    @property
    def tags(self) -> list:
        """Return the tool tags."""
        return ["mailbox", "communication", "messaging"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for the AI on how to use this tool."""
        return """Use the check_mail tool to check your mailbox for messages.
        
Parameters:
- unread_only: Show only unread messages (default: true)
- limit: Maximum number of messages to retrieve (default: 10)

Example usage:
- Check all unread: check_mail()
- Check last 5 messages: check_mail(unread_only=false, limit=5)
"""
    
    def execute(self, **kwargs) -> str:
        """Execute the tool to check mail."""
        # Check if we're getting 'arguments' instead of kwargs
        if 'arguments' in kwargs and isinstance(kwargs['arguments'], dict):
            # Tool is being called with arguments pattern
            actual_args = kwargs['arguments']
        else:
            # Tool is being called with **kwargs pattern
            actual_args = kwargs
            
        # Extract parameters
        unread_only = actual_args.get('unread_only', True)
        limit = actual_args.get('limit', 10)
        
        # Get current agent name from context
        # Try different possible parameter names that might contain agent info
        agent_name = (kwargs.get('_from_agent') or kwargs.get('_agent_name') or 
                     kwargs.get('_agent_id') or actual_args.get('_from_agent') or 
                     actual_args.get('_agent_name') or actual_args.get('_agent_id') or '')
        
        # Get the mailbox instance
        mailbox = get_mailbox()
        
        # Get messages based on unread_only parameter
        if unread_only:
            # check_mail returns only unread messages and marks them as read
            messages = mailbox.check_mail(agent_name)
        else:
            # get_all_mail returns all messages (read and unread)
            messages = mailbox.get_all_mail(agent_name, include_read=True, include_archived=False)
        
        if not messages:
            return "No messages found in your mailbox."
        
        # Format messages for display
        result = f"You have {len(messages)} {'unread' if unread_only else ''} message(s):\n\n"
        
        for i, mail in enumerate(messages[:limit], 1):
            # Use the status field instead of is_read
            status = mail.status.value.upper()
            result += f"{i}. [{status}] From: {mail.from_agent or 'User'}\n"
            result += f"   Subject: {mail.subject}\n"
            result += f"   Priority: {mail.priority.value}\n"
            result += f"   Body: {mail.body[:100]}{'...' if len(mail.body) > 100 else ''}\n"
            result += f"   ID: {mail.message_id}\n\n"
        
        if len(messages) > limit:
            result += f"(Showing {limit} of {len(messages)} messages)"
        
        return result