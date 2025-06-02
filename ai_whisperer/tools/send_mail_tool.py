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
from ai_whisperer.tools.base_tool import BaseTool, ToolResult, ToolDefinition, ParameterDefinition
from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox

class SendMailTool(BaseTool):
    """Tool for sending mail messages to agents or users."""
    
    def get_definition(self) -> ToolDefinition:
        """Get the tool definition."""
        return ToolDefinition(
            name="send_mail",
            description="Send a message to another agent or the user via the mailbox system",
            parameters=[
                ParameterDefinition(
                    name="to_agent",
                    description="Name of recipient agent (leave empty to send to user)",
                    type="string",
                    required=False
                ),
                ParameterDefinition(
                    name="subject",
                    description="Subject line of the message",
                    type="string",
                    required=True
                ),
                ParameterDefinition(
                    name="body",
                    description="Body content of the message",
                    type="string",
                    required=True
                ),
                ParameterDefinition(
                    name="priority",
                    description="Message priority: low, normal, high, urgent",
                    type="string",
                    required=False
                ),
                ParameterDefinition(
                    name="reply_to",
                    description="Message ID this is replying to (if applicable)",
                    type="string",
                    required=False
                ),
                ParameterDefinition(
                    name="metadata",
                    description="Additional metadata as JSON string",
                    type="string",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the send mail tool."""
        try:
            # Get current agent name from context if available
            from_agent = kwargs.get('_agent_name', 'unknown')
            
            # Parse priority
            priority_str = kwargs.get('priority', 'normal').lower()
            priority_map = {
                'low': MessagePriority.LOW,
                'normal': MessagePriority.NORMAL,
                'high': MessagePriority.HIGH,
                'urgent': MessagePriority.URGENT
            }
            priority = priority_map.get(priority_str, MessagePriority.NORMAL)
            
            # Parse metadata if provided
            metadata = {}
            if 'metadata' in kwargs:
                try:
                    metadata = json.loads(kwargs['metadata'])
                except json.JSONDecodeError:
                    return ToolResult(
                        success=False,
                        data={},
                        error="Invalid JSON in metadata parameter"
                    )
            
            # Create mail
            mail = Mail(
                from_agent=from_agent,
                to_agent=kwargs.get('to_agent', ''),
                subject=kwargs['subject'],
                body=kwargs['body'],
                priority=priority,
                reply_to=kwargs.get('reply_to'),
                metadata=metadata
            )
            
            # Send via mailbox
            mailbox = get_mailbox()
            message_id = mailbox.send_mail(mail)
            
            # Check if recipient has notification
            recipient = mail.to_agent or "user"
            notification = ""
            if mailbox.has_unread_mail(mail.to_agent):
                count = mailbox.get_unread_count(mail.to_agent)
                notification = f"{recipient} has {count} unread message(s)"
            
            return ToolResult(
                success=True,
                data={
                    'message_id': message_id,
                    'to': recipient,
                    'subject': mail.subject,
                    'notification': notification
                },
                metadata={'priority': priority_str}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Failed to send mail: {str(e)}"
            )
