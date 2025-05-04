import yaml
from pathlib import Path
from .exceptions import ProcessingError

def read_markdown(file_path: str) -> str:
    """
    Reads the content of a Markdown file.

    Args:
        file_path: The path to the Markdown file.

    Returns:
        The content of the file as a string.

    Raises:
        ProcessingError: If the file cannot be found or read.
    """
    try:
        path = Path(file_path)
        # Ensure the path doesn't point to a directory
        if path.is_dir():
            raise ProcessingError(f"Path points to a directory, not a file: {file_path}")
        # Read the file with UTF-8 encoding
        content = path.read_text(encoding='utf-8')
        return content
    except FileNotFoundError:
        raise ProcessingError(f"File not found: {file_path}") from None
    except UnicodeDecodeError as e:
        raise ProcessingError(f"Error reading file {file_path} due to encoding issue: {e}") from e
    except OSError as e: # Catch other potential OS errors like permission issues
        raise ProcessingError(f"Error reading file {file_path}: {e}") from e


def save_yaml(data: dict, file_path: str) -> None:
    """
    Saves a dictionary to a YAML file.

    Args:
        data: The dictionary to save.
        file_path: The path to the output YAML file.

    Raises:
        ProcessingError: If the data cannot be written to the file.
    """
    try:
        path = Path(file_path)
        # Ensure the parent directory exists before trying to write
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except (IOError, OSError) as e: # Catch file system errors (permissions, disk full, etc.)
        raise ProcessingError(f"Error writing file {file_path}: {e}") from e
    except yaml.YAMLError as e:
        raise ProcessingError(f"Error serializing data to YAML for file {file_path}: {e}") from e


def format_prompt(template: str, md_content: str, config_vars: dict) -> str:
    """
    Formats the prompt using a template string and provided variables.

    Args:
        template: The prompt template string (using .format() style placeholders).
        md_content: The content read from the requirements Markdown file.
        config_vars: A dictionary containing configuration variables.

    Returns:
        The formatted prompt string.

    Raises:
        ProcessingError: If a placeholder in the template is not found in the
                         combined variables (md_content + config_vars).
    """
    try:
        # Combine md_content with other config variables for formatting
        format_data = config_vars.copy()
        format_data['md_content'] = md_content # Correct key to match template placeholder
        return template.format(**format_data)
    except KeyError as e:
        raise ProcessingError(f"Missing variable in config/markdown for prompt template placeholder: {e}") from e
    except Exception as e: # Catch other potential formatting errors
        raise ProcessingError(f"Error formatting prompt template: {e}") from e


def process_response(response_text: str) -> dict | list:
    """
    Processes the raw text response from the API, expecting YAML format.

    Args:
        response_text: The raw string response from the API.

    Returns:
        The parsed YAML data as a Python dictionary or list.

    Raises:
        ProcessingError: If the response is empty or cannot be parsed as valid YAML.
    """
    if not response_text or response_text.isspace():
        raise ProcessingError("Error parsing API response YAML: Empty response")

    # Strip potential markdown code fences
    cleaned_text = response_text.strip()
    if cleaned_text.startswith("```yaml") and cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[len("```yaml"): -len("```")]
    elif cleaned_text.startswith("```") and cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[len("```"): -len("```")]

    # Strip leading/trailing whitespace again after removing fences
    cleaned_text = cleaned_text.strip()

    # Check if the cleaned text is now empty
    if not cleaned_text:
        raise ProcessingError("Error parsing API response YAML: Response contained only markdown fences or whitespace.")

    try:
        # Use safe_load on the cleaned text
        parsed_data = yaml.safe_load(cleaned_text)
        if parsed_data is None and not cleaned_text.strip().startswith('---'):
            is_only_comments = all(line.strip().startswith('#') or not line.strip() for line in cleaned_text.splitlines())
            if not is_only_comments:
                raise ProcessingError("Error parsing API response YAML: Resulted in None, possibly invalid structure.")
            else:
                raise ProcessingError("Error parsing API response YAML: Response contained only comments or whitespace.")
        if not isinstance(parsed_data, (dict, list)):
            raise ProcessingError(f"Error parsing API response YAML: Expected a dictionary or list, but got {type(parsed_data).__name__}.")
        return parsed_data
    except yaml.YAMLError as e:
        raise ProcessingError(f"Error parsing API response YAML: {e}") from e
