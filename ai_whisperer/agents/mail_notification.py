"""
Mail Notification System - Adds "You've got mail" notifications to agent responses.
"""
import logging
from typing import Dict, Any, Optional

from .mailbox import get_mailbox

logger = logging.getLogger(__name__)


class MailNotificationMixin:
    """Mixin to add mail notification capabilities to agents."""
    
    def check_for_mail_notification(self, agent_name: str) -> Optional[str]:
        """Check if agent has mail and return notification string.
        
        Args:
            agent_name: Name of the agent to check
            
        Returns:
            Notification string if there's mail, None otherwise
        """
        mailbox = get_mailbox()
        
        if mailbox.has_unread_mail(agent_name):
            count = mailbox.get_unread_count(agent_name)
            if count == 1:
                return f"📬 You have 1 unread message in your mailbox."
            else:
                return f"📬 You have {count} unread messages in your mailbox."
        
        return None
    
    def add_mail_notification_to_response(self, response: str, agent_name: str) -> str:
        """Add mail notification to agent response if needed.
        
        Args:
            response: The agent's response
            agent_name: Name of the agent
            
        Returns:
            Response with mail notification appended if applicable
        """
        notification = self.check_for_mail_notification(agent_name)
        
        if notification:
            # Add notification at the end of response
            if response.strip():
                return f"{response}\n\n{notification}"
            else:
                return notification
        
        return response
    
    def format_mail_summary(self, agent_name: str, limit: int = 3) -> str:
        """Get a formatted summary of unread mail.
        
        Args:
            agent_name: Name of the agent
            limit: Maximum number of messages to summarize
            
        Returns:
            Formatted mail summary
        """
        mailbox = get_mailbox()
        unread = mailbox.check_mail(agent_name)
        
        if not unread:
            return "No unread messages."
        
        summary_parts = [f"📬 Unread messages ({len(unread)} total):"]
        
        # Show up to 'limit' messages
        for i, mail in enumerate(unread[:limit]):
            from_str = mail.from_agent or "user"
            priority_icon = "🔴" if mail.priority.value == "urgent" else "🔵" if mail.priority.value == "high" else ""
            summary_parts.append(
                f"{i+1}. {priority_icon} From {from_str}: {mail.subject}"
            )
        
        if len(unread) > limit:
            summary_parts.append(f"... and {len(unread) - limit} more messages")
        
        summary_parts.append("\nUse check_mail tool to read messages.")
        
        return "\n".join(summary_parts)


def get_mail_notification(agent_name: str) -> Optional[str]:
    """Helper function to generate mail notification string."""
    mailbox = get_mailbox()
    if mailbox.has_unread_mail(agent_name):
        count = mailbox.get_unread_count(agent_name)
        return f"📬 You have {count} unread message{'s' if count > 1 else ''} in your mailbox."
    return None
def inject_mail_notification(agent_method):
    """Decorator to inject mail notifications into agent responses.
    
    Usage:
        @inject_mail_notification
        async def process_message(self, message):
            # ... process message ...
            return response
    """
    async def wrapper(self, *args, **kwargs):
        # Get agent name from self
        agent_name = getattr(self, 'name', getattr(self, 'agent_name', 'unknown'))
        
        # Call original method
        response = await agent_method(self, *args, **kwargs)
        
        # Add mail notification if response is a string
        if isinstance(response, str):
            mailbox = get_mailbox()
            if mailbox.has_unread_mail(agent_name):
                count = mailbox.get_unread_count(agent_name)
                notification = f"\n\n📬 You have {count} unread message{'s' if count > 1 else ''} in your mailbox."
                response += notification
        
        return response
    
    return wrapper