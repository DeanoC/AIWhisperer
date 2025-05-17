"""
Handle Required Fields Postprocessing Step

This module provides a function to ensure required fields are present with default values
and optionally remove invalid fields based on a provided schema.
This version is compatible with JSON data.
"""

import json
import logging
from typing import Union, Tuple, Dict

logger = logging.getLogger(__name__)


def handle_required_fields(content: Union[str, dict, list], data: dict = None) -> Tuple[Union[str, dict, list], Dict]:
    """
    Ensure required fields are present with default values based on a schema.

    Args:
        content (str | dict | list): The input content as a string, dictionary, or list.
        data (dict): The input parameter dictionary; results and logs are stored here.
                     Must contain a 'schema' key with the expected structure and defaults.

    Returns:
        tuple: A tuple containing:
            - processed_content (str | dict | list): The content with required fields handled.
              If input was a valid string, output is a formatted JSON string.
              If input was a dict/list, output is the processed dict/list.
              If input was an invalid string, output is the original string.
            - updated_data (dict): The updated data dictionary with processing logs.

    Raises:
        ValueError: If the input type is unsupported or if the 'schema' is missing from data.
    """
    if data is None:
        data = {}
    if "logs" not in data:
        data["logs"] = []
    if "errors" not in data:
        data["errors"] = []

    schema = data.get("schema")
    if schema is None:
        err_msg = "Schema is missing from the 'data' dictionary."
        logger.error(err_msg)
        data["logs"].append(f"ERROR: {err_msg}")
        data["errors"].append(err_msg)
        raise ValueError(err_msg)

    parsed_content = None
    original_type_was_str = isinstance(content, str)

    if original_type_was_str:
        if not content.strip():
            # Treat empty/whitespace string as an empty object for processing
            parsed_content = {}
            data["logs"].append("Input string is empty or whitespace-only, treating as empty object.")
        else:
            try:
                parsed_content = json.loads(content)
                data["logs"].append("Successfully parsed JSON string.")
            except json.JSONDecodeError as e:
                err_msg = f"Error parsing JSON string for required fields: {e}"
                logger.warning(f"{err_msg} - Content: '{content[:100]}...'")
                data["logs"].append(f"WARNING: {err_msg}")
                data["errors"].append(err_msg)
                # If parsing fails, return original content and log error
                return (content, data)
            except Exception as e:
                err_msg = f"An unexpected error occurred during JSON parsing: {e}"
                logger.error(err_msg)
                data["logs"].append(f"ERROR: {err_msg}")
                data["errors"].append(err_msg)
                # Return original content and log error
                return (content, data)
    elif isinstance(content, (dict, list)):
        parsed_content = content
        data["logs"].append(f"Input is a {type(content).__name__}, processing directly.")
    else:
        err_msg = f"Unsupported content type: {type(content)}. Expected str, dict, or list."
        logger.error(err_msg)
        data["logs"].append(f"ERROR: {err_msg}")
        data["errors"].append(err_msg)
        raise ValueError(err_msg)

    # Ensure parsed_content is a dictionary for field processing, if schema is for a dict
    if isinstance(schema, dict) and not isinstance(parsed_content, dict):
        # If schema is a dict but parsed content is not (e.g., a list or scalar from JSON string),
        # we cannot apply a dictionary schema directly. This might indicate an issue
        # with the input structure relative to the expected schema.
        # For now, we'll log a warning and return the parsed content as is.
        # A later validation step against the full schema should catch this.
        warn_msg = f"Schema is for a dictionary, but parsed content is {type(parsed_content).__name__}. Skipping field processing."
        logger.warning(warn_msg)
        data["logs"].append(f"WARNING: {warn_msg}")
        # Return the parsed content (which might be a list or scalar)
        processed_content = parsed_content
    elif isinstance(schema, dict):
        # Process fields based on the schema
        def process_fields(content_part, schema_part):
            # Start with a copy of the content part if it's a dictionary, otherwise an empty dict
            result = content_part.copy() if isinstance(content_part, dict) else {}

            # Iterate through the schema to add missing required fields
            for key, schema_value in schema_part.items():
                if isinstance(schema_value, dict):
                    # For objects, check if they have properties and required fields
                    if "type" in schema_value and schema_value["type"] == "object":
                        # Handle nested object properties
                        props = schema_value.get("properties", {})
                        if key in result and isinstance(result[key], dict):
                            result[key] = process_fields(result[key], props)
                        else:
                            # Only create missing object if it's required
                            if key in schema_value.get("required", []):
                                result[key] = process_fields({}, props)
                    elif "properties" in schema_value:
                        # Direct object schema
                        if key in result and isinstance(result[key], dict):
                            result[key] = process_fields(result[key], schema_value["properties"])
                        else:
                            # Only create missing object if it's required
                            if key in schema_part.get("required", []):
                                result[key] = process_fields({}, schema_value["properties"])
                else:
                    # For non-objects, only add if missing and required
                    if key not in result and key in schema_part.get("required", []):
                        # Use default value if specified, otherwise null
                        default_value = (
                            schema_value.get("default")
                            if isinstance(schema_value, dict) and "default" in schema_value
                            else None
                        )
                        result[key] = default_value

            # After ensuring required fields are present, remove extra fields if additionalProperties is false
            if schema_part.get("additionalProperties", True) is False:
                allowed_properties = set(schema_part.get("properties", {}).keys())
                keys_to_remove = [key for key in result if key not in allowed_properties]
                for key in keys_to_remove:
                    del result[key]
                    logger.debug(f"Removed disallowed property: {key}")
                    data["logs"].append(f"Removed disallowed property: {key}")

            return result

        processed_content = process_fields(parsed_content, schema)
        data["logs"].append("Required fields processed and disallowed properties removed based on schema.")
    else:
        # If schema is not a dictionary (e.g., schema for a list or scalar),
        # this step doesn't apply in the same way. Return parsed content as is.
        warn_msg = f"Schema is not a dictionary (type: {type(schema).__name__}). Skipping field processing."
        logger.warning(warn_msg)
        data["logs"].append(f"WARNING: {warn_msg}")
        processed_content = parsed_content

    # Return the same type as the original input if possible
    if original_type_was_str and isinstance(processed_content, (dict, list)):
        # If input was a valid string and processing resulted in a dict/list,
        # convert back to a formatted JSON string.
        try:
            output_string = json.dumps(processed_content, indent=4, ensure_ascii=False)
            data["logs"].append("Converted processed content back to formatted JSON string.")
            return (output_string, data)
        except Exception as e:
            err_msg = f"Error dumping processed content to JSON string: {e}"
            logger.error(err_msg)
            data["logs"].append(f"ERROR: {err_msg}")
            data["errors"].append(err_msg)
            # If dumping fails, return the processed content as is (dict/list)
            return (processed_content, data)
    else:
        # Otherwise, return the processed content as is (dict, list, or original invalid string)
        return (processed_content, data)


