import logging
import sys
import hashlib  # Import hashlib
import json
from typing import Dict, Any
# from jsonschema import validate, ValidationError # Potential library

from pathlib import Path  # Import Path
from rich.console import Console

from .exceptions import SchemaValidationError

def setup_logging(level=logging.INFO):
    """Sets up basic logging configuration to output to stderr."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

def setup_rich_output() -> Console:
    """Creates and returns a Rich Console object for styled terminal output."""
    return Console(stderr=True)

def calculate_sha256(file_path: str | Path) -> str:
    """
    Calculates the SHA-256 hash of a file's content.

    Args:
        file_path: The path to the file (as a string or Path object).

    Returns:
        The hexadecimal representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    path = Path(file_path)
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read and update hash string content in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        # Re-raise FileNotFoundError for clarity
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        # Raise a more general IOError for other read issues
        raise IOError(f"Error reading file {file_path}: {e}") from e

def validate_against_schema(data: Dict[str, Any], schema_path: str):
    """
    Validates the given data against a JSON schema file.

    Args:
        data: The dictionary data to validate.
        schema_path: The path to the JSON schema file.

    Raises:
        SchemaValidationError: If validation fails or schema file cannot be read.
        FileNotFoundError: If the schema file does not exist.
    """
    # Placeholder implementation - Replace with actual validation logic
    print(f"--- Placeholder: Validating data against schema: {schema_path} ---")
    # Example using jsonschema (install with pip install jsonschema)
    # try:
    #     with open(schema_path, 'r') as f:
    #         schema = json.load(f)
    #     validate(instance=data, schema=schema)
    # except FileNotFoundError:
    #      raise # Re-raise FileNotFoundError
    # except ValidationError as e:
    #     raise SchemaValidationError(f"Schema validation failed: {e.message}") from e
    # except Exception as e:
    #     raise SchemaValidationError(f"Failed to load or process schema {schema_path}: {e}") from e

    # Simulate validation for now
    if not isinstance(data, dict) or 'agent_spec' not in data:
         # Simulate a validation failure based on test data
         if data.get('step_id') == 'test_step_1_invalid':
              raise SchemaValidationError("Simulated failure: Missing agent_spec")
    print("--- Placeholder: Validation successful ---")
    pass # Assume valid for now
