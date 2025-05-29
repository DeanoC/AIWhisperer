"""
Test continuation depth tracking in stateless session manager.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import WebSocket

from interactive_server.stateless_session_manager import StatelessInteractiveSession


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    ws = Mock(spec=WebSocket)
    ws.send_json = AsyncMock()
    return ws


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "openrouter": {
            "api_key": "test-key",
            "model": "google/gemini-2.5-flash-preview",
            "params": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
    }


@pytest.fixture
def session(mock_websocket, mock_config):
    """Create a test session."""
    return StatelessInteractiveSession(
        session_id="test-session",
        websocket=mock_websocket,
        config=mock_config
    )


@pytest.mark.asyncio
async def test_continuation_depth_reset_on_non_tool_response(session):
    """Test that continuation depth resets when receiving a non-tool response."""
    # Set initial depth
    session._continuation_depth = 2
    
    # Create a mock agent
    await session.create_agent("test", "Test agent")
    
    # Mock agent to return a non-tool response
    mock_agent = session.agents["test"]
    mock_agent.process_message = AsyncMock(return_value={
        'response': 'Just a text response',
        'tool_calls': None
    })
    
    # Send message
    await session.send_user_message("Hello")
    
    # Verify depth was reset
    assert session._continuation_depth == 0


@pytest.mark.asyncio
async def test_continuation_depth_increments_on_tool_continuation(session):
    """Test that continuation depth increments when continuing after tools."""
    # Create a mock agent
    await session.create_agent("test", "Test agent")
    
    # Mock agent to return tool calls first, then text
    mock_agent = session.agents["test"]
    call_count = 0
    
    async def mock_process(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: return tool call
            return {
                'response': 'Let me list the RFCs',
                'tool_calls': [{'function': {'name': 'list_rfcs'}}]
            }
        else:
            # Continuation: return text only
            return {
                'response': 'Here are the RFCs listed above',
                'tool_calls': None
            }
    
    mock_agent.process_message = mock_process
    
    # Mock _should_continue_after_tools to return True once
    with patch.object(session, '_should_continue_after_tools') as mock_should_continue:
        mock_should_continue.side_effect = [True, False]
        
        # Send message
        await session.send_user_message("List RFCs")
        
        # Verify depth was incremented then reset
        assert session._continuation_depth == 0  # Reset after completion
        assert call_count == 2  # Original + 1 continuation


@pytest.mark.asyncio
async def test_max_continuation_depth_prevents_infinite_loop(session):
    """Test that max continuation depth prevents infinite loops."""
    # Create a mock agent
    await session.create_agent("test", "Test agent")
    
    # Mock agent to always return tool calls
    mock_agent = session.agents["test"]
    mock_agent.process_message = AsyncMock(return_value={
        'response': 'Always using tools',
        'tool_calls': [{'function': {'name': 'some_tool'}}]
    })
    
    # Mock _should_continue_after_tools to always return True
    with patch.object(session, '_should_continue_after_tools', return_value=True):
        # Send message
        result = await session.send_user_message("Do something")
        
        # Verify we hit the max depth
        assert session._continuation_depth == 0  # Reset after hitting max
        
        # Verify we called process_message exactly max_depth + 1 times
        # (1 original + max_continuation_depth continuations)
        assert mock_agent.process_message.call_count == session._max_continuation_depth + 1


@pytest.mark.asyncio
async def test_continuation_depth_reset_on_error(session):
    """Test that continuation depth resets on error."""
    # Set initial depth
    session._continuation_depth = 2
    
    # Create a mock agent
    await session.create_agent("test", "Test agent")
    
    # Mock agent to raise an error
    mock_agent = session.agents["test"]
    mock_agent.process_message = AsyncMock(side_effect=Exception("Test error"))
    
    # Send message and expect error
    with pytest.raises(Exception, match="Test error"):
        await session.send_user_message("Hello")
    
    # Verify depth was reset
    assert session._continuation_depth == 0


@pytest.mark.asyncio
async def test_continuation_with_is_continuation_flag(session):
    """Test that is_continuation flag is properly passed in recursive calls."""
    # Create a mock agent
    await session.create_agent("test", "Test agent")
    
    # Track calls with is_continuation parameter
    original_send = session.send_user_message
    calls = []
    
    async def track_calls(msg, is_continuation=False):
        calls.append((msg, is_continuation))
        # Only continue once to avoid infinite recursion
        if not is_continuation:
            return await original_send(msg, is_continuation)
        else:
            # Return a non-tool response to stop continuation
            session.agents["test"].process_message = AsyncMock(return_value={
                'response': 'Done',
                'tool_calls': None
            })
            return await original_send(msg, is_continuation)
    
    # Patch send_user_message to track calls
    session.send_user_message = track_calls
    
    # Mock agent to return tool calls on first call
    mock_agent = session.agents["test"]
    mock_agent.process_message = AsyncMock(return_value={
        'response': 'Using tools',
        'tool_calls': [{'function': {'name': 'test_tool'}}]
    })
    
    # Mock _should_continue_after_tools
    with patch.object(session, '_should_continue_after_tools') as mock_should_continue:
        mock_should_continue.side_effect = [True, False]
        
        # Send message
        await session.send_user_message("Test message")
        
        # Verify calls
        assert len(calls) >= 2
        assert calls[0] == ("Test message", False)  # Original call
        assert calls[1] == ("Please continue with the next step.", True)  # Continuation