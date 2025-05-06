import pytest
import os
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields

@pytest.mark.parametrize("input_yaml, expected_yaml, expected_changes", [
    # Case: Valid YAML - no changes needed
    ("key: value\n", "key: value\n", 0),

    # Case: Missing colon in a line that looks like natural language
    ("key: value\nmodel information and an optional CSV output parameter.\n",
     "key: value\n\"model information and an optional CSV output parameter.\"\n", 1),

    # Case: Multiple lines with missing colons
    ("key: value\nThis is a line without a colon\nAnother problematic line here\nkey2: value2\n",
     "key: value\n\"This is a line without a colon\"\n\"Another problematic line here\"\nkey2: value2\n", 2),

    # Case: Line with special YAML characters
    ("key: value\nThis has a colon: but no proper YAML format\n",
     "key: value\n\"This has a colon: but no proper YAML format\"\n", 1),

    # Case: Indented line that should be part of a multiline field
    ("key:\n  subkey: value\n  this line is indented but has no colon\n",
     "key:\n  subkey: value\n  \"this line is indented but has no colon\"\n", 1),

    # Case: Already properly quoted string
    ('key: "This is already quoted"\n', 'key: "This is already quoted"\n', 0),

    # Case: Empty file
    ("", "", 0),

    # Case: Only comments
    ("# This is a comment\n", "# This is a comment\n", 0),
])
def test_escape_text_fields(input_yaml, expected_yaml, expected_changes):
    output_yaml, result = escape_text_fields(input_yaml)

    assert output_yaml == expected_yaml
    assert "logs" in result
    assert len(result["logs"]) > 0

    # Check if the log correctly reflects the number of changes made
    if expected_changes > 0:
        assert f"Escaped {expected_changes}" in result["logs"][-1]
    else:
        assert "No text fields requiring" in result["logs"][-1] or "Input is a dictionary" in result["logs"][-1]

def test_escape_text_fields_with_dictionary_input():
    yaml_dict = {"key": "value"}
    output, result = escape_text_fields(yaml_dict)

    assert output == yaml_dict
    assert "Input is a dictionary" in result["logs"][-1]

def test_escape_text_fields_with_existing_quotes():
    input_yaml = 'key: value\nText with "quotes" that needs escaping\n'
    expected_yaml = 'key: value\n"Text with \\"quotes\\" that needs escaping"\n'

    output_yaml, result = escape_text_fields(input_yaml)
    assert output_yaml == expected_yaml
    assert "Escaped 1" in result["logs"][-1]

def test_escape_text_fields_with_real_world_example():
    """
    Test the escape_text_fields function with a real-world example
    that was causing YAML parsing issues.

    This test ensures that our function can handle complex YAML with nested structures,
    backticks, and natural language text that might contain colons.
    """
    # Create a test file with problematic lines
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_yaml_example.txt')

    # Write a simplified version with just the problematic parts
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write("""
natural_language_goal: Enhance the `--list-models` command to provide detailed model information and an option to export it to a CSV file.
description: Analyze requirements and outline the necessary changes in `main.py` and the OpenRouter API integration to support detailed model listing and CSV export.
instructions: Outline the specific modifications needed in `main.py` to handle the new `--output-csv` argument and integrate with the enhanced API call.
Detail the structure of the data expected from the API and how it should be formatted for both console output and CSV export.
Identify potential utility functions needed for data formatting or CSV writing.
Document the plan in `docs/list_models_enhancement_plan.md`.
""")

    try:
        # Read the test file
        with open(test_file_path, 'r', encoding='utf-8') as f:
            input_yaml = f.read()

        # Process the YAML content
        output_yaml, result = escape_text_fields(input_yaml)

        # Verify that the function processed the content without errors
        assert "logs" in result
        assert len(result["logs"]) > 0

        # The function should have made changes to properly escape text fields
        assert "Escaped" in result["logs"][-1]

        # Check that specific problematic lines were properly escaped
        assert '`--list-models`' in output_yaml
        assert '`main.py`' in output_yaml

        # Check that lines with natural language and colons are properly quoted
        assert '"Detail the structure of the data expected from the API' in output_yaml
        assert '"Identify potential utility functions needed for data formatting' in output_yaml
        assert '"Document the plan in' in output_yaml

    finally:
        # Clean up the test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
