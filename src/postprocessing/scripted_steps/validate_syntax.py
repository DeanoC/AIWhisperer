"""
Validate JSON Syntax Postprocessing Step

This module provides a function to validate the syntax of JSON content.
It checks if the input is well-formed JSON and if the root is an object or array.
"""

import json
from typing import Tuple, Union


def validate_syntax(content: Union[str, dict, list], data: dict = None) -> tuple:
    """
    Validates the JSON content.

    Args:
        content (str | dict | list): The input JSON content as a string, dictionary, or list.
        data (dict): The input parameter dictionary; results and logs are stored here.

    Returns:
        tuple: A tuple containing:
            - processed_content (str | dict | list): The original content if valid.
            - updated_data (dict): The updated data dictionary with processing logs.

    Raises:
        ValueError: If the JSON content is invalid, not an object/array at the root,
                    or if the input string is empty/whitespace.

    Note:
        This function follows the required signature for all scripted processing steps.
    """
    if data is None:
        data = {}
    if "logs" not in data:
        data["logs"] = []
    if "errors" not in data:
        data["errors"] = []

    if isinstance(content, (dict, list)):
        data["logs"].append(f"Input is a {type(content).__name__}, syntax is considered valid.")
        return (content, data)

    if not isinstance(content, str):
        err_msg = f"Unsupported content type: {type(content)}. Expected str, dict, or list."
        data["logs"].append(f"ERROR: {err_msg}")
        data["errors"].append(err_msg)
        raise ValueError(err_msg)

    if not content.strip():
        err_msg = "Empty or whitespace-only content is not valid JSON."
        data["logs"].append(f"ERROR: {err_msg}")
        data["errors"].append(err_msg)
        raise ValueError(err_msg)

    try:
        parsed_json = json.loads(content)
        if not isinstance(parsed_json, (dict, list)):
            err_msg = "JSON root is not an object or array."
            data["logs"].append(f"ERROR: {err_msg} (Actual type: {type(parsed_json).__name__})")
            data["errors"].append(err_msg)
            raise ValueError(err_msg)

        data["logs"].append("JSON syntax validated successfully.")
        # Return the parsed JSON content as a dictionary or list
        return (parsed_json, data)

    except json.JSONDecodeError as e:
        err_msg = f"Invalid JSON syntax: {e}"
        data["logs"].append(f"ERROR: {err_msg}")
        data["errors"].append(err_msg)
        raise ValueError(err_msg) from e
    except Exception as e:  # Catch any other unexpected errors
        err_msg = f"An unexpected error occurred during JSON syntax validation: {e}"
        data["logs"].append(f"ERROR: {err_msg}")
        data["errors"].append(err_msg)
        raise ValueError(err_msg) from e


if __name__ == "__main__":
    # Example Usage (for local testing)
    test_cases = [
        ('{"key": "value"}', "Valid JSON object"),
        ('[1, "two"]', "Valid JSON array"),
        ({"already": "dict"}, "Input is a dictionary"),
        (["already_list"], "Input is a list"),
        ('{"key": "value"', "Invalid JSON: Missing closing brace"),
        ('{"key1": "value1",}', "Invalid JSON: Trailing comma in object"),
        ('"just a string"', "Invalid JSON root: string literal"),
        ("123", "Invalid JSON root: number literal"),
        ("", "Empty string"),
        ("   ", "Whitespace-only string"),
        ('{"name": "テスト"}', "Valid JSON with unicode"),
    ]

    for i, (test_content, desc) in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {desc} ---")
        current_data = {"logs": [], "errors": []}
        try:
            (output_content, output_data) = validate_syntax(test_content, current_data)
            print("Status: Valid")
            print("Output Content:", output_content)
        except ValueError as ve:
            print(f"Status: Invalid (ValueError: {ve})")
        finally:
            print("Logs:", json.dumps(output_data.get("logs", []), indent=2))
            if output_data.get("errors"):
                print("Errors:", json.dumps(output_data.get("errors", []), indent=2))
    print("\nAll validate_syntax examples executed.")
