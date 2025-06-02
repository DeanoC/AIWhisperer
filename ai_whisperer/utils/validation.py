import json
import uuid
from datetime import datetime, timezone
from jsonschema import validate, ValidationError
import os
from typing import Optional
# Default schema directory using new hierarchical config structure
def get_default_schema_dir() -> str:
    """Get the default schema directory from the new config structure."""
    try:
        from ai_whisperer.core.config import get_schema_path
        # Get any schema path to determine the schemas directory
        schema_path = get_schema_path("initial_plan_schema")
        return str(schema_path.parent)
    except:
        # Fallback to old location if config system fails
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "schemas"))

DEFAULT_SCHEMA_DIR = get_default_schema_dir()

# Global variable to hold the configured schema directory
_schema_directory: Optional[str] = None

def set_schema_directory(directory: str):
    """Sets the global schema directory."""
    global _schema_directory
    _schema_directory = directory

def get_schema_directory() -> str:
    """Gets the current schema directory, defaulting to DEFAULT_SCHEMA_DIR."""
    return _schema_directory if _schema_directory is not None else DEFAULT_SCHEMA_DIR

def load_schema(schema_path):
    """Loads a JSON schema from the given path."""
    try:
        with open(schema_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # This should ideally not happen if paths are correct
        raise RuntimeError(f"Schema file not found: {schema_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding schema file {schema_path}: {e}")

def generate_uuid():
    """Generates a new UUID string."""
    return str(uuid.uuid4())

def format_timestamp(dt_object=None):
    """
    Converts a datetime object to an ISO 8601 string in UTC.
    If no dt_object is provided, uses the current UTC time.
    """
    if dt_object is None:
        dt_object = datetime.now(timezone.utc)
    return dt_object.isoformat()

def parse_timestamp(timestamp_str):
    """
    Converts an ISO 8601 string to a datetime object.
    Assumes the timestamp is in UTC if no timezone info is present.
    """
    try:
        dt_object = datetime.fromisoformat(timestamp_str)
        # If the datetime object is naive (no timezone info), assume UTC
        if dt_object.tzinfo is None:
            dt_object = dt_object.replace(tzinfo=timezone.utc)
        return dt_object
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}. Error: {e}")

def validate_against_schema(data: dict, schema_name: str):
    """
    Validates a dictionary against a specified JSON schema.

    Args:
        data (dict): The data to validate.
        schema_name (str): The name of the schema file (e.g., 'subtask_plan_schema.json').

    Returns:
        tuple: (is_valid, error_message_or_none)
               is_valid (bool): True if validation passes, False otherwise.
               error_message (str or None): Detailed error message if validation fails, None otherwise.
    """
    try:
        # Try to use the new config system first
        from ai_whisperer.core.config import get_schema_path
        # Remove .json extension if present since get_schema_path adds it
        clean_schema_name = schema_name.replace('.json', '')
        schema_path = get_schema_path(clean_schema_name)
    except:
        # Fallback to old method
        schema_path = os.path.join(get_schema_directory(), schema_name)
    
    try:
        schema_content = load_schema(schema_path)
    except RuntimeError as e:
        return (False, f"Schema could not be loaded from {schema_path}. Validation cannot proceed. Error: {e}")

    try:
        validate(instance=data, schema=schema_content)
        return (True, None)
    except ValidationError as e:
        # Re-raise the ValidationError after catching it
        raise e
    except Exception as e:
        return (False, f"An unexpected error occurred during validation: {str(e)}")
