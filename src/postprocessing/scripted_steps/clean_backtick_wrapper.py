"""
Clean Backtick Wrapper for YAML Postprocessing

This module provides a function to remove code block wrappers (e.g., ```yaml) 
and their associated closing backticks from YAML data. It is useful for cleaning 
up YAML content extracted from markdown or similar formats.
"""

from typing import Dict, Tuple
import re


def clean_backtick_wrapper(yaml_data: str, result_data: Dict) -> Tuple[str, Dict]:
    """
    Removes code block wrappers (e.g., ```yaml) from the YAML data.
    
    Args:
        yaml_data (str): The YAML data as a string, potentially wrapped in backticks.
        result_data (dict): A dictionary containing processing status and logs.
        
    Returns:
        tuple: A tuple containing the cleaned YAML data and the result_data.
    
    Example:
        >>> yaml_data = "```yaml\\ntask: example\\n```"
        >>> result_data = {"success": True, "steps": {}, "logs": []}
        >>> output_yaml, output_result = clean_backtick_wrapper(yaml_data, result_data)
        >>> assert output_yaml == "task: example\\n"
        >>> assert output_result == result_data
    """
    # Use regex to remove opening and closing backtick wrappers
    cleaned_yaml = re.sub(r"^```[a-zA-Z]*\n|```$", "", yaml_data, flags=re.MULTILINE)
    
    # Log the cleaning step
    if "logs" in result_data:
        result_data["logs"].append("Removed backtick wrappers from YAML data.")
    
    return cleaned_yaml, result_data
