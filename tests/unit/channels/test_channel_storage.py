"""
Unit tests for channel storage.
"""

import pytest
from datetime import datetime, timedelta, timezone
from ai_whisperer.channels.storage import ChannelStorage
from ai_whisperer.channels.types import ChannelType, ChannelMessage, ChannelMetadata


class TestChannelStorage:
    """Test ChannelStorage functionality."""
    
    @pytest.fixture
    def storage(self):
        """Create a storage instance."""
        return ChannelStorage(max_messages_per_channel=10)
    
    @pytest.fixture
    def sample_message(self):
        """Create a sample message."""
        metadata = ChannelMetadata(
            sequence=1,
            agent_id="alice",
            session_id="test_session"
        )
        return ChannelMessage(
            channel=ChannelType.FINAL,
            content="Hello, world!",
            metadata=metadata
        )
    
    def test_add_and_get_message(self, storage, sample_message):
        """Test adding and retrieving messages."""
        storage.add_message("test_session", sample_message)
        
        messages = storage.get_messages("test_session")
        
        assert len(messages) == 1
        assert messages[0].content == "Hello, world!"
        assert messages[0].channel == ChannelType.FINAL
    
    def test_get_channel_specific_messages(self, storage):
        """Test retrieving messages from specific channels."""
        # Add messages to different channels
        for i in range(3):
            storage.add_message("session1", ChannelMessage(
                channel=ChannelType.FINAL,
                content=f"Final {i}",
                metadata=ChannelMetadata(sequence=i*3+1)
            ))
            storage.add_message("session1", ChannelMessage(
                channel=ChannelType.COMMENTARY,
                content=f"Commentary {i}",
                metadata=ChannelMetadata(sequence=i*3+2)
            ))
            storage.add_message("session1", ChannelMessage(
                channel=ChannelType.ANALYSIS,
                content=f"Analysis {i}",
                metadata=ChannelMetadata(sequence=i*3+3)
            ))
        
        # Get final channel only
        final_messages = storage.get_channel_messages("session1", ChannelType.FINAL)
        assert len(final_messages) == 3
        assert all(m.channel == ChannelType.FINAL for m in final_messages)
        
        # Get all messages
        all_messages = storage.get_messages("session1")
        assert len(all_messages) == 9
    
    def test_get_user_visible_messages(self, storage):
        """Test retrieving user-visible messages."""
        # Add messages to different channels
        storage.add_message("session1", ChannelMessage(
            channel=ChannelType.ANALYSIS,
            content="Hidden analysis",
            metadata=ChannelMetadata(sequence=1)
        ))
        storage.add_message("session1", ChannelMessage(
            channel=ChannelType.FINAL,
            content="User sees this",
            metadata=ChannelMetadata(sequence=2)
        ))
        storage.add_message("session1", ChannelMessage(
            channel=ChannelType.COMMENTARY,
            content="Tool call",
            metadata=ChannelMetadata(sequence=3)
        ))
        
        # Get user visible with commentary
        visible = storage.get_user_visible_messages("session1", include_commentary=True)
        assert len(visible) == 2
        assert all(m.channel != ChannelType.ANALYSIS for m in visible)
        
        # Get user visible without commentary
        visible_no_tools = storage.get_user_visible_messages("session1", include_commentary=False)
        assert len(visible_no_tools) == 1
        assert visible_no_tools[0].channel == ChannelType.FINAL
    
    def test_message_limit_enforcement(self, storage):
        """Test that message limits are enforced."""
        # Add more messages than the limit
        for i in range(15):
            storage.add_message("session1", ChannelMessage(
                channel=ChannelType.FINAL,
                content=f"Message {i}",
                metadata=ChannelMetadata(sequence=i)
            ))
        
        messages = storage.get_channel_messages("session1", ChannelType.FINAL)
        
        # Should only have the last 10 messages
        assert len(messages) == 10
        assert messages[0].content == "Message 5"
        assert messages[-1].content == "Message 14"
    
    def test_clear_session(self, storage, sample_message):
        """Test clearing a session."""
        storage.add_message("session1", sample_message)
        storage.set_session_metadata("session1", {"user": "test"})
        
        assert "session1" in storage.get_active_sessions()
        
        storage.clear_session("session1")
        
        assert "session1" not in storage.get_active_sessions()
        assert len(storage.get_messages("session1")) == 0
        assert storage.get_session_metadata("session1") is None
    
    def test_clear_channel(self, storage):
        """Test clearing a specific channel."""
        # Add messages to different channels
        storage.add_message("session1", ChannelMessage(
            channel=ChannelType.FINAL,
            content="Final",
            metadata=ChannelMetadata(sequence=1)
        ))
        storage.add_message("session1", ChannelMessage(
            channel=ChannelType.ANALYSIS,
            content="Analysis",
            metadata=ChannelMetadata(sequence=2)
        ))
        
        storage.clear_channel("session1", ChannelType.ANALYSIS)
        
        messages = storage.get_messages("session1")
        assert len(messages) == 1
        assert messages[0].channel == ChannelType.FINAL
    
    def test_session_stats(self, storage):
        """Test getting session statistics."""
        # Add messages
        for _ in range(3):
            storage.add_message("session1", ChannelMessage(
                channel=ChannelType.FINAL,
                content="",
                metadata=ChannelMetadata(sequence=1)
            ))
        for _ in range(2):
            storage.add_message("session1", ChannelMessage(
                channel=ChannelType.COMMENTARY,
                content="",
                metadata=ChannelMetadata(sequence=1)
            ))
        
        stats = storage.get_session_stats("session1")
        
        assert stats["final_count"] == 3
        assert stats["commentary_count"] == 2
        assert stats["analysis_count"] == 0
    
    def test_cleanup_old_sessions(self, storage):
        """Test cleaning up old sessions."""
        # Add a message with old timestamp
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        old_metadata = ChannelMetadata(
            sequence=1,
            timestamp=old_time
        )
        storage.add_message("old_session", ChannelMessage(
            channel=ChannelType.FINAL,
            content="Old",
            metadata=old_metadata
        ))
        
        # Add a recent message
        storage.add_message("new_session", ChannelMessage(
            channel=ChannelType.FINAL,
            content="New",
            metadata=ChannelMetadata(sequence=2)
        ))
        
        # Clean up sessions older than 24 hours
        cleaned = storage.cleanup_old_sessions(max_age_hours=24)
        
        assert cleaned == 1
        assert "old_session" not in storage.get_active_sessions()
        assert "new_session" in storage.get_active_sessions()
    
    def test_get_messages_with_filters(self, storage):
        """Test getting messages with various filters."""
        # Add messages
        for i in range(5):
            storage.add_message("session1", ChannelMessage(
                channel=ChannelType.FINAL,
                content=f"Message {i}",
                metadata=ChannelMetadata(sequence=i+1)
            ))
        
        # Test limit
        limited = storage.get_messages("session1", limit=3)
        assert len(limited) == 3
        assert limited[0].content == "Message 2"  # Should get last 3
        
        # Test since_sequence
        since = storage.get_messages("session1", since_sequence=3)
        assert len(since) == 2
        assert since[0].content == "Message 3"
        assert since[1].content == "Message 4"