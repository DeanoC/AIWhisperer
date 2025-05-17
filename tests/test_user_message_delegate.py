import pytest
import sys
import io
from enum import Enum
from monitor.user_message_delegate import UserMessageColour, UserMessageLevel
from monitor.basic_output_display_message import ANSIConsoleUserMessageHandler

class TestANSIConsoleUserMessageHandler:

    @pytest.fixture
    def handler(self):
        """Fixture to provide an instance of the handler."""
        return ANSIConsoleUserMessageHandler()

    @pytest.fixture
    def capsys(self, capsys):
        """Fixture to capture stdout and stderr."""
        return capsys

    def test_display_message_info(self, handler, capsys):
        """Test displaying an INFO level message."""
        message = "This is an info message."
        handler.display_message(self, {"message": message, "level": UserMessageLevel.INFO})
        captured = capsys.readouterr()
        expected_output = f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}\n"
        assert captured.out == expected_output
        assert captured.err == ""

    def test_display_message_detail_at_detail_level(self, handler, capsys):
        """Test displaying a DETAIL level message when handler detail level is DETAIL."""
        handler.set_detail_level(UserMessageLevel.DETAIL) # Set handler detail level to DETAIL
        message = "This is a detail message."
        level = UserMessageLevel.DETAIL
        handler.display_message(self, {"message": message, "level": level})
        captured = capsys.readouterr()
        expected_output = f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}\n"
        assert captured.out == expected_output
        assert captured.err == ""

    def test_display_message_detail_at_info_level(self, handler, capsys):
        """Test displaying a DETAIL level message when handler detail level is INFO."""
        handler.set_detail_level(UserMessageLevel.INFO) # Set handler detail level to INFO
        message = "This is a detail message."
        level = UserMessageLevel.DETAIL
        handler.display_message(self, {"message": message, "level": level})
        captured = capsys.readouterr()
        assert captured.out == "" # Should not display DETAIL message at INFO level
        assert captured.err == ""

    def test_display_message_info_at_info_level(self, handler, capsys):
        """Test displaying an INFO level message when handler detail level is INFO."""
        handler.set_detail_level(UserMessageLevel.INFO) # Set handler detail level to INFO
        message = "This is an info message."
        level = UserMessageLevel.INFO
        handler.display_message(self, {"message": message, "level": level})
        captured = capsys.readouterr()
        expected_output = f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}\n"
        assert captured.out == expected_output
        assert captured.err == ""

    def test_display_message_unknown_level(self, handler, capsys, caplog): # Add caplog fixture
        """Test displaying a message with an unknown level."""
        # Create a dummy enum value not in the COLOR_MAP
        from enum import Enum # Import Enum locally for the dummy class
        class DummyLevel(Enum):
            UNKNOWN = "UNKNOWN"

        message = "This is an unknown message."
        level = DummyLevel.UNKNOWN

        # Expect no exception and check for a warning log message
        import logging # Import logging for caplog
        with caplog.at_level(logging.WARNING): # Capture logs at WARNING level
            handler.display_message(self, {"message": message, "level": level})

        captured = capsys.readouterr() # Re-add capsys.readouterr()

        # Check for the warning log message
        assert "Unexpected message level type 'DummyLevel'. Defaulting to INFO." in caplog.text
        # Assert that the message was printed to stdout with default formatting (INFO level)
        expected_output = f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}\n"
        assert captured.out == expected_output
        assert captured.err == "" # Ensure nothing was printed to stderr
