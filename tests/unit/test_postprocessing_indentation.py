import pytest
from src.postprocessing.scripted_steps.normalize_indentation import normalize_indentation

@pytest.mark.parametrize("input_yaml, expected_yaml", [
    # Correctly indented YAML
    ("key:\n  subkey: value\n", "key:\n  subkey: value\n"),
    # Inconsistent indentation (mixed spaces and tabs)
    ("key:\n\t  subkey: value\n", "key:\n  subkey: value\n"),
    # Excessive indentation
    ("key:\n        subkey: value\n", "key:\n  subkey: value\n"),
    # Insufficient indentation
    ("key:\n subkey: value\n", "key:\n  subkey: value\n"),
    # Edge case: Empty file
    ("", ""),
    # Edge case: File with only comments
    ("# This is a comment\n", "# This is a comment\n"),
])
def test_normalize_indentation(input_yaml, expected_yaml):
    assert normalize_indentation(input_yaml) == expected_yaml
