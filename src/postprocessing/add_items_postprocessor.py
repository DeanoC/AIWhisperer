"""
Postprocessing step to add arbitrary items to AI-generated YAML output.

This module provides a function that can be used as a scripted step in the
PostprocessingPipeline to add specified items to YAML content at designated positions.
"""

import yaml
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

def add_items_postprocessor(yaml_string: str, result_data: Dict) -> Tuple[str, Dict]:
    """
    Adds specified items to the YAML string at designated positions.
    
    Args:
        yaml_string: The YAML string to process
        result_data: Dictionary containing processing results and metadata
        
    Returns:
        Tuple containing:
        - The modified YAML string with items added
        - The updated result_data dictionary
    """
    # Initialize step result in the result_data dictionary
    if "steps" not in result_data:
        result_data["steps"] = {}
    
    step_result = {
        "success": True,
        "changes": [],
        "errors": [],
        "warnings": [],
        "logs": []
    }
    
    # Check if there are items to add
    if not result_data.get("items_to_add"):
        step_result["logs"].append("No items to add specified")
        result_data["steps"]["add_items_postprocessor"] = step_result
        result_data["success"] = True
        return yaml_string, result_data
    
    # Parse the YAML string
    try:
        if not yaml_string.strip():
            raise ValueError("Empty YAML string provided")
        
        yaml_dict = yaml.safe_load(yaml_string)
        if yaml_dict is None:
            yaml_dict = {}  # Handle case where yaml_string is empty but valid
        
        if not isinstance(yaml_dict, dict):
            raise ValueError(f"Parsed YAML is not a dictionary (got {type(yaml_dict).__name__})")
    except Exception as e:
        step_result["success"] = False
        step_result["errors"].append(f"Failed to parse YAML: {str(e)}")
        result_data["steps"]["add_items_postprocessor"] = step_result
        result_data["success"] = False
        return yaml_string, result_data
    
    # Add top-level items
    top_level_items = result_data.get("items_to_add", {}).get("top_level", {})
    if top_level_items:
        for key, value in top_level_items.items():
            if key in yaml_dict:
                step_result["warnings"].append(f"Key '{key}' already exists in YAML, not overwriting")
            else:
                yaml_dict[key] = value
                step_result["changes"].append(f"Added top-level item: {key}")
    
    # Add step-level items
    step_level_items = result_data.get("items_to_add", {}).get("step_level", {})
    if step_level_items:
        # Determine the container key for steps
        step_container = result_data.get("items_to_add", {}).get("step_container", "plan")
        
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
        result_data["steps"]["add_items_postprocessor"] = step_result
        result_data["success"] = False
        return yaml_string, result_data
    
    # Update result_data
    result_data["steps"]["add_items_postprocessor"] = step_result
    result_data["success"] = step_result["success"]
    
    return modified_yaml_string, result_data
