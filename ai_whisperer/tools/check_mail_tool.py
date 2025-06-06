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

import logging
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, MessageStatus

logger = logging.getLogger(__name__)

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
    
    def execute(self, **kwargs) -> dict:
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
        
        logger.info(f"[CHECK_MAIL] Agent '{agent_name}' checking mail: unread_only={unread_only}, limit={limit}")
        logger.debug(f"[CHECK_MAIL] Full kwargs: {kwargs}")
        
        # Get the mailbox instance
        mailbox = get_mailbox()
        logger.info(f"[CHECK_MAIL] Got mailbox instance")
        
        # Get messages based on unread_only parameter
        if unread_only:
            # check_mail returns only unread messages and marks them as read
            logger.info(f"[CHECK_MAIL] Calling mailbox.check_mail('{agent_name}')...")
            messages = mailbox.check_mail(agent_name)
            logger.info(f"[CHECK_MAIL] Found {len(messages)} unread messages for agent '{agent_name}'")
        else:
            # get_all_mail returns all messages (read and unread)
            logger.info(f"[CHECK_MAIL] Calling mailbox.get_all_mail('{agent_name}', include_read=True)...")
            messages = mailbox.get_all_mail(agent_name, include_read=True, include_archived=False)
            logger.info(f"[CHECK_MAIL] Found {len(messages)} total messages for agent '{agent_name}'")
        
        # Format messages for structured output
        formatted_messages = []
        for idx, mail in enumerate(messages[:limit]):
            logger.info(f"[CHECK_MAIL] Message {idx}: id={mail.message_id}, from={mail.from_agent}, to={mail.to_agent}, subject='{mail.subject}'")
            logger.debug(f"[CHECK_MAIL] Message {idx} body: '{mail.body}'")
            formatted_messages.append({
                "message_id": mail.message_id,
                "from": mail.from_agent or "User",
                "to": mail.to_agent if mail.to_agent else agent_name,
                "subject": mail.subject,
                "body": mail.body,
                "priority": mail.priority.value,
                "status": mail.status.value,
                "timestamp": mail.timestamp.isoformat() if hasattr(mail, 'timestamp') else None
            })
        
        result = {
            "messages": formatted_messages,
            "count": len(messages),
            "total_count": len(messages),
            "limit": limit,
            "unread_only": unread_only,
            "truncated": len(messages) > limit
        }
        
        logger.info(f"[CHECK_MAIL] Returning {len(formatted_messages)} messages to agent '{agent_name}'")
        logger.info(f"[CHECK_MAIL] Full result being returned: {result}")
        return result