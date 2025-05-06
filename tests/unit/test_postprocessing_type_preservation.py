import pytest
import yaml
from typing import Dict, Any, Tuple

from src.postprocessing.scripted_steps.identity_transform import identity_transform
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor
from src.postprocessing.scripted_steps.normalize_indentation import normalize_indentation
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper


class TestTypePreservation:
    """Test suite to ensure all postprocessing steps preserve input type in their output."""

    @pytest.fixture
    def sample_dict_yaml(self):
        """Sample YAML content as a dictionary."""
        return {
            "task_id": "sample-task-123",
            "description": "Test type preservation",
            "plan": [
                {
                    "step_id": "step1",
                    "description": "First step"
                },
                {
                    "step_id": "step2",
                    "description": "Second step"
                }
            ]
        }

    @pytest.fixture
    def sample_str_yaml(self):
        """Sample YAML content as a string."""
        return """
task_id: sample-task-123
description: Test type preservation
plan:
  - step_id: step1
    description: First step
  - step_id: step2
    description: Second step
"""

    @pytest.fixture
    def result_data(self):
        """Sample result data dictionary."""
        return {
            "success": True,
            "steps": {},
            "logs": []
        }

    def test_identity_transform_preserves_dict_type(self, sample_dict_yaml, result_data):
        """Test that identity_transform preserves dictionary input type."""
        output_yaml, _ = identity_transform(sample_dict_yaml, result_data)
        assert isinstance(output_yaml, dict)
        assert output_yaml == sample_dict_yaml

    def test_identity_transform_preserves_str_type(self, sample_str_yaml, result_data):
        """Test that identity_transform preserves string input type."""
        output_yaml, _ = identity_transform(sample_str_yaml, result_data)
        assert isinstance(output_yaml, str)
        assert output_yaml == sample_str_yaml

    def test_add_items_postprocessor_preserves_dict_type(self, sample_dict_yaml, result_data):
        """Test that add_items_postprocessor preserves dictionary input type."""
        result_data["items_to_add"] = {
            "top_level": {
                "new_field": "new_value"
            }
        }
        output_yaml, _ = add_items_postprocessor(sample_dict_yaml, result_data)
        assert isinstance(output_yaml, dict)
        assert "new_field" in output_yaml

    def test_add_items_postprocessor_preserves_str_type(self, sample_str_yaml, result_data):
        """Test that add_items_postprocessor preserves string input type."""
        result_data["items_to_add"] = {
            "top_level": {
                "new_field": "new_value"
            }
        }
        output_yaml, _ = add_items_postprocessor(sample_str_yaml, result_data)
        assert isinstance(output_yaml, str)
        assert "new_field" in output_yaml

    def test_normalize_indentation_preserves_dict_type(self, sample_dict_yaml, result_data):
        """Test that normalize_indentation preserves dictionary input type."""
        output_yaml, _ = normalize_indentation(sample_dict_yaml, result_data)
        assert isinstance(output_yaml, dict)
        assert output_yaml == sample_dict_yaml

    def test_normalize_indentation_preserves_str_type(self, sample_str_yaml, result_data):
        """Test that normalize_indentation preserves string input type."""
        output_yaml, _ = normalize_indentation(sample_str_yaml, result_data)
        assert isinstance(output_yaml, str)

    def test_handle_required_fields_preserves_dict_type(self, sample_dict_yaml, result_data):
        """Test that handle_required_fields preserves dictionary input type."""
        result_data["schema"] = {
            "task_id": "default-task",
            "description": "default-description"
        }
        output_yaml, _ = handle_required_fields(sample_dict_yaml, result_data)
        assert isinstance(output_yaml, dict)

    def test_handle_required_fields_preserves_str_type(self, sample_str_yaml, result_data):
        """Test that handle_required_fields preserves string input type."""
        result_data["schema"] = {
            "task_id": "default-task",
            "description": "default-description"
        }
        output_yaml, _ = handle_required_fields(sample_str_yaml, result_data)
        assert isinstance(output_yaml, str)

    def test_validate_syntax_preserves_dict_type(self, sample_dict_yaml, result_data):
        """Test that validate_syntax preserves dictionary input type."""
        output_yaml, _ = validate_syntax(sample_dict_yaml, result_data)
        assert isinstance(output_yaml, dict)
        assert output_yaml == sample_dict_yaml

    def test_validate_syntax_preserves_str_type(self, sample_str_yaml, result_data):
        """Test that validate_syntax preserves string input type."""
        output_yaml, _ = validate_syntax(sample_str_yaml, result_data)
        assert isinstance(output_yaml, str)

    def test_clean_backtick_wrapper_preserves_dict_type(self, sample_dict_yaml, result_data):
        """Test that clean_backtick_wrapper preserves dictionary input type."""
        output_yaml, _ = clean_backtick_wrapper(sample_dict_yaml, result_data)
        assert isinstance(output_yaml, dict)
        assert output_yaml == sample_dict_yaml

    def test_clean_backtick_wrapper_preserves_str_type(self, sample_str_yaml, result_data):
        """Test that clean_backtick_wrapper preserves string input type."""
        # Add backticks to the sample string
        backtick_yaml = f"```yaml\n{sample_str_yaml}\n```"
        output_yaml, _ = clean_backtick_wrapper(backtick_yaml, result_data)
        assert isinstance(output_yaml, str)
        assert "```" not in output_yaml