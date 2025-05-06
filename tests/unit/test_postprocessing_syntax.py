import pytest
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax

@pytest.mark.parametrize("input_yaml, expected_yaml, should_raise", [
    # Case: Valid YAML
    ("key: value\n", "key: value\n", False),
    # Case: Missing colon
    ("key value\n", None, True),
    # Case: Incorrect indentation
    ("key:\n    subkey: value\n", "key:\n  subkey: value\n", False),
    # Case: Invalid characters
    ("key: value\nkey2: @invalid\n", None, True),
    # Case: Empty file
    ("", "", False),
    # Case: File with only comments
    ("# This is a comment\n", "# This is a comment\n", False),
    # Case: Mixed valid and invalid YAML
    ("key: value\nkey2 value\n", None, True),
])
def test_validate_syntax(input_yaml, expected_yaml, should_raise):
    if should_raise:
        with pytest.raises(ValueError):
            validate_syntax(input_yaml)
    else:
        output_yaml, result = validate_syntax(input_yaml)
        assert output_yaml == expected_yaml
        assert "logs" in result
        assert len(result["logs"]) > 0
