"""
Clean Backtick Wrapper for YAML Postprocessing

This module provides a function to remove code block wrappers (e.g., ```yaml) 
and their associated closing backticks from YAML data. It is useful for cleaning 
up YAML content extracted from markdown or similar formats.
"""

from typing import Dict, Tuple
import re


def clean_backtick_wrapper(yaml_content: str | dict, data: dict) -> tuple:
    """
    Removes code block wrappers (e.g., ```yaml) from the YAML data.

    Args:
        yaml_content (str | dict): The input YAML content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_yaml_content must be in the same format as the input (str | dict).
        tuple: (processed_yaml_content (str | dict), updated_result (dict))

    Example:
        >>> yaml_content = "```yaml\\ntask: example\\n```"
        >>> data = {"logs": []}
        >>> output_yaml, output_data = clean_backtick_wrapper(yaml_content, data)
        >>> assert output_yaml == "task: example\\n"
        >>> assert output_data == data
    """
    # If yaml_content is a dictionary, return it as is
    if isinstance(yaml_content, dict):
        if "logs" in data:
            data["logs"].append("Input is a dictionary, no backtick wrappers to remove.")
        return yaml_content, data

    # Use regex to remove opening and closing backtick wrappers
    cleaned_yaml = re.sub(r"^```[a-zA-Z]*\n|```$", "", yaml_content, flags=re.MULTILINE)

    # Log the cleaning step
    if "logs" in data:
        data["logs"].append("Removed backtick wrappers from YAML data.")

    return cleaned_yaml, data
