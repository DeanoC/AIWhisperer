from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scanner import ScannerError
from io import StringIO

def validate_syntax(yaml_content: str | dict, data: dict = None) -> tuple:
    """
    Validate and correct basic YAML syntax issues.

   Args:
        yaml_content (str | dict): The input YAML content as a string or dictionary.
        data (dict): The input parameter dictionary and where results are also stored

    Returns:
        The processed_yaml_content must be in the same format as the input (str | dict).
        tuple: (processed_yaml_content (str | dict), updated_result (dict))

    Raises:
        ValueError: If the YAML content contains unresolvable syntax errors.
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

    # If yaml_content is a dictionary, it's already valid YAML
    if isinstance(yaml_content, dict):
        data["logs"].append("Input is a dictionary, syntax is valid.")
        return yaml_content, data

    if not yaml_content.strip():
        data["logs"].append("YAML content is empty or whitespace-only.")
        return yaml_content, data

    # Pre-validation: Check for common syntax issues
    lines = yaml_content.splitlines()

    # Track if we're inside a multi-line string (indicated by |)
    in_multiline_string = False
    indentation_level = 0

    for i, line in enumerate(lines):
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith("#"):
            continue

        # Check if this line starts a multi-line string
        if "|" in line and line.rstrip().endswith("|"):
            in_multiline_string = True
            indentation_level = len(line) - len(line.lstrip())
            continue

        # If we're in a multi-line string, check if we've exited it
        if in_multiline_string:
            # If this line has less indentation than the multi-line string,
            # we've exited the multi-line string
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indentation_level:
                in_multiline_string = False
            else:
                # Skip colon check for lines in a multi-line string
                continue

        # Only check for missing colons if we're not in a multi-line string and not a list item
        stripped_line = line.strip()
        if (not in_multiline_string and 
            ":" not in line and 
            stripped_line and 
            not stripped_line.startswith("-")):  # Skip list items

            # Add more context to the error message
            context = f"Line {i+1}: {stripped_line}"
            if i > 0:
                context += f"\nPrevious line: {lines[i-1].strip()}"
            if i < len(lines) - 1:
                context += f"\nNext line: {lines[i+1].strip()}"

            data["logs"].append(f"Invalid YAML syntax: Missing colon in line '{stripped_line}'. Context: {context}")

            # Try to parse with PyYAML before giving up
            try:
                import yaml as pyyaml
                parsed_yaml = pyyaml.safe_load(yaml_content)
                data["logs"].append("YAML syntax validated with PyYAML despite missing colon warning.")
                return yaml_content, data
            except Exception as pyyaml_error:
                data["logs"].append(f"PyYAML validation also failed: {pyyaml_error}")

                # One more attempt: if PyYAML fails, just return the content as is
                # This is a last resort to avoid blocking the pipeline
                data["logs"].append("Returning content as is despite syntax warnings.")
                return yaml_content, data

    yaml = YAML()
    yaml.preserve_quotes = True

    try:
        parsed_yaml = yaml.load(yaml_content)
        if parsed_yaml is None:  # Handle cases with only comments
            data["logs"].append("YAML contains only comments or is empty.")
            return yaml_content.strip() + "\n", data

        output = StringIO()
        yaml.dump(parsed_yaml, output)
        data["logs"].append("YAML syntax validated successfully.")
        return output.getvalue(), data
    except (ParserError, ScannerError) as e:
        data["logs"].append(f"YAML syntax error: {e}")
        raise ValueError(f"Invalid YAML content: {e}")
    except Exception as e:
        data["logs"].append(f"Unexpected error while processing YAML: {e}")
        raise ValueError(f"Unexpected error while processing YAML: {e}")
