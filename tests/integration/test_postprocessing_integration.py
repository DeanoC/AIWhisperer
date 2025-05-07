"""
Integration tests for the postprocessing steps with orchestrator and subtask generator.
"""

import pytest
import json
import uuid
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.ai_whisperer.orchestrator import Orchestrator
from src.ai_whisperer.subtask_generator import SubtaskGenerator
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.pipeline import PostprocessingPipeline


class TestOrchestratorPostprocessingIntegration:
    """Test the integration of the add_items_postprocessor with the Orchestrator."""

    @patch("src.ai_whisperer.openrouter_api.OpenRouterAPI")
    @patch("src.ai_whisperer.orchestrator.uuid.uuid4")
    @patch("src.postprocessing.pipeline.PostprocessingPipeline.process")
    def test_orchestrator_adds_task_id_and_hashes(self, mock_process, mock_uuid4, mock_api):
        """Test that the orchestrator adds task_id and input_hashes via the postprocessor."""
        # Setup
        mock_uuid4.return_value = "test-uuid"
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Create a JSON string with proper indentation, including task_id and input_hashes
        json_dict = {
            "natural_language_goal": "Test goal",
            "plan": [
                {
                    "step_id": "test_step",
                    "description": "Test step",
                    "agent_spec": {
                        "type": "test",
                        "instructions": "Test instructions"
                    }
                }
            ],
            "task_id": "test-uuid",
            "input_hashes": {
                "requirements_md": "test-hash-1",
                "config_json": "test-hash-2",
                "prompt_file": "test-hash-3",
            }
        }

        # Mock the API response
        mock_api_instance.call_chat_completion.return_value = "Some JSON content"

        # Mock the process method to return a valid JSON dictionary and result
        mock_process.return_value = (json_dict, {
            "success": True,
            "steps": {},
            "logs": []
        })

        # Ensure the mock is used instead of making real API calls
        with patch(
            "src.ai_whisperer.orchestrator.openrouter_api.OpenRouterAPI",
            return_value=mock_api_instance,
        ):
            # Create a test config
            test_config = {
                "openrouter": {
                    "api_key": "test-key",
                    "model": "test-model",
                    "params": {},
                },
                "prompts": {
                    "orchestrator_prompt_content": "Test prompt",
                    "subtask_generator_prompt_content": "Test prompt",
                },
            }

            # Create temporary files for testing
            tmp_dir = Path("./tmp_test")
            tmp_dir.mkdir(exist_ok=True)

            requirements_path = tmp_dir / "test_requirements.md"
            with open(requirements_path, "w") as f:
                f.write("Test requirements")

            config_path = tmp_dir / "test_config.json"
            with open(config_path, "w") as f:
                json.dump(test_config, f)

            # Create orchestrator and call generate_initial_json
            orchestrator = Orchestrator(test_config, output_dir=str(tmp_dir))

            # Mock the _calculate_input_hashes method to return a fixed hash
            with patch.object(
                orchestrator,
                "_calculate_input_hashes",
                return_value={
                    "requirements_md": "test-hash-1",
                    "config_json": "test-hash-2",
                    "prompt_file": "test-hash-3",
                },
            ):
                # Mock the _validate_json_response method to avoid validation
                # Mock the save_json method to capture the JSON content
                with patch.object(
                    orchestrator, "save_json", return_value=tmp_dir / "output.json"
                ) as mock_save:
                    orchestrator.generate_initial_json(
                        str(requirements_path), str(config_path)
                    )

                    # Get the JSON content that would have been saved
                    saved_json = mock_save.call_args[0][0]
                    # If the saved content is a string, parse it as JSON
                    if isinstance(saved_json, str):
                        saved_json = json.loads(saved_json)

                    # Verify that task_id and input_hashes were added
                    assert "task_id" in saved_json
                    assert saved_json["task_id"] == "test-uuid"
                    assert "input_hashes" in saved_json
                    assert saved_json["input_hashes"] == {
                        "requirements_md": "test-hash-1",
                        "config_json": "test-hash-2",
                        "prompt_file": "test-hash-3",
                    }

            # Clean up
            import shutil

            shutil.rmtree(tmp_dir)


