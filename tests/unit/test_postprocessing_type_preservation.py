import pytest
import json  # Import json
from typing import Dict, Any, Tuple

from src.postprocessing.scripted_steps.identity_transform import identity_transform
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper


class TestTypePreservation:
    """Test suite to ensure all postprocessing steps preserve input type in their output."""

    @pytest.fixture
    def sample_dict_json(self):
        """Sample JSON content as a dictionary."""
        return {
            "task_id": "sample-task-123",
            "description": "Test type preservation",
            "plan": [
                {"subtask_id": "step1", "description": "First step"},
                {"subtask_id": "step2", "description": "Second step"},
            ],
        }

    @pytest.fixture
    def sample_str_json(self):
        """Sample JSON content as a string."""
        return """
{
  "task_id": "sample-task-123",
  "description": "Test type preservation",
  "plan": [
    {
      "subtask_id": "step1",
      "description": "First step"
    },
    {
      "subtask_id": "step2",
      "description": "Second step"
    }
  ]
}
"""

    @pytest.fixture
    def result_data(self):
        """Sample result data dictionary."""
        return {"success": True, "steps": {}, "logs": []}

    def test_identity_transform_preserves_dict_type(self, sample_dict_json, result_data):
        """Test that identity_transform preserves dictionary input type."""
        (output_json, _) = identity_transform(sample_dict_json, result_data)
        assert isinstance(output_json, dict)
        assert output_json == sample_dict_json

    def test_identity_transform_preserves_str_type(self, sample_str_json, result_data):
        """Test that identity_transform preserves string input type."""
        (output_json, _) = identity_transform(sample_str_json, result_data)
        assert isinstance(output_json, str)
        assert output_json == sample_str_json

    def test_add_items_postprocessor_preserves_dict_type(self, sample_dict_json, result_data):
        """Test that add_items_postprocessor preserves dictionary input type."""
        result_data["items_to_add"] = {"top_level": {"new_field": "new_value"}}
        (output_json, _) = add_items_postprocessor(sample_dict_json, result_data)
        assert isinstance(output_json, dict)
        assert "new_field" in output_json

    def test_add_items_postprocessor_preserves_str_type(self, sample_str_json, result_data):
        """Test that add_items_postprocessor preserves string input type."""
        result_data["items_to_add"] = {"top_level": {"new_field": "new_value"}}
        (output_json, _) = add_items_postprocessor(sample_str_json, result_data)
        assert isinstance(output_json, str)
        # We expect the output to be a JSON string with the new field added
        assert '"new_field": "new_value"' in output_json

    def test_handle_required_fields_preserves_dict_type(self, sample_dict_json, result_data):
        """Test that handle_required_fields preserves dictionary input type."""
        result_data["schema"] = {"task_id": "default-task", "description": "default-description"}
        (output_json, _) = handle_required_fields(sample_dict_json, result_data)
        assert isinstance(output_json, dict)

    def test_handle_required_fields_preserves_str_type(self, sample_str_json, result_data):
        """Test that handle_required_fields preserves string input type."""
        result_data["schema"] = {"task_id": "default-task", "description": "default-description"}
        (output_json, _) = handle_required_fields(sample_str_json, result_data)
        assert isinstance(output_json, str)
        # We expect the output to be a JSON string with default values added if missing
        assert '"task_id": "sample-task-123"' in output_json or '"task_id": "default-task"' in output_json
        assert (
            '"description": "Test type preservation"' in output_json
            or '"description": "default-description"' in output_json
        )

    def test_validate_syntax_preserves_dict_type(self, sample_dict_json, result_data):
        """Test that validate_syntax preserves dictionary input type."""
        (output_json, _) = validate_syntax(sample_dict_json, result_data)
        assert isinstance(output_json, dict)
        assert output_json == sample_dict_json

    def test_validate_syntax_preserves_str_type(self, sample_str_json, result_data):
        """Test that validate_syntax preserves string input type."""
        (output_json, _) = validate_syntax(sample_str_json, result_data)
        assert isinstance(output_json, dict)
        # We expect the output to be the parsed JSON dictionary if it's valid
        assert output_json == json.loads(sample_str_json)

    def test_clean_backtick_wrapper_preserves_dict_type(self, sample_dict_json, result_data):
        """Test that clean_backtick_wrapper preserves dictionary input type."""
        (output_json, _) = clean_backtick_wrapper(sample_dict_json, result_data)
        assert isinstance(output_json, dict)
        assert output_json == sample_dict_json

    def test_clean_backtick_wrapper_preserves_str_type(self, sample_str_json, result_data):
        """Test that clean_backtick_wrapper preserves string input type."""
        # Add backticks to the sample string
        backtick_json = f"```json\n{sample_str_json}\n```"
        (output_json, _) = clean_backtick_wrapper(backtick_json, result_data)
        assert isinstance(output_json, str)
        assert "```" not in output_json
        # The cleaned output should be the original JSON string with a leading newline
        assert output_json.strip() == sample_str_json.strip()
