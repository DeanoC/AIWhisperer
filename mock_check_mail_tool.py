"""
Module: ai_whisperer/tools/check_mail_tool.py
Purpose: MOCK AI tool implementation for checking mail

This is a MOCK version that returns a fake mail for testing.
"""

import logging
from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class CheckMailTool(AITool):
    """Mock tool for checking mail messages - returns fake mail."""
    
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
        """Execute the mock tool to return fake mail."""
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
        agent_name = (kwargs.get('_from_agent') or kwargs.get('_agent_name') or 
                     kwargs.get('_agent_id') or actual_args.get('_from_agent') or 
                     actual_args.get('_agent_name') or actual_args.get('_agent_id') or 'debbie')
        
        logger.info(f"[MOCK CHECK_MAIL] Agent '{agent_name}' checking mail: unread_only={unread_only}, limit={limit}")
        logger.info(f"[MOCK CHECK_MAIL] Returning FAKE mail asking to use list_directory tool")
        
        # Return a fake mail asking to use list_directory
        formatted_messages = [{
            "message_id": "mock-test-001",
            "from": "alice",
            "to": agent_name,
            "subject": "Tool Request",
            "body": "Please use the list_directory tool to show the contents of the current directory.",
            "priority": "normal",
            "status": "unread",
            "timestamp": "2025-06-05T20:45:00.000Z"
        }]
        
        result = {
            "messages": formatted_messages,
            "count": 1,
            "total_count": 1,
            "limit": limit,
            "unread_only": unread_only,
            "truncated": False
        }
        
        logger.info(f"[MOCK CHECK_MAIL] Returning {len(formatted_messages)} FAKE messages to agent '{agent_name}'")
        logger.info(f"[MOCK CHECK_MAIL] Mock mail content: {result}")
        return result