from ruamel.yaml import YAML
from io import StringIO

def normalize_indentation(yaml_content: str, indent: int = 2) -> str:
    """
    Normalize the indentation of a YAML string to a consistent number of spaces.

    Args:
        yaml_content (str): The input YAML content as a string.
        indent (int): The number of spaces for indentation (default is 2).

    Returns:
        str: The YAML content with normalized indentation.
    """
    if not yaml_content.strip():
        return yaml_content  # Return as is for empty or whitespace-only content

    # Replace tabs with spaces
    yaml_content = yaml_content.replace('\t', ' ' * indent)

    yaml = YAML()
    yaml.preserve_quotes = True  # Preserve quotes
    yaml.indent(mapping=indent, sequence=indent, offset=indent)
    yaml.allow_duplicate_keys = True  # Allow duplicate keys to avoid parsing errors
    yaml.default_flow_style = False  # Ensure block style for YAML

    try:
        parsed_yaml = yaml.load(yaml_content)  # Parse the YAML content
        if parsed_yaml is None:  # Handle cases with only comments
            return yaml_content.strip() + "\n"  # Preserve comments as-is
        output = StringIO()
        yaml.dump(parsed_yaml, output)
        return output.getvalue()  # Keep trailing newline for consistency
    except Exception as e:
        raise ValueError(f"Invalid YAML content: {e}")
