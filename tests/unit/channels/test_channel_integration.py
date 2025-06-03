"""
Unit tests for channel integration module.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from ai_whisperer.channels.integration import ChannelIntegration, get_channel_integration
from ai_whisperer.channels.types import ChannelType, ChannelMessage, ChannelMetadata
from ai_whisperer.channels.router import ChannelRouter
from ai_whisperer.channels.storage import ChannelStorage


class TestChannelIntegration:
    """Test cases for ChannelIntegration class."""
    
    def test_init(self):
        """Test ChannelIntegration initialization."""
        integration = ChannelIntegration()
        
        assert isinstance(integration._storage, ChannelStorage)
        assert isinstance(integration._routers, dict)
        assert isinstance(integration._visibility_preferences, dict)
        assert integration._default_visibility == {
            "show_commentary": True,
            "show_analysis": False
        }
    
    def test_get_router_creates_new(self):
        """Test get_router creates new router when needed."""
        integration = ChannelIntegration()
        
        router = integration.get_router("session1", "agent1")
        
        assert isinstance(router, ChannelRouter)
        assert "session1:agent1" in integration._routers
        assert integration._routers["session1:agent1"] == router
    
    def test_get_router_returns_existing(self):
        """Test get_router returns existing router."""
        integration = ChannelIntegration()
        
        router1 = integration.get_router("session1", "agent1")
        router2 = integration.get_router("session1", "agent1")
        
        assert router1 is router2
    
    def test_process_ai_response_basic(self):
        """Test processing a basic AI response."""
        integration = ChannelIntegration()
        
        # Test with simple response
        messages = integration.process_ai_response(
            "session1",
            "Hello, how can I help you?",
            agent_id="agent1"
        )
        
        # Should have at least one message
        assert len(messages) > 0
        
        # Check WebSocket format
        msg = messages[0]
        assert msg["type"] == "channel_message"
        assert msg["channel"] in ["analysis", "commentary", "final"]
        assert "content" in msg
        assert "metadata" in msg
    
    def test_process_ai_response_with_channels(self):
        """Test processing AI response with channel markers."""
        integration = ChannelIntegration()
        
        # Enable analysis visibility to see all channels
        integration.set_visibility_preferences("session1", True, True)
        
        content = """
        [ANALYSIS]I need to understand what the user wants[/ANALYSIS]
        [COMMENTARY]Preparing response[/COMMENTARY]
        [FINAL]I'll help you with that task.[/FINAL]
        """
        
        messages = integration.process_ai_response(
            "session1",
            content,
            agent_id="agent1"
        )
        
        # Should have messages for each channel
        channels = [msg["channel"] for msg in messages]
        assert "analysis" in channels
        assert "commentary" in channels
        assert "final" in channels
    
    def test_visibility_filtering(self):
        """Test visibility filtering of messages."""
        integration = ChannelIntegration()
        
        # Set visibility to hide analysis
        integration.set_visibility_preferences("session1", True, False)
        
        content = """
        [ANALYSIS]Internal reasoning[/ANALYSIS]
        [COMMENTARY]Tool execution[/COMMENTARY]
        [FINAL]Here's the result[/FINAL]
        """
        
        messages = integration.process_ai_response(
            "session1",
            content,
            agent_id="agent1"
        )
        
        # Analysis should be filtered out
        channels = [msg["channel"] for msg in messages]
        assert "analysis" not in channels
        assert "commentary" in channels
        assert "final" in channels
    
    def test_websocket_format_conversion(self):
        """Test conversion to WebSocket format."""
        integration = ChannelIntegration()
        
        # Create a test message
        message = ChannelMessage(
            channel=ChannelType.FINAL,
            content="Test content",
            metadata=ChannelMetadata(
                sequence=1,
                timestamp=datetime.now(timezone.utc),
                agent_id="agent1",
                session_id="session1",
                tool_calls=["tool1", "tool2"],
                continuation_depth=2,
                is_partial=False,
                custom={"key": "value"}
            )
        )
        
        result = integration._to_websocket_format(message)
        
        assert result["type"] == "channel_message"
        assert result["channel"] == "final"
        assert result["content"] == "Test content"
        assert result["metadata"]["sequence"] == 1
        assert result["metadata"]["agentId"] == "agent1"
        assert result["metadata"]["sessionId"] == "session1"
        assert result["metadata"]["toolCalls"] == ["tool1", "tool2"]
        assert result["metadata"]["continuationDepth"] == 2
        assert result["metadata"]["isPartial"] is False
        assert result["metadata"]["key"] == "value"
    
    def test_get_channel_history(self):
        """Test getting channel history."""
        integration = ChannelIntegration()
        
        # Add some messages first
        integration.process_ai_response("session1", "Message 1")
        integration.process_ai_response("session1", "[ANALYSIS]Analysis[/ANALYSIS]")
        integration.process_ai_response("session1", "[COMMENTARY]Commentary[/COMMENTARY]")
        
        # Get all history
        history = integration.get_channel_history("session1")
        
        assert "messages" in history
        assert "totalCount" in history
        assert history["totalCount"] > 0
        
        # Get specific channel
        history = integration.get_channel_history("session1", channels=["analysis"])
        messages = history["messages"]
        for msg in messages:
            assert msg["channel"] == "analysis"
    
    def test_visibility_preferences(self):
        """Test visibility preference management."""
        integration = ChannelIntegration()
        
        # Default preferences
        prefs = integration.get_visibility_preferences("session1")
        assert prefs["show_commentary"] is True
        assert prefs["show_analysis"] is False
        
        # Update preferences
        integration.set_visibility_preferences("session1", False, True)
        
        prefs = integration.get_visibility_preferences("session1")
        assert prefs["show_commentary"] is False
        assert prefs["show_analysis"] is True
    
    def test_clear_session(self):
        """Test clearing session data."""
        integration = ChannelIntegration()
        
        # Add data
        integration.process_ai_response("session1", "Test message")
        integration.set_visibility_preferences("session1", True, True)
        router = integration.get_router("session1", "agent1")
        
        # Clear session
        integration.clear_session("session1")
        
        # Check data is cleared
        stats = integration.get_session_stats("session1")
        # Stats should show 0 messages for all channels
        assert stats.get("final_count", 0) == 0
        assert stats.get("analysis_count", 0) == 0
        assert stats.get("commentary_count", 0) == 0
        
        # Preferences should be reset
        prefs = integration.get_visibility_preferences("session1")
        assert prefs == integration._default_visibility
    
    def test_get_session_stats(self):
        """Test getting session statistics."""
        integration = ChannelIntegration()
        
        # Add various messages
        integration.process_ai_response("session1", "Message 1")
        integration.process_ai_response("session1", "[ANALYSIS]Analysis[/ANALYSIS]")
        integration.process_ai_response("session1", "[COMMENTARY]Commentary[/COMMENTARY]")
        
        stats = integration.get_session_stats("session1")
        
        # Check expected stat fields based on storage implementation
        assert "final_count" in stats
        assert "analysis_count" in stats
        assert "commentary_count" in stats
        assert "visibility" in stats
        
        # Should have at least one message of each type
        assert stats["final_count"] >= 1
        assert stats["analysis_count"] >= 1
        assert stats["commentary_count"] >= 1
    
    def test_cleanup_old_sessions(self):
        """Test cleanup of old sessions."""
        integration = ChannelIntegration()
        
        # Add sessions
        integration.process_ai_response("session1", "Message 1")
        integration.process_ai_response("session2", "Message 2")
        integration.get_router("session1", "agent1")
        integration.get_router("session2", "agent2")
        integration.set_visibility_preferences("session1", True, True)
        integration.set_visibility_preferences("session2", False, False)
        
        # Mock storage cleanup to return 1
        with patch.object(integration._storage, 'cleanup_old_sessions', return_value=1):
            with patch.object(integration._storage, 'get_active_sessions', return_value=["session2"]):
                cleaned = integration.cleanup_old_sessions(24)
        
        assert cleaned == 1
        
        # Session1 should be cleaned from routers and preferences
        assert "session1:agent1" not in integration._routers
        assert "session1" not in integration._visibility_preferences
        
        # Session2 should remain
        assert "session2:agent2" in integration._routers
        assert "session2" in integration._visibility_preferences
    
    def test_partial_responses(self):
        """Test handling of partial responses."""
        integration = ChannelIntegration()
        
        # Process partial response
        messages = integration.process_ai_response(
            "session1",
            "Partial response...",
            is_partial=True
        )
        
        # Check metadata indicates partial
        for msg in messages:
            assert msg["metadata"]["isPartial"] is True
        
        # Process final response
        messages = integration.process_ai_response(
            "session1",
            "Complete response.",
            is_partial=False
        )
        
        for msg in messages:
            assert msg["metadata"]["isPartial"] is False


class TestGetChannelIntegration:
    """Test cases for get_channel_integration function."""
    
    def test_returns_singleton(self):
        """Test that get_channel_integration returns singleton."""
        integration1 = get_channel_integration()
        integration2 = get_channel_integration()
        
        assert integration1 is integration2
        assert isinstance(integration1, ChannelIntegration)
    
    def test_creates_instance_when_none(self):
        """Test that function creates instance when none exists."""
        # Reset global instance
        import ai_whisperer.channels.integration
        ai_whisperer.channels.integration._channel_integration = None
        
        integration = get_channel_integration()
        
        assert integration is not None
        assert isinstance(integration, ChannelIntegration)
        assert ai_whisperer.channels.integration._channel_integration is integration