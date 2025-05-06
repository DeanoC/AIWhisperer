"""
Escape Text Fields for YAML Postprocessing

This module provides a function to escape or properly quote text fields in YAML data that
might contain YAML special characters like colons, which would otherwise cause parsing errors.
It identifies lines that look like natural language descriptions without proper YAML formatting
and ensures they are properly quoted or escaped.
"""

import re
from typing import Dict, Tuple

def escape_text_fields(yaml_content: str | dict, data: dict = None) -> Tuple[str | dict, Dict]:
    """
    Escapes or properly quotes text fields in YAML that contain special characters
    like colons that might cause parsing errors.

    Args:
        yaml_content (str | dict): The input YAML content as a string or dictionary
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_yaml_content in the same format as the input (str | dict).
        tuple: (processed_yaml_content (str | dict), updated_result (dict))
    """
    # Initialize data if it's None
    if data is None:
        data = {
            "success": True,
            "steps": {},
            "logs": []
        }

    # Ensure data has a logs key
    if "logs" not in data:
        data["logs"] = []

    # If yaml_content is a dictionary, it's already parsed YAML, so return it as is
    if isinstance(yaml_content, dict):
        data["logs"].append("Input is a dictionary, no text field escaping needed.")
        return yaml_content, data

    if not yaml_content.strip():
        data["logs"].append("No text fields requiring escaping were found.")
        return yaml_content, data

    # Process line by line
    lines = yaml_content.splitlines()
    processed_lines = []
    changes_made = 0

    for line in lines:
        stripped_line = line.strip()

        # Skip empty lines or comments
        if not stripped_line or stripped_line.startswith("#"):
            processed_lines.append(line)
            continue

        # Check if this is a properly formatted YAML line with key-value pairs
        # Valid YAML key-value format: key: value or key:
        if re.match(r'^\s*[^:\s]+\s*:(\s.*)?$', line) and not re.search(r'^\s*[^:]+:[^:]+:.*$', line):
            processed_lines.append(line)
            continue

        # Check if line contains a colon but not in a valid YAML key-value format
        # These are often natural language descriptions that need quoting
        if ":" in line:
            indent = len(line) - len(line.lstrip())
            indentation = line[:indent]
            content = stripped_line.replace('"', '\\"')
            quoted_line = f'{indentation}"{content}"'
            processed_lines.append(quoted_line)
            changes_made += 1
            continue

        # Handle regular text without colons that needs quoting
        if stripped_line:
            indent = len(line) - len(line.lstrip())
            indentation = line[:indent]
            content = stripped_line.replace('"', '\\"')
            quoted_line = f'{indentation}"{content}"'
            processed_lines.append(quoted_line)
            changes_made += 1
        else:
            processed_lines.append(line)

    if changes_made > 0:
        data["logs"].append(f"Escaped {changes_made} text fields with potential YAML special characters.")
    else:
        data["logs"].append("No text fields requiring escaping were found.")

    # Add a newline at the end to match expected output
    result = "\n".join(processed_lines)
    if yaml_content.endswith("\n"):
        result += "\n"

    return result, data
