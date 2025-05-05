"""
Identity Transform for YAML Postprocessing

This module provides a simple identity transform function that passes YAML data
through unchanged. It serves as the simplest possible implementation of a scripted
postprocessing step and can be used as a template for more complex transforms.
"""

def identity_transform(yaml_data, result_data):
    """
    A simple identity transform that returns the input data unchanged.
    
    This function follows the standard interface for scripted postprocessing steps:
    it accepts YAML data and a result tracking object and returns both unchanged.
    
    Args:
        yaml_data (dict): The parsed YAML data structure to process
        result_data (dict): A dictionary containing processing status and logs
        
    Returns:
        tuple: A tuple containing (yaml_data, result_data) unchanged
    
    Example:
        >>> yaml_data = {"task": "example"}
        >>> result_data = {"success": True, "steps": {}, "logs": []}
        >>> output_yaml, output_result = identity_transform(yaml_data, result_data)
        >>> assert output_yaml == yaml_data
        >>> assert output_result == result_data
    """
    # Simply return the inputs unchanged
    return yaml_data, result_data
