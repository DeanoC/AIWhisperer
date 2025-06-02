"""
Unit tests for ai_whisperer.tools.message_injector_tool

Tests for the MessageInjectorTool that injects messages into AI sessions
to unstick agents or simulate user responses. This is a HIGH PRIORITY
module with 10/10 complexity score.
"""

import pytest
import time
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ai_whisperer.tools.message_injector_tool import (
    MessageInjectorTool, InjectionType, InjectionResult
)
from ai_whisperer.core.logging import LogLevel, ComponentType, LogSource


class TestInjectionType:
    """Test InjectionType enum."""
    
    def test_injection_type_values(self):
        """Test all injection type values."""
        assert InjectionType.CONTINUATION.value == "continuation"
        assert InjectionType.USER_MESSAGE.value == "user_message"
        assert InjectionType.SYSTEM_PROMPT.value == "system_prompt"
        assert InjectionType.ERROR_RECOVERY.value == "error_recovery"
        assert InjectionType.RESET.value == "reset"
    
    def test_injection_type_from_string(self):
        """Test creating injection type from string."""
        assert InjectionType("continuation") == InjectionType.CONTINUATION
        assert InjectionType("error_recovery") == InjectionType.ERROR_RECOVERY


class TestInjectionResult:
    """Test InjectionResult dataclass."""
    
    def test_injection_result_creation(self):
        """Test creating injection result."""
        timestamp = datetime.now()
        result = InjectionResult(
            success=True,
            session_id="test123",
            injection_type=InjectionType.CONTINUATION,
            message="Continue",
            timestamp=timestamp
        )
        
        assert result.success is True
        assert result.session_id == "test123"
        assert result.injection_type == InjectionType.CONTINUATION
        assert result.message == "Continue"
        assert result.timestamp == timestamp
        assert result.response_received is False
        assert result.response_time_ms is None
        assert result.error is None
    
    def test_injection_result_to_dict(self):
        """Test converting injection result to dict."""
        timestamp = datetime.now()
        result = InjectionResult(
            success=True,
            session_id="test123",
            injection_type=InjectionType.USER_MESSAGE,
            message="Test message",
            timestamp=timestamp,
            response_received=True,
            response_time_ms=150.5,
            error=None
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] is True
        assert result_dict['session_id'] == "test123"
        assert result_dict['injection_type'] == "user_message"
        assert result_dict['message'] == "Test message"
        assert result_dict['timestamp'] == timestamp.isoformat()
        assert result_dict['response_received'] is True
        assert result_dict['response_time_ms'] == 150.5
        assert result_dict['error'] is None


class TestMessageInjectorToolInit:
    """Test MessageInjectorTool initialization."""
    
    def test_init_default(self):
        """Test initialization with default values."""
        tool = MessageInjectorTool()
        
        assert tool.session_manager is None
        assert tool.message_handler is None
        assert tool.injection_history == []
        assert tool.rate_limit == 10
        assert tool.rate_tracker == {}
    
    def test_init_with_handlers(self):
        """Test initialization with session manager and message handler."""
        mock_session_manager = Mock()
        mock_message_handler = Mock()
        
        tool = MessageInjectorTool(
            session_manager=mock_session_manager,
            message_handler=mock_message_handler
        )
        
        assert tool.session_manager == mock_session_manager
        assert tool.message_handler == mock_message_handler
    
    def test_tool_properties(self):
        """Test tool name and description properties."""
        tool = MessageInjectorTool()
        
        assert tool.name == "message_injector"
        assert "unstick agents" in tool.description
        assert tool.category == "Debugging"
        assert "debugging" in tool.tags
        assert "recovery" in tool.tags
    
    def test_parameters_schema(self):
        """Test parameters schema definition."""
        tool = MessageInjectorTool()
        schema = tool.parameters_schema
        
        assert schema["type"] == "object"
        assert "session_id" in schema["properties"]
        assert "message" in schema["properties"]
        assert "injection_type" in schema["properties"]
        assert "wait_for_response" in schema["properties"]
        assert "timeout_seconds" in schema["properties"]
        
        # Check required fields
        assert "session_id" in schema["required"]
        
        # Check enums
        injection_types = schema["properties"]["injection_type"]["enum"]
        assert "continuation" in injection_types
        assert "error_recovery" in injection_types
    
    def test_ai_prompt_instructions(self):
        """Test AI prompt instructions."""
        tool = MessageInjectorTool()
        instructions = tool.get_ai_prompt_instructions()
        
        assert "unstick agents" in instructions.lower()
        assert "continuation" in instructions
        assert "error_recovery" in instructions
        assert "rate limited" in instructions.lower()


