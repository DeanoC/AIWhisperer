import pytest
import sys
import io
from enum import Enum
from user_message_delegate import UserMessageColour, UserMessageLevel
from basic_output_display_message import ANSIConsoleUserMessageHandler

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

    def test_display_message_detail(self, handler, capsys):
        """Test displaying a DETAIL level message."""
        message = "This is a detail message."
        level = UserMessageLevel.DETAIL
        handler.display_message(self, {"message": message, "level": level})
        captured = capsys.readouterr()
        expected_output = f"{UserMessageColour.RESET}{message}{UserMessageColour.RESET}\n"
        assert captured.out == expected_output
        assert captured.err == ""

    def test_display_message_unknown_level(self, handler, capsys):
        """Test displaying a message with an unknown level."""
        # Create a dummy enum value not in the COLOR_MAP
        from enum import Enum # Import Enum locally for the dummy class
        class DummyLevel(Enum):
            UNKNOWN = "UNKNOWN"

        message = "This is an unknown message."
        level = DummyLevel.UNKNOWN
        with pytest.raises(Exception):
            handler.display_message(self, {"message": message, "level": level})
