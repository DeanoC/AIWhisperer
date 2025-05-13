import pytest
import time # Import time
import logging # Import logging module
from src.ai_whisperer.monitoring import TerminalMonitor
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType # Import ComponentType
import io
import sys
from unittest.mock import Mock # Import Mock

# Helper to capture stdout
@pytest.fixture
def capsys_stdout(capsys):
    # Redirect stdout to a StringIO object
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    yield sys.stdout
    # Restore stdout
    sys.stdout = old_stdout

def test_terminal_monitor_initialization():
    """Test that the TerminalMonitor can be initialized."""
    mock_state_manager = Mock() # Create a mock StateManager
    monitor = TerminalMonitor(state_manager=mock_state_manager) # Pass the mock
    assert isinstance(monitor, TerminalMonitor)

def test_terminal_monitor_segment_layout(capsys_stdout):
    """Test the basic three-segment layout and central subdivision."""
    mock_state_manager = Mock() # Create a mock StateManager
    # Mock the get_global_state and get_task_status methods as they are called in update_display
    mock_state_manager.get_global_state.return_value = "Running"
    mock_state_manager.get_task_status.return_value = "Pending"
    mock_state_manager.state = {"plan": []} # Mock the state attribute

    monitor = TerminalMonitor(state_manager=mock_state_manager) # Pass the mock
    # Simulate some output that would trigger the monitor display
    # This test assumes the monitor's display method is called internally
    # or can be triggered by sending data.
    # For now, we'll simulate sending data and check the output structure.
    # A more robust test would involve mocking dependencies if necessary,
    # but the instruction is to target the existing class directly.

    # Simulate sending a simple message with MONITOR component type
    log_message = LogMessage(
        timestamp=time.time(),
        level=LogLevel.INFO,
        component=ComponentType.MONITOR, # Use MONITOR component type
        action="monitor_event", # Add the action argument
        event_summary="Test message for central segment.",
        subtask_id=None
    )
    # Create a mock LogRecord
    log_record = Mock(spec=logging.LogRecord)
    log_record.levelno = logging.INFO
    log_record.level = LogLevel.INFO # Add level attribute for easier access in test
    log_record.component = ComponentType.MONITOR.value
    log_record.action = "monitor_event"
    log_record.event_summary = "Test message for central segment."
    log_record.subtask_id = None
    log_record.message = "Test message for central segment." # Add message attribute as fallback
    log_record.timestamp = time.time() # Add timestamp attribute
    log_record.details = {} # Add details attribute
    log_record.duration_ms = None # Add duration_ms attribute
    log_record.event_id = None # Add event_id attribute
    log_record.state_before = None # Add state_before attribute
    log_record.state_after = None # Add state_after attribute

    monitor.emit(log_record) # Use emit

    # Since update_display is called within add_log_message when monitor_enabled is True (default)
    # and Live is started in run(), we need to simulate the display update.
    # A more realistic test would involve running the monitor in a separate thread
    # or using a different testing approach for Rich Live displays.
    # For now, we'll directly call update_display to generate the output.
    monitor.update_display()


    captured = capsys_stdout.getvalue()

    # Basic checks for segment presence (using simplified markers for now)
    # These markers would need to correspond to the actual ASCII art output
    assert "Left" in captured # Check for Panel title
    assert "Right" in captured # Check for Panel title
    assert "Logs for Step:" in captured or "General Logs" in captured # Check for Monitor Output Panel title
    assert "Command:" in captured # Check for Command Box Panel title
    assert "AIWhisperer Runner" in captured # Check for Top Border Panel title
    assert "Status" in captured # Check for Bottom Border Panel title


    # Check for the test message in the central segment (monitor output)
    assert "Test message for central segment." in captured

def test_terminal_monitor_ascii_outlining(capsys_stdout):
    """Test that segments are outlined with ASCII characters."""
    mock_state_manager = Mock() # Create a mock StateManager
    mock_state_manager.get_global_state.return_value = "Running"
    mock_state_manager.get_task_status.return_value = "Pending"
    mock_state_manager.state = {"plan": []}

    monitor = TerminalMonitor(state_manager=mock_state_manager) # Pass the mock
    log_message = LogMessage(
        timestamp=time.time(),
        level=LogLevel.INFO,
        component=ComponentType.MONITOR,
        action="monitor_event", # Add the action argument
        event_summary="Testing outlines.",
        subtask_id=None
    )
    # Create a mock LogRecord
    log_record = Mock(spec=logging.LogRecord)
    log_record.levelno = logging.INFO
    log_record.level = LogLevel.INFO # Add level attribute for easier access in test
    log_record.component = ComponentType.MONITOR.value
    log_record.action = "monitor_event"
    log_record.event_summary = "Testing outlines."
    log_record.subtask_id = None
    log_record.message = "Testing outlines." # Add message attribute as fallback
    log_record.timestamp = time.time() # Add timestamp attribute
    log_record.details = {} # Add details attribute
    log_record.duration_ms = None # Add duration_ms attribute
    log_record.event_id = None # Add event_id attribute
    log_record.state_before = None # Add state_before attribute
    log_record.state_after = None # Add state_after attribute

    monitor.emit(log_record)
    monitor.update_display()


    captured = capsys_stdout.getvalue()

    # Check for specific ASCII characters used for outlining (from Panel)
    assert "┌" in captured # Corner character (Rich Panel default)
    assert "─" in captured # Horizontal line character (Rich Panel default)
    assert "│" in captured # Vertical line character (Rich Panel default)

