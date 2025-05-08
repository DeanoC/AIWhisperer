import pytest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

# We need to manipulate sys.argv, so store the original
original_argv = sys.argv.copy()

# Import the actual function
from src.ai_whisperer.main import main
from src.ai_whisperer.openrouter_api import OpenRouterAPI # Import OpenRouterAPI

# Define dummy data for mocking
DUMMY_CONFIG = {
    'openrouter': {'api_key': 'test-key', 'model': 'test-model', 'params': {'temperature': 0.5}},
    'prompts': {'task_generation': 'Generate task for: {md_content}'}
}

# Create a class to wrap the config dictionary and provide the openrouter_api_key attribute
class ConfigWrapper:
    def __init__(self, config_dict):
        self.config_dict = config_dict

    def __getitem__(self, key):
        return self.config_dict[key]

    def get(self, key, default=None):
        return self.config_dict.get(key, default)

class TestMainListModels:
    """Test cases for the list-models functionality in main.py."""

    CONF_FILE = 'config.yaml' # Define CONF_FILE here

    def setup_method(self, method):
        """Setup before each test method."""
        sys.argv = original_argv.copy() # Restore original sys.argv before each test

    def teardown_method(self, method):
        """Cleanup after each test method."""
        sys.argv = original_argv.copy() # Restore original sys.argv after each test

    @patch('sys.exit')
    @patch('src.ai_whisperer.main.setup_rich_output')
    @patch('src.ai_whisperer.main.setup_logging')
    @patch('src.ai_whisperer.main.OpenRouterAPI', wraps=OpenRouterAPI) # Use wraps to call the actual class
    @patch('src.ai_whisperer.main.load_config')
    @patch('requests.get') # Mock requests.get
    def test_main_list_models_success_rewritten(self, mock_requests_get, mock_load_config, mock_api_cls, mock_setup_logging, mock_setup_rich, mock_sys_exit):
        """Test successful models listing (rewritten)."""
        # Setup mocks
        dummy_openrouter_config = {'api_key': 'test-key', 'model': 'test-model', 'params': {'temperature': 0.5}}
        mock_load_config.return_value = {'openrouter': dummy_openrouter_config} # Mock load_config to return a dictionary

        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "model1", "name": "Model One", "pricing": {}, "supported_parameters": {}, "context_length": 1000, "description": "Desc 1"},
                {"id": "model2", "name": "Model Two", "pricing": {}, "supported_parameters": {}, "context_length": 2000, "description": "Desc 2"},
            ]
        }
        mock_requests_get.return_value = mock_response

        mock_console = MagicMock()
        mock_setup_rich.return_value = mock_console

        # mock_api_instance is now an instance of the wrapped OpenRouterAPI class
        # mock_api_cls.return_value = mock_api_instance # Not needed with wraps
        # mock_api_instance.api_key = 'test-key' # Not needed with wraps, __init__ is called
        # We no longer need to mock list_models return value as we are mocking requests.get

        # Set command-line args for list models
        sys.argv = ['main.py', 'list-models', '--config', self.CONF_FILE]

        # Call the function
        with pytest.raises(SystemExit) as excinfo:
            main()

        # Verify the right API calls were made and output generated
        mock_setup_logging.assert_called_once()
        mock_setup_rich.assert_called_once()
        mock_load_config.assert_called_once_with(self.CONF_FILE)
        mock_api_cls.assert_called_once_with(dummy_openrouter_config) # Check OpenRouterAPI was instantiated with the correct config part
        mock_requests_get.assert_called_once() # Assert requests.get was called
        assert excinfo.value.code == 0  # Should exit with success code

        # Check that the models were printed to console
        mock_console.print.assert_any_call("[bold green]Available OpenRouter Models:[/bold green]") # Updated assertion
        mock_console.print.assert_any_call("- model1") # Updated assertion
        mock_console.print.assert_any_call("- model2") # Updated assertion