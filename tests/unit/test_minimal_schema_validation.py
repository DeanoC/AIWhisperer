from jsonschema import validate, ValidationError
import pytest

def test_minimal_required_field():
    # Define a minimal schema with a required field
    schema = {
        "type": "object",
        "properties": {
            "required_field": {"type": "string"}
        },
        "required": ["required_field"]
    }

    # Define invalid data missing the required field
    invalid_data = {}

    # Validate and expect a ValidationError
    with pytest.raises(ValidationError) as excinfo:
        validate(instance=invalid_data, schema=schema)

    # Assert the error message contains the missing field
    assert "'required_field' is a required property" in str(excinfo.value)
