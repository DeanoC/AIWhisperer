import pytest
from unittest.mock import patch, MagicMock
from monitor.basic_output_display_message import ANSIConsoleUserMessageHandler
from monitor.user_message_delegate import UserMessageLevel # Corrected import

class TestANSIConsoleUserMessageHandler:

    def test_default_detail_level_is_info(self):
        """Test that the default detail level is INFO."""
        handler = ANSIConsoleUserMessageHandler()
        # Compare values to avoid potential module identity issues in tests
        assert handler.get_detail_level().value == "INFO"

    def test_set_detail_level(self):
        """Test setting the detail level."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.DETAIL) # Use enum member
        # Compare values to avoid potential module identity issues in tests
        assert handler.get_detail_level().value == "DETAIL"

    def test_set_detail_level_with_invalid_type_raises_valueerror(self):
        """Test setting the detail level with an invalid type raises ValueError."""
        handler = ANSIConsoleUserMessageHandler()
        # Update regex to match the current error message in set_detail_level
        with pytest.raises(ValueError, match="Detail level must be a UserMessageLevel enum member, not str"):
            handler.set_detail_level("INVALID_LEVEL")
        with pytest.raises(ValueError, match="Detail level must be a UserMessageLevel enum member, not int"):
            handler.set_detail_level(123) # Test with another invalid type

    @patch('builtins.print')
    def test_display_message_info_level_default(self, mock_print):
        """Test display_message with INFO level when default detail level is INFO."""
        handler = ANSIConsoleUserMessageHandler()
        data = {"message": "This is an info message", "level": UserMessageLevel.INFO} # Use enum member
        handler.display_message(MagicMock(), data)
        mock_print.assert_called_once_with(f"\x1b[0mThis is an info message\x1b[0m")

    @patch('builtins.print')
    def test_display_message_detail_level_default(self, mock_print):
        """Test display_message with DETAIL level when default detail level is INFO."""
        handler = ANSIConsoleUserMessageHandler()
        data = {"message": "This is a detail message", "level": UserMessageLevel.DETAIL} # Use enum member
        handler.display_message(MagicMock(), data)
        mock_print.assert_not_called() # DETAIL messages should not be printed at INFO level

    @patch('builtins.print')
    def test_display_message_info_level_explicit_info(self, mock_print):
        """Test display_message with INFO level when detail level is explicitly set to INFO."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.INFO) # Use enum member
        data = {"message": "This is an info message", "level": UserMessageLevel.INFO} # Use enum member
        handler.display_message(MagicMock(), data)
        mock_print.assert_called_once_with(f"\x1b[0mThis is an info message\x1b[0m")

    @patch('builtins.print')
    def test_display_message_detail_level_explicit_info(self, mock_print):
        """Test display_message with DETAIL level when detail level is explicitly set to INFO."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.INFO) # Use enum member
        data = {"message": "This is a detail message", "level": UserMessageLevel.DETAIL} # Use enum member
        handler.display_message(MagicMock(), data)
        mock_print.assert_not_called() # DETAIL messages should not be printed at INFO level

    @patch('builtins.print')
    def test_display_message_info_level_explicit_detail(self, mock_print):
        """Test display_message with INFO level when detail level is explicitly set to DETAIL."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.DETAIL) # Use enum member
        data = {"message": "This is an info message", "level": UserMessageLevel.INFO} # Use enum member
        handler.display_message(MagicMock(), data)
        mock_print.assert_called_once_with(f"\x1b[0mThis is an info message\x1b[0m")

    @patch('builtins.print')
    def test_display_message_detail_level_explicit_detail(self, mock_print):
        """Test display_message with DETAIL level when detail level is explicitly set to DETAIL."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.DETAIL) # Use enum member
        data = {"message": "This is a detail message", "level": UserMessageLevel.DETAIL} # Use enum member
        handler.display_message(MagicMock(), data)
        mock_print.assert_called_once_with(f"\x1b[0mThis is a detail message\x1b[0m")

    @patch('builtins.print')
    def test_display_message_with_string_level_info(self, mock_print):
        """Test display_message with level as string 'INFO'."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.DETAIL) # Set to DETAIL to ensure filtering works
        data = {"message": "This is an info message string", "level": "INFO"}
        handler.display_message(MagicMock(), data)
        mock_print.assert_called_once_with(f"\x1b[0mThis is an info message string\x1b[0m")

    @patch('builtins.print')
    def test_display_message_with_string_level_detail(self, mock_print):
        """Test display_message with level as string 'DETAIL'."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.DETAIL)
        data = {"message": "This is a detail message string", "level": "DETAIL"}
        handler.display_message(MagicMock(), data)
        mock_print.assert_called_once_with(f"\x1b[0mThis is a detail message string\x1b[0m")

    @patch('builtins.print')
    def test_display_message_with_invalid_string_level(self, mock_print):
        """Test display_message with an invalid string level."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.DETAIL) # Set to DETAIL to ensure filtering works
        data = {"message": "This message has invalid level", "level": "INVALID"}
        handler.display_message(MagicMock(), data)
        # Expect a warning and default to INFO, so message should be displayed at DETAIL level
        mock_print.assert_called_once_with(f"\x1b[0mThis message has invalid level\x1b[0m")

    @patch('builtins.print')
    def test_display_message_with_unexpected_level_type(self, mock_print):
        """Test display_message with an unexpected level type."""
        handler = ANSIConsoleUserMessageHandler()
        handler.set_detail_level(UserMessageLevel.DETAIL) # Set to DETAIL to ensure filtering works
        data = {"message": "This message has unexpected level type", "level": 123}
        handler.display_message(MagicMock(), data)
        # Expect a warning and default to INFO, so message should be displayed at DETAIL level
        mock_print.assert_called_once_with(f"\x1b[0mThis message has unexpected level type\x1b[0m")