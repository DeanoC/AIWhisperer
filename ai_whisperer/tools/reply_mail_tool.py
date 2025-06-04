"""
Module: ai_whisperer/tools/reply_mail_tool.py
Purpose: AI tool implementation for replying to mail

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- ReplyMailTool: Tool for replying to mail messages.

Usage:
    tool = ReplyMailTool()
    result = tool.execute(**parameters)

Related:
- See docs/agent-e-consolidated-implementation.md

"""

from typing import Dict, Any
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox

class ReplyMailTool(AITool):
    """Tool for replying to mail messages."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "reply_mail"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Reply to a message in your mailbox"
    
    @property
    def parameters_schema(self) -> dict:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "ID of the message to reply to"
                },
                "body": {
                    "type": "string",
                    "description": "Reply message body"
                },
                "subject": {
                    "type": "string",
                    "description": "Reply subject (optional, defaults to 'Re: <original subject>')"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "description": "Priority level of the reply",
                    "default": "normal"
                }
            },
            "required": ["message_id", "body"]
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
        return """Use the reply_mail tool to reply to messages in your mailbox.
        
Parameters:
- message_id: ID of the message to reply to (get from check_mail)
- body: Your reply message
- subject: Optional custom subject (defaults to 'Re: <original>')
- priority: Reply priority (low/normal/high/urgent)

Example usage:
- Simple reply: reply_mail(message_id="msg123", body="Thank you for your message...")
- Custom subject: reply_mail(message_id="msg123", body="...", subject="Updated: RFC Review")
"""
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool to reply to mail."""
        # Extract parameters
        message_id = kwargs.get('message_id', '')
        body = kwargs.get('body', '')
        subject = kwargs.get('subject', None)
        priority_str = kwargs.get('priority', 'normal').lower()
        
        if not message_id:
            return {
                "error": "message_id is required to reply to a message",
                "sent": False,
                "message_id": None
            }
        
        if not body:
            return {
                "error": "body is required for the reply",
                "sent": False,
                "message_id": message_id
            }
        
        # Map priority string to enum
        priority_map = {
            'low': MessagePriority.LOW,
            'normal': MessagePriority.NORMAL,
            'high': MessagePriority.HIGH,
            'urgent': MessagePriority.URGENT
        }
        priority = priority_map.get(priority_str, MessagePriority.NORMAL)
        
        # Get the mailbox instance
        mailbox = get_mailbox()
        
        # Get current agent name from context
        from_agent = kwargs.get('_from_agent', 'Unknown')
        
        # Get the original message to reply to
        original = mailbox.get_message(message_id)
        if not original:
            return {
                "error": f"Message with ID {message_id} not found",
                "sent": False,
                "message_id": message_id
            }
        
        # Generate reply subject if not provided
        if not subject:
            subject = f"Re: {original.subject}"
        
        # Create reply mail object
        mail = Mail(
            from_agent=from_agent,
            to_agent=original.from_agent,  # Reply to sender
            subject=subject,
            body=body,
            priority=priority
            # Note: reply_to will be set by reply_to_mail method
        )
        
        # Send the reply using reply_to_mail to maintain threading
        reply_id = mailbox.reply_to_mail(message_id, mail)
        
        return {
            "sent": True,
            "reply_id": reply_id,
            "original_message_id": message_id,
            "to": original.from_agent or 'User',
            "from": from_agent,
            "subject": subject,
            "priority": priority_str,
            "thread_id": original.thread_id if hasattr(original, 'thread_id') else None
        }