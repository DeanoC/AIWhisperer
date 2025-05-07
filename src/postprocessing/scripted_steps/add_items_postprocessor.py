"""
Postprocessing step to add arbitrary items to AI-generated JSON output.

This module provides a function that can be used as a scripted step in the
PostprocessingPipeline to add specified items to JSON content at designated positions.
"""

import json
import logging
from typing import Dict, Any, Tuple, List, Optional, Union

logger = logging.getLogger(__name__)

def add_items_postprocessor(content: Union[str, dict, list], data: dict) -> Tuple[Union[str, dict, list], Dict]:
    logger.debug(f"add_items_postprocessor input - content type: {type(content).__name__}, data keys: {data.keys()}")
    logger.debug(f"add_items_postprocessor input - items_to_add: {data.get('items_to_add')}")
    """
    Adds specified items to the JSON content at designated positions.

    Args:
        content (str | dict | list): The input content as a string, dictionary, or list.
        data (dict): The input parameter dictionary and where results are also stored.
                     Must contain an 'items_to_add' key with 'top_level' and/or
                     'step_level' dictionaries, and optionally 'step_container'.

    Returns:
        tuple: A tuple containing:
            - processed_content (str | dict | list): The content with items added.
              If input was a valid string, output is a formatted JSON string.
              If input was a dict/list, output is the modified dict/list.
              If input was an invalid string, output is the original string.
            - updated_data (dict): The updated data dictionary with processing logs,
                                   changes, errors, and warnings.

    Raises:
        ValueError: If the input type is unsupported.
    """
    # Initialize step result in the data dictionary
    if "steps" not in data:
        data["steps"] = {}

    step_result = {
        "success": True,
        "changes": [],
        "errors": [],
        "warnings": [],
        "logs": []
    }
    data["steps"]["add_items_postprocessor"] = step_result # Initialize step result

    items_to_add = data.get("items_to_add")
    if not items_to_add:
        step_result["logs"].append("No items to add specified")
        return content, data

    parsed_content = None
    original_type_was_str = isinstance(content, str)

    if original_type_was_str:
        if not content.strip():
            # Treat empty/whitespace string as an empty object for processing
            parsed_content = {}
            step_result["logs"].append("Input string is empty or whitespace-only, treating as empty object.")
            step_result["warnings"].append("Using empty dictionary due to empty input string")
        else:
            logger.debug(f"Attempting to parse content as JSON. Content start: '{content[:100]}...'")
            try:
                parsed_content = json.loads(content)
                step_result["logs"].append("Successfully parsed content as JSON.")
                logger.debug("Successfully parsed content as JSON.")
            except json.JSONDecodeError as e:
                err_msg = f"Failed to parse content as JSON in add_items_postprocessor: {e}"
                logger.warning(f"{err_msg} - Content: '{content[:100]}...'")
                step_result["logs"].append(f"WARNING: {err_msg}")
                step_result["errors"].append(err_msg)
                step_result["success"] = False
                # Return original content if parsing fails
                logger.debug(f"add_items_postprocessor returning original content due to JSONDecodeError. Data keys: {data.keys()}")
                return content, data
            except Exception as e:
                err_msg = f"An unexpected error occurred during JSON parsing: {e}"
                logger.debug(f"add_items_postprocessor returning original content due to unexpected error. Data keys: {data.keys()}")
                logger.error(err_msg)
                step_result["logs"].append(f"ERROR: {err_msg}")
                step_result["errors"].append(err_msg)
                step_result["success"] = False
                # Return original content if parsing fails
                return content, data
    elif isinstance(content, (dict, list)):
        parsed_content = content
        logger.debug(f"add_items_postprocessor input is dict/list. Data keys: {data.keys()}")
        input_type = type(content).__name__.lower()
        step_result["logs"].append(f"Input is a {input_type}, processing directly.")
        logger.debug(f"Input is a {input_type}, processing directly.")
    else:
        err_msg = f"Unsupported content type: {type(content)}. Expected str, dict, or list."
        logger.error(err_msg)
        step_result["logs"].append(f"ERROR: {err_msg}")
        step_result["errors"].append(err_msg)
        step_result["success"] = False
        raise ValueError(err_msg) # Raise for unsupported types
    
    logger.debug(f"add_items_postprocessor - parsed_content type: {type(parsed_content).__name__}")

    # Ensure parsed_content is mutable if it was a string that parsed successfully
    # and is a dict or list. Scalars from JSON strings are immutable.
    if original_type_was_str and isinstance(parsed_content, (dict, list)):
         logger.debug("Input was string, deep copying parsed content to ensure mutability.")
         parsed_content = json.loads(json.dumps(parsed_content)) # Deep copy to ensure mutability

    # Add top-level items
    top_level_items = items_to_add.get("top_level", {})
    if isinstance(parsed_content, dict) and top_level_items:
        for key, value in top_level_items.items():
            # Always add/overwrite top-level items from items_to_add
            parsed_content[key] = value
            step_result["changes"].append(f"Added/Overwrote top-level item: {key}")
    elif top_level_items:
         step_result["warnings"].append(f"Top-level items specified, but content is not a dictionary (type: {type(parsed_content).__name__})")


    # Add step-level items
    step_level_items = items_to_add.get("step_level", {})
    if step_level_items:
        step_container_key_from_items = items_to_add.get("step_container")
        if step_container_key_from_items is not None:
            step_container_key = step_container_key_from_items
        else:
            step_container_key = data.get("step_container", "plan")

        def find_and_add_to_steps(obj, container_key, items_to_add_dict):
            logger.debug(f"Searching for step container '{container_key}' in object of type {type(obj).__name__}")
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == container_key:
                        logger.debug(f"Found potential step container key: '{key}'")
                        if isinstance(value, list):
                            # Found the step container list
                            for item in value:
                                if isinstance(item, dict):
                                    for item_key, item_value in items_to_add_dict.items():
                                        if item_key in item:
                                            step_result["warnings"].append(f"Key '{item_key}' already exists in a step, not overwriting")
                                        else:
                                            item[item_key] = item_value
                                            step_result["changes"].append(f"Added step-level item: {item_key}")
                                            logger.debug(f"Added step-level item '{item_key}' to a step.")
                                else:
                                    warn_msg = f"Skipping non-dictionary item in step container list: {item}"
                                    logger.warning(warn_msg)
                                    step_result["warnings"].append(warn_msg)
                        else:
                            # Key matches container_key, but it's not a list
                            step_result["warnings"].append(f"Found key '{container_key}' but it is not a list (type: {type(value).__name__}), cannot add step-level items here.")
                    elif isinstance(value, (dict, list)):
                        # Recursively search in nested dictionaries or lists
                        obj[key] = find_and_add_to_steps(value, container_key, items_to_add_dict)
            elif isinstance(obj, list):
                # Recursively search in items within the list
                for i, item in enumerate(obj):
                    obj[i] = find_and_add_to_steps(item, container_key, items_to_add_dict)
            return obj # Return the modified object

        initial_changes_count = len(step_result["changes"])
        parsed_content = find_and_add_to_steps(parsed_content, step_container_key, step_level_items)
        # Check if any changes were made specifically by step-level additions.
        # The warning for "not found or not a list" should only appear if no step-level items were added *at all*.
        # If warnings about "not a list" were already added, we don't need the generic one.
        
        # Count how many step-level items were actually added
        step_level_changes_count = sum(1 for change in step_result["changes"][initial_changes_count:] if "step-level item" in change)

        if step_level_changes_count == 0:
            # Check if there were any warnings about the container key being found but not being a list
            container_key_found_but_not_list = any(f"Found key '{step_container_key}' but it is not a list" in warning for warning in step_result["warnings"])
            if not container_key_found_but_not_list:
                 step_result["warnings"].append(f"Step container '{step_container_key}' not found or not a list of dictionaries.")


    # Determine the final output format
    if original_type_was_str and isinstance(parsed_content, (dict, list)) and step_result["success"]:
        # If input was a valid string and processing was successful,
        # convert the processed content back to a formatted JSON string.
        try:
            output_string = json.dumps(parsed_content, indent=4, ensure_ascii=False)
            step_result["logs"].append("Converted processed content back to formatted JSON string.")
            logger.debug(f"add_items_postprocessor returning formatted JSON string. Data keys: {data.keys()}")
            return output_string, data
        except Exception as e:
            err_msg = f"Error dumping processed content to JSON string: {e}"
            logger.error(err_msg)
            step_result["logs"].append(f"ERROR: {err_msg}")
            step_result["errors"].append(err_msg)
            step_result["success"] = False
            # If dumping fails, return the processed content as is (dict/list)
            logger.debug(f"add_items_postprocessor returning processed content (dict/list) due to dump error. Data keys: {data.keys()}")
            return parsed_content, data
    else:
        # Otherwise, return the processed content as is (dict, list, or original invalid string)
        logger.debug(f"add_items_postprocessor returning processed content as is. Data keys: {data.keys()}")
        return parsed_content, data

