import json
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
        content = path.read_text(encoding="utf-8")
        return content
    except FileNotFoundError:
        raise ProcessingError(f"File not found: {file_path}") from None
    except UnicodeDecodeError as e:
        raise ProcessingError(f"Error reading file {file_path} due to encoding issue: {e}") from e
    except OSError as e:  # Catch other potential OS errors like permission issues
        raise ProcessingError(f"Error reading file {file_path}: {e}") from e


def save_json(data: dict, file_path: str) -> None:
    """
    Saves a dictionary to a JSON file.

    Args:
        data: The dictionary to save.
        file_path: The path to the output JSON file.

    Raises:
        ProcessingError: If the data cannot be written to the file.
    """
    try:
        path = Path(file_path)
        # Ensure the parent directory exists before trying to write
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)  # Use json.dump for JSON
    except (IOError, OSError) as e:  # Catch file system errors (permissions, disk full, etc.)
        raise ProcessingError(f"Error writing file {file_path}: {e}") from e
    except TypeError as e:  # Catch JSON serialization errors
        raise ProcessingError(f"Error serializing data to JSON for file {file_path}: {e}") from e


def format_prompt(template: str, requirements: str, config_vars: dict) -> str:
    """
    Formats the prompt using a template string and provided variables.

    Args:
        template: The prompt template string (using .format() style placeholders).
        requirements: The content read from the requirements Markdown file.
        config_vars: A dictionary containing configuration variables.

    Returns:
        The formatted prompt string.

    Raises:
        ProcessingError: If a placeholder in the template is not found in the
                         combined variables (requirements + config_vars).
    """
    try:
        # Combine requirements with other config variables for formatting
        format_data = config_vars.copy()
        format_data["requirements"] = requirements  # Correct key to match template placeholder
        return template.format(**format_data)
    except KeyError as e:
        raise ProcessingError(f"Missing variable in config/markdown for prompt template placeholder: {e}") from e
    except Exception as e:  # Catch other potential formatting errors
        raise ProcessingError(f"Error formatting prompt template: {e}") from e


def process_response(response_text: str) -> dict | list:
    """
    Processes the raw text response from the API, expecting JSON format.

    Args:
        response_text: The raw string response from the API.

    Returns:
        The parsed YAML data as a Python dictionary or list.

    Raises:
        ProcessingError: If the response is empty or cannot be parsed as valid JSON.
    """
    if not response_text or response_text.isspace():
        raise ProcessingError("Error parsing API response JSON: Empty response")

    # Strip potential markdown code fences for JSON
    cleaned_text = response_text.strip()
    if cleaned_text.startswith("```json") and cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[len("```json") : -len("```")]
    elif cleaned_text.startswith("```") and cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[len("```") : -len("```")]

    # Strip leading/trailing whitespace again after removing fences
    cleaned_text = cleaned_text.strip()

    # Check if the cleaned text is now empty
    if not cleaned_text:
        raise ProcessingError("Error parsing API response JSON: Response contained only markdown fences or whitespace.")

    try:
        # Use json.loads on the cleaned text
        parsed_data = json.loads(cleaned_text)
        # json.loads will raise JSONDecodeError for invalid JSON, including empty string
        # We already handled empty/whitespace before, but this catches other invalid cases.
        if not isinstance(parsed_data, (dict, list)):
            raise ProcessingError(
                f"Error parsing API response JSON: Expected a dictionary or list, but got {type(parsed_data).__name__}."
            )
        return parsed_data
    except json.JSONDecodeError as e:
        raise ProcessingError(f"Error parsing API response JSON: {e}") from e
    except Exception as e:  # Catch any other unexpected errors during parsing
        raise ProcessingError(f"An unexpected error occurred during JSON parsing: {e}") from e
