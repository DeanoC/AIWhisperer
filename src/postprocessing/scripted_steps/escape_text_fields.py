"""
Escape Text Fields for JSON Postprocessing (Simplified)

This module provides a function to primarily validate if string input is parsable JSON.
For JSON, actual string escaping is handled by json.dumps during serialization.
This step ensures that if string content is provided, it's valid JSON,
otherwise, it passes through dictionaries and lists.
"""

import json
from typing import Union, Tuple, Dict
import logging

logger = logging.getLogger(__name__)

def escape_text_fields(content: Union[str, dict, list], data: dict = None) -> Tuple[Union[str, dict, list], Dict]:
    """
    For string input, checks if it's valid JSON. For dict/list, passes through.
    Actual JSON string escaping is handled by json.dumps().

    Args:
        content (str | dict | list): The input content.
        data (dict): The input parameter dictionary; results and logs are stored here.

    Returns:
        tuple: A tuple containing:
            - processed_content (str | dict | list): The original content.
            - updated_data (dict): The updated data dictionary with processing logs.
    """
    if data is None:
        data = {}
    if "logs" not in data:
        data["logs"] = []
    if "errors" not in data: # Ensure errors list exists
        data["errors"] = []

    logger.debug(f"escape_text_fields input type: {type(content)}")

    if isinstance(content, (dict, list)):
        data["logs"].append(f"Input is a {type(content).__name__}, no escaping performed by this step.")
        return content, data

    if not isinstance(content, str):
        err_msg = f"Unsupported content type: {type(content)}. Expected str, dict, or list."
        logger.error(err_msg)
        data["logs"].append(f"ERROR: {err_msg}")
        data["errors"].append(err_msg)
        # Return original content as per current test expectations for unsupported types
        return content, data

    if not content.strip():
        data["logs"].append("Input content is empty or whitespace-only.")
        return content, data

    try:
        # Attempt to parse the string to see if it's valid JSON
        json.loads(content)
        data["logs"].append("Input is a valid JSON string. No escaping applied by this step.")
    except json.JSONDecodeError as e:
        err_msg = f"Failed to parse content as JSON in escape_text_fields: {e}"
        logger.warning(f"{err_msg} - Content: '{content[:100]}...'") # Log part of content for context
        data["logs"].append(f"WARNING: {err_msg}") # Log as warning, not breaking error
        data["errors"].append(err_msg) # Also add to errors for testability
        # Return original content; subsequent validation step should catch this.
    
    return content, data

if __name__ == '__main__':
    # Example Usage
    test_cases = [
        ('{"key": "value", "text": "This is a string: with a colon."}', "Valid JSON string"),
        ('[1, "string with spaces", {"nested": "value: more text"}]', "Valid JSON array string"),
        ({"key": "value", "text": "A string: with colon"}, "Input is dictionary"),
        ([1, "string with colon:", {"nested": "value"}], "Input is list"),
        ('{"key": "value, "text": "missing end quote}', "Invalid JSON string (missing quote)"),
        ('{"key": "value",}', "Invalid JSON string (trailing comma)"),
        ("", "Empty string"),
        ("   \n\t  ", "Whitespace string"),
        ('"a string literal"', "JSON string literal"),
        (12345, "Unsupported type (int)"),
    ]

    for i, (test_content, desc) in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {desc} ---")
        current_data = {"logs": [], "errors": []}
        output_content, output_data = escape_text_fields(test_content, current_data)
        
        print("Output Content:", output_content)
        print("Logs:", json.dumps(output_data.get("logs", []), indent=2))
        if output_data.get("errors"):
            print("Errors:", json.dumps(output_data.get("errors", []), indent=2))
        if isinstance(output_content, str) and output_content.strip() and not output_data.get("errors"):
            try:
                print("Parsed output (if string):", json.loads(output_content))
            except:
                print("Could not parse output string as JSON.")

    print("\nAll escape_text_fields examples executed.")