if __name__ == "__main__":
    # Example Usage (for local testing)
    SCHEMA_EXAMPLE = {
        "type": "object",  # Added type for better schema representation
        "properties": {
            "name": {"type": "string", "default": "Untitled"},
            "version": {"type": "number", "default": 1},
            "details": {
                "type": "object",
                "properties": {
                    "author": {"type": "string", "default": "Unknown"},
                    "date": {
                        "type": ["string", "null"]
                    },  # Example of a field that might be None and we don't set a default
                },
                "required": ["author"],  # Make author required in details
                "additionalProperties": False,  # Disallow extra properties in details
            },
            "items": {"type": "array", "default": []},  # Example of a required list
        },
        "required": ["name", "version", "details", "items"],  # Make top-level fields required
        "additionalProperties": False,  # Disallow extra properties at the top level
    }

    test_cases = [
        ('{"name": "My Plan", "details": {"author": "Roo"}}', "Valid JSON string, missing fields"),
        ("{}", "Empty JSON string"),
        ("   ", "Whitespace only JSON string"),
        ({"name": "My Plan Dict", "items": [1, 2]}, "Dictionary input, missing fields"),
        ([], "List input (schema is for dict)"),  # This case should log a warning
        ('{"name": "My Plan", "details": null}', "JSON string with null nested field"),
        ('{"name": "My Plan", "extra": "field"}', "JSON string with extra field"),  # Should remove 'extra'
        (
            '{"name": "My Plan", "version": "invalid_type"}',
            "JSON string with incorrect type (should preserve)",
        ),  # Should preserve type, validation happens later
        ('{"name": "My Plan", "details": {"author": "Roo", "date": "today"}}', "Valid JSON string, all fields present"),
        ('{"name": "My Plan", "details": {"author": "Roo", "date": null}}', "Valid JSON string, nested field is null"),
        (
            '{"name": "My Plan", "details": {"author": "Roo", "extra_detail": "value"}}',
            "JSON string with extra nested field",
        ),  # Should remove 'extra_detail'
        ('{"key": "value"', "Invalid JSON string"),  # Should return original string
    ]

    for i, (test_content, desc) in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {desc} ---")
        current_data = {"schema": SCHEMA_EXAMPLE, "logs": [], "errors": []}
        try:
            (output_content, output_data) = handle_required_fields(test_content, current_data)
            print("Output Content:", output_content)
        except ValueError as ve:
            print(f"Status: Error (ValueError: {ve})")
        finally:
            print("Logs:", json.dumps(output_data.get("logs", []), indent=2))
            if output_data.get("errors"):
                print("Errors:", json.dumps(output_data.get("errors", []), indent=2))
            # For string outputs, try parsing to show the structure
            if isinstance(output_content, str) and output_content.strip() and not output_data.get("errors"):
                try:
                    print("Parsed Output:", json.loads(output_content))
                except:
                    print("Could not parse output string as JSON.")

    print("\nAll handle_required_fields examples executed.")
