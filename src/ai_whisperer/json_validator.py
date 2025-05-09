import json
import uuid
from datetime import datetime, timezone
from jsonschema import validate, ValidationError
import os

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')
TASK_PLAN_SCHEMA_PATH = os.path.join(SCHEMA_DIR, 'task_plan_schema.json')
SUBTASK_SCHEMA_PATH = os.path.join(SCHEMA_DIR, 'subtask_schema.json')

def load_schema(schema_path):
    """Loads a JSON schema from the given path."""
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # This should ideally not happen if paths are correct
        raise RuntimeError(f"Schema file not found: {schema_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding schema file {schema_path}: {e}")

# Load schemas once when the module is imported
try:
    task_plan_schema = load_schema(TASK_PLAN_SCHEMA_PATH)
    subtask_schema = load_schema(SUBTASK_SCHEMA_PATH)
except RuntimeError as e:
    # Handle schema loading errors, perhaps log them or raise a custom exception
    # For now, we'll re-raise to make it clear during development
    print(f"Error loading schemas: {e}")
    task_plan_schema = None
    subtask_schema = None


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


def validate_task_plan(task_plan_data):
    """
    Validates a task plan dictionary against the task_plan_schema.json.

    Args:
        task_plan_data (dict): The task plan data to validate.

    Returns:
        tuple: (is_valid, error_message_or_none)
               is_valid (bool): True if validation passes, False otherwise.
               error_message (str or None): Detailed error message if validation fails, None otherwise.
    """
    if task_plan_schema is None:
        return False, "Task plan schema could not be loaded. Validation cannot proceed."
    try:
        validate(instance=task_plan_data, schema=task_plan_schema)
        return True, None
    except ValidationError as e:
        # Provide a more user-friendly error message
        error_path = " -> ".join(map(str, e.path)) if e.path else "root"
        return False, f"Task Plan Validation Error at '{error_path}': {e.message}"
    except Exception as e:
        return False, f"An unexpected error occurred during task plan validation: {str(e)}"


def validate_subtask(subtask_data):
    """
    Validates a subtask dictionary against the subtask_schema.json.

    Args:
        subtask_data (dict): The subtask data to validate.

    Returns:
        tuple: (is_valid, error_message_or_none)
               is_valid (bool): True if validation passes, False otherwise.
               error_message (str or None): Detailed error message if validation fails, None otherwise.
    """
    if subtask_schema is None:
        return False, "Subtask schema could not be loaded. Validation cannot proceed."
    try:
        validate(instance=subtask_data, schema=subtask_schema)
        return True, None
    except ValidationError as e:
        error_path = " -> ".join(map(str, e.path)) if e.path else "root"
        return False, f"Subtask Validation Error at '{error_path}': {e.message}"
    except Exception as e:
        return False, f"An unexpected error occurred during subtask validation: {str(e)}"