class TestMessageInjectorTemplates:
    """Test injection message templates."""
    
    def test_continuation_templates(self):
        """Test continuation message templates."""
        tool = MessageInjectorTool()
        templates = tool.INJECTION_TEMPLATES[InjectionType.CONTINUATION]
        
        assert len(templates) > 0
        assert any("continue" in t.lower() for t in templates)
        assert any("task" in t.lower() for t in templates)
    
    def test_error_recovery_templates(self):
        """Test error recovery templates."""
        tool = MessageInjectorTool()
        templates = tool.INJECTION_TEMPLATES[InjectionType.ERROR_RECOVERY]
        
        assert len(templates) > 0
        assert any("error" in t.lower() for t in templates)
        assert any("retry" in t.lower() or "different" in t.lower() for t in templates)
    
    def test_reset_templates(self):
        """Test reset templates."""
        tool = MessageInjectorTool()
        templates = tool.INJECTION_TEMPLATES[InjectionType.RESET]
        
        assert len(templates) > 0
        assert any("fresh" in t.lower() or "reset" in t.lower() for t in templates)


class TestMessageGeneration:
    """Test message generation functionality."""
    
    def test_generate_message_from_template(self):
        """Test generating message from templates."""
        tool = MessageInjectorTool()
        
        # Test continuation message
        msg = tool._generate_message(InjectionType.CONTINUATION, "session123")
        assert msg in tool.INJECTION_TEMPLATES[InjectionType.CONTINUATION]
    
    def test_generate_message_rotation(self):
        """Test that messages rotate through templates."""
        tool = MessageInjectorTool()
        
        # Generate multiple messages
        messages = []
        for i in range(10):
            tool.injection_history.append(Mock())  # Simulate history
            msg = tool._generate_message(InjectionType.CONTINUATION, "session123")
            messages.append(msg)
        
        # Should use different templates
        unique_messages = set(messages)
        assert len(unique_messages) > 1
    
    def test_generate_message_no_template(self):
        """Test generating message for types without templates."""
        tool = MessageInjectorTool()
        
        # User message type
        msg = tool._generate_message(InjectionType.USER_MESSAGE, "session123")
        assert "status update" in msg.lower()
        
        # System prompt type
        msg = tool._generate_message(InjectionType.SYSTEM_PROMPT, "session123")
        assert "system" in msg.lower()


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_check_under_limit(self):
        """Test rate limit check when under limit."""
        tool = MessageInjectorTool()
        
        # First injection should pass
        assert tool._check_rate_limit("session123") is True
        
        # Multiple injections under limit should pass
        for _ in range(5):
            assert tool._check_rate_limit("session123") is True
    
    def test_rate_limit_check_at_limit(self):
        """Test rate limit check when at limit."""
        tool = MessageInjectorTool()
        
        # Fill up to rate limit
        for _ in range(tool.rate_limit):
            assert tool._check_rate_limit("session123") is True
        
        # Next injection should fail
        assert tool._check_rate_limit("session123") is False
    
    def test_rate_limit_time_window(self):
        """Test rate limit resets after time window."""
        tool = MessageInjectorTool()
        
        # Fill up rate limit
        now = time.time()
        tool.rate_tracker["session123"] = [now - 70] * tool.rate_limit  # 70s ago
        
        # Should pass since old entries are outside window
        assert tool._check_rate_limit("session123") is True
    
    def test_rate_limit_multiple_sessions(self):
        """Test rate limits are per session."""
        tool = MessageInjectorTool()
        
        # Fill limit for session1
        for _ in range(tool.rate_limit):
            tool._check_rate_limit("session1")
        
        # session2 should still be allowed
        assert tool._check_rate_limit("session2") is True


class TestSessionValidation:
    """Test session validation functionality."""
    
    def test_get_current_session_no_manager(self):
        """Test getting current session without manager."""
        tool = MessageInjectorTool()
        
        session_id = tool._get_current_session_id()
        assert session_id is None
    
    def test_get_current_session_with_manager(self):
        """Test getting current session with manager."""
        mock_manager = Mock()
        mock_manager.current_session_id = "active123"
        
        tool = MessageInjectorTool(session_manager=mock_manager)
        
        session_id = tool._get_current_session_id()
        assert session_id == "active123"
    
    def test_validate_session_no_manager(self):
        """Test session validation without manager."""
        tool = MessageInjectorTool()
        
        # Should return True (mock validation)
        assert tool._validate_session("any_session") is True
    
    def test_validate_session_with_manager(self):
        """Test session validation with manager."""
        mock_manager = Mock()
        mock_manager.is_session_active.return_value = True
        
        tool = MessageInjectorTool(session_manager=mock_manager)
        
        assert tool._validate_session("session123") is True
        mock_manager.is_session_active.assert_called_once_with("session123")