class TestSubtaskGeneratorPostprocessingIntegration:
    """Test the integration of the add_items_postprocessor with the SubtaskGenerator."""

    @patch("src.ai_whisperer.openrouter_api.OpenRouterAPI")
    @patch("src.ai_whisperer.subtask_generator.uuid.uuid4")
    @patch("src.postprocessing.pipeline.PostprocessingPipeline.process")
    def test_subtask_generator_adds_subtask_id(self, mock_process, mock_uuid4, mock_api):
        """Test that the subtask generator adds subtask_id via the postprocessor."""
        # Setup
        mock_uuid4.return_value = "test-subtask-uuid"
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Create a JSON dictionary with the expected fields
        json_dict = {
            "step_id": "test_step",
            "description": "Test step",
            "agent_spec": {
                "type": "test",
                "instructions": "Test instructions"
            },
            "subtask_id": "test-subtask-uuid"
        }

        # Mock the API response with a simple JSON
        mock_api_instance.call_chat_completion.return_value = """
{
  "step_id": "test_step",
  "description": "Test step",
  "agent_spec": {
    "type": "test",
    "instructions": "Test instructions"
  }
}
"""
        # Set model and params attributes on the mock
        mock_api_instance.model = "test-model"
        mock_api_instance.params = {}

        # Mock the process method to return a valid JSON dictionary and result
        mock_process.return_value = (json_dict, {
            "success": True,
            "steps": {},
            "logs": []
        })

        # Ensure the mock is used instead of making real API calls
        with patch(
            "src.ai_whisperer.openrouter_api.OpenRouterAPI",
            return_value=mock_api_instance,
        ):
            # Create a test config
            test_config = {
                "openrouter": {
                    "api_key": "test-key",
                    "model": "test-model",
                    "params": {},
                },
                "prompts": {
                    "orchestrator_prompt_content": "Test prompt",
                    "subtask_generator_prompt_content": "Test prompt",
                },
            }

            # Create temporary directory for testing
            tmp_dir = Path("./tmp_test")
            tmp_dir.mkdir(exist_ok=True)

            config_path = tmp_dir / "test_config.json"
            with open(config_path, "w") as f:
                json.dump(test_config, f)

            # Create input step
            input_step = {
                "step_id": "test_step",
                "description": "Test step",
                "agent_spec": {"type": "test", "instructions": "Test instructions"},
            }

            # Create subtask generator
            subtask_generator = SubtaskGenerator(
                str(config_path), output_dir=str(tmp_dir)
            )

            # Replace the openrouter_client with our mock
            subtask_generator.openrouter_client = mock_api_instance

            # Mock the validate_against_schema method to avoid validation
            with patch("src.ai_whisperer.subtask_generator.validate_against_schema"):
                # Create a simple schema for testing
                subtask_schema = {
                    "type": "object",
                    "properties": {
                        "step_id": {"type": "string"},
                        "subtask_id": {"type": "string"},
                        "description": {"type": "string"},
                        "agent_spec": {"type": "object"}
                    },
                    "required": ["step_id", "subtask_id", "description", "agent_spec"]
                }

                # Mock the open function to avoid writing to a file
                with patch("builtins.open", mock_open()):
                    # Create result_data with items to add and the schema
                    result_data = {
                        "items_to_add": {
                            "top_level": {
                                "subtask_id": str(mock_uuid4.return_value),  # Use mocked UUID
                                "step_id": input_step["step_id"],  # Preserve the original step_id
                            },
                            "step_level": {},  # No step-level items for subtasks
                        },
                        "success": True,
                        "steps": {},
                        "logs": [],
                        "schema": subtask_schema, # Add the schema here
                    }

                    # Call generate_subtask with the updated result_data
                    subtask_generator.generate_subtask(input_step, result_data=result_data)

                    # Verify that the process method was called with the expected arguments
                    mock_process.assert_called_once()

                    # Verify that the returned JSON dictionary has the expected fields
                    assert json_dict["step_id"] == "test_step"
                    assert json_dict["subtask_id"] == "test-subtask-uuid"
                    assert json_dict["description"] == "Test step"
                    assert json_dict["agent_spec"]["type"] == "test"
                    assert json_dict["agent_spec"]["instructions"] == "Test instructions"

            # Clean up
            import shutil

            shutil.rmtree(tmp_dir)
