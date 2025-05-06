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

    # Log the original content for debugging
    if "logs" in data:
        data["logs"].append(f"Original content starts with: {yaml_content[:20]}")

    # Use regex to remove opening and closing backtick wrappers
    # More robust pattern that handles various backtick wrapper formats
    cleaned_yaml = re.sub(r"^```[a-zA-Z]*\s*|```\s*$", "", yaml_content, flags=re.MULTILINE)

    # Check if the backtick wrapper was actually removed
    if yaml_content.startswith("```") and not cleaned_yaml.startswith("```"):
        if "logs" in data:
            data["logs"].append("Successfully removed opening backtick wrapper.")
    elif yaml_content.startswith("```"):
        if "logs" in data:
            data["logs"].append("WARNING: Failed to remove opening backtick wrapper.")
            # Try a more aggressive approach
            if yaml_content.startswith("```yaml"):
                cleaned_yaml = yaml_content[7:]  # Remove ```yaml
                data["logs"].append("Used direct string slicing to remove ```yaml prefix.")

    # Check for closing backticks
    if yaml_content.rstrip().endswith("```") and not cleaned_yaml.rstrip().endswith("```"):
        if "logs" in data:
            data["logs"].append("Successfully removed closing backtick wrapper.")
    elif yaml_content.rstrip().endswith("```"):
        if "logs" in data:
            data["logs"].append("WARNING: Failed to remove closing backtick wrapper.")
            # Try a more aggressive approach
            if cleaned_yaml.rstrip().endswith("```"):
                cleaned_yaml = cleaned_yaml.rstrip()[:-3]  # Remove trailing ```
                data["logs"].append("Used direct string slicing to remove trailing ``` suffix.")

    # Log the cleaning step
    if "logs" in data:
        data["logs"].append(f"Cleaned content starts with: {cleaned_yaml[:20]}")

    return cleaned_yaml, data
