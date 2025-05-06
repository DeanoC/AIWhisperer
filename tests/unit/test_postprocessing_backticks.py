import pytest
import os
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper

@pytest.mark.parametrize("input_json, expected_json", [
    # Case: No backticks - no changes needed
    ('{"key": "value"}', '{"key": "value"}'),

    # Case: Simple backtick wrapper
    ('```json\n{"key": "value"}\n```', '{"key": "value"}\n'),

    # Case: Backtick wrapper with language specified
    ('```javascript\n{"key": "value"}\n```', '{"key": "value"}\n'),

    # Case: Multiple backtick wrappers (note: function removes all matching backticks)
    ('```json\n{"key": "```nested```"}\n```', '{"key": "```nested```"}\n'),

    # Case: Empty file
    ("", ""),

    # Case: Only backticks without content
    ("```json\n```", "\n"),

    # Case: Backticks with multiple lines
    ('```json\n{\n  "key1": "value1",\n  "key2": "value2"\n}\n```', '{\n  "key1": "value1",\n  "key2": "value2"\n}\n'),
])
def test_clean_backtick_wrapper(input_json, expected_json):
    """Test that clean_backtick_wrapper correctly removes backtick wrappers."""
    # Initialize result data
    result_data = {
        "success": True,
        "steps": {},
        "logs": []
    }

    # Call the function
    output_json, updated_result = clean_backtick_wrapper(input_json, result_data)

    # Assert that the output matches the expected output, ignoring whitespace
    assert output_json.strip() == expected_json.strip()

    # Assert that the logs were updated
    assert len(updated_result["logs"]) > 0
    assert "Removed all backticks. Cleaned content starts with:" in updated_result["logs"][-1]

def test_clean_backtick_wrapper_with_dictionary_input():
    """Test that clean_backtick_wrapper preserves dictionary input."""
    # Sample dictionary input
    yaml_dict = {"key": "value"}

    # Initialize result data
    result_data = {
        "success": True,
        "steps": {},
        "logs": []
    }

    # Call the function
    output_yaml, updated_result = clean_backtick_wrapper(yaml_dict, result_data)

    # Assert that the output is the same as the input
    assert output_yaml == yaml_dict

    # Assert that the logs were updated
    assert len(updated_result["logs"]) > 0
    assert "Input is a dictionary" in updated_result["logs"][-1]

def test_clean_backtick_wrapper_with_real_world_example():
    """
    Test the clean_backtick_wrapper function with a real-world example
    from temp.txt that was causing JSON parsing issues.

    This test ensures that our function can handle complex JSON with nested structures
    and properly remove the backtick wrappers.
    """
    # Create a test file with content from temp.txt
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_backtick_example.txt')

    # Write a simplified version of temp.txt
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write("""```json
{
  "natural_language_goal": "Enhance the OpenRouter `--list-models` command to include detailed model information and an option to output results to a CSV file.",
  "overall_context": "The task is to improve the existing `--list-models` command in the ai-whisperer tool. The enhancement involves fetching more comprehensive model details from the OpenRouter API and providing an optional `--output-csv` flag to save these details to a CSV file. The console output should remain functional when the CSV option is not used.",
  "plan": [
    {
      "step_id": "planning_cli_and_api_changes",
      "description": "Plan the necessary modifications to the CLI argument parsing and the OpenRouter API interaction logic.",
      "depends_on": [],
      "agent_spec": {
        "type": "planning",
        "input_artifacts": [
          "main.py",
          "ai_whisperer/openrouter_api.py"
        ],
        "output_artifacts": [
          "docs/planning_summary.md"
        ],
        "instructions": "Analyze the existing `main.py` to determine how to add the optional `--output-csv` argument using argparse. Examine `ai_whisperer/openrouter_api.py` to understand the current `list_models` method and how it needs to be modified to fetch detailed model metadata instead of just names."
      }
    }
  ]
}
```""")

    try:
        # Read the test file
        with open(test_file_path, 'r', encoding='utf-8') as f:
            input_json = f.read()

        # Initialize result data
        result_data = {
            "success": True,
            "steps": {},
            "logs": []
        }

        # Process the JSON content
        output_json, updated_result = clean_backtick_wrapper(input_json, result_data)

        # Verify that the function processed the content without errors
        assert "logs" in updated_result
        assert len(updated_result["logs"]) > 0

        # The function should have removed the backtick wrappers
        assert "Removed all backticks." in updated_result["logs"][-1]

        # Check that the backtick wrappers were removed, ignoring whitespace
        assert not output_json.strip().startswith("```")
        assert not output_json.strip().endswith("```")

        # Check that the content is preserved
        assert '"natural_language_goal": "Enhance the OpenRouter' in output_json
        assert '"plan": [' in output_json
        assert '"step_id": "planning_cli_and_api_changes"' in output_json

        # Check that backticks within the content are preserved
        assert "`--list-models`" in output_json
        assert "`--output-csv`" in output_json
        assert "`main.py`" in output_json

    finally:
        # Clean up the test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
