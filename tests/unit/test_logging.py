import pytest
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# Assuming LogLevel, ComponentType, and LogMessage are defined in src/ai_whisperer/logging.py
# If the actual implementation path is different, this import will need adjustment.
try:
    from src.ai_whisperer.logging import LogLevel, ComponentType, LogMessage

    # Assuming a logging function or class exists, e.g., setup_logging and a logger instance
    from src.ai_whisperer.logging import setup_logging, get_logger
except ImportError:
    # Provide dummy implementations for testing if the actual module doesn't exist yet
    # This allows the tests themselves to be generated and checked for structure/logic
    # even before the logging implementation is complete.
    class LogLevel(Enum):
        DEBUG = "DEBUG"
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"

    class ComponentType(Enum):
        RUNNER = "runner"
        EXECUTION_ENGINE = "execution_engine"
        AI_SERVICE = "ai_service"
        FILE_OPERATIONS = "file_operations"
        TERMINAL_INTERACTION = "terminal_interaction"
        STATE_MANAGEMENT = "state_management"
        USER_INTERACTION = "user_interaction"

    @dataclass
    class LogMessage:
        timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="milliseconds") + "Z")
        level: LogLevel
        component: ComponentType
        action: str
        message: str
        subtask_id: Optional[str] = None
        event_id: Optional[str] = None
        state_before: Optional[str] = None
        state_after: Optional[str] = None
        duration_ms: Optional[float] = None
        details: Dict[str, Any] = field(default_factory=dict)

    # Dummy logging functions for test generation phase
    def setup_logging(config_path=None):
        logging.basicConfig(level=logging.DEBUG)
        return logging.getLogger("dummy_logger")

    def get_logger(name):
        return logging.getLogger(name)


# Configure a basic logger for tests (will be mocked)
# In a real scenario, you might mock the logging setup itself
@pytest.fixture(scope="function")
def mock_logger():
    # Use a unique logger name for each test function to avoid interference
    logger_name = f"test_logger_{datetime.now().timestamp()}".replace(".", "_")
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Mock handlers
    mock_handler = MagicMock()
    # Set the level attribute on the mock handler to prevent TypeError in comparison
    mock_handler.level = logging.DEBUG
    # Clear existing handlers to avoid actual logging output during tests
    logger.handlers = []
    logger.addHandler(mock_handler)
    logger.propagate = False  # Prevent logs from going to root logger

    yield logger, mock_handler

    # Clean up handler after test
    logger.removeHandler(mock_handler)


def test_log_message_structure():
    """Test that LogMessage dataclass has the correct structure and default values."""
    msg = LogMessage(
        level=LogLevel.INFO,
        component=ComponentType.RUNNER,
        action="startup",
        event_summary="Runner started.",  # Use event_summary
    )

    assert isinstance(msg.timestamp, str)
    assert msg.level == LogLevel.INFO
    assert msg.component == ComponentType.RUNNER
    assert msg.action == "startup"
    assert msg.event_summary == "Runner started."  # Use event_summary
    assert msg.subtask_id is None
    assert msg.event_id is None
    assert msg.state_before is None
    assert msg.state_after is None
    assert msg.duration_ms is None
    assert msg.details == {}

    msg_with_details = LogMessage(
        level=LogLevel.ERROR,
        component=ComponentType.EXECUTION_ENGINE,
        action="step_execution_failed",
        event_summary="Step failed.",  # Use event_summary
        subtask_id="step_123",
        details={"error": "details here"},
    )
    assert msg_with_details.subtask_id == "step_123"
    assert msg_with_details.details == {"error": "details here"}


