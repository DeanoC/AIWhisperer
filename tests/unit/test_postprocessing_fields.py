import pytest
import yaml
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields

# Mock schema for testing
SCHEMA = {
    "required_field_1": "default_value_1",
    "required_field_2": "default_value_2",
    "nested_field": {
        "nested_required_1": "nested_default_1"
    }
}

@pytest.mark.parametrize("input_yaml, expected_yaml", [
    # Case: All required fields present
    (
        {"required_field_1": "value1", "required_field_2": "value2", "nested_field": {"nested_required_1": "value3"}},
        {"required_field_1": "value1", "required_field_2": "value2", "nested_field": {"nested_required_1": "value3"}}
    ),
    # Case: Missing required fields
    (
        {"required_field_1": "value1"},
        {"required_field_1": "value1", "required_field_2": "default_value_2", "nested_field": {"nested_required_1": "nested_default_1"}}
    ),
    # Case: Extra invalid fields
    (
        {"required_field_1": "value1", "extra_field": "invalid"},
        {"required_field_1": "value1", "required_field_2": "default_value_2", "nested_field": {"nested_required_1": "nested_default_1"}}
    ),
    # Case: Incorrect data types
    (
        {"required_field_1": 123, "required_field_2": None},
        {"required_field_1": "default_value_1", "required_field_2": "default_value_2", "nested_field": {"nested_required_1": "nested_default_1"}}
    ),
    # Case: Empty YAML
    (
        {},
        {"required_field_1": "default_value_1", "required_field_2": "default_value_2", "nested_field": {"nested_required_1": "nested_default_1"}}
    ),
    # Case: Fields set to null
    (
        {"required_field_1": None},
        {"required_field_1": "default_value_1", "required_field_2": "default_value_2", "nested_field": {"nested_required_1": "nested_default_1"}}
    ),
])
def test_handle_required_fields(input_yaml, expected_yaml):
    # Create data dictionary with schema
    data = {"schema": SCHEMA, "logs": []}

    # Call the function with the required signature (yaml_content, data)
    processed_yaml, updated_data = handle_required_fields(input_yaml, data)

    # Parse the YAML string back to a dictionary for comparison
    if isinstance(processed_yaml, str):
        processed_yaml = yaml.safe_load(processed_yaml)

    # Assert that the processed YAML matches the expected YAML
    assert processed_yaml == expected_yaml
