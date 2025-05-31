"""
Check Mail Tool - Allows agents to check their mailbox for messages.
"""
from typing import Dict, Any, List

from ai_whisperer.tools.base_tool import BaseTool, ToolResult, ToolDefinition, ParameterDefinition
from ai_whisperer.agents.mailbox import get_mailbox


class CheckMailTool(BaseTool):
    """Tool for checking mailbox messages."""
    
    def get_definition(self) -> ToolDefinition:
        """Get the tool definition."""
        return ToolDefinition(
            name="check_mail",
            description="Check mailbox for new messages or view message history",
            parameters=[
                ParameterDefinition(
                    name="unread_only",
                    description="Only show unread messages (default: true)",
                    type="boolean",
                    required=False
                ),
                ParameterDefinition(
                    name="include_archived",
                    description="Include archived messages (default: false)",
                    type="boolean",
                    required=False
                ),
                ParameterDefinition(
                    name="limit",
                    description="Maximum number of messages to return",
                    type="integer",
                    required=False
                )
            ]
        )
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the check mail tool."""
        try:
            # Get current agent name from context
            agent_name = kwargs.get('_agent_name', '')
            
            # Parse parameters
            unread_only = kwargs.get('unread_only', True)
            include_archived = kwargs.get('include_archived', False)
            limit = kwargs.get('limit', 50)
            
            # Get mailbox
            mailbox = get_mailbox()
            
            # Get messages based on parameters
            if unread_only:
                messages = mailbox.check_mail(agent_name)
            else:
                messages = mailbox.get_all_mail(
                    agent_name,
                    include_read=True,
                    include_archived=include_archived
                )
            
            # Apply limit
            if limit and len(messages) > limit:
                messages = messages[:limit]
            
            # Format messages for output
            formatted_messages = []
            for mail in messages:
                formatted_messages.append({
                    'message_id': mail.message_id,
                    'from': mail.from_agent or 'user',
                    'subject': mail.subject,
                    'body': mail.body,
                    'timestamp': mail.timestamp.isoformat(),
                    'priority': mail.priority.value,
                    'status': mail.status.value,
                    'reply_to': mail.reply_to
                })
            
            # Get unread count for notification
            unread_count = mailbox.get_unread_count(agent_name)
            
            return ToolResult(
                success=True,
                data={
                    'messages': formatted_messages,
                    'count': len(formatted_messages),
                    'unread_count': unread_count,
                    'has_more': len(messages) == limit if limit else False
                },
                metadata={
                    'agent': agent_name or 'user',
                    'unread_only': unread_only
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={'messages': [], 'count': 0, 'unread_count': 0},
                error=f"Failed to check mail: {str(e)}"
            )