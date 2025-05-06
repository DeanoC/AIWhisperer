import pytest
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