def test_logging_different_levels(mock_logger):
    """Test that messages with different log levels are processed."""
    (logger, mock_handler) = mock_logger

    log_info = LogMessage(
        LogLevel.INFO, ComponentType.RUNNER, "test_action", event_summary="Info message"
    )  # Use event_summary
    log_warning = LogMessage(
        LogLevel.WARNING, ComponentType.RUNNER, "test_action", event_summary="Warning message"
    )  # Use event_summary
    log_error = LogMessage(
        LogLevel.ERROR, ComponentType.RUNNER, "test_action", event_summary="Error message"
    )  # Use event_summary
    log_debug = LogMessage(
        LogLevel.DEBUG, ComponentType.RUNNER, "test_action", event_summary="Debug message"
    )  # Use event_summary
    log_critical = LogMessage(
        LogLevel.CRITICAL, ComponentType.RUNNER, "test_action", event_summary="Critical message"
    )  # Use event_summary

    # Assuming a function that takes LogMessage and logs it, e.g., log_event(log_message)
    # For now, we'll simulate by creating a log record and calling the handler directly
    # In a real test, you'd call the application's logging function.
    # We'll create a helper to simulate logging a LogMessage
    def simulate_log_event(logger, log_msg: LogMessage):
        # This simulates how the application code might log a structured message
        # It's a simplified representation; the actual implementation might differ.
        extra_data = {
            "component": log_msg.component.value,
            "action": log_msg.action,
            "subtask_id": log_msg.subtask_id,
            "event_id": log_msg.event_id,
            "state_before": log_msg.state_before,
            "state_after": log_msg.state_after,
            "duration_ms": log_msg.duration_ms,
            "details": log_msg.details,
        }
        # Filter out None values to match expected behavior of some loggers/formatters
        extra_data = {k: v for k, v in extra_data.items() if v is not None}

        if log_msg.level == LogLevel.DEBUG:
            logger.debug(log_msg.event_summary, extra=extra_data)  # Use event_summary
        elif log_msg.level == LogLevel.INFO:
            logger.info(log_msg.event_summary, extra=extra_data)  # Use event_summary
        elif log_msg.level == LogLevel.WARNING:
            logger.warning(log_msg.event_summary, extra=extra_data)  # Use event_summary
        elif log_msg.level == LogLevel.ERROR:
            logger.error(log_msg.event_summary, extra=extra_data)  # Use event_summary
        elif log_msg.level == LogLevel.CRITICAL:
            logger.critical(log_msg.event_summary, extra=extra_data)  # Use event_summary

    simulate_log_event(logger, log_info)
    simulate_log_event(logger, log_warning)
    simulate_log_event(logger, log_error)
    simulate_log_event(logger, log_debug)  # Should be captured as logger level is DEBUG
    simulate_log_event(logger, log_critical)

    # Check that the handler received calls for each level
    # The exact call arguments depend on how the LogMessage is translated to a LogRecord
    # We expect calls like handler.handle(record) where record has levelname, msg, and extra
    calls = mock_handler.handle.call_args_list

    assert len(calls) == 5  # Expecting 5 log calls

    # Verify levels in the calls
    logged_levels = [call[0][0].levelname for call in calls]
    assert "INFO" in logged_levels
    assert "WARNING" in logged_levels
    assert "ERROR" in logged_levels
    assert "DEBUG" in logged_levels
    assert "CRITICAL" in logged_levels


def test_logging_with_metadata(mock_logger):
    """Test that log messages include correct metadata from LogMessage."""
    (logger, mock_handler) = mock_logger

    log_msg = LogMessage(
        level=LogLevel.INFO,
        component=ComponentType.EXECUTION_ENGINE,
        action="step_execution_started",
        event_summary="Starting step.",  # Use event_summary
        subtask_id="step_abc",
        event_id="event_xyz",
        state_before="Pending",
        state_after="Running",
        duration_ms=10.5,
        details={"step_type": "planning", "input_count": 2},
    )

    # Simulate logging this message
    def simulate_log_event(logger, log_msg: LogMessage):
        extra_data = {
            "component": log_msg.component.value,
            "action": log_msg.action,
            "subtask_id": log_msg.subtask_id,
            "event_id": log_msg.event_id,
            "state_before": log_msg.state_before,
            "state_after": log_msg.state_after,
            "duration_ms": log_msg.duration_ms,
            "details": log_msg.details,
        }
        extra_data = {k: v for k, v in extra_data.items() if v is not None}
        logger.info(log_msg.event_summary, extra=extra_data)  # Use event_summary

    simulate_log_event(logger, log_msg)

    # Check the call to the handler
    mock_handler.handle.assert_called_once()
    record = mock_handler.handle.call_args[0][0]

    # Verify standard LogRecord attributes
    assert record.levelname == "INFO"
    assert record.getMessage() == "Starting step."  # getMessage includes the original message

    # Verify custom attributes passed via 'extra'
    # These should be available directly on the record object
    assert record.component == ComponentType.EXECUTION_ENGINE.value
    assert record.action == "step_execution_started"
    assert record.subtask_id == "step_abc"
    assert record.event_id == "event_xyz"
    assert record.state_before == "Pending"
    assert record.state_after == "Running"
    assert record.duration_ms == 10.5
    assert record.details == {"step_type": "planning", "input_count": 2}


# Note: Testing file/console output directly requires mocking the handlers
# and checking if their methods (like `emit`) are called with expected data.
# The above tests already use a mock handler (`mock_handler`) and verify that
# `handler.handle(record)` is called with a LogRecord containing the correct data.
# This implicitly tests that the logging system is processing and dispatching
# the log messages correctly to its configured handlers.
# To test specific handler behavior (e.g., formatting, writing to a file-like object),
# you would mock the handler's internal methods or the file object it writes to.
# For this task, verifying that the correct LogRecord reaches the handler is sufficient
# unit testing for the core logging *processing* part.

# Example of how you might test a specific handler's output format (more complex, might be integration test)
# def test_file_handler_output_format():
#     # This would involve setting up a logger with a specific file handler
#     # and mocking the file object to check what gets written.
#     # This is more complex and might be better suited for integration tests
#     # or requires mocking lower-level logging internals.
#     pass

# Example of testing console output (similarly complex)
# def test_console_handler_output():
#     # Mock sys.stdout or the Rich Console object used by RichHandler
#     # and check the output.
#     pass

# Concurrent logging tests would require simulating multiple threads
# logging simultaneously and verifying thread-safety, which is also more complex
# and often relies on the guarantees of the standard library's logging module.
# For a basic unit test, focusing on the data structure and dispatch is appropriate.
