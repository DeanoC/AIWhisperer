import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from src.ai_whisperer.subtask_generator import SubtaskGenerator
from src.ai_whisperer.orchestrator import Orchestrator
from src.ai_whisperer.exceptions import ConfigError

# Sample configuration for testing
SAMPLE_CONFIG = {
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
    'prompts': {
        'orchestrator_prompt_path': 'prompts/orchestrator_default.md',
        'subtask_generator_prompt_path': 'prompts/subtask_generator_default.md',
        'orchestrator_prompt_content': 'Test orchestrator prompt content',
        'subtask_generator_prompt_content': 'Test subtask generator prompt content'
    },
    'output_dir': './output/',
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

# Helper function to create a temporary config file
def create_temp_config(content):
    temp_dir = tempfile.gettempdir()
    config_path = Path(temp_dir) / "test_config.yaml"

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(config_path)

# Tests for SubtaskGenerator integration with model_selector
class TestSubtaskGeneratorModelIntegration:
    @patch('src.ai_whisperer.subtask_generator.get_model_for_task')
    @patch('src.ai_whisperer.subtask_generator.load_config')
    @patch('src.ai_whisperer.subtask_generator.OpenRouterAPI')
    def test_subtask_generator_uses_model_selector(self, mock_openrouter, mock_load_config, mock_get_model):
        # Setup mocks
        mock_load_config.return_value = SAMPLE_CONFIG

        # Mock the model_selector to return a specific configuration
        mock_model_config = {
            'api_key': 'test-api-key',
            'model': 'anthropic/claude-3-opus',
            'params': {
                'temperature': 0.5,
                'max_tokens': 4096
            },
            'site_url': 'http://localhost:8000',
            'app_name': 'AIWhisperer'
        }
        mock_get_model.return_value = mock_model_config

        # Create a SubtaskGenerator instance
        subtask_generator = SubtaskGenerator(
            config_path="dummy_path.yaml",
            overall_context="Test context",
            workspace_context="Test workspace"
        )

        # Verify that get_model_for_task was called with the correct arguments
        mock_get_model.assert_called_once_with(SAMPLE_CONFIG, "Subtask Generation")

        # Verify that OpenRouterAPI was initialized with the configuration from get_model_for_task
        mock_openrouter.assert_called_once_with(config=mock_model_config)

    @patch('src.ai_whisperer.subtask_generator.get_model_for_task')
    @patch('src.ai_whisperer.subtask_generator.load_config')
    @patch('src.ai_whisperer.subtask_generator.OpenRouterAPI')
    def test_subtask_generator_handles_different_model_config(self, mock_openrouter, mock_load_config, mock_get_model):
        # Setup mocks
        mock_load_config.return_value = SAMPLE_CONFIG

        # Mock the model_selector to return a different configuration
        mock_model_config = {
            'api_key': 'test-api-key',
            'model': 'mistralai/mistral-large',
            'params': {
                'temperature': 0.8,
                'max_tokens': 8192
            },
            'site_url': 'http://localhost:8000',
            'app_name': 'AIWhisperer'
        }
        mock_get_model.return_value = mock_model_config

        # Create a SubtaskGenerator instance
        subtask_generator = SubtaskGenerator(
            config_path="dummy_path.yaml",
            overall_context="Test context",
            workspace_context="Test workspace"
        )

        # Verify that get_model_for_task was called with the correct arguments
        mock_get_model.assert_called_once_with(SAMPLE_CONFIG, "Subtask Generation")

        # Verify that OpenRouterAPI was initialized with the configuration from get_model_for_task
        mock_openrouter.assert_called_once_with(config=mock_model_config)

# Tests for Orchestrator integration with model_selector
class TestOrchestratorModelIntegration:
    @patch('src.ai_whisperer.orchestrator.get_model_for_task')
    @patch('src.ai_whisperer.openrouter_api.OpenRouterAPI')
    def test_orchestrator_uses_model_selector(self, mock_openrouter, mock_get_model):
        # Mock the model_selector to return a specific configuration
        mock_model_config = {
            'api_key': 'test-api-key',
            'model': 'mistralai/mistral-large',
            'params': {
                'temperature': 0.8,
                'max_tokens': 8192
            },
            'site_url': 'http://localhost:8000',
            'app_name': 'AIWhisperer'
        }
        mock_get_model.return_value = mock_model_config

        # Create an Orchestrator instance
        orchestrator = Orchestrator(config=SAMPLE_CONFIG)

        # Verify that get_model_for_task was called with the correct arguments
        mock_get_model.assert_called_once_with(SAMPLE_CONFIG, "Orchestrator")

        # Verify that OpenRouterAPI was initialized with the configuration from get_model_for_task
        mock_openrouter.assert_called_once_with(config=mock_model_config)

    @patch('src.ai_whisperer.orchestrator.get_model_for_task')
    @patch('src.ai_whisperer.openrouter_api.OpenRouterAPI')
    def test_orchestrator_handles_different_model_config(self, mock_openrouter, mock_get_model):
        # Mock the model_selector to return a different configuration
        mock_model_config = {
            'api_key': 'test-api-key',
            'model': 'anthropic/claude-3-opus',
            'params': {
                'temperature': 0.5,
                'max_tokens': 4096
            },
            'site_url': 'http://localhost:8000',
            'app_name': 'AIWhisperer'
        }
        mock_get_model.return_value = mock_model_config

        # Create an Orchestrator instance
        orchestrator = Orchestrator(config=SAMPLE_CONFIG)

        # Verify that get_model_for_task was called with the correct arguments
        mock_get_model.assert_called_once_with(SAMPLE_CONFIG, "Orchestrator")

        # Verify that OpenRouterAPI was initialized with the configuration from get_model_for_task
        mock_openrouter.assert_called_once_with(config=mock_model_config)
