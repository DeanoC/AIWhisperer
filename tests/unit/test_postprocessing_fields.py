import pytest
import json
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields

# Mock schema for testing
SCHEMA = {
    "required": ["required_field_1", "required_field_2", "nested_field"],
    "required_field_1": {"default": "default_value_1"},
    "required_field_2": {"default": "default_value_2"},
    "nested_field": {
        "type": "object",
        "required": ["nested_required_1"],
        "properties": {"nested_required_1": {"default": "nested_default_1"}},
    },
    "optional_field": None,  # Optional field with no default
}


@pytest.mark.parametrize(
    "description, input_content, expected_content",
    [
        # Case: All required fields present (dict input)
        (
            "All required fields present (dict)",
            {
                "required_field_1": "value1",
                "required_field_2": "value2",
                "nested_field": {"nested_required_1": "value3"},
            },
            {
                "required_field_1": "value1",
                "required_field_2": "value2",
                "nested_field": {"nested_required_1": "value3"},
            },
        ),
        # Case: Missing required fields (dict input) - only adds fields that are explicitly required in their own schema
        ("Missing required fields (dict)", {"required_field_1": "value1"}, {"required_field_1": "value1"}),
        # Case: Extra fields (dict input) - should be preserved, no additional fields added
        (
            "Extra fields (dict)",
            {"required_field_1": "value1", "extra_field": "invalid"},
            {"required_field_1": "value1", "extra_field": "invalid"},
        ),
        # Case: Incorrect data types (dict input) - should preserve incorrect type for non-null, preserve null
        (
            "Incorrect data types (dict)",
            {"required_field_1": 123, "required_field_2": None, "nested_field": {"nested_required_1": 456}},
            {"required_field_1": 123, "required_field_2": None, "nested_field": {"nested_required_1": 456}},
        ),
        # Case: Empty input (dict) - no fields added as none are explicitly required in their own schema
        ("Empty input (dict)", {}, {}),
        # Case: Fields set to null (dict input) - nulls are preserved, no missing fields added
        (
            "Fields set to null (dict)",
            {"required_field_1": None, "nested_field": {"nested_required_1": None}},
            {"required_field_1": None, "nested_field": {"nested_required_1": None}},
        ),
        # Case: All required fields present (JSON string input)
        (
            "All required fields present (JSON string)",
            '{"required_field_1": "value1", "required_field_2": "value2", "nested_field": {"nested_required_1": "value3"}}',
            {
                "required_field_1": "value1",
                "required_field_2": "value2",
                "nested_field": {"nested_required_1": "value3"},
            },
        ),
        # Case: Missing required fields (JSON string input) - only adds fields that are explicitly required in their own schema
        ("Missing required fields (JSON string)", '{"required_field_1": "value1"}', {"required_field_1": "value1"}),
        # Case: Extra fields (JSON string input) - should be preserved, no additional fields added
        (
            "Extra fields (JSON string)",
            '{"required_field_1": "value1", "extra_field": "invalid"}',
            {"required_field_1": "value1", "extra_field": "invalid"},
        ),
        # Case: Incorrect data types (JSON string input) - should preserve incorrect type for non-null, preserve null
        (
            "Incorrect data types (JSON string)",
            '{"required_field_1": 123, "required_field_2": null, "nested_field": {"nested_required_1": 456}}',
            {"required_field_1": 123, "required_field_2": None, "nested_field": {"nested_required_1": 456}},
        ),
        # Case: Empty input (JSON string) - no fields added as none are explicitly required in their own schema
        ("Empty input (JSON string)", "{}", {}),
        # Case: Fields set to null (JSON string input) - nulls are preserved, no missing fields added
        (
            "Fields set to null (JSON string)",
            '{"required_field_1": null, "nested_field": {"nested_required_1": null}}',
            {"required_field_1": None, "nested_field": {"nested_required_1": None}},
        ),
        # Case: JSON string with only whitespace - treated as empty object, no fields added
        ("Whitespace only (JSON string)", "   \n  ", {}),
        # Case: JSON string with only comments (should be treated as empty) - Not applicable for JSON
        # Case: Invalid JSON string - should return original string and log error
        ("Invalid JSON string", '{"key": "value"', '{"key": "value"'),  # Expected output is the original invalid string
    ],
)
def test_handle_required_fields(description, input_content, expected_content):
    """
    Tests the handle_required_fields function with various inputs (dict and JSON string).
    """
    # Create data dictionary with schema
    data = {"schema": SCHEMA, "logs": [], "errors": []}  # Ensure errors list is initialized

    # Call the function with the required signature (content, data)
    (processed_content, updated_data) = handle_required_fields(input_content, data)

    # If the input was a string and it was invalid JSON, the function should return the original string.
    # In this case, we don't attempt to parse the output for comparison.
    if isinstance(input_content, str) and expected_content == input_content:
        assert (
            processed_content == expected_content
        ), f"Test: {description} - Output content mismatch for invalid string"
        assert any(
            "WARNING: Error parsing JSON string for required fields:" in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected warning log not found for invalid string"
        assert any(
            "Error parsing JSON string for required fields:" in err for err in updated_data.get("errors", [])
        ), f"Test: {description} - Expected error message for invalid string not found"
    else:
        # If the output is a string (meaning input was a valid string), parse it to a dictionary for comparison
        if isinstance(processed_content, str):
            try:
                processed_content = json.loads(processed_content)
            except json.JSONDecodeError as e:
                pytest.fail(
                    f"Test: {description} - Failed to parse processed JSON string: {e}\nContent: {processed_content}"
                )

        # Assert that the processed content (as a dictionary) matches the expected dictionary
        assert processed_content == expected_content, f"Test: {description} - Processed content mismatch"

    assert "logs" in updated_data, f"Test: {description} - Missing logs"
    # Check for specific log messages based on input type and validity
    if isinstance(input_content, (dict, list)):
        assert any(
            f"Input is a {type(input_content).__name__}, processing directly." in log
            for log in updated_data["logs"]
        ), f"Test: {description} - Expected log for dict/list input not found"
        assert any(
            "Required fields processed and disallowed properties removed based on schema." in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected success log for dict/list input not found"
    elif isinstance(input_content, str) and not input_content.strip():
        assert any(
            "Input string is empty or whitespace-only, treating as empty object." in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected log for empty/whitespace string not found"
        assert any(
            "Required fields processed and disallowed properties removed based on schema." in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected success log for empty/whitespace string not found"
    elif isinstance(input_content, str) and expected_content == input_content:  # Invalid JSON string case
        assert any(
            "WARNING: Error parsing JSON string for required fields:" in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected warning log not found"
        assert any(
            "Error parsing JSON string for required fields:" in err for err in updated_data.get("errors", [])
        ), f"Test: {description} - Expected error message for invalid string not found"
    elif isinstance(input_content, str):  # Valid JSON string case
        assert any(
            "Successfully parsed JSON string." in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected parsing success log not found"
        assert any(
            "Required fields processed and disallowed properties removed based on schema." in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected processing success log not found"
        assert any(
            "Converted processed content back to formatted JSON string." in log for log in updated_data["logs"]
        ), f"Test: {description} - Expected dumping success log not found"
    else:
        # This case should be caught by the ValueError for unsupported types,
        # but as a fallback, ensure no success log is present if it somehow reaches here.
        assert not any(
            "Required fields processed." in log for log in updated_data["logs"]
        ), f"Test: {description} - Unexpected success log for unsupported type"
