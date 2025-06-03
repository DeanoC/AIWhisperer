"""
Tests for the universal mailbox system.
"""
import pytest
from datetime import datetime, timezone

from ai_whisperer.extensions.mailbox.mailbox import (
    Mail, MailboxSystem, MessagePriority, MessageStatus,
    get_mailbox, reset_mailbox
)


class TestMailboxSystem:
    """Test the mailbox system functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset mailbox before each test."""
        reset_mailbox()
    
    def test_send_and_check_mail(self):
        """Test sending and checking mail."""
        mailbox = get_mailbox()
        
        # Send mail from patricia to eamonn
        mail = Mail(
            from_agent="patricia",
            to_agent="eamonn",
            subject="Task clarification",
            body="Please use JWT authentication"
        )
        
        message_id = mailbox.send_mail(mail)
        assert message_id == mail.message_id
        
        # Check eamonn has unread mail
        assert mailbox.has_unread_mail("eamonn")
        assert mailbox.get_unread_count("eamonn") == 1
        
        # Check mail
        unread = mailbox.check_mail("eamonn")
        assert len(unread) == 1
        assert unread[0].subject == "Task clarification"
        assert unread[0].status == MessageStatus.READ
        
        # No more unread
        assert not mailbox.has_unread_mail("eamonn")
    
    def test_reply_to_mail(self):
        """Test replying to messages."""
        mailbox = get_mailbox()
        
        # Original message
        original = Mail(
            from_agent="eamonn",
            to_agent="patricia",
            subject="Need help",
            body="What authentication method?"
        )
        original_id = mailbox.send_mail(original)
        
        # Reply
        reply = Mail(
            from_agent="patricia",
            to_agent="eamonn",
            subject="Re: Need help",
            body="Use OAuth2"
        )
        reply_id = mailbox.reply_to_mail(original_id, reply)
        
        assert reply.reply_to == original_id
        
        # Check conversation thread
        thread = mailbox.get_conversation_thread(reply_id)
        assert len(thread) == 2
        assert thread[0].message_id == original_id
        assert thread[1].message_id == reply_id
    
    def test_priority_messages(self):
        """Test message priorities."""
        mailbox = get_mailbox()
        
        # Send urgent message
        urgent = Mail(
            from_agent="user",
            to_agent="patricia",
            subject="URGENT: System down",
            body="Production is down!",
            priority=MessagePriority.URGENT
        )
        
        mailbox.send_mail(urgent)
        
        messages = mailbox.check_mail("patricia")
        assert len(messages) == 1
        assert messages[0].priority == MessagePriority.URGENT
    
    def test_user_mail(self):
        """Test mail to/from user (empty agent name)."""
        mailbox = get_mailbox()
        
        # Agent to user
        mail = Mail(
            from_agent="eamonn",
            to_agent="",  # Empty means user
            subject="Task completed",
            body="Authentication implemented"
        )
        
        mailbox.send_mail(mail)
        
        # Check user mailbox
        assert mailbox.has_unread_mail("")  # Empty string for user
        user_mail = mailbox.check_mail("")
        assert len(user_mail) == 1
        assert user_mail[0].from_agent == "eamonn"
    
    def test_notification_handler(self):
        """Test notification callbacks."""
        mailbox = get_mailbox()
        
        # Track notifications
        notifications = []
        
        def handler(mail):
            notifications.append(mail)
        
        # Register handler
        mailbox.register_notification_handler("patricia", handler)
        
        # Send mail
        mail = Mail(
            from_agent="eamonn",
            to_agent="patricia",
            subject="Test",
            body="Test notification"
        )
        
        mailbox.send_mail(mail)
        
        # Handler should have been called
        assert len(notifications) == 1
        assert notifications[0].subject == "Test"
    
    def test_archive_mail(self):
        """Test archiving messages."""
        mailbox = get_mailbox()
        
        # Send and read mail
        mail = Mail(
            from_agent="patricia",
            to_agent="eamonn",
            subject="Old task",
            body="Completed"
        )
        message_id = mailbox.send_mail(mail)
        mailbox.check_mail("eamonn")  # Mark as read
        
        # Archive it
        success = mailbox.archive_mail(message_id)
        assert success
        
        # Not in regular mail
        regular = mailbox.get_all_mail("eamonn", include_archived=False)
        assert len(regular) == 0
        
        # But available with include_archived
        all_mail = mailbox.get_all_mail("eamonn", include_archived=True)
        assert len(all_mail) == 1
        assert all_mail[0].status == MessageStatus.ARCHIVED