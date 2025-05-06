from ruamel.yaml import YAML
from io import StringIO
import re
import yaml as pyyaml  # Import PyYAML as a fallback

def normalize_indentation(yaml_content: str | dict, data: dict = None) -> tuple:
    # Debug print to see what's being passed in
    print(f"normalize_indentation called with type: {type(yaml_content)}")
    if isinstance(yaml_content, str):
        print(f"Content starts with: {yaml_content[:50]}")
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

    # Backtick code block markers should have been removed by clean_backtick_wrapper
    # This function should focus only on normalizing indentation

    # Replace tabs with spaces
    yaml_content = yaml_content.replace('\t', ' ' * indent)

    # Check if the YAML contains complex nested structures with lists
    # If it does, we'll use a more careful approach to avoid changing the structure
    if isinstance(yaml_content, str) and re.search(r'^\s*-\s+\w+:', yaml_content, re.MULTILINE):
        try:
            # First, try to parse the YAML to validate it
            yaml = YAML()
            yaml.preserve_quotes = True
            parsed_yaml = yaml.load(yaml_content)

            # If parsing succeeds, the YAML is valid, so we'll just normalize simple indentation issues
            # without changing the structure
            lines = yaml_content.splitlines()
            normalized_lines = []

            for line in lines:
                # Skip empty lines or comments
                if not line.strip() or line.strip().startswith('#'):
                    normalized_lines.append(line)
                    continue

                # Normalize indentation for non-list items
                if not line.strip().startswith('-'):
                    # Count leading spaces
                    leading_spaces = len(line) - len(line.lstrip())
                    # Calculate the correct indentation level
                    indent_level = leading_spaces // indent
                    # Normalize the indentation
                    normalized_line = ' ' * (indent_level * indent) + line.lstrip()
                    normalized_lines.append(normalized_line)
                else:
                    # For list items, preserve the original indentation
                    normalized_lines.append(line)

            result = '\n'.join(normalized_lines)
            if yaml_content.endswith('\n'):
                result += '\n'

            data["logs"].append("Complex structure detected, indentation normalized with structure preservation.")

            # If the original input was a dictionary, we need to parse the result back to a dictionary
            if is_dict_input:
                yaml = YAML()
                yaml.preserve_quotes = True
                parsed_result = yaml.load(result)
                return parsed_result, data
            else:
                return result, data

        except Exception as e:
            # If parsing fails, log the error and continue with the standard approach
            data["logs"].append(f"Error during structure-preserving normalization: {e}")
            # Fall through to the standard approach

    # First, try direct parsing with PyYAML since we know it works with our problematic YAML
    print("Trying direct parsing with PyYAML first")
    try:
        # Parse with PyYAML
        parsed_yaml = pyyaml.safe_load(yaml_content)

        # Dump back to string with proper indentation
        output = pyyaml.dump(parsed_yaml, default_flow_style=False, indent=indent)
        data["logs"].append("Indentation normalized using PyYAML direct approach.")
        print("PyYAML direct parsing successful")

        # Return the same type as the input
        if is_dict_input:
            return parsed_yaml, data
        else:
            return output, data
    except Exception as pyyaml_error:
        print(f"PyYAML direct parsing failed: {pyyaml_error}")
        data["logs"].append(f"Error with PyYAML direct parsing: {pyyaml_error}")
        data["logs"].append("Falling back to ruamel.yaml.")

        # Standard approach using ruamel.yaml for simpler YAML structures
        try:
            print("Trying ruamel.yaml as fallback")
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.indent(mapping=indent, sequence=indent, offset=indent)

            parsed_yaml = yaml.load(yaml_content)
            output = StringIO()
            yaml.dump(parsed_yaml, output)
            data["logs"].append("Indentation normalized using ruamel.yaml fallback approach.")
            print("ruamel.yaml fallback successful")

            # Return the same type as the input
            if is_dict_input:
                return parsed_yaml, data
            else:
                return output.getvalue(), data
        except Exception as ruamel_error:
            print(f"ruamel.yaml fallback failed: {ruamel_error}")
            data["logs"].append(f"Error with ruamel.yaml fallback: {ruamel_error}")

            # If both approaches fail, try a more direct approach
            print("Both parsing approaches failed, trying a more direct approach")
            data["logs"].append("Both parsing approaches failed, trying a more direct approach.")

            # Just normalize the indentation manually without parsing
            try:
                print("Normalizing indentation manually")
                lines = yaml_content.splitlines()
                normalized_lines = []

                for line in lines:
                    # Skip empty lines
                    if not line.strip():
                        normalized_lines.append(line)
                        continue

                    # Count leading spaces
                    leading_spaces = len(line) - len(line.lstrip())
                    # Calculate the correct indentation level
                    indent_level = leading_spaces // indent
                    # Normalize the indentation
                    normalized_line = ' ' * (indent_level * indent) + line.lstrip()
                    normalized_lines.append(normalized_line)

                result = '\n'.join(normalized_lines)
                if yaml_content.endswith('\n'):
                    result += '\n'

                data["logs"].append("Indentation normalized using direct line-by-line approach.")
                print("Manual indentation normalization successful")
                return result, data
            except Exception as direct_error:
                print(f"Manual indentation normalization failed: {direct_error}")
                data["logs"].append(f"Error with direct approach: {direct_error}")
                # If all approaches fail, raise the original error
                raise ValueError(f"Error normalizing indentation: {pyyaml_error}")
