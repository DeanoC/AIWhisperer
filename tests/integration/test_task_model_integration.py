import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from src.ai_whisperer.subtask_generator import SubtaskGenerator
# from src.ai_whisperer.orchestrator import Orchestrator
from src.ai_whisperer.exceptions import ConfigError
from src.ai_whisperer.config import load_config  # Import load_config for mocking

# Sample configuration for testing (input config structure)
SAMPLE_CONFIG_INPUT = {
    "openrouter": {
        "api_key": "default-api-key",
        "model": "default-model",
        "params": {"temperature": 0.7, "max_tokens": 2048},
        "site_url": "http://localhost:8000",
        "app_name": "AIWhisperer",
    },
    "output_dir": "./output/",
    "task_models": {
        "Subtask Generation": {"model": "anthropic/claude-3-opus", "params": {"temperature": 0.5, "max_tokens": 4096}},
        "Orchestrator": {"model": "mistralai/mistral-large", "params": {"temperature": 0.8, "max_tokens": 8192}},
    },
    "task_prompts": {
        "subtask_generator": "prompts/subtask_generator_default.md",
        "orchestrator": "prompts/orchestrator_default.md",
    },
}


# Helper function to create a temporary config file
def create_temp_config(content):
    temp_dir = tempfile.gettempdir()
    config_path = Path(temp_dir) / "test_config.yaml"

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(config_path)


# Tests for SubtaskGenerator integration with config loading
class TestSubtaskGeneratorModelIntegration:
    @patch("src.ai_whisperer.subtask_generator.load_config")
    @patch("src.ai_whisperer.subtask_generator.OpenRouterAPI")
    def test_subtask_generator_uses_correct_model_config(self, mock_openrouter, mock_load_config):
        # Setup mocks
        # Create a mock config that includes the expected task_model_configs and task_prompts_content, as load_config would return
        mock_loaded_config = SAMPLE_CONFIG_INPUT.copy()
        mock_loaded_config["task_model_configs"] = {
            "subtask_generator": {
                "api_key": "default-api-key",
                "model": "anthropic/claude-3-opus",
                "params": {"temperature": 0.5, "max_tokens": 4096},
                "site_url": "http://localhost:8000",
                "app_name": "AIWhisperer",
            }
        }
        mock_loaded_config["task_prompts_content"] = {"subtask_generator": "Mock Subtask Generator Prompt Content"}
        mock_load_config.return_value = mock_loaded_config

        # Expected model configuration for Subtask Generation from the mock loaded config
        expected_model_config = mock_loaded_config["task_model_configs"]["subtask_generator"]

        # Create a SubtaskGenerator instance, passing a dummy config_path
        subtask_generator = SubtaskGenerator(
            config_path="dummy_path.yaml",  # Pass config_path
            overall_context="Test context",
            workspace_context="Test workspace",
        )

        # Verify that load_config was called with the correct path
        mock_load_config.assert_called_once_with("dummy_path.yaml")

        # Verify that OpenRouterAPI was initialized with the correct model configuration from the loaded config
        mock_openrouter.assert_called_once_with(config=expected_model_config)

    @patch("src.ai_whisperer.subtask_generator.load_config")
    @patch("src.ai_whisperer.subtask_generator.OpenRouterAPI")
    def test_subtask_generator_handles_missing_task_model_config(self, mock_openrouter, mock_load_config):
        # Setup mocks with a mock loaded config missing the 'Subtask Generation' task model config
        mock_loaded_config_missing_task_model = SAMPLE_CONFIG_INPUT.copy()
        mock_loaded_config_missing_task_model["task_model_configs"] = (
            {}
        )  # Simulate missing task model config after loading
        mock_loaded_config_missing_task_model["task_prompts_content"] = (
            {  # Still need prompt content for the check after model config
                "subtask_generator": "Mock Subtask Generator Prompt Content"
            }
        )

        mock_load_config.return_value = mock_loaded_config_missing_task_model

        # Based on src/ai_whisperer/subtask_generator.py, it should raise ConfigError if missing
        # So, the test should assert that ConfigError is raised when initializing with a dummy config_path.
        with pytest.raises(
            ConfigError, match="Model configuration for 'subtask_generator' task is missing in the loaded config."
        ):
            SubtaskGenerator(
                config_path="dummy_path.yaml",  # Pass config_path
                overall_context="Test context",
                workspace_context="Test workspace",
            )

        # Verify that load_config was called with the correct path
        mock_load_config.assert_called_once_with("dummy_path.yaml")

        # OpenRouterAPI should NOT be called if ConfigError is raised
        mock_openrouter.assert_not_called()


# Tests for Orchestrator integration with config loading
class TestOrchestratorModelIntegration:
    @patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI")  # Correct patch target
    def test_orchestrator_uses_correct_model_config(self, mock_openrouter):
        # Create a mock config that includes the expected task_model_configs and task_prompts_content, simulating load_config output
        mock_loaded_config = SAMPLE_CONFIG_INPUT.copy()
        mock_loaded_config["task_model_configs"] = {
            "orchestrator": {
                "api_key": "default-api-key",
                "model": "mistralai/mistral-large",
                "params": {"temperature": 0.8, "max_tokens": 8192},
                "site_url": "http://localhost:8000",
                "app_name": "AIWhisperer",
            }
        }
        mock_loaded_config["task_prompts_content"] = {"orchestrator": "Mock Orchestrator Prompt Content"}

        # Expected model configuration for Orchestrator from the mock loaded config
        expected_model_config = mock_loaded_config["task_model_configs"]["orchestrator"]

        # Create an Orchestrator instance, passing the mock loaded config
        orchestrator = Orchestrator(config=mock_loaded_config)

        # Verify that OpenRouterAPI was initialized with the correct model configuration from the loaded config
        mock_openrouter.assert_called_once_with(config=expected_model_config)

    @patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI")  # Correct patch target
    def test_orchestrator_handles_missing_task_model_config(self, mock_openrouter):
        # Create a mock config that includes task_prompts_content but is missing the 'Orchestrator' task model config
        mock_loaded_config_missing_task_model = SAMPLE_CONFIG_INPUT.copy()
        mock_loaded_config_missing_task_model["task_model_configs"] = (
            {}
        )  # Simulate missing task model config after loading
        mock_loaded_config_missing_task_model["task_prompts_content"] = (
            {  # Still need prompt content for the check after model config
                "orchestrator": "Mock Orchestrator Prompt Content"
            }
        )

        # Based on src/ai_whisperer/orchestrator.py, it should raise ConfigError if missing
        # So, the test should assert that ConfigError is raised when initializing with the mock loaded config.
        with pytest.raises(
            ConfigError, match="Model configuration for 'orchestrator' task is missing in the loaded config."
        ):
            Orchestrator(config=mock_loaded_config_missing_task_model)

        # OpenRouterAPI should NOT be called if ConfigError is raised
        mock_openrouter.assert_not_called()
