"""
Unit tests for the JSON postprocessing pipeline.

This module tests the overall structure and execution flow of the postprocessing pipeline,
ensuring that the scripted and AI improvement phases work together correctly.
"""
import pytest
from src.postprocessing.pipeline import PostprocessingPipeline
from src.postprocessing.scripted_steps.identity_transform import identity_transform
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper

def test_pipeline_with_identity_step():
    """
    Test that the pipeline correctly chains steps and processes JSON data.
    
    This test uses the identity transform for both the scripted phase and the AI phase,
    which means the output should be identical to the input.
    """
    # Sample JSON input represented as a Python dictionary
    sample_json_data = {
        "task_id": "pipeline-test-123",
        "natural_language_goal": "Test the postprocessing pipeline",
        "overall_context": "Ensuring our chain of processing steps works correctly",
        "plan": [
            {
                "step_id": "step1",
                "description": "First step in the plan",
                "depends_on": []
            },
            {
                "step_id": "step2",
                "description": "Second step in the plan",
                "depends_on": ["step1"]
            }
        ]
    }
    
    # Create a pipeline with identity_transform as the only scripted step
    # Note: The pipeline implementation will handle the AI phase internally,
    # which is also initially an identity transform
    pipeline = PostprocessingPipeline(
        scripted_steps=[identity_transform],
        # The dummy AI phase is handled internally in the pipeline
    )
    
    # Process the JSON data through the pipeline
    output_json_data, output_result = pipeline.process(sample_json_data)

    # Assert that the output JSON is identical to the input
    assert output_json_data == sample_json_data
    
    # Assert that the pipeline execution was successful
    assert output_result["success"] is True
    
    # Check that the result includes entries for all steps including the AI phase
    assert "identity_transform" in output_result["steps"]
    assert "ai_improvement_phase" in output_result["steps"]


def test_pipeline_with_multiple_identity_steps():
    """
    Test that the pipeline correctly handles multiple scripted steps.
    
    This test uses multiple identity transforms in the scripted phase to ensure
    the chaining mechanism works correctly.
    """
    # Sample JSON input
    sample_json_data = {
        "task_id": "multi-step-test-456",
        "description": "Testing multiple scripted steps"
    }
    
    # Initial result object
    initial_result = {
        "success": True,
        "steps": {},
        "logs": []
    }
    
    # Create a pipeline with multiple identity transforms
    # Each transform is the same function but will be tracked separately in the results
    pipeline = PostprocessingPipeline(
        scripted_steps=[identity_transform, identity_transform, identity_transform],
        # The AI phase is handled internally
    )
    
    # Process the JSON data
    output_json_data, output_result = pipeline.process(sample_json_data, initial_result)
    
    # Assert output matches input
    assert output_json_data == sample_json_data

    # Check that the result object tracks all steps correctly
    # We expect to see entries for the identity transform steps and the AI phase
    step_keys = output_result["steps"].keys()
    
    # Check if we have an AI phase
    assert "ai_improvement_phase" in step_keys
    
    # Count identity transform steps (may include variations like identity_transform_1, etc.)
    identity_steps = [key for key in step_keys if key.startswith("identity_transform")]
    assert len(identity_steps) >= 1
    
    # Ensure overall success
    assert output_result["success"] is True

def test_clean_backtick_wrapper():
    """
    Test that clean_backtick_wrapper removes code block wrappers correctly.
    """
    json_data = "```json\n{\n  \"task\": \"example\"\n}\n```"
    result_data = {"success": True, "steps": {}, "logs": []}
    
    cleaned_json, updated_result = clean_backtick_wrapper(json_data, result_data)
    
    assert cleaned_json == "{\n  \"task\": \"example\"\n}\n"
    assert updated_result["success"] is True
