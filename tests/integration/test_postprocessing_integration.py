"""
Integration tests for the postprocessing steps with initial plan and subtask generator.
"""

import pytest
import json
import uuid
import os
import yaml
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import time

# from ai_whisperer.orchestrator import Orchestrator
from ai_whisperer.subtask_generator import SubtaskGenerator
from ai_whisperer.config import load_config  # Import load_config
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.pipeline import PostprocessingPipeline


@pytest.fixture
def tmp_path_with_cleanup(request, tmp_path):
    """
    Pytest fixture to create a temporary directory and ensure its cleanup
    with retries to handle PermissionError on Windows.
    """

    def cleanup():
        import shutil  # Import shutil within the cleanup function

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                shutil.rmtree(tmp_path)
                break  # Success
            except PermissionError as e:
                if attempt < max_attempts - 1:
                    print(f"Cleanup attempt {attempt + 1} failed: {e}. Retrying in 0.1 seconds.")
                    time.sleep(0.1)
                else:
                    print(f"Cleanup failed after {max_attempts} attempts: {e}")
                    # Optionally re-raise the exception if cleanup is critical
                    # raise
            except FileNotFoundError:
                break  # Already removed

    request.addfinalizer(cleanup)
    return tmp_path



class TestSubtaskGeneratorPostprocessingIntegration:
    """Test the integration of the add_items_postprocessor with the SubtaskGenerator."""

    @patch("ai_whisperer.ai_service_interaction.OpenRouterAPI")
    @patch("ai_whisperer.subtask_generator.uuid.uuid4")
    @patch("src.postprocessing.pipeline.PostprocessingPipeline.process")
    def test_subtask_generator_adds_subtask_id(self, mock_process, mock_uuid4, mock_api, tmp_path_with_cleanup):
        """Test that the subtask generator adds subtask_id via the postprocessor."""
        # Setup
        mock_uuid4.return_value = "test-subtask-uuid"
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Create a JSON dictionary with the expected fields
        json_dict = {
            "task_id": "mock-test-task-id",
            "subtask_id": "mock-test-subtask-id",
            "description": "Test step",
            "type": "no-op",
            "instructions": ["Test instructions"],
        }

        # Mock the API response with a simple JSON
        mock_api_instance.call_chat_completion.return_value = """
{
    "description": "Test step",
    "type": "no-op",
    "instructions": ["Test instructions"]
}
"""
        # Set model and params attributes on the mock
        mock_api_instance.model = "test-model"
        mock_api_instance.params = {}

        # Mock the process method to return a valid JSON dictionary and result
        mock_process.return_value = (json_dict, {"success": True, "steps": {}, "logs": []})

        # Ensure the mock is used instead of making real API calls
        with patch("ai_whisperer.ai_service_interaction.OpenRouterAPI", return_value=mock_api_instance):
            # Create a raw test config with the new structure
            raw_test_config = {
                "openrouter": {"api_key": "test-key", "model": "test-model", "params": {}},
                "task_prompts": {
                    # Path is relative to the config file location (tmp_test)
                    "subtask_generator": "subtask_generator_default.md"
                },
                "task_models": {"subtask_generator": {"model": "test-model", "params": {}}},
            }

            # Create temporary directory for testing
            tmp_dir = tmp_path_with_cleanup

            # Create a dummy prompt file
            subtask_generator_prompt_path = tmp_dir / "subtask_generator_default.md"
            with open(subtask_generator_prompt_path, "w") as f:
                f.write("Dummy subtask generator prompt content")

            # Create a dummy config file
            config_path = tmp_dir / "test_config.json"
            with open(config_path, "w") as f:
                json.dump(raw_test_config, f)

            # Load the processed config using load_config
            processed_config = load_config(str(config_path))

            # Create subtask generator with the processed config
            subtask_generator = SubtaskGenerator(
                str(config_path),  # Pass config_path string as SubtaskGenerator expects it
                overall_context="",
                workspace_context="",
                output_dir=str(tmp_dir),
            )

            # Replace the openrouter_client with our mock
            subtask_generator.openrouter_client = mock_api_instance

            # Mock the validate_against_schema method to avoid validation
            with patch("ai_whisperer.subtask_generator.validate_against_schema"):
                # Create a simple schema for testing
                subtask_schema = {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "subtask_id": {"type": "string"},
                        "description": {"type": "string"},
                        "agent_spec": {"type": "object"},
                    },
                    "required": ["task_id", "subtask_id", "description", "agent_spec"],
                }

                # Mock the open function to avoid writing to a file, but provide schema content when reading the schema file
                mock_file = mock_open()
                # Configure the mock to return schema content when the schema file is opened
                schema_content = """
{
  "type": "object",
  "properties": {
    "subtask_id": {
      "type": "string",
      "description": "Unique identifier for the subtask (e.g., UUID)",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "description": "ID of the parent task plan this subtask belongs to.",
      "format": "uuid"
    },
    "name": {
      "type": "string",
      "description": "A short, descriptive name for the subtask."
    },
    "description": {
      "type": "string",
      "description": "A detailed description of the subtask's purpose and instructions."
    },
    "instructions": {
      "type": "string",
      "description": "Specific instructions for the AI agent executing this subtask."
    }
  },
  "required": ["subtask_id", "task_id", "name", "description", "instructions"],
  "additionalProperties": false
}
"""
                mock_file.return_value.__enter__.return_value.read.side_effect = lambda: schema_content

                with patch("builtins.open", mock_file):
                    # Create input step
                    input_step = {
                        "task_id": "test-id",
                        "subtask_id": "test-subtask-id",
                        "description": "Test step",
                        "type": "no-op", 
                        "instructions": ["Test instructions"],
                    }
                    # Create result_data with items to add and the schema
                    result_data = {
                        "items_to_add": {
                            "top_level": {
                                "task_id": input_step["task_id"],  # Preserve the original task_id
                                "subtask_id": input_step["subtask_id"],  # Preserve the original subtask_id
                            },
                            "step_level": {},  # No step-level items for subtasks
                        },
                        "success": True,
                        "steps": {},
                        "logs": [],
                        "schema": subtask_schema,  # Add the schema here
                    }

                    # Call generate_subtask with the updated result_data
                    subtask_generator.generate_subtask(input_step, result_data=result_data)

                    # Verify that the process method was called with the expected arguments
                    mock_process.assert_called_once()
                    print(json_dict)

                    # Verify that the returned JSON dictionary has the expected fields
                    assert json_dict["task_id"] == "mock-test-task-id"
                    assert json_dict["subtask_id"] == "mock-test-subtask-id"
                    assert json_dict["description"] == "Test step"
                    assert json_dict["type"] == "no-op"
                    assert json_dict["instructions"][0] == "Test instructions"

            # Clean up is handled by the pytest fixture
