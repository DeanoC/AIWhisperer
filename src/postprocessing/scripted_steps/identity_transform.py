"""
Identity Transform for YAML Postprocessing

This module provides a simple identity transform function that passes YAML data
through unchanged. It serves as the simplest possible implementation of a scripted
postprocessing step and can be used as a template for more complex transforms.
"""

from typing import Dict, Tuple


def identity_transform(yaml_content: str | dict, data: dict) -> tuple:
    """
    A simple identity transform that returns the input data unchanged.

    This function follows the standard interface for scripted postprocessing steps:
    it accepts YAML data and a result tracking object and returns both unchanged.

   Args:
        yaml_content (str | dict): The input YAML content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_yaml_content must be in the same format as the input (str | dict).
        tuple: (processed_yaml_content (str | dict), updated_result (dict))

    Example:
        >>> yaml_content = {"task": "example"}
        >>> data = {"logs": []}
        >>> output_yaml, output_data = identity_transform(yaml_content, data)
        >>> assert output_yaml == yaml_content
        >>> assert output_data == data
    """
    # Simply return the inputs unchanged
    return (yaml_content, data)
