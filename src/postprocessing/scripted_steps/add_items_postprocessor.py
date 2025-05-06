"""
Postprocessing step to add arbitrary items to AI-generated YAML output.

This module provides a function that can be used as a scripted step in the
PostprocessingPipeline to add specified items to YAML content at designated positions.
"""

import yaml
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

def add_items_postprocessor(yaml_content: str | dict, data: dict) -> tuple:
    """
    Adds specified items to the YAML string at designated positions.

    Args:
        yaml_content (str | dict): The input YAML content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_yaml_content must be in the same format as the input (str | dict).
        tuple: (processed_yaml_content (str | dict), updated_result (dict))
   """
    # Initialize step result in the result_data dictionary
    if "steps" not in data:
        data["steps"] = {}

    step_result = {
        "success": True,
        "changes": [],
        "errors": [],
        "warnings": [],
        "logs": []
    }

    # Check if there are items to add
    if not data.get("items_to_add"):
        step_result["logs"].append("No items to add specified")
        data["steps"]["add_items_postprocessor"] = step_result
        data["success"] = True
        return yaml_content, data

    # Parse the YAML content into a dictionary if it's a string - always parse in this step
    # to ensure we don't rely on previously parsed YAML
    try:
        if isinstance(yaml_content, str):
            if not yaml_content.strip():
                raise ValueError("Empty YAML string provided")

            # Try to parse with PyYAML
            try:
                yaml_dict = yaml.safe_load(yaml_content)
                if yaml_dict is None:
                    yaml_dict = {}  # Handle case where yaml_content is empty but valid
                step_result["logs"].append("Successfully parsed YAML with PyYAML")
            except Exception as yaml_error:
                step_result["logs"].append(f"Failed to parse YAML with PyYAML: {str(yaml_error)}")

                # If parsing fails, create a minimal dictionary with the items to add
                yaml_dict = {}
                step_result["logs"].append("Created minimal dictionary for items to add")
                step_result["warnings"].append("Using minimal dictionary due to parsing failure")
        elif isinstance(yaml_content, dict):
            yaml_dict = yaml_content
        else:
            raise ValueError(f"Invalid input type. Expected a YAML string or dictionary, got {type(yaml_content).__name__}")

        if not isinstance(yaml_dict, dict):
            raise ValueError(f"Parsed YAML is not a dictionary (got {type(yaml_dict).__name__})")
    except Exception as e:
        step_result["success"] = False
        step_result["errors"].append(f"Failed to parse YAML: {str(e)}")
        data["steps"]["add_items_postprocessor"] = step_result
        data["success"] = False

        # Return the content as is to avoid blocking the pipeline
        step_result["logs"].append("Returning content as is due to parsing failure")
        return yaml_content, data

    # Add top-level items
    top_level_items = data.get("items_to_add", {}).get("top_level", {})
    if top_level_items:
        for key, value in top_level_items.items():
            if key in yaml_dict:
                step_result["warnings"].append(f"Key '{key}' already exists in YAML, not overwriting")
            else:
                yaml_dict[key] = value
                step_result["changes"].append(f"Added top-level item: {key}")

    # Add step-level items
    step_level_items = data.get("items_to_add", {}).get("step_level", {})
    if step_level_items:
        # Determine the container key for steps
        step_container = data.get("items_to_add", {}).get("step_container", "plan")

        if step_container in yaml_dict and isinstance(yaml_dict[step_container], list):
            for step in yaml_dict[step_container]:
                if isinstance(step, dict):
                    for key, value in step_level_items.items():
                        if key in step:
                            step_result["warnings"].append(f"Key '{key}' already exists in step, not overwriting")
                        else:
                            step[key] = value
                            step_result["changes"].append(f"Added step-level item: {key}")
        elif step_level_items:
            step_result["warnings"].append(f"Step container '{step_container}' not found or not a list")

    # Convert the modified dictionary back to YAML
    try:
        modified_yaml_string = yaml.dump(yaml_dict, sort_keys=False, default_flow_style=False)
        step_result["logs"].append(f"Successfully added {len(step_result['changes'])} items")
    except Exception as e:
        step_result["success"] = False
        step_result["errors"].append(f"Failed to convert modified dictionary back to YAML: {str(e)}")
        data["steps"]["add_items_postprocessor"] = step_result
        data["success"] = False
        return yaml_content, data

    # Update result_data
    data["steps"]["add_items_postprocessor"] = step_result
    data["success"] = step_result["success"]

    # If the input was a dictionary, return the modified dictionary
    if isinstance(yaml_content, dict):
        return yaml_dict, data
    else:
        return modified_yaml_string, data
