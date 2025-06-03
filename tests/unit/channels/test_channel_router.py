"""
Unit tests for channel router.
"""

import pytest
from ai_whisperer.channels.router import ChannelRouter
from ai_whisperer.channels.types import ChannelType


class TestChannelRouter:
    """Test ChannelRouter functionality."""
    
    @pytest.fixture
    def router(self):
        """Create a router instance."""
        return ChannelRouter(session_id="test_session", agent_id="test_agent")
    
    def test_route_explicit_channels(self, router):
        """Test routing content with explicit channel markers."""
        content = """
        [ANALYSIS]
        I need to think about this problem...
        [/ANALYSIS]
        
        [COMMENTARY]
        {"tool": "search_files", "query": "test"}
        [/COMMENTARY]
        
        [FINAL]
        I'll search for the test files now.
        [/FINAL]
        """
        
        messages = router.route_response(content)
        
        assert len(messages) == 3
        
        # Check analysis message
        analysis = next(m for m in messages if m.channel == ChannelType.ANALYSIS)
        assert "think about this problem" in analysis.content
        
        # Check commentary message
        commentary = next(m for m in messages if m.channel == ChannelType.COMMENTARY)
        assert "search_files" in commentary.content
        
        # Check final message
        final = next(m for m in messages if m.channel == ChannelType.FINAL)
        assert "search for the test files" in final.content
    
    def test_route_unmarked_tool_calls(self, router):
        """Test routing unmarked content with tool calls."""
        content = """
        Let me search for that file.
        
        ```json
        {"tool": "search_files", "query": "config.py"}
        ```
        
        I found the configuration file.
        """
        
        messages = router.route_response(content)
        
        # Should have commentary and final messages
        assert len(messages) == 2
        
        commentary = next(m for m in messages if m.channel == ChannelType.COMMENTARY)
        assert "search_files" in commentary.content
        assert commentary.metadata.tool_calls is not None
        
        final = next(m for m in messages if m.channel == ChannelType.FINAL)
        assert "Let me search" in final.content
        assert "found the configuration" in final.content
    
    def test_route_continuation_metadata(self, router):
        """Test routing continuation metadata to analysis channel."""
        content = "Processing complete. CONTINUE: true"
        
        messages = router.route_response(content)
        
        assert len(messages) == 1
        assert messages[0].channel == ChannelType.ANALYSIS
        assert messages[0].metadata.custom.get("contains_continuation") is True
    
    def test_route_plain_text(self, router):
        """Test routing plain text defaults to final channel."""
        content = "Here's the answer to your question."
        
        messages = router.route_response(content)
        
        assert len(messages) == 1
        assert messages[0].channel == ChannelType.FINAL
        assert messages[0].content == content
    
    def test_partial_response_handling(self, router):
        """Test handling of partial responses."""
        content = "[FINAL]Still thinking..."
        
        messages = router.route_response(content, is_partial=True)
        
        assert len(messages) == 1
        assert messages[0].metadata.is_partial is True
    
    def test_sequence_numbering(self, router):
        """Test that sequence numbers increment correctly."""
        router.route_response("First")
        router.route_response("Second")
        messages = router.route_response("Third")
        
        assert messages[0].metadata.sequence == 3
    
    def test_parse_channel_markers(self, router):
        """Test utility method for parsing channel markers."""
        content = """
        [ANALYSIS]Internal thought[/ANALYSIS]
        <commentary>Tool call</commentary>
        <final>User response</final>
        """
        
        parsed = router.parse_channel_markers(content)
        
        assert len(parsed) == 3
        assert (ChannelType.ANALYSIS, "Internal thought") in parsed
        assert (ChannelType.COMMENTARY, "Tool call") in parsed
        assert (ChannelType.FINAL, "User response") in parsed
    
    def test_detect_channel_hints(self, router):
        """Test channel hint detection."""
        content = """
        [ANALYSIS]Thinking[/ANALYSIS]
        {"tool": "test"}
        CONTINUE: true
        """
        
        hints = router.detect_channel_hints(content)
        
        assert hints["has_analysis_markers"] is True
        assert hints["has_tool_calls"] is True
        assert hints["has_continuation"] is True
        assert hints["has_final_markers"] is False
    
    def test_alternative_channel_markers(self, router):
        """Test alternative channel marker formats."""
        content = """
        <thinking>This is my analysis</thinking>
        <tool_call>{"function": "search"}</tool_call>
        """
        
        messages = router.route_response(content)
        
        assert len(messages) == 2
        
        analysis = next(m for m in messages if m.channel == ChannelType.ANALYSIS)
        assert "This is my analysis" in analysis.content
        
        commentary = next(m for m in messages if m.channel == ChannelType.COMMENTARY)
        assert "search" in commentary.content