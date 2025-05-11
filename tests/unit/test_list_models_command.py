# tests/unit/test_commands.py

import pytest
from unittest.mock import patch, MagicMock

from src.ai_whisperer.commands import ListModelsCommand, console
from src.ai_whisperer.model_info_provider import ModelInfoProvider

# Mocked tests for list-models
@patch('src.ai_whisperer.commands.console')
@patch('src.ai_whisperer.commands.load_config')
@patch('src.ai_whisperer.commands.ModelInfoProvider')
def test_list_models_mocked(mock_model_info_provider, mock_load_config, mock_console):
    """Tests the list-models command using mocked ModelInfoProvider."""
    mock_load_config.return_value = {"servers": {}} # Return a dummy config
    mock_instance = mock_model_info_provider.return_value
    mock_instance.list_models.return_value = [ # Corrected return value to match list_models
        {"id": "mock_server_1/model_a", "name": "model_a"},
        {"id": "mock_server_1/model_b", "name": "model_b"},
        {"id": "mock_server_2/model_c", "name": "model_c"}
    ]

    command = ListModelsCommand(config_path="dummy_config.yaml")
    command.execute()

    mock_instance.list_models.assert_called_once()
    # Assertions on console output
    mock_console.print.assert_any_call("Loading configuration from: dummy_config.yaml")
    mock_console.print.assert_any_call("[bold green]Available OpenRouter Models:[/bold green]")
    mock_console.print.assert_any_call("- mock_server_1/model_a")
    mock_console.print.assert_any_call("- mock_server_1/model_b")
    mock_console.print.assert_any_call("- mock_server_2/model_c")

# Mocked tests for list-models CSV output
@patch('src.ai_whisperer.commands.console')
@patch('src.ai_whisperer.commands.load_config')
@patch('src.ai_whisperer.commands.ModelInfoProvider')
def test_list_models_csv_mocked(mock_model_info_provider, mock_load_config, mock_console):
    """Tests the list-models command with CSV output using mocked ModelInfoProvider."""
    mock_load_config.return_value = {"servers": {}} # Return a dummy config
    mock_instance = mock_model_info_provider.return_value

    output_csv_path = "dummy_output.csv"
    command = ListModelsCommand(config_path="dummy_config.yaml", output_csv=output_csv_path)
    command.execute()

    mock_instance.list_models_to_csv.assert_called_once_with(output_csv_path)
    # Assertions on console output for CSV case
    mock_console.print.assert_any_call("Loading configuration from: dummy_config.yaml")
    mock_console.print.assert_any_call(f"[green]Successfully wrote model list to CSV: {output_csv_path}[/green]")


# Tests interacting with actual servers (marked as integration/slow)
# These tests require actual server configuration and network access.
# They should ideally be run after the mocked tests pass.
@pytest.mark.integration
@pytest.mark.slow
@patch('src.ai_whisperer.commands.console')
def test_list_models_actual_servers(mock_console):
    """Tests the list-models command with actual server interaction."""
    # This test requires a valid configuration with actual servers defined.
    # It will attempt to connect to configured servers.
    # If no servers are configured or accessible, this test might fail or show empty output.
    # Use a real config file path if available and appropriate for integration tests
    # For this example, we'll use a placeholder and assume a config exists for the test environment
    command = ListModelsCommand(config_path="config.yaml") # Use a real config path

    # Capture output by mocking console.print
    with patch('src.ai_whisperer.commands.console.print') as mock_print:
        command.execute()

    # Basic assertion: command should run without error (exit code is returned by execute)
    # We can't easily check exit code here, but we can check if execute ran without raising exception
    # and if console.print was called with expected output structure.
    mock_print.assert_any_call("Loading configuration from: config.yaml")
    mock_print.assert_any_call("[bold green]Available OpenRouter Models:[/bold green]")
    # Further assertions would depend on the expected output from actual servers.
    # We can check if any model names were printed, indicating interaction with servers.
    # This is a basic check for integration test.
    # Check if any call to print starts with "- " which indicates a model being listed
    printed_lines = [call_args[0][0] for call_args in mock_print.call_args_list]
    assert any(line.startswith("- ") for line in printed_lines)

# Tests interacting with actual servers for CSV output (marked as integration/slow)
@pytest.mark.integration
@pytest.mark.slow
def test_list_models_csv_actual_servers(tmp_path):
    """Tests the list-models command with CSV output and actual server interaction."""
    # This test requires a valid configuration with actual servers defined.
    # It will attempt to connect to configured servers and write to a temporary CSV file.
    output_csv_path = tmp_path / "actual_models.csv"
    command = ListModelsCommand(config_path="config.yaml", output_csv=str(output_csv_path))

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