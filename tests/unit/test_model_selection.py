import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from src.ai_whisperer.exceptions import ConfigError

# Import the function to be tested - this will fail until we implement it
# from src.ai_whisperer.model_selector import get_model_for_task

# Sample configuration data for testing
VALID_CONFIG_WITH_TASK_MODELS = {
    'openrouter': {
        'api_key': 'default-api-key',
        'model': 'default-model',
        'params': {
            'temperature': 0.7,
            'max_tokens': 2048
        },
        'site_url': 'http://localhost:8000',
        'app_name': 'AIWhisperer'
    },
    'task_models': {
        'Subtask Generation': {
            'provider': 'openrouter',
            'model': 'anthropic/claude-3-opus',
            'params': {
                'temperature': 0.5,
                'max_tokens': 4096
            }
        },
        'Orchestrator': {
            'provider': 'openrouter',
            'model': 'mistralai/mistral-large',
            'params': {
                'temperature': 0.8,
                'max_tokens': 8192
            }
        }
    }
}

VALID_CONFIG_WITHOUT_TASK_MODELS = {
    'openrouter': {
        'api_key': 'default-api-key',
        'model': 'default-model',
        'params': {
            'temperature': 0.7,
            'max_tokens': 2048
        },
        'site_url': 'http://localhost:8000',
        'app_name': 'AIWhisperer'
    },
    'task_models': {}
}

CONFIG_WITH_INVALID_TASK_MODEL = {
    'openrouter': {
        'api_key': 'default-api-key',
        'model': 'default-model',
        'params': {
            'temperature': 0.7,
            'max_tokens': 2048
        },
        'site_url': 'http://localhost:8000',
        'app_name': 'AIWhisperer'
    },
    'task_models': {
        'Subtask Generation': {
            # Missing 'provider' field
            'model': 'anthropic/claude-3-opus'
        },
        'Orchestrator': {
            'provider': 'openrouter'
            # Missing 'model' field
        }
    }
}

# Test cases for the get_model_for_task function
@pytest.mark.parametrize(
    "config, task_name, expected_provider, expected_model",
    [
        # Test case 1: Task with specific configuration
        (
            VALID_CONFIG_WITH_TASK_MODELS,
            "Subtask Generation",
            "openrouter",
            "anthropic/claude-3-opus"
        ),
        # Test case 2: Another task with specific configuration
        (
            VALID_CONFIG_WITH_TASK_MODELS,
            "Orchestrator",
            "openrouter",
            "mistralai/mistral-large"
        ),
        # Test case 3: Task without specific configuration (fallback to default)
        (
            VALID_CONFIG_WITH_TASK_MODELS,
            "Unknown Task",
            "openrouter",
            "default-model"
        ),
        # Test case 4: Empty task_models section (fallback to default)
        (
            VALID_CONFIG_WITHOUT_TASK_MODELS,
            "Subtask Generation",
            "openrouter",
            "default-model"
        )
    ]
)
def test_get_model_for_task_valid_cases(config, task_name, expected_provider, expected_model):
    """Test that get_model_for_task returns the correct model configuration for valid cases."""
    # This test will fail until we implement the get_model_for_task function
    with patch('src.ai_whisperer.model_selector.get_model_for_task', autospec=True) as mock_get_model:
        # Configure the mock to return a dictionary with the expected values
        mock_result = {
            'provider': expected_provider,
            'model': expected_model
        }
        mock_get_model.return_value = mock_result
        
        # Call the mocked function
        result = mock_get_model(config, task_name)
        
        # Verify the result
        assert result['provider'] == expected_provider
        assert result['model'] == expected_model
        
        # Verify the function was called with the correct arguments
        mock_get_model.assert_called_once_with(config, task_name)

def test_get_model_for_task_missing_required_fields():
    """Test that get_model_for_task raises ConfigError when task config is missing required fields."""
    # This test will fail until we implement the get_model_for_task function
    with patch('src.ai_whisperer.model_selector.get_model_for_task', autospec=True) as mock_get_model:
        # Configure the mock to raise ConfigError
        mock_get_model.side_effect = ConfigError("Task model configuration is missing required fields.")
        
        # Verify that calling the function with invalid config raises ConfigError
        with pytest.raises(ConfigError):
            mock_get_model(CONFIG_WITH_INVALID_TASK_MODEL, "Subtask Generation")
        
        # Verify the function was called with the correct arguments
        mock_get_model.assert_called_once_with(CONFIG_WITH_INVALID_TASK_MODEL, "Subtask Generation")

def test_get_model_for_task_openrouter_provider():
    """Test that get_model_for_task correctly merges task config with default openrouter config."""
    # This test will fail until we implement the get_model_for_task function
    with patch('src.ai_whisperer.model_selector.get_model_for_task', autospec=True) as mock_get_model:
        # Configure the mock to return a merged configuration
        mock_result = {
            'api_key': 'default-api-key',
            'site_url': 'http://localhost:8000',
            'app_name': 'AIWhisperer',
            'model': 'anthropic/claude-3-opus',
            'params': {
                'temperature': 0.5,
                'max_tokens': 4096
            }
        }
        mock_get_model.return_value = mock_result
        
        # Call the mocked function
        result = mock_get_model(VALID_CONFIG_WITH_TASK_MODELS, "Subtask Generation")
        
        # Verify the result contains the merged configuration
        assert result['api_key'] == 'default-api-key'
        assert result['site_url'] == 'http://localhost:8000'
        assert result['app_name'] == 'AIWhisperer'
        assert result['model'] == 'anthropic/claude-3-opus'
        assert result['params']['temperature'] == 0.5
        assert result['params']['max_tokens'] == 4096
        
        # Verify the function was called with the correct arguments
        mock_get_model.assert_called_once_with(VALID_CONFIG_WITH_TASK_MODELS, "Subtask Generation")

def test_get_model_for_task_non_openrouter_provider():
    """Test that get_model_for_task returns the task config as is for non-openrouter providers."""
    # Create a config with a non-openrouter provider
    config_with_non_openrouter = {
        'openrouter': {
            'api_key': 'default-api-key',
            'model': 'default-model'
        },
        'task_models': {
            'Custom Task': {
                'provider': 'custom-provider',
                'model': 'custom-model',
                'api_key': 'custom-api-key'
            }
        }
    }
    
    # This test will fail until we implement the get_model_for_task function
    with patch('src.ai_whisperer.model_selector.get_model_for_task', autospec=True) as mock_get_model:
        # Configure the mock to return the task config as is
        mock_result = {
            'provider': 'custom-provider',
            'model': 'custom-model',
            'api_key': 'custom-api-key'
        }
        mock_get_model.return_value = mock_result
        
        # Call the mocked function
        result = mock_get_model(config_with_non_openrouter, "Custom Task")
        
        # Verify the result is the task config as is
        assert result['provider'] == 'custom-provider'
        assert result['model'] == 'custom-model'
        assert result['api_key'] == 'custom-api-key'
        
        # Verify the function was called with the correct arguments
        mock_get_model.assert_called_once_with(config_with_non_openrouter, "Custom Task")