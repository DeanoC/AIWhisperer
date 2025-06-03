"""
Unit tests for channel types.
"""

import pytest
from datetime import datetime, timezone
from ai_whisperer.channels.types import ChannelType, ChannelMessage, ChannelMetadata


class TestChannelType:
    """Test ChannelType enum."""
    
    def test_channel_values(self):
        """Test channel type values."""
        assert ChannelType.ANALYSIS.value == "analysis"
        assert ChannelType.COMMENTARY.value == "commentary"
        assert ChannelType.FINAL.value == "final"
    
    def test_from_string(self):
        """Test string conversion."""
        assert ChannelType.from_string("analysis") == ChannelType.ANALYSIS
        assert ChannelType.from_string("COMMENTARY") == ChannelType.COMMENTARY
        assert ChannelType.from_string("Final") == ChannelType.FINAL
        assert ChannelType.from_string("invalid") is None
    
    def test_is_user_visible(self):
        """Test user visibility check."""
        assert ChannelType.FINAL.is_user_visible() is True
        assert ChannelType.COMMENTARY.is_user_visible() is True
        assert ChannelType.ANALYSIS.is_user_visible() is False
    
    def test_requires_formatting(self):
        """Test formatting requirement check."""
        assert ChannelType.COMMENTARY.requires_formatting() is True
        assert ChannelType.FINAL.requires_formatting() is False
        assert ChannelType.ANALYSIS.requires_formatting() is False


class TestChannelMetadata:
    """Test ChannelMetadata dataclass."""
    
    def test_creation(self):
        """Test metadata creation."""
        metadata = ChannelMetadata(
            sequence=1,
            agent_id="test_agent",
            session_id="test_session"
        )
        
        assert metadata.sequence == 1
        assert metadata.agent_id == "test_agent"
        assert metadata.session_id == "test_session"
        assert isinstance(metadata.timestamp, datetime)
        assert metadata.is_partial is False
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        metadata = ChannelMetadata(
            sequence=1,
            agent_id="test_agent",
            tool_calls=["search_files", "read_file"],
            custom={"key": "value"}
        )
        
        data = metadata.to_dict()
        
        assert data["sequence"] == 1
        assert data["agent_id"] == "test_agent"
        assert data["tool_calls"] == ["search_files", "read_file"]
        assert data["key"] == "value"
        assert "timestamp" in data
        assert data["is_partial"] is False


class TestChannelMessage:
    """Test ChannelMessage dataclass."""
    
    def test_creation(self):
        """Test message creation."""
        metadata = ChannelMetadata(sequence=1)
        message = ChannelMessage(
            channel=ChannelType.FINAL,
            content="Hello, world!",
            metadata=metadata
        )
        
        assert message.channel == ChannelType.FINAL
        assert message.content == "Hello, world!"
        assert message.metadata.sequence == 1
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        metadata = ChannelMetadata(
            sequence=1,
            agent_id="alice"
        )
        message = ChannelMessage(
            channel=ChannelType.COMMENTARY,
            content='{"tool": "search_files"}',
            metadata=metadata
        )
        
        data = message.to_dict()
        
        assert data["channel"] == "commentary"
        assert data["content"] == '{"tool": "search_files"}'
        assert data["metadata"]["sequence"] == 1
        assert data["metadata"]["agent_id"] == "alice"
    
    def test_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "channel": "final",
            "content": "Test content",
            "metadata": {
                "sequence": 5,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": "test",
                "is_partial": True
            }
        }
        
        message = ChannelMessage.from_dict(data)
        
        assert message.channel == ChannelType.FINAL
        assert message.content == "Test content"
        assert message.metadata.sequence == 5
        assert message.metadata.agent_id == "test"
        assert message.metadata.is_partial is True