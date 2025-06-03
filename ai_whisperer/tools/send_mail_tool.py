"""
Module: ai_whisperer/tools/send_mail_tool.py
Purpose: AI tool implementation for send mail

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- SendMailTool: Tool for sending mail messages to agents or users.

Usage:
    tool = SendMailTool()
    result = await tool.execute(**parameters)

Related:
- See docs/agent-e-consolidated-implementation.md
- See docs/dependency-analysis-report.md
- See docs/archive/phase2_consolidation/agent-e-implementation-summary.md

"""

import json
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox

class SendMailTool(AITool):
    """Tool for sending mail messages to agents or users."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "send_mail"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Send a message to another agent or the user via the mailbox system"
    
    @property
    def parameters_schema(self) -> dict:
        """Return the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "to_agent": {
                    "type": "string",
                    "description": "Name of recipient agent (leave empty to send to user)"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject line of the message"
                },
                "body": {
                    "type": "string",
                    "description": "Body content of the message"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "description": "Priority level of the message",
                    "default": "normal"
                }
            },
            "required": ["subject", "body"]
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
        return """Use the send_mail tool to send messages to other agents or the user.
        
Parameters:
- to_agent: Name of recipient agent (e.g., 'Patricia', 'Debbie'). Leave empty to send to user.
- subject: Subject line of the message
- body: Main content of the message
- priority: Message priority (low/normal/high/urgent)

Example usage:
- To another agent: send_mail(to_agent="Patricia", subject="RFC Review Request", body="Please review the attached RFC...")
- To the user: send_mail(subject="Task Complete", body="I have completed the requested task...")
"""
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to send mail."""
        # Debug: Check if we're getting 'arguments' instead of kwargs
        if 'arguments' in kwargs and isinstance(kwargs['arguments'], dict):
            # Tool is being called with arguments pattern
            actual_args = kwargs['arguments']
        else:
            # Tool is being called with **kwargs pattern
            actual_args = kwargs
            
        # Extract parameters from the correct source
        to_agent = actual_args.get('to_agent', '').strip()
        subject = actual_args.get('subject', '')
        body = actual_args.get('body', '')
        priority_str = actual_args.get('priority', 'normal').lower()
        
        # Validate required fields
        if not subject:
            return {
                "error": "Subject is required for sending mail",
                "message_id": None,
                "sent": False
            }
        if not body:
            return {
                "error": "Body is required for sending mail",
                "message_id": None,
                "sent": False
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
        
        # Determine sender - in tool context, we'll use the current agent name if available
        # Try different possible parameter names that might contain agent info
        # Check both actual_args (for user params) and kwargs (for system params)
        from_agent = (kwargs.get('_from_agent') or kwargs.get('_agent_name') or 
                     kwargs.get('_agent_id') or actual_args.get('_from_agent') or 
                     actual_args.get('_agent_name') or actual_args.get('_agent_id') or 'Unknown')
        
        # Create mail object
        mail = Mail(
            from_agent=from_agent,
            to_agent=to_agent,  # Don't convert empty string to None
            subject=subject,
            body=body,
            priority=priority
        )
        
        try:
            # Send the mail
            message_id = mailbox.send_mail(mail)
            
            # Return structured result
            return {
                "message_id": message_id,
                "to": to_agent if to_agent else "user",
                "from": from_agent,
                "subject": subject,
                "priority": priority_str,
                "sent": True,
                "error": None
            }
        except ValueError as e:
            return {
                "error": f"Error sending mail: {str(e)}",
                "message_id": None,
                "to": to_agent if to_agent else "user",
                "sent": False
            }