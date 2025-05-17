import pytest
from unittest.mock import patch # Import patch
from ai_whisperer.cli import cli, execute_commands_and_capture_output
from ai_whisperer.delegate_manager import DelegateManager
from user_message_delegate import UserMessageLevel
from basic_output_display_message import ANSIConsoleUserMessageHandler # Import the handler

@patch('builtins.print') # Patch builtins.print
def test_detail_level_cli_option_filters_output(mock_print):
    """Verify --detail-level filters output messages based on their detail level using list-models."""
    
    # Create a DelegateManager instance for the test
    delegate_manager = DelegateManager()
    
    # Register the ANSIConsoleUserMessageHandler with the delegate manager
    user_message_handler = ANSIConsoleUserMessageHandler()
    delegate_manager.register_notification("user_message_display", user_message_handler.display_message)
    
import re # Import re for regex

# Helper to get the printed output from the mock and remove ANSI escape codes
def get_printed_output(mock):
    # Regex to find ANSI escape codes
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    raw_output = "".join([call_arg[0][0] for call_arg in mock.call_args_list])
    return ansi_escape.sub('', raw_output)


    # Test with default detail level (INFO)
    commands_info = cli(["--config", "tests/code_generator/aiwhisperer_config.yaml", "list-models"], delegate_manager=delegate_manager)
    execute_commands_and_capture_output(commands_info, delegate_manager)
    output_info = get_printed_output(mock_print)
    
    assert "Available OpenRouter Models" in output_info # Updated assertion
    # Assuming INFO level includes model names
    assert "gpt-4o" in output_info
    assert "gpt-3.5-turbo" in output_info
    # Assert that detailed information is NOT present at INFO level
    assert "Context Window:" not in output_info
    assert "Pricing:" not in output_info
    
    # Reset the mock for the next test case
    mock_print.reset_mock()

    # Test with DETAIL detail level
    commands_detail = cli(["--config", "tests/code_generator/aiwhisperer_config.yaml", "--detail-level", "DETAIL", "list-models"], delegate_manager=delegate_manager)
    execute_commands_and_capture_output(commands_detail, delegate_manager)
    output_detail = get_printed_output(mock_print)
    
    assert "Available OpenRouter Models" in output_detail # Updated assertion
    # Assert that model names are present at DETAIL level
    assert "gpt-4o" in output_detail
    assert "gpt-3.5-turbo" in output_detail
    # Assert that detailed information IS present at DETAIL level
    assert "Context Window:" in output_detail
    assert "Pricing:" in output_detail
    
    # Reset the mock for the next test case
    mock_print.reset_mock()

    # Test with INFO detail level explicitly
    commands_info_explicit = cli(["--config", "tests/code_generator/aiwhisperer_config.yaml", "--detail-level", "INFO", "list-models"], delegate_manager=delegate_manager)
    execute_commands_and_capture_output(commands_info_explicit, delegate_manager)
    output_info_explicit = get_printed_output(mock_print)
    
    assert "Available OpenRouter Models" in output_info_explicit # Updated assertion
    # Assert that model names are present at INFO level
    assert "gpt-4o" in output_info_explicit
    assert "gpt-3.5-turbo" in output_info_explicit
    # Assert that detailed information is NOT present at INFO level
    assert "Context Window:" not in output_info_explicit
    assert "Pricing:" not in output_info_explicit