def test_terminal_monitor_output_suppression(capsys_stdout):
    """Test that non-monitor output is suppressed."""
    mock_state_manager = Mock() # Create a mock StateManager
    mock_state_manager.get_global_state.return_value = "Running"
    mock_state_manager.get_task_status.return_value = "Pending"
    mock_state_manager.state = {"plan": []}

    monitor = TerminalMonitor(state_manager=mock_state_manager) # Pass the mock

    # Simulate writing non-monitor output directly to stdout before monitor display
    print("This is non-monitor output.")

    # Simulate adding a monitor log message
    monitor_log_message = LogMessage(
        timestamp=time.time(),
        level=LogLevel.INFO,
        component=ComponentType.MONITOR, # Use MONITOR component type
        action="monitor_event", # Add the action argument
        event_summary="This is monitor output.",
        subtask_id=None
    )
    # Create a mock LogRecord
    monitor_log_record = Mock(spec=logging.LogRecord)
    monitor_log_record.levelno = logging.INFO
    monitor_log_record.level = LogLevel.INFO # Add level attribute for easier access in test
    monitor_log_record.component = ComponentType.MONITOR.value
    monitor_log_record.action = "monitor_event"
    monitor_log_record.event_summary = "This is monitor output."
    monitor_log_record.subtask_id = None
    monitor_log_record.message = "This is monitor output." # Add message attribute as fallback
    monitor_log_record.timestamp = time.time() # Add timestamp attribute
    monitor_log_record.details = {} # Add details attribute
    monitor_log_record.duration_ms = None # Add duration_ms attribute
    monitor_log_record.event_id = None # Add event_id attribute
    monitor_log_record.state_before = None # Add state_before attribute
    monitor_log_record.state_after = None # Add state_after attribute

    monitor.emit(monitor_log_record)
    monitor.update_display()


    captured = capsys_stdout.getvalue()

    # The non-monitor output should NOT be in the captured output if suppression works
    assert "This is non-monitor output." not in captured
    # The monitor output SHOULD be in the captured output
    assert "This is monitor output." in captured

