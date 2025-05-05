"""
Integration tests for the add_items_postprocessor with orchestrator and subtask generator.
"""

import pytest
import yaml
import uuid
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.ai_whisperer.orchestrator import Orchestrator
from src.ai_whisperer.subtask_generator import SubtaskGenerator
from src.postprocessing.add_items_postprocessor import add_items_postprocessor


class TestOrchestratorPostprocessingIntegration:
    """Test the integration of the add_items_postprocessor with the Orchestrator."""

    @patch('src.ai_whisperer.openrouter_api.OpenRouterAPI')
    @patch('src.ai_whisperer.orchestrator.uuid.uuid4')
    def test_orchestrator_adds_task_id_and_hashes(self, mock_uuid4, mock_api):
        """Test that the orchestrator adds task_id and input_hashes via the postprocessor."""
        # Setup
        mock_uuid4.return_value = "test-uuid"
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        
        # Mock the API response with a simple YAML
        mock_api_instance.call_chat_completion.return_value = """
natural_language_goal: Test goal
plan:
  - step_id: test_step
    description: Test step
    agent_spec:
      type: test
      instructions: Test instructions
"""
        # Ensure the mock is used instead of making real API calls
        with patch('src.ai_whisperer.orchestrator.openrouter_api.OpenRouterAPI', return_value=mock_api_instance):
            # Create a test config
            test_config = {
            'openrouter': {
                'api_key': 'test-key',
                'model': 'test-model',
                'params': {}
            },
            'prompts': {
                'orchestrator_prompt_content': 'Test prompt',
                'subtask_generator_prompt_content': 'Test prompt'
            }
        }
        
            # Create temporary files for testing
            tmp_dir = Path("./tmp_test")
            tmp_dir.mkdir(exist_ok=True)
            
            requirements_path = tmp_dir / "test_requirements.md"
            with open(requirements_path, 'w') as f:
                f.write("Test requirements")
            
            config_path = tmp_dir / "test_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Create orchestrator and call generate_initial_yaml
            orchestrator = Orchestrator(test_config, output_dir=str(tmp_dir))
        
            # Mock the _calculate_input_hashes method to return a fixed hash
            with patch.object(orchestrator, '_calculate_input_hashes', return_value={
                'requirements_md': 'test-hash-1',
                'config_yaml': 'test-hash-2',
                'prompt_file': 'test-hash-3'
            }):
                # Mock the _validate_yaml_response method to avoid validation
                with patch.object(orchestrator, '_validate_yaml_response'):
                    # Mock the save_yaml method to capture the YAML content
                    with patch.object(orchestrator, 'save_yaml', return_value=tmp_dir / "output.yaml") as mock_save:
                        orchestrator.generate_initial_yaml(str(requirements_path), str(config_path))
                        
                        # Get the YAML content that would have been saved
                        saved_yaml = mock_save.call_args[0][0]
                        
                        # Verify that task_id and input_hashes were added
                        assert 'task_id' in saved_yaml
                        assert saved_yaml['task_id'] == "test-uuid"
                        assert 'input_hashes' in saved_yaml
                        assert saved_yaml['input_hashes'] == {
                            'requirements_md': 'test-hash-1',
                            'config_yaml': 'test-hash-2',
                            'prompt_file': 'test-hash-3'
                        }
            
            # Clean up
            import shutil
            shutil.rmtree(tmp_dir)


class TestSubtaskGeneratorPostprocessingIntegration:
    """Test the integration of the add_items_postprocessor with the SubtaskGenerator."""

    @patch('src.ai_whisperer.openrouter_api.OpenRouterAPI')
    @patch('src.ai_whisperer.subtask_generator.uuid.uuid4')
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
        with patch('src.ai_whisperer.openrouter_api.OpenRouterAPI', return_value=mock_api_instance):
            # Create a test config
            test_config = {
            'openrouter': {
                'api_key': 'test-key',
                'model': 'test-model',
                'params': {}
            },
            'prompts': {
                'orchestrator_prompt_content': 'Test prompt',
                'subtask_generator_prompt_content': 'Test prompt'
            }
        }
        
            # Create temporary directory for testing
            tmp_dir = Path("./tmp_test")
            tmp_dir.mkdir(exist_ok=True)
            
            config_path = tmp_dir / "test_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Create input step
            input_step = {
                'step_id': 'test_step',
                'description': 'Test step',
                'agent_spec': {
                    'type': 'test',
                    'instructions': 'Test instructions'
                }
            }
            
            # Create subtask generator with the mocked API client
            with patch.object(SubtaskGenerator, 'openrouter_client', mock_api_instance):
                subtask_generator = SubtaskGenerator(str(config_path), output_dir=str(tmp_dir))
        
            # Mock the validate_against_schema method to avoid validation
            with patch('src.ai_whisperer.subtask_generator.validate_against_schema'):
                # Patch open to capture the written YAML
                with patch('builtins.open', create=True) as mock_open:
                    # Call generate_subtask
                    subtask_generator.generate_subtask(input_step)
                    
                    # Get the YAML content that would have been written
                    # This is a bit tricky since we're mocking open
                    # We need to find the call where the YAML was written
                    for call in mock_open.mock_calls:
                        if call[0] == '().__enter__().write':
                            # Convert the written string back to YAML
                            written_yaml = yaml.safe_load(call[1][0])
                            
                            # Verify that subtask_id was added
                            assert 'subtask_id' in written_yaml
                            assert written_yaml['subtask_id'] == "test-subtask-uuid"
                            break
            
            # Clean up
            import shutil
            shutil.rmtree(tmp_dir)


class TestPostprocessorDirectIntegration:
    """Test the direct integration of the add_items_postprocessor with the pipeline."""

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
                    "input_hashes": {"file1": "hash1", "file2": "hash2"}
                },
                "step_level": {
                    "subtask_id": "test-subtask-id"
                }
            },
            "success": True,
            "steps": {},
            "logs": []
        }
        
        # Create pipeline with the add_items_postprocessor
        pipeline = PostprocessingPipeline(
            scripted_steps=[add_items_postprocessor]
        )
        
        # Process the YAML string
        modified_yaml_string, result = pipeline.process(yaml_string, result_data)
        
        # Parse the modified YAML
        modified_yaml = yaml.safe_load(modified_yaml_string)
        
        # Verify that the items were added
        assert 'task_id' in modified_yaml
        assert modified_yaml['task_id'] == "test-task-id"
        assert 'input_hashes' in modified_yaml
        assert modified_yaml['input_hashes'] == {"file1": "hash1", "file2": "hash2"}
        
        # Verify that step-level items were added
        for step in modified_yaml['plan']:
            assert 'subtask_id' in step
            assert step['subtask_id'] == "test-subtask-id"
