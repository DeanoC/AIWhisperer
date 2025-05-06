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
    for line in lines:
        if ":" not in line and line.strip() and not line.strip().startswith("#"):
            data["logs"].append(f"Invalid YAML syntax: Missing colon in line '{line.strip()}'")
            raise ValueError(f"Invalid YAML syntax: Missing colon in line '{line.strip()}'")

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
