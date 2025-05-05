"""
Unit tests for the scripted postprocessing identity transform.
"""
import pytest
from src.postprocessing.scripted_steps.identity_transform import identity_transform


def test_identity_transform():
    """
    Test that the identity transform returns the input YAML data unchanged.
    """
    # Sample YAML input represented as a Python dictionary
    sample_yaml_data = {
        "task_id": "sample-task-123",
        "natural_language_goal": "Test the identity transform",
        "overall_context": "Ensuring our postprocessing pipeline works correctly",
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
    
    # Sample result data structure
    sample_result_data = {
        "success": True,
        "steps": {},
        "logs": []
    }
    
    # Call the identity transform function
    output_yaml_data, output_result_data = identity_transform(sample_yaml_data, sample_result_data)
    
    # Assert that the output YAML is identical to the input
    assert output_yaml_data == sample_yaml_data
    
    # Assert that the output result data is identical to the input
    assert output_result_data == sample_result_data
    
    # Additionally, check that they are the same objects (identity)
    assert output_yaml_data is sample_yaml_data
    assert output_result_data is sample_result_data


def test_identity_transform_with_empty_input():
    """
    Test that the identity transform handles empty input correctly.
    """
    # Empty YAML data
    empty_yaml_data = {}
    
    # Empty result data
    empty_result_data = {
        "success": True,
        "steps": {},
        "logs": []
    }
    
    # Call the identity transform function
    output_yaml_data, output_result_data = identity_transform(empty_yaml_data, empty_result_data)
    
    # Assert that the outputs match the inputs
    assert output_yaml_data == empty_yaml_data
    assert output_result_data == empty_result_data


def test_identity_transform_with_complex_nested_structure():
    """
    Test that the identity transform handles complex nested structures correctly.
    """
    # More complex nested YAML structure
    complex_yaml_data = {
        "task_id": "complex-task-456",
        "metadata": {
            "created_at": "2025-05-05T10:00:00Z",
            "created_by": "test_user",
            "tags": ["test", "identity", "transform"]
        },
        "configuration": {
            "settings": {
                "verbose": True,
                "debug": False,
                "timeout": 30,
                "retry": {
                    "attempts": 3,
                    "delay": 5
                }
            },
            "environment": {
                "variables": {
                    "API_KEY": "sample-key-123",
                    "BASE_URL": "https://example.com/api"
                }
            }
        },
        "data": [
            {"id": 1, "name": "Item 1", "active": True},
            {"id": 2, "name": "Item 2", "active": False},
            {"id": 3, "name": "Item 3", "active": True}
        ]
    }
    
    # Result data with some pre-existing information
    complex_result_data = {
        "success": True,
        "steps": {
            "previous_step": {
                "success": True,
                "changes": ["Changed something"],
                "errors": [],
                "warnings": ["Just a warning"]
            }
        },
        "logs": ["Previous step completed"]
    }
    
    # Call the identity transform function
    output_yaml_data, output_result_data = identity_transform(complex_yaml_data, complex_result_data)
    
    # Assert that the outputs match the inputs
    assert output_yaml_data == complex_yaml_data
    assert output_result_data == complex_result_data
