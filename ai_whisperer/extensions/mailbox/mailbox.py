"""
Module: ai_whisperer/agents/mailbox.py
Purpose: AI agent implementation for specialized task handling

Universal Mailbox System for Agent and User Communication.
Provides a standardized way for agents to send and receive messages.

Key Components:
- MessagePriority: Message priority levels.
- MessageStatus: Message delivery status.
- Mail: A mail message in the system.
- get_mailbox(): Get the global mailbox system instance.
- reset_mailbox(): Reset the mailbox system (mainly for testing).

Usage:
    messagepriority = MessagePriority()

Dependencies:
- logging
- dataclasses
- uuid

Related:
- See docs/agent-e-consolidated-implementation.md
- See docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
- See docs/archive/phase2_consolidation/agent-e-implementation-summary.md

"""

from typing import Any, Dict, List, Optional, Set

import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class MessageStatus(Enum):
    """Message delivery status."""
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"

@dataclass
class Mail:
    """A mail message in the system."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""  # Empty string means from user
    to_agent: str = ""    # Empty string means to user
    subject: str = ""
    body: str = ""
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: MessageStatus = MessageStatus.UNREAD
    reply_to: Optional[str] = None  # ID of message this is replying to
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mail to dictionary."""
        return {
            'message_id': self.message_id,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'subject': self.subject,
            'body': self.body,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'reply_to': self.reply_to,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mail':
        """Create mail from dictionary."""
        return cls(
            message_id=data.get('message_id', str(uuid.uuid4())),
            from_agent=data.get('from_agent', ''),
            to_agent=data.get('to_agent', ''),
            subject=data.get('subject', ''),
            body=data.get('body', ''),
            priority=MessagePriority(data.get('priority', 'normal')),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(timezone.utc),
            status=MessageStatus(data.get('status', 'unread')),
            reply_to=data.get('reply_to'),
            metadata=data.get('metadata', {})
        )

class MailboxSystem:
    """Centralized mailbox system for all agents and users."""
    
    def __init__(self):
        """Initialize the mailbox system."""
        # Each agent/user has their own inbox
        self._inboxes: Dict[str, List[Mail]] = defaultdict(list)
        # Track unread counts for efficiency
        self._unread_counts: Dict[str, int] = defaultdict(int)
        # Message archive for history
        self._archive: List[Mail] = []
        # Notification callbacks
        self._notification_handlers: Dict[str, Any] = {}
    
    def send_mail(self, mail: Mail) -> str:
        """Send a mail message.
        
        Args:
            mail: The mail to send
            
        Returns:
            Message ID
        """
        # Add to recipient's inbox
        recipient = mail.to_agent or "user"
        self._inboxes[recipient].append(mail)
        
        # Update unread count
        if mail.status == MessageStatus.UNREAD:
            self._unread_counts[recipient] += 1
        
        # Log the message
        logger.info(f"Mail sent from {mail.from_agent or 'user'} to {recipient}: {mail.subject}")
        
        # Trigger notification if handler registered
        if recipient in self._notification_handlers:
            handler = self._notification_handlers[recipient]
            handler(mail)
        
        return mail.message_id
    
    def check_mail(self, agent_name: str = "") -> List[Mail]:
        """Check mailbox for new messages.
        
        Args:
            agent_name: Name of agent checking mail (empty for user)
            
        Returns:
            List of unread messages
        """
        recipient = agent_name or "user"
        inbox = self._inboxes[recipient]
        
        # Get unread messages
        unread = [mail for mail in inbox if mail.status == MessageStatus.UNREAD]
        
        # Mark as read
        for mail in unread:
            mail.status = MessageStatus.READ
        
        # Update unread count
        self._unread_counts[recipient] = 0
        
        return unread
    
    def get_all_mail(self, agent_name: str = "", 
                     include_read: bool = True,
                     include_archived: bool = False) -> List[Mail]:
        """Get all mail for an agent/user.
        
        Args:
            agent_name: Name of agent (empty for user)
            include_read: Include read messages
            include_archived: Include archived messages
            
        Returns:
            List of mail messages
        """
        recipient = agent_name or "user"
        inbox = self._inboxes[recipient]
        
        result = []
        for mail in inbox:
            if mail.status == MessageStatus.ARCHIVED and not include_archived:
                continue
            if mail.status == MessageStatus.READ and not include_read:
                continue
            result.append(mail)
        
        return result
    
    def has_unread_mail(self, agent_name: str = "") -> bool:
        """Check if agent/user has unread mail.
        
        Args:
            agent_name: Name of agent (empty for user)
            
        Returns:
            True if there are unread messages
        """
        recipient = agent_name or "user"
        return self._unread_counts[recipient] > 0
    
    def get_unread_count(self, agent_name: str = "") -> int:
        """Get count of unread messages.
        
        Args:
            agent_name: Name of agent (empty for user)
            
        Returns:
            Number of unread messages
        """
        recipient = agent_name or "user"
        return self._unread_counts[recipient]
    
    def reply_to_mail(self, original_message_id: str, reply: Mail) -> str:
        """Reply to a mail message.
        
        Args:
            original_message_id: ID of message being replied to
            reply: The reply mail
            
        Returns:
            Reply message ID
        """
        # Set reply_to field
        reply.reply_to = original_message_id
        
        # Find original message to update status
        for inbox in self._inboxes.values():
            for mail in inbox:
                if mail.message_id == original_message_id:
                    mail.status = MessageStatus.REPLIED
                    break
        
        # Send the reply
        return self.send_mail(reply)
    
    def archive_mail(self, message_id: str) -> bool:
        """Archive a mail message.
        
        Args:
            message_id: ID of message to archive
            
        Returns:
            True if message was archived
        """
        for inbox in self._inboxes.values():
            for mail in inbox:
                if mail.message_id == message_id:
                    mail.status = MessageStatus.ARCHIVED
                    self._archive.append(mail)
                    return True
        return False
    
    def register_notification_handler(self, agent_name: str, handler):
        """Register a notification handler for new mail.
        
        Args:
            agent_name: Name of agent (empty for user)
            handler: Callback function that takes a Mail object
        """
        recipient = agent_name or "user"
        self._notification_handlers[recipient] = handler
    
    def get_conversation_thread(self, message_id: str) -> List[Mail]:
        """Get all messages in a conversation thread.
        
        Args:
            message_id: Any message ID in the thread
            
        Returns:
            List of messages in chronological order
        """
        thread = []
        visited = set()
        
        def find_thread_messages(msg_id: str):
            if msg_id in visited:
                return
            visited.add(msg_id)
            
            # Find the message
            for inbox in self._inboxes.values():
                for mail in inbox:
                    if mail.message_id == msg_id:
                        thread.append(mail)
                        # Follow reply chain
                        if mail.reply_to:
                            find_thread_messages(mail.reply_to)
                        # Find replies to this message
                        for other_mail in inbox:
                            if other_mail.reply_to == msg_id:
                                find_thread_messages(other_mail.message_id)
                        break
        
        find_thread_messages(message_id)
        
        # Sort by timestamp
        thread.sort(key=lambda m: m.timestamp)
        
        return thread

# Global mailbox instance
_mailbox_system = None

def get_mailbox() -> MailboxSystem:
    """Get the global mailbox system instance."""
    global _mailbox_system
    if _mailbox_system is None:
        _mailbox_system = MailboxSystem()
    return _mailbox_system

def reset_mailbox():
    """Reset the mailbox system (mainly for testing)."""
    global _mailbox_system
    _mailbox_system = MailboxSystem()