def test_terminal_monitor_coloring_event_types(capsys_stdout):
    """Test that different event types are colored correctly."""
    mock_state_manager = Mock() # Create a mock StateManager
    mock_state_manager.get_global_state.return_value = "Running"
    mock_state_manager.get_task_status.return_value = "Pending"
    mock_state_manager.state = {"plan": []}

    monitor = TerminalMonitor(state_manager=mock_state_manager) # Pass the mock

    # Simulate displaying messages with different event types/log levels
    info_log = LogMessage(time.time(), LogLevel.INFO, ComponentType.MONITOR, "monitor_event", "Info message.", None) # Add action
    warning_log = LogMessage(time.time(), LogLevel.WARNING, ComponentType.MONITOR, "monitor_event", "Warning message.", None) # Add action
    error_log = LogMessage(time.time(), LogLevel.ERROR, ComponentType.MONITOR, "monitor_event", "Error message.", None) # Add action

    # Create mock LogRecords for different levels
    info_log_record = Mock(spec=logging.LogRecord)
    info_log_record.levelno = logging.INFO
    info_log_record.level = LogLevel.INFO # Add level attribute for easier access in test
    info_log_record.component = ComponentType.MONITOR.value
    info_log_record.action = "monitor_event"
    info_log_record.event_summary = "Info message."
    info_log_record.subtask_id = None
    info_log_record.message = "Info message." # Add message attribute as fallback
    info_log_record.timestamp = time.time() # Add timestamp attribute
    info_log_record.details = {} # Add details attribute
    info_log_record.duration_ms = None # Add duration_ms attribute
    info_log_record.event_id = None # Add event_id attribute
    info_log_record.state_before = None # Add state_before attribute
    info_log_record.state_after = None # Add state_after attribute

    warning_log_record = Mock(spec=logging.LogRecord)
    warning_log_record.levelno = logging.WARNING
    warning_log_record.level = LogLevel.WARNING # Add level attribute for easier access in test
    warning_log_record.component = ComponentType.MONITOR.value
    warning_log_record.action = "monitor_event"
    warning_log_record.event_summary = "Warning message."
    warning_log_record.subtask_id = None
    warning_log_record.message = "Warning message." # Add message attribute as fallback
    warning_log_record.timestamp = time.time() # Add timestamp attribute
    warning_log_record.details = {} # Add details attribute
    warning_log_record.duration_ms = None # Add duration_ms attribute
    warning_log_record.event_id = None # Add event_id attribute
    warning_log_record.state_before = None # Add state_before attribute
    warning_log_record.state_after = None # Add state_after attribute

    error_log_record = Mock(spec=logging.LogRecord)
    error_log_record.levelno = logging.ERROR
    error_log_record.level = LogLevel.ERROR # Add level attribute for easier access in test
    error_log_record.component = ComponentType.MONITOR.value
    error_log_record.action = "monitor_event"
    error_log_record.event_summary = "Error message."
    error_log_record.subtask_id = None
    error_log_record.message = "Error message." # Add message attribute as fallback
    error_log_record.timestamp = time.time() # Add timestamp attribute
    error_log_record.details = {} # Add details attribute
    error_log_record.duration_ms = None # Add duration_ms attribute
    error_log_record.event_id = None # Add event_id attribute
    error_log_record.state_before = None # Add state_before attribute
    error_log_record.state_after = None # Add state_after attribute

    monitor.emit(info_log_record)
    monitor.emit(warning_log_record)
    monitor.emit(error_log_record)
    monitor.update_display()


    captured = capsys_stdout.getvalue()

    # Check for the presence of ANSI color codes corresponding to each level
    # These color codes need to match the actual implementation's color scheme
    assert "\033[36m" in captured # Cyan for INFO (as implemented)
    assert "\033[33m" in captured # Yellow for WARNING
    assert "\033[31m" in captured # Red for ERROR

def test_terminal_monitor_coloring_json_pretty_print(capsys_stdout):
    """Test that JSON strings are pretty-printed and syntax highlighted."""
    mock_state_manager = Mock() # Create a mock StateManager
    mock_state_manager.get_global_state.return_value = "Running"
    mock_state_manager.get_task_status.return_value = "Pending"
    mock_state_manager.state = {"plan": []}

    monitor = TerminalMonitor(state_manager=mock_state_manager) # Pass the mock

    json_string = '{"name": "Test", "value": 123, "status": true}'
    json_log = LogMessage(time.time(), LogLevel.INFO, ComponentType.MONITOR, "monitor_event", json_string, None) # Add action and use MONITOR component type
    # Create a mock LogRecord with JSON event_summary
    json_log_record = Mock(spec=logging.LogRecord)
    json_log_record.levelno = logging.INFO
    json_log_record.level = LogLevel.INFO # Add level attribute for easier access in test
    json_log_record.component = ComponentType.MONITOR.value
    json_log_record.action = "monitor_event"
    json_log_record.event_summary = json_string
    json_log_record.subtask_id = None
    json_log_record.message = json_string # Add message attribute as fallback
    json_log_record.timestamp = time.time() # Add timestamp attribute
    json_log_record.details = {} # Add details attribute
    json_log_record.duration_ms = None # Add duration_ms attribute
    json_log_record.event_id = None # Add event_id attribute
    json_log_record.state_before = None # Add state_before attribute
    json_log_record.state_after = None # Add state_after attribute

    monitor.emit(json_log_record)
    monitor.update_display()


    captured = capsys_stdout.getvalue()

    # Check for pretty-printed JSON structure (basic indentation check)
    assert '{\n  "name": "Test",' in captured
    assert '\n  "value": 123,' in captured
    assert '\n  "status": true\n}' in captured

    # Check for presence of color codes for JSON syntax highlighting (using ansi_dark theme defaults)
    # These color codes need to match the actual implementation's JSON coloring
    assert "\x1b[0;36m" in captured # Cyan for keys
    assert "\x1b[0;34;91m" in captured # Red for string values (example from ansi_dark)
    assert "\x1b[0;34;92m" in captured # Green for boolean values (example from ansi_dark)
    assert "\x1b[0;34;94m" in captured # Blue for number values (example from ansi_dark)

# Note: These tests are based on the requirements analysis and make assumptions
# about the methods and internal workings of the TerminalMonitor class.
# They will need to be refined and potentially adjusted once the actual
# implementation of the TerminalMonitor display logic is available.
# The key is that they target the *existing* class and verify the expected
# output characteristics based on the requirements.
# The tests now include mocking for the StateManager dependency.