class TestMessageInjection:
    """Test message injection functionality."""
    
    def test_execute_basic_injection(self):
        """Test basic message injection."""
        tool = MessageInjectorTool()
        
        result = tool.execute(
            session_id="test123",
            message="Test injection",
            injection_type="continuation"
        )
        
        assert result["success"] is True
        assert result["result"]["session_id"] == "test123"
        assert result["result"]["message"] == "Test injection"
        assert result["result"]["injection_type"] == "continuation"
    
    def test_execute_invalid_injection_type(self):
        """Test injection with invalid type."""
        tool = MessageInjectorTool()
        
        result = tool.execute(
            session_id="test123",
            message="Test",
            injection_type="invalid_type"
        )
        
        assert "error" in result
        assert "Invalid injection type" in result["error"]
    
    def test_execute_current_session_no_active(self):
        """Test injection to current session when none active."""
        tool = MessageInjectorTool()
        
        result = tool.execute(
            session_id="current",
            injection_type="continuation"
        )
        
        assert "error" in result
        assert "No active session" in result["error"]
    
    def test_execute_rate_limit_exceeded(self):
        """Test injection when rate limit exceeded."""
        tool = MessageInjectorTool()
        
        # Fill rate limit
        for _ in range(tool.rate_limit):
            tool._check_rate_limit("test123")
        
        result = tool.execute(
            session_id="test123",
            injection_type="continuation"
        )
        
        assert result["success"] is False
        assert "Rate limit exceeded" in result["error"]
    
    def test_execute_auto_generate_message(self):
        """Test injection with auto-generated message."""
        tool = MessageInjectorTool()
        
        result = tool.execute(
            session_id="test123",
            injection_type="continuation"
        )
        
        # Should generate message from templates
        generated_msg = result["result"]["message"]
        assert generated_msg in tool.INJECTION_TEMPLATES[InjectionType.CONTINUATION]
    
    def test_execute_with_message_handler(self):
        """Test injection with message handler."""
        mock_handler = Mock()
        mock_handler.send_message = Mock()
        
        tool = MessageInjectorTool(message_handler=mock_handler)
        
        result = tool.execute(
            session_id="test123",
            message="Test message",
            injection_type="user_message",
            wait_for_response=False
        )
        
        assert result["success"] is True
        mock_handler.send_message.assert_called_once()
    
    def test_execute_with_async_handler(self):
        """Test injection with async message handler."""
        mock_handler = Mock()
        mock_handler.send_message = AsyncMock()
        
        tool = MessageInjectorTool(message_handler=mock_handler)
        
        # Create event loop and run the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = tool.execute(
                session_id="test123",
                message="Async test",
                injection_type="continuation",
                wait_for_response=False
            )
            
            # For async handler, it creates a task and runs it
            assert result["success"] is True
            loop.run_until_complete(asyncio.sleep(0.1))  # Let async tasks complete
        finally:
            # Clean up pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            asyncio.set_event_loop(None)


class TestResponseHandling:
    """Test response waiting functionality."""
    
    def test_wait_for_response_no_manager(self):
        """Test waiting for response without session manager."""
        tool = MessageInjectorTool()
        
        start = time.time()
        # Should do mock wait
        received = tool._wait_for_response("test123", 1)
        elapsed = time.time() - start
        
        assert received is True
        assert elapsed >= 0.5  # Mock wait time
    
    def test_wait_for_response_timeout(self):
        """Test response timeout."""
        mock_manager = Mock()
        tool = MessageInjectorTool(session_manager=mock_manager)
        
        # Mock no response
        with patch.object(tool, '_check_for_response', return_value=False):
            start = time.time()
            received = tool._wait_for_response("test123", 0.5)
            elapsed = time.time() - start
            
            assert received is False
            assert elapsed >= 0.5
    
    def test_check_for_response_mock(self):
        """Test mock response checking."""
        tool = MessageInjectorTool()
        
        # Mock always returns True after 1 second
        start = time.time()
        
        # Should return False immediately
        assert tool._check_for_response("test123", start) is False
        
        # Should return True after 1+ seconds
        time.sleep(1.1)
        assert tool._check_for_response("test123", start) is True


