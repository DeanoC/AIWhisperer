"""
Test the existing synchronous mail switching mechanism.

This tests the current implementation where send_mail to another agent
triggers a synchronous switch via AgentSwitchHandler.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from interactive_server.agent_switch_handler import AgentSwitchHandler
from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox


class TestExistingSyncMailSwitch:
    """Test the existing synchronous mail switching."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        session = Mock()
        session.active_agent = "a"  # Alice
        session.agents = {
            "a": Mock(context=Mock()),
            "d": Mock(context=Mock())
        }
        session.switch_agent = AsyncMock()
        session.send_user_message = AsyncMock(return_value={
            "response": "I've checked my mailbox and found your message!"
        })
        return session
    
    @pytest.fixture
    def handler(self, mock_session):
        """Create handler with mock session."""
        return AgentSwitchHandler(mock_session)
    
    @pytest.mark.asyncio
    async def test_send_mail_triggers_switch(self, handler):
        """Test that send_mail to agent triggers switch."""
        # Arrange
        tool_calls = [{
            "function": {
                "name": "send_mail",
                "arguments": json.dumps({
                    "to_agent": "Debbie",
                    "subject": "Test",
                    "body": "Please analyze workspace"
                })
            }
        }]
        tool_results = "Mail sent successfully to Debbie"
        
        # Act
        switch_occurred, additional_response = await handler.handle_tool_results(
            tool_calls, tool_results
        )
        
        # Assert
        assert switch_occurred is True
        assert handler.session.switch_agent.call_count == 2  # Switch to Debbie, then back
        
        # Verify switch sequence
        calls = handler.session.switch_agent.call_args_list
        assert calls[0][0][0] == "d"  # First switch to Debbie
        assert calls[1][0][0] == "a"  # Then back to Alice
        
    @pytest.mark.asyncio
    async def test_mail_to_user_no_switch(self, handler):
        """Test that mail to user doesn't trigger switch."""
        # Arrange - mail without to_agent (goes to user)
        tool_calls = [{
            "function": {
                "name": "send_mail", 
                "arguments": json.dumps({
                    "subject": "Update",
                    "body": "Task completed"
                })
            }
        }]
        tool_results = "Mail sent successfully"
        
        # Act
        switch_occurred, _ = await handler.handle_tool_results(
            tool_calls, tool_results
        )
        
        # Assert
        assert switch_occurred is False
        handler.session.switch_agent.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_failed_mail_no_switch(self, handler):
        """Test that failed mail doesn't trigger switch."""
        # Arrange
        tool_calls = [{
            "function": {
                "name": "send_mail",
                "arguments": json.dumps({
                    "to_agent": "Debbie",
                    "subject": "Test"
                })
            }
        }]
        tool_results = "Error: Failed to send mail"
        
        # Act
        switch_occurred, _ = await handler.handle_tool_results(
            tool_calls, tool_results
        )
        
        # Assert
        assert switch_occurred is False
        handler.session.switch_agent.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_agent_name_mapping(self, handler):
        """Test various agent name formats are mapped correctly."""
        test_cases = [
            ("debbie", "d"),
            ("Debbie", "d"),
            ("debbie the debugger", "d"),
            ("patricia", "p"),
            ("Patricia the Planner", "p"),
            ("alice", "a"),
            ("eamonn", "e")
        ]
        
        for name, expected_id in test_cases:
            tool_calls = [{
                "function": {
                    "name": "send_mail",
                    "arguments": json.dumps({
                        "to_agent": name,
                        "subject": "Test"
                    })
                }
            }]
            
            await handler.handle_tool_results(tool_calls, "Mail sent successfully")
            
            # Check that switch was called with correct ID
            handler.session.switch_agent.assert_called()
            first_call = handler.session.switch_agent.call_args_list[-2][0][0]
            assert first_call == expected_id
            
            # Reset for next test
            handler.session.switch_agent.reset_mock()
            
    @pytest.mark.asyncio
    async def test_switch_stack_management(self, handler):
        """Test that switch stack properly tracks nested switches."""
        # Initial state
        assert len(handler.switch_stack) == 0
        
        # Perform switch
        tool_calls = [{
            "function": {
                "name": "send_mail",
                "arguments": json.dumps({
                    "to_agent": "Debbie",
                    "subject": "Test"
                })
            }
        }]
        
        await handler.handle_tool_results(tool_calls, "Mail sent successfully")
        
        # Stack should be empty after complete switch
        assert len(handler.switch_stack) == 0
        
    @pytest.mark.asyncio  
    async def test_error_recovery(self, handler):
        """Test that errors during switch attempt recovery."""
        # Make switch_agent raise an error
        handler.session.switch_agent.side_effect = [
            None,  # First switch succeeds
            Exception("Switch failed")  # Second switch fails
        ]
        
        tool_calls = [{
            "function": {
                "name": "send_mail",
                "arguments": json.dumps({
                    "to_agent": "Debbie",
                    "subject": "Test"
                })
            }
        }]
        
        # Should not raise, but return error response
        switch_occurred, response = await handler.handle_tool_results(
            tool_calls, "Mail sent successfully"
        )
        
        assert switch_occurred is True
        assert "Error" in response