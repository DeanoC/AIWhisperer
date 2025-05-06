from ruamel.yaml import YAML
from io import StringIO

def normalize_indentation(yaml_content: str | dict, data: dict = None) -> tuple:
    """
    Normalize the indentation of a YAML string to a consistent number of spaces.

    Args:
        yaml_content (str | dict): The input YAML content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_yaml_content must be in the same format as the input (str | dict).
        tuple: (processed_yaml_content (str | dict), updated_result (dict))
   """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Default indentation value
    indent = 2

    # Get custom indentation from data if available
    if "indent" in data:
        indent = data["indent"]

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # Store the original input type
    is_dict_input = isinstance(yaml_content, dict)

    # If yaml_content is a dictionary, convert it to a string for processing
    if is_dict_input:
        # Create a temporary YAML instance to convert dict to string
        temp_yaml = YAML()
        temp_yaml.preserve_quotes = True
        temp_output = StringIO()
        temp_yaml.dump(yaml_content, temp_output)
        yaml_content = temp_output.getvalue()

    if not yaml_content.strip():
        return yaml_content, data  # Return as is for empty or whitespace-only content

    # Check if the content contains only comments or empty lines
    if all(line.strip().startswith('#') or not line.strip() for line in yaml_content.splitlines()):
        data["logs"].append("Content contains only comments, preserving as is.")
        return yaml_content, data

    # Replace tabs with spaces
    yaml_content = yaml_content.replace('\t', ' ' * indent)

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=indent, sequence=indent, offset=indent)

    try:
        parsed_yaml = yaml.load(yaml_content)
        output = StringIO()
        yaml.dump(parsed_yaml, output)
        data["logs"].append("Indentation normalized.")

        # Return the same type as the input
        if is_dict_input:
            return parsed_yaml, data
        else:
            return output.getvalue(), data
    except Exception as e:
        data["logs"].append(f"Error normalizing indentation: {e}")
        raise ValueError(f"Error normalizing indentation: {e}")