class TestInjectionHistory:
    """Test injection history tracking."""
    
    def test_track_injection(self):
        """Test tracking injection in history."""
        tool = MessageInjectorTool()
        
        result = InjectionResult(
            success=True,
            session_id="test123",
            injection_type=InjectionType.CONTINUATION,
            message="Test",
            timestamp=datetime.now()
        )
        
        tool._track_injection(result)
        
        assert len(tool.injection_history) == 1
        assert tool.injection_history[0] == result
    
    def test_history_size_limit(self):
        """Test history size is limited."""
        tool = MessageInjectorTool()
        
        # Add more than limit
        for i in range(150):
            result = InjectionResult(
                success=True,
                session_id=f"session{i}",
                injection_type=InjectionType.CONTINUATION,
                message="Test",
                timestamp=datetime.now()
            )
            tool._track_injection(result)
        
        # Should keep only last 100
        assert len(tool.injection_history) == 100
        assert tool.injection_history[0].session_id == "session50"
    
    def test_get_injection_history_all(self):
        """Test getting all injection history."""
        tool = MessageInjectorTool()
        
        # Add some injections
        for i in range(5):
            tool.injection_history.append(
                InjectionResult(
                    success=True,
                    session_id=f"session{i}",
                    injection_type=InjectionType.CONTINUATION,
                    message="Test",
                    timestamp=datetime.now()
                )
            )
        
        history = tool.get_injection_history(last_n=10)
        
        assert len(history) == 5
        assert all(isinstance(h, dict) for h in history)
    
    def test_get_injection_history_filtered(self):
        """Test getting filtered injection history."""
        tool = MessageInjectorTool()
        
        # Add various injections
        for i in range(10):
            tool.injection_history.append(
                InjectionResult(
                    success=True,
                    session_id="session1" if i < 5 else "session2",
                    injection_type=InjectionType.CONTINUATION if i % 2 == 0 else InjectionType.ERROR_RECOVERY,
                    message="Test",
                    timestamp=datetime.now()
                )
            )
        
        # Filter by session
        history = tool.get_injection_history(session_id="session1")
        assert len(history) == 5
        
        # Filter by type
        history = tool.get_injection_history(injection_type=InjectionType.ERROR_RECOVERY)
        assert len(history) == 5
        
        # Filter by both
        history = tool.get_injection_history(
            session_id="session2",
            injection_type=InjectionType.CONTINUATION
        )
        assert len(history) == 2


class TestLogging:
    """Test logging functionality."""
    
    @patch('ai_whisperer.tools.message_injector_tool.logger')
    def test_log_injection_success(self, mock_logger):
        """Test logging successful injection."""
        tool = MessageInjectorTool()
        
        result = InjectionResult(
            success=True,
            session_id="test123",
            injection_type=InjectionType.CONTINUATION,
            message="Test",
            timestamp=datetime.now(),
            response_received=True,
            response_time_ms=100.0
        )
        
        tool._log_injection(result)
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "continuation" in call_args[0][0]
        assert "test123" in call_args[0][0]
    
    @patch('ai_whisperer.tools.message_injector_tool.logger')
    def test_log_injection_error(self, mock_logger):
        """Test logging failed injection."""
        tool = MessageInjectorTool()
        
        result = InjectionResult(
            success=False,
            session_id="test123",
            injection_type=InjectionType.ERROR_RECOVERY,
            message="Test",
            timestamp=datetime.now(),
            error="Connection failed"
        )
        
        tool._log_injection(result)
        
        mock_logger.info.assert_called_once()
        extra = mock_logger.info.call_args[1]['extra']
        assert extra['level'] == LogLevel.ERROR.value  # Compare string values
        assert extra['details']['error'] == "Connection failed"


class TestErrorHandling:
    """Test error handling in execute method."""
    
    def test_execute_exception_handling(self):
        """Test exception handling in execute."""
        tool = MessageInjectorTool()
        
        # Mock internal method to raise exception
        with patch.object(tool, '_validate_session', side_effect=Exception("Test error")):
            result = tool.execute(
                session_id="test123",
                injection_type="continuation"
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "Test error" in result["error"]
    
    def test_invalid_session_validation(self):
        """Test handling invalid session."""
        mock_manager = Mock()
        mock_manager.is_session_active.return_value = False
        
        tool = MessageInjectorTool(session_manager=mock_manager)
        
        result = tool.execute(
            session_id="invalid123",
            injection_type="continuation"
        )
        
        assert "error" in result
        assert "not found or inactive" in result["error"]


class TestMockInjection:
    """Test mock injection for testing mode."""
    
    def test_mock_injection_result(self):
        """Test mock injection returns proper result."""
        tool = MessageInjectorTool()
        
        timestamp = datetime.now()
        result = tool._mock_injection(
            "test123",
            "Mock message",
            InjectionType.USER_MESSAGE,
            timestamp
        )
        
        assert result.success is True
        assert result.session_id == "test123"
        assert result.message == "Mock message"
        assert result.injection_type == InjectionType.USER_MESSAGE
        assert result.timestamp == timestamp
        assert result.response_received is True
        assert result.response_time_ms == 200.0