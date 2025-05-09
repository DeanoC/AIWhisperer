import pytest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

# We need to manipulate sys.argv, so store the original
original_argv = sys.argv.copy()

# Import the actual function
from src.ai_whisperer.main import main
from src.ai_whisperer.ai_service_interaction import OpenRouterAPI # Import OpenRouterAPI
from src.ai_whisperer.exceptions import ( # Import necessary exceptions
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError
)

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

class TestMainListModelsError:
    """Test cases for list-models error handling in main.py."""

    CONF_FILE = 'config.yaml' # Define CONF_FILE here
    WRAPPED_CONFIG = ConfigWrapper(DUMMY_CONFIG) # Define WRAPPED_CONFIG here

    def setup_method(self, method):
        """Setup before each test method."""
        sys.argv = original_argv.copy() # Restore original sys.argv before each test

    def teardown_method(self, method):
        """Cleanup after each test method."""
        sys.argv = original_argv.copy() # Restore original sys.argv after each test

    @patch('sys.exit')
    @patch('src.ai_whisperer.main.setup_rich_output')
    @patch('src.ai_whisperer.main.setup_logging')
    @patch('src.ai_whisperer.main.OpenRouterAPI')
    @patch('src.ai_whisperer.main.load_config')
    def test_main_list_models_api_error(self, mock_load_config, mock_api_cls, mock_setup_logging, mock_setup_rich, mock_sys_exit):
        """Test list_models error handling."""
        # Setup mocks
        mock_load_config.return_value = self.WRAPPED_CONFIG
        mock_console = MagicMock()
        mock_setup_rich.return_value = mock_console
        mock_api_instance = MagicMock()
        mock_api_cls.return_value = mock_api_instance
        mock_api_instance.list_models.side_effect = Exception("API Error")

        # Set command-line args for list models
        sys.argv = ['main.py', 'list-models', '--config', self.CONF_FILE]

        # Call the function
        with pytest.raises(SystemExit) as excinfo:
            main()

        # Verify error handling
        mock_load_config.assert_called_once_with(self.CONF_FILE)
        mock_api_cls.assert_called_once_with(self.WRAPPED_CONFIG['openrouter'])
        mock_api_instance.list_models.assert_called_once()
        assert excinfo.value.code == 1  # Should exit with error code