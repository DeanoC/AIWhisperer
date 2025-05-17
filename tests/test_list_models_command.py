# tests/unit/test_commands.py

import pytest
from unittest.mock import patch, MagicMock

from ai_whisperer.commands import ListModelsCommand
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.model_info_provider import ModelInfoProvider
from basic_output_display_message import ANSIConsoleUserMessageHandler
from user_message_delegate import UserMessageLevel # Import UserMessageLevel

# Mocked tests for list-models
@patch('ai_whisperer.commands.ModelInfoProvider')
def test_list_models_mocked(mock_model_info_provider):
    """Tests the list-models command using mocked ModelInfoProvider."""
    mock_instance = mock_model_info_provider.return_value
    mock_instance.list_models.return_value = [
        {"id": "mock_server_1/model_a", "name": "model_a"},
        {"id": "mock_server_1/model_b", "name": "model_b"},
        {"id": "mock_server_2/model_c", "name": "model_c"}
    ]

    mock_delegate_manager = MagicMock()
    config = {"servers": {}, "config_path": "dummy_config.yaml"}
    detail_level = UserMessageLevel.INFO # Set detail level for this test

    command = ListModelsCommand(config=config, output_csv=None, delegate_manager=mock_delegate_manager, detail_level=detail_level)
    command.execute()

    mock_instance.list_models.assert_called_once()

    # Assertions on delegate_manager.invoke_notification calls
    mock_delegate_manager.invoke_notification.assert_any_call(
        sender=command,
        event_type="user_message_display",
        event_data={"message": "Available OpenRouter Models (3):", "level": UserMessageLevel.INFO}
    )
    mock_delegate_manager.invoke_notification.assert_any_call(
        sender=command,
        event_type="user_message_display",
        event_data={"message": "- mock_server_1/model_a", "level": UserMessageLevel.INFO}
    )
    mock_delegate_manager.invoke_notification.assert_any_call(
        sender=command,
        event_type="user_message_display",
        event_data={"message": "- mock_server_1/model_b", "level": UserMessageLevel.INFO}
    )
    mock_delegate_manager.invoke_notification.assert_any_call(
        sender=command,
        event_type="user_message_display",
        event_data={"message": "- mock_server_2/model_c", "level": UserMessageLevel.INFO}
    )
    # Ensure no DETAIL level messages were sent at INFO detail level
    for call_args, call_kwargs in mock_delegate_manager.invoke_notification.call_args_list:
        event_data = call_kwargs.get('event_data')
        if event_data and event_data.get('level') == UserMessageLevel.DETAIL:
            assert False, "DETAIL level message was sent when detail_level was INFO"

# Mocked tests for list-models CSV output
@patch('ai_whisperer.commands.ModelInfoProvider')
def test_list_models_csv_mocked(mock_model_info_provider):
    """Tests the list-models command with CSV output using mocked ModelInfoProvider."""
    mock_instance = mock_model_info_provider.return_value

    mock_delegate_manager = MagicMock()
    output_csv_path = "dummy_output.csv"
    config = {"servers": {}, "config_path": "dummy_config.yaml"}
    detail_level = UserMessageLevel.INFO # Detail level should not affect CSV output

    command = ListModelsCommand(config=config, output_csv=output_csv_path, delegate_manager=mock_delegate_manager, detail_level=detail_level)
    command.execute()

    mock_instance.list_models_to_csv.assert_called_once_with(output_csv_path)

    # Assertions on delegate_manager.invoke_notification calls for CSV case
    mock_delegate_manager.invoke_notification.assert_any_call(
        sender=command,
        event_type="user_message_display",
        event_data={"message": f"Successfully wrote model list to CSV: {output_csv_path}", "level": UserMessageLevel.INFO}
    )
    # Ensure no other messages were sent
    assert mock_delegate_manager.invoke_notification.call_count == 1



# Tests interacting with actual servers (marked as integration/slow)
# These tests require actual server configuration and network access.
# They should ideally be run after the mocked tests pass.
@pytest.mark.integration
@pytest.mark.slow
def test_list_models_actual_servers():
    """Tests the list-models command with actual server interaction."""
    from ai_whisperer.config import load_config
    config_path = "config.yaml"
    config = load_config(config_path)
    config["config_path"] = config_path
    delegate_manager = DelegateManager()
    ansi_handler = ANSIConsoleUserMessageHandler()
    delegate_manager.register_notification(
        event_type="user_message_display",
        delegate=ansi_handler.display_message
    )
    # Add detail_level to the command instantiation
    command = ListModelsCommand(config=config, output_csv=None, delegate_manager=delegate_manager, detail_level=UserMessageLevel.INFO)

    # Capture output by mocking logger.debug
    with patch('ai_whisperer.commands.logger.debug') as mock_print:
        command.execute()

    # Basic assertion: command should run without error (exit code is returned by execute)
    # We can't easily check exit code here, but we can check if execute ran without raising exception
    # and if logger.debug was called with expected output structure.
    mock_print.assert_any_call("Loading configuration from: config.yaml")
    # Further assertions would depend on the expected output from actual servers.
    # We can check if any model names were printed, indicating interaction with servers.
    # This is a basic check for integration test.
    # Check if any call to print looks like a model id (contains a server/model pattern)
    import re
    printed_lines = [call_args[0][0] for call_args in mock_print.call_args_list]
    # Regex: at least one word, slash, at least one word (loosely matches server/model)
    model_line_regex = re.compile(r"[\w.-]+/[\w.-]+")
    model_lines = [line for line in printed_lines if model_line_regex.search(line)]
    if not model_lines:
        print("DEBUG: logger.debug calls:")
        for line in printed_lines:
            print(repr(line))
    assert model_lines, "No model lines found in logger.debug output. See debug above."

# Tests interacting with actual servers for CSV output (marked as integration/slow)
@pytest.mark.integration
@pytest.mark.slow
def test_list_models_csv_actual_servers(tmp_path):
    """Tests the list-models command with CSV output and actual server interaction."""
    from ai_whisperer.config import load_config
    config_path = "config.yaml"
    config = load_config(config_path)
    config["config_path"] = config_path

    output_csv_path = tmp_path / "actual_models.csv"
    delegate_manager = DelegateManager()
    # Add detail_level to the command instantiation
    command = ListModelsCommand(config=config, output_csv=str(output_csv_path), delegate_manager=delegate_manager, detail_level=UserMessageLevel.INFO)

    command.execute()

    # Assert that the CSV file was created and has content
    assert output_csv_path.exists()
    assert output_csv_path.stat().st_size > 0

    # Optional: Read the CSV and perform more specific assertions if needed
    # For example, check for expected headers or data structure
    # with open(output_csv_path, 'r', encoding='utf-8') as f:
    #     reader = csv.reader(f)
    #     header = next(reader)
    #     assert header == ["id", "name", ...] # Adjust based on actual CSV format
    #     rows = list(reader)
    #     assert len(rows) > 0 # Check if any models were written