if __name__ == '__main__':
    # Example Usage (for local testing)
    test_cases = [
        ('{"title": "Test", "plan": [{"step_id": "1"}]}', {"items_to_add": {"top_level": {"task_id": "abc"}, "step_level": {"status": "new"}}}, "Add top and step level"),
        ('{}', {"items_to_add": {"top_level": {"task_id": "abc"}}}, "Add to empty string"),
        ('   ', {"items_to_add": {"top_level": {"task_id": "abc"}}}, "Add to whitespace string"),
        ('{"title": "Test"}', {"items_to_add": {"step_level": {"status": "new"}}}, "Add step level to dict without container"),
        ('{"title": "Test", "plan": "not a list"}', {"items_to_add": {"step_level": {"status": "new"}}}, "Step container not a list"),
        ('{"title": "Test", "plan": [{"step_id": "1", "status": "done"}]}', {"items_to_add": {"step_level": {"status": "new"}}}, "Add step level with existing key"),
        ('{"title": "Test", "subtasks": [{"step_id": "1"}]}', {"items_to_add": {"step_level": {"status": "new"}, "step_container": "subtasks"}}, "Add step level to custom container"),
        ('{"key": "value"', {"items_to_add": {"top_level": {"task_id": "abc"}}}, "Invalid JSON string"),
        ({"title": "Test Dict", "plan": [{"step_id": "1"}]}, {"items_to_add": {"top_level": {"task_id": "abc"}, "step_level": {"status": "new"}}}, "Dict input"),
        ([{"step_id": "1"}], {"items_to_add": {"top_level": {"task_id": "abc"}}}, "List input (no top level add)"),
        ('{"tasks": [{"steps": [{"step_id": "1"}]}]}', {"items_to_add": {"step_level": {"status": "new"}, "step_container": "steps"}}, "Nested step container"),
        ('{"tasks": [{"steps": "not a list"}]}', {"items_to_add": {"step_level": {"status": "new"}, "step_container": "steps"}}, "Nested step container not a list"),
        ('{"tasks": [{"steps": [{"step_id": "1"}, "not a dict"]}]}', {"items_to_add": {"step_level": {"status": "new"}, "step_container": "steps"}}, "Step container with non-dict items"),
    ]

    for i, (test_content, test_data, desc) in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {desc} ---")
        current_data = test_data.copy() # Use a copy to avoid modifying original test data
        current_data["logs"] = []
        current_data["errors"] = []
        current_data["warnings"] = []

        try:
            output_content, output_data = add_items_postprocessor(test_content, current_data)
            print("Output Content:", output_content)
        except ValueError as ve:
            print(f"Status: Error (ValueError: {ve})")
        finally:
            print("Logs:", json.dumps(output_data.get("steps", {}).get("add_items_postprocessor", {}).get("logs", []), indent=2))
            if output_data.get("steps", {}).get("add_items_postprocessor", {}).get("errors"):
                print("Errors:", json.dumps(output_data.get("steps", {}).get("add_items_postprocessor", {}).get("errors", []), indent=2))
            if output_data.get("steps", {}).get("add_items_postprocessor", {}).get("warnings"):
                print("Warnings:", json.dumps(output_data.get("steps", {}).get("add_items_postprocessor", {}).get("warnings", []), indent=2))
            if output_data.get("steps", {}).get("add_items_postprocessor", {}).get("changes"):
                print("Changes:", json.dumps(output_data.get("steps", {}).get("add_items_postprocessor", {}).get("changes", []), indent=2))
            print("Success:", output_data.get("steps", {}).get("add_items_postprocessor", {}).get("success"))

    print("\nAll add_items_postprocessor examples executed.")
