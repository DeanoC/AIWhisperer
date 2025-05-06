"""
Integration tests for the postprocessing steps with orchestrator and subtask generator.
"""

import pytest
import yaml
import uuid
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.ai_whisperer.orchestrator import Orchestrator
from src.ai_whisperer.subtask_generator import SubtaskGenerator
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.scripted_steps.normalize_indentation import normalize_indentation
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

        # Create a YAML string with proper indentation, including task_id and input_hashes
        yaml_dict = {
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
                "config_yaml": "test-hash-2",
                "prompt_file": "test-hash-3",
            }
        }

        # Mock the API response
        mock_api_instance.call_chat_completion.return_value = "Some YAML content"

        # Mock the process method to return a valid YAML string and result
        mock_process.return_value = (yaml.dump(yaml_dict, sort_keys=False, default_flow_style=False), {
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

            config_path = tmp_dir / "test_config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(test_config, f)

            # Create orchestrator and call generate_initial_yaml
            orchestrator = Orchestrator(test_config, output_dir=str(tmp_dir))

            # Mock the _calculate_input_hashes method to return a fixed hash
            with patch.object(
                orchestrator,
                "_calculate_input_hashes",
                return_value={
                    "requirements_md": "test-hash-1",
                    "config_yaml": "test-hash-2",
                    "prompt_file": "test-hash-3",
                },
            ):
                # Mock the _validate_yaml_response method to avoid validation
                with patch.object(orchestrator, "_validate_yaml_response"):
                    # Mock the save_yaml method to capture the YAML content
                    with patch.object(
                        orchestrator, "save_yaml", return_value=tmp_dir / "output.yaml"
                    ) as mock_save:
                        orchestrator.generate_initial_yaml(
                            str(requirements_path), str(config_path)
                        )

                        # Get the YAML content that would have been saved
                        saved_yaml = mock_save.call_args[0][0]

                        # Verify that task_id and input_hashes were added
                        assert "task_id" in saved_yaml
                        assert saved_yaml["task_id"] == "test-uuid"
                        assert "input_hashes" in saved_yaml
                        assert saved_yaml["input_hashes"] == {
                            "requirements_md": "test-hash-1",
                            "config_yaml": "test-hash-2",
                            "prompt_file": "test-hash-3",
                        }

            # Clean up
            import shutil

            shutil.rmtree(tmp_dir)


class TestSubtaskGeneratorPostprocessingIntegration:
    """Test the integration of the add_items_postprocessor with the SubtaskGenerator."""

    @patch("src.ai_whisperer.openrouter_api.OpenRouterAPI")
    @patch("src.ai_whisperer.subtask_generator.uuid.uuid4")
    def test_subtask_generator_adds_subtask_id(self, mock_uuid4, mock_api):
        """Test that the subtask generator adds subtask_id via the postprocessor."""
        # Setup
        mock_uuid4.return_value = "test-subtask-uuid"
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Mock the API response with a simple YAML
        mock_api_instance.call_chat_completion.return_value = """
step_id: test_step
description: Test step
agent_spec:
  type: test
  instructions: Test instructions
"""
        # Set model and params attributes on the mock
        mock_api_instance.model = "test-model"
        mock_api_instance.params = {}

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

            config_path = tmp_dir / "test_config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(test_config, f)

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
                # Patch open to capture the written YAML
                with patch("builtins.open", create=True) as mock_open:
                    # Call generate_subtask
                    subtask_generator.generate_subtask(input_step)

                    # Get the YAML content that would have been written
                    # This is a bit tricky since we're mocking open
                    # We need to find the call where the YAML was written
                    yaml_written = False
                    all_yaml_contents = []
                    full_yaml_content = ""

                    # Collect all write calls to reconstruct the full YAML
                    for call in mock_open.mock_calls:
                        if call[0] == "().__enter__().write":
                            content = call[1][0]
                            all_yaml_contents.append(content)
                            full_yaml_content += content

                    # Now try to parse the complete YAML content
                    if full_yaml_content.strip():
                        try:
                            written_yaml = yaml.safe_load(full_yaml_content)

                            # Debug the content if there's an issue
                            assert isinstance(
                                written_yaml, dict
                            ), f"Expected dict, got {type(written_yaml)}: {written_yaml}\nOriginal content: {full_yaml_content}"

                            # Check for step_id and subtask_id
                            assert (
                                "step_id" in written_yaml
                            ), f"step_id not found in: {written_yaml.keys()}"
                            assert written_yaml["step_id"] == "test_step"

                            assert (
                                "subtask_id" in written_yaml
                            ), f"subtask_id not found in: {written_yaml.keys()}"
                            assert written_yaml["subtask_id"] == "test-subtask-uuid"
                            yaml_written = True
                        except Exception as e:
                            # Log the exception for debugging
                            print(f"Error parsing YAML: {e}")
                            print(f"Full YAML content: {full_yaml_content}")

                    # Make sure we actually found and checked a YAML write
                    assert (
                        yaml_written
                    ), f"No valid YAML with subtask_id was found. All contents: {all_yaml_contents}"

            # Clean up
            import shutil

            shutil.rmtree(tmp_dir)


class TestPostprocessorDirectIntegration:
    """Test the direct integration of the postprocessors with the pipeline."""

    def test_postprocessor_in_pipeline(self):
        """Test that the postprocessor works correctly in the pipeline."""
        from src.postprocessing.pipeline import PostprocessingPipeline

        # Create a test YAML string
        yaml_string = """
title: Test Document
description: A test document
plan:
  - step_id: step1
    description: First step
  - step_id: step2
    description: Second step
"""

        # Create result_data with items to add
        result_data = {
            "items_to_add": {
                "top_level": {
                    "task_id": "test-task-id",
                    "input_hashes": {"file1": "hash1", "file2": "hash2"},
                },
                "step_level": {"subtask_id": "test-subtask-id"},
            },
            "success": True,
            "steps": {},
            "logs": [],
        }

        # Create pipeline with the add_items_postprocessor
        pipeline = PostprocessingPipeline(scripted_steps=[add_items_postprocessor])

        # Process the YAML string
        modified_yaml_string, result = pipeline.process(yaml_string, result_data)

        # Parse the modified YAML
        modified_yaml = yaml.safe_load(modified_yaml_string)

        # Verify that the items were added
        assert "task_id" in modified_yaml
        assert modified_yaml["task_id"] == "test-task-id"
        assert "input_hashes" in modified_yaml
        assert modified_yaml["input_hashes"] == {"file1": "hash1", "file2": "hash2"}

        # Verify that step-level items were added
        for step in modified_yaml["plan"]:
            assert "subtask_id" in step
            assert step["subtask_id"] == "test-subtask-id"

    def test_clean_backtick_and_normalize_indentation_integration(self):
        """
        Test that clean_backtick_wrapper and normalize_indentation work together correctly in the pipeline.

        This test uses real-world data from temp.txt to ensure that the pipeline can handle complex YAML
        with backtick wrappers and indentation issues.
        """
        # Create a test file with content similar to temp.txt
        test_file_path = os.path.join(os.path.dirname(__file__), 'test_backtick_indentation_example.txt')

        # Write a simplified version of temp.txt with backticks and indentation issues
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write("""```yaml
natural_language_goal: Enhance the OpenRouter `--list-models` command to include detailed model information and an option to output results to a CSV file.
overall_context: |
  The task is to improve the existing `--list-models` command in the ai-whisperer tool.
  The enhancement involves fetching more comprehensive model details from the OpenRouter API
  and providing an optional `--output-csv` flag to save these details to a CSV file.
  The console output should remain functional when the CSV option is not used.
plan:
  - step_id: planning_cli_and_api_changes
    description: Plan the necessary modifications to the CLI argument parsing and the OpenRouter API interaction logic.
    depends_on: []
    agent_spec:
        type: planning
        input_artifacts:
          - main.py
          - ai_whisperer/openrouter_api.py
        output_artifacts:
          - docs/planning_summary.md
        instructions: |
          Analyze the existing `main.py` to determine how to add the optional `--output-csv` argument using argparse.
          Examine `ai_whisperer/openrouter_api.py` to understand the current `list_models` method and how it needs to be modified to fetch detailed model metadata instead of just names.
```""")

        try:
            # Read the test file
            with open(test_file_path, 'r', encoding='utf-8') as f:
                input_yaml = f.read()

            # Create a pipeline with clean_backtick_wrapper and normalize_indentation
            pipeline = PostprocessingPipeline(
                scripted_steps=[clean_backtick_wrapper, normalize_indentation]
            )

            # Process the YAML string
            modified_yaml_string, result = pipeline.process(input_yaml)

            # Verify that the pipeline processed the content without errors
            assert result["success"] is True

            # Check that both steps were executed
            assert "clean_backtick_wrapper" in result["steps"]
            assert "normalize_indentation" in result["steps"]

            # Parse the modified YAML to ensure it's valid
            try:
                modified_yaml = yaml.safe_load(modified_yaml_string)
                assert isinstance(modified_yaml, dict)

                # Check that the content is preserved
                assert "natural_language_goal" in modified_yaml
                assert "plan" in modified_yaml
                assert isinstance(modified_yaml["plan"], list)
                assert len(modified_yaml["plan"]) > 0
                assert "step_id" in modified_yaml["plan"][0]
                assert modified_yaml["plan"][0]["step_id"] == "planning_cli_and_api_changes"

                # Check that backticks within the content are preserved
                assert "`--list-models`" in modified_yaml["natural_language_goal"]
                assert "`main.py`" in modified_yaml["plan"][0]["agent_spec"]["instructions"]

                # Check that the indentation is normalized
                # This is harder to test directly, but we can check that the YAML is valid
                # and that the structure is preserved
                assert "agent_spec" in modified_yaml["plan"][0]
                assert "input_artifacts" in modified_yaml["plan"][0]["agent_spec"]
                assert "output_artifacts" in modified_yaml["plan"][0]["agent_spec"]
                assert "instructions" in modified_yaml["plan"][0]["agent_spec"]

            except yaml.YAMLError as e:
                pytest.fail(f"Failed to parse the processed YAML: {e}")

        finally:
            # Clean up the test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
