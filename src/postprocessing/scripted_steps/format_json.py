"""
Format JSON Postprocessing Step

This module provides a function to format and standardize JSON output.
It parses the JSON content and re-serializes it with consistent formatting.
"""

import json
from typing import Tuple

def format_json(content: str | dict, data: dict) -> tuple:
    """
    Formats the JSON content for consistency.

    Args:
        content (str | dict): The input JSON content as a string or dictionary.
        data (dict): The input parameter dictionary; results and logs are stored here.

    Returns:
        tuple: A tuple containing:
            - processed_content (str | dict): The formatted JSON content.
              If input is a string, output is a formatted string.
              If input is a dict, output is the same dict (already parsed).
            - updated_data (dict): The updated data dictionary with processing logs.

    Note:
        This function follows the required signature for all scripted processing steps:
        - Takes (content, data) as input
        - Returns a tuple of (processed_content, updated_data)
        - The parameter and return types are fixed and cannot be changed:
          * content: str | dict
          * data: dict
          * return: tuple[str | dict, dict]
        - Preserves the input format (str or dict) in the output where appropriate.
          If input is a string, it's formatted. If a dict, it's assumed to be
          already correctly parsed and structured.
    """
    if "logs" not in data:
        data["logs"] = []

    original_type_was_str = isinstance(content, str)

    try:
        if original_type_was_str:
            # If content is a string, parse it
            parsed_json = json.loads(content)
            # Re-serialize with standard formatting
            processed_content = json.dumps(parsed_json, indent=4, ensure_ascii=False)
            data["logs"].append("Successfully parsed and formatted JSON string.")
        elif isinstance(content, dict):
            # If content is already a dictionary, assume it's valid and structured.
            processed_content = content
            data["logs"].append("Input is a dictionary, no formatting applied. Assumed to be valid.")
        else:
            # This case should ideally not be reached if type hints are respected.
            processed_content = content # Return original content
            error_message = f"Unsupported content type: {type(content)}. Expected str or dict."
            data["logs"].append(f"ERROR: {error_message}")
            if "errors" not in data:
                data["errors"] = []
            data["errors"].append(error_message)

    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON syntax: {e}"
        data["logs"].append(f"ERROR: {error_message}")
        if "errors" not in data:
            data["errors"] = []
        data["errors"].append(error_message)
        # Return original content if parsing fails and it was a string
        processed_content = content
    except Exception as e:
        error_message = f"An unexpected error occurred during JSON formatting: {e}"
        data["logs"].append(f"ERROR: {error_message}")
        if "errors" not in data:
            data["errors"] = []
        data["errors"].append(error_message)
        processed_content = content # Return original content

    return processed_content, data

if __name__ == '__main__':
    # Example Usage - This part is for local testing and won't be run by unittest
    test_data_str_valid = '{"name": "Test", "items": [1, 2, 3], "details": {"type": "example"}}'
    test_data_dict = {"name": "TestDict", "items": [4,5,6]}
    test_data_str_invalid = '{"name": "Test", "items": [1, 2, 3], "details": {"type": "example"}' # Missing closing brace
    test_data_str_ugly = '{\n"name":"TestUgly",\n  "items" : [ 1,2,3 ]\n}'

    print("--- Test Case 1: Valid JSON String ---")
    output_content, output_data = format_json(test_data_str_valid, {"logs": []})
    print("Formatted Content:\n", output_content)
    print("Logs:\n", json.dumps(output_data["logs"], indent=2))
    assert isinstance(output_content, str)
    assert json.loads(output_content)["name"] == "Test"

    print("\n--- Test Case 2: Dictionary Input ---")
    output_content_dict, output_data_dict = format_json(test_data_dict, {"logs": []})
    print("Formatted Content (dict input):\n", output_content_dict)
    print("Logs (dict input):\n", json.dumps(output_data_dict["logs"], indent=2))
    assert isinstance(output_content_dict, dict)
    assert output_content_dict["name"] == "TestDict"

    print("\n--- Test Case 3: Invalid JSON String ---")
    output_content_invalid, output_data_invalid = format_json(test_data_str_invalid, {"logs": []})
    print("Formatted Content (invalid input):\n", output_content_invalid)
    print("Logs (invalid input):\n", json.dumps(output_data_invalid["logs"], indent=2))
    assert "errors" in output_data_invalid
    assert output_content_invalid == test_data_str_invalid

    print("\n--- Test Case 4: Ugly JSON String ---")
    output_content_ugly, output_data_ugly = format_json(test_data_str_ugly, {"logs": []})
    print("Formatted Content (ugly input):\n", output_content_ugly)
    print("Logs (ugly input):\n", json.dumps(output_data_ugly["logs"], indent=2))
    assert isinstance(output_content_ugly, str)
    expected_ugly_formatted = """{
    "name": "TestUgly",
    "items": [
        1,
        2,
        3
    ]
}"""
    # Note: The example in the original prompt had a slightly different expected output
    # for the ugly string. This ensures it matches the test case.
    # The test case `test_format_valid_json_string` uses a more complex ugly string.
    # This example is simpler.
    # For the specific ugly string here: '{\n"name":"TestUgly",\n  "items" : [ 1,2,3 ]\n}'
    # The output will be:
    # {
    #     "name": "TestUgly",
    #     "items": [
    #         1,
    #         2,
    #         3
    #     ]
    # }
    assert output_content_ugly == json.dumps(json.loads(test_data_str_ugly), indent=4, ensure_ascii=False)
    print("All format_json examples executed.")