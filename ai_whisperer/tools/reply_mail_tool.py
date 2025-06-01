"""
Reply Mail Tool - Allows agents to reply to messages in their mailbox.
"""
from typing import Dict, Any

from ai_whisperer.tools.base_tool import BaseTool, ToolResult, ToolDefinition, ParameterDefinition
from ai_whisperer.agents.mailbox import Mail, MessagePriority, get_mailbox


class ReplyMailTool(BaseTool):
    """Tool for replying to mail messages."""
    
    def get_definition(self) -> ToolDefinition:
        """Get the tool definition."""
        return ToolDefinition(
            name="reply_mail",
            description="Reply to a message in the mailbox",
            parameters=[
                ParameterDefinition(
                    name="message_id",
                    description="ID of the message to reply to",
                    type="string",
                    required=True
                ),
                ParameterDefinition(
                    name="body",
                    description="Reply message body",
                    type="string",
                    required=True
                ),
                ParameterDefinition(
                    name="subject",
                    description="Reply subject (optional, defaults to 'Re: <original subject>')",
                    type="string",
                    required=False
                ),
                ParameterDefinition(
                    name="priority",
                    description="Message priority: low, normal, high, urgent",
                    type="string",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the reply mail tool."""
        try:
            # Get current agent name from context
            from_agent = kwargs.get('_agent_name', 'unknown')
            
            # Get mailbox
            mailbox = get_mailbox()
            
            # Find original message to get sender
            original_mail = None
            for mail_list in mailbox._inboxes.values():
                for mail in mail_list:
                    if mail.message_id == kwargs['message_id']:
                        original_mail = mail
                        break
                if original_mail:
                    break
            
            if not original_mail:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Message {kwargs['message_id']} not found"
                )
            
            # Determine reply subject
            subject = kwargs.get('subject')
            if not subject:
                if original_mail.subject.startswith("Re: "):
                    subject = original_mail.subject
                else:
                    subject = f"Re: {original_mail.subject}"
            
            # Parse priority
            priority_str = kwargs.get('priority', 'normal').lower()
            priority_map = {
                'low': MessagePriority.LOW,
                'normal': MessagePriority.NORMAL,
                'high': MessagePriority.HIGH,
                'urgent': MessagePriority.URGENT
            }
            priority = priority_map.get(priority_str, MessagePriority.NORMAL)
            
            # Create reply
            reply = Mail(
                from_agent=from_agent,
                to_agent=original_mail.from_agent,  # Reply goes back to sender
                subject=subject,
                body=kwargs['body'],
                priority=priority,
                metadata={'original_subject': original_mail.subject}
            )
            
            # Send reply
            reply_id = mailbox.reply_to_mail(kwargs['message_id'], reply)
            
            # Check if recipient has notification
            recipient = reply.to_agent or "user"
            notification = ""
            if mailbox.has_unread_mail(reply.to_agent):
                count = mailbox.get_unread_count(reply.to_agent)
                notification = f"{recipient} has {count} unread message(s)"
            
            return ToolResult(
                success=True,
                data={
                    'reply_id': reply_id,
                    'to': recipient,
                    'subject': reply.subject,
                    'in_reply_to': kwargs['message_id'],
                    'notification': notification
                },
                metadata={'priority': priority_str}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Failed to reply to mail: {str(e)}"
            )