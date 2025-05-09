# Unit tests for src/ai_whisperer/json_validator.py
import pytest
import uuid
from datetime import datetime, timezone
from jsonschema import ValidationError
import json
import os
from unittest.mock import patch, MagicMock

# Assuming the schemas are in the correct relative path for the validator
# We might need to mock schema loading in more complex scenarios,
# but for basic tests, we'll assume the validator can load them.
# If tests fail due to schema loading, we'll address it then.

from src.ai_whisperer.json_validator import (
    generate_uuid,
    format_timestamp,
    parse_timestamp,
    validate_task_plan,
    validate_subtask,
    load_schema, # Import load_schema to potentially use in tests if needed
    TASK_PLAN_SCHEMA_PATH,
    SUBTASK_SCHEMA_PATH
)

# Define minimal valid/invalid data structures based on expected schemas
# These are simplified and might need refinement if schema details are known.
VALID_TASK_PLAN_DATA = {
    "task_id": str(uuid.uuid4()),
    "task_description": "Test task",
    "subtasks": [],
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat()
}

INVALID_TASK_PLAN_DATA_MISSING_FIELD = {
    "task_description": "Test task",
    "subtasks": [],
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat()
}

VALID_SUBTASK_DATA = {
    "subtask_id": str(uuid.uuid4()),
    "subtask_description": "Test subtask",
    "tool_name": "test_tool",
    "tool_arguments": {},
    "status": "pending",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat()
}

INVALID_SUBTASK_DATA_INVALID_STATUS = {
    "subtask_id": str(uuid.uuid4()),
    "subtask_description": "Test subtask",
    "tool_name": "test_tool",
    "tool_arguments": {},
    "status": "invalid_status",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat()
}

# Dummy schemas for mocking
DUMMY_TASK_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "task_description": {"type": "string"},
        "subtasks": {"type": "array"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"}
    },
    "required": ["task_id", "task_description", "subtasks", "created_at", "updated_at"]
}

DUMMY_SUBTASK_SCHEMA = {
    "type": "object",
    "properties": {
        "subtask_id": {"type": "string"},
        "subtask_description": {"type": "string"},
        "tool_name": {"type": "string"},
        "tool_arguments": {"type": "object"},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed"]},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"}
    },
    "required": ["subtask_id", "subtask_description", "tool_name", "tool_arguments", "status", "created_at", "updated_at"]
}


def test_generate_uuid():
    """Test that generate_uuid returns a valid UUID string."""
    id_str = generate_uuid()
    assert isinstance(id_str, str)
    try:
        uuid.UUID(id_str, version=4)
    except ValueError:
        pytest.fail(f"Generated string '{id_str}' is not a valid UUID v4.")

def test_format_timestamp():
    """Test that format_timestamp returns a valid ISO 8601 UTC string."""
    timestamp_str = format_timestamp()
    assert isinstance(timestamp_str, str)
    # Basic check for ISO 8601 format (ends with +00:00 or Z for UTC)
    assert timestamp_str.endswith('+00:00') or timestamp_str.endswith('Z')
    # Test with a specific datetime object
    test_dt = datetime(2023, 10, 27, 10, 30, 0, tzinfo=timezone.utc)
    formatted_test_dt = format_timestamp(test_dt)
    assert formatted_test_dt == '2023-10-27T10:30:00+00:00'

def test_parse_timestamp():
    """Test that parse_timestamp correctly parses ISO 8601 strings."""
    # Test with UTC timestamp
    utc_timestamp_str = '2023-10-27T10:30:00+00:00'
    dt_object = parse_timestamp(utc_timestamp_str)
    assert isinstance(dt_object, datetime)
    assert dt_object.year == 2023
    assert dt_object.month == 10
    assert dt_object.day == 27
    assert dt_object.hour == 10
    assert dt_object.minute == 30
    assert dt_object.second == 0
    assert dt_object.tzinfo == timezone.utc

    # Test with Z notation for UTC
    z_timestamp_str = '2023-10-27T10:30:00Z'
    dt_object_z = parse_timestamp(z_timestamp_str)
    assert isinstance(dt_object_z, datetime)
    assert dt_object_z.tzinfo == timezone.utc

    # Test with naive timestamp (should assume UTC)
    naive_timestamp_str = '2023-10-27T10:30:00'
    dt_object_naive = parse_timestamp(naive_timestamp_str)
    assert isinstance(dt_object_naive, datetime)
    assert dt_object_naive.tzinfo == timezone.utc

    # Test with invalid format
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        parse_timestamp("invalid-timestamp-string")

@patch('src.ai_whisperer.json_validator.task_plan_schema', DUMMY_TASK_PLAN_SCHEMA)
def test_validate_task_plan_valid():
    """Test validate_task_plan with valid data."""
    is_valid, error_message = validate_task_plan(VALID_TASK_PLAN_DATA)
    assert is_valid is True
    assert error_message is None

@patch('src.ai_whisperer.json_validator.task_plan_schema', DUMMY_TASK_PLAN_SCHEMA)
def test_validate_task_plan_invalid():
    """Test validate_task_plan with invalid data (missing field)."""
    is_valid, error_message = validate_task_plan(INVALID_TASK_PLAN_DATA_MISSING_FIELD)
    assert is_valid is False
    assert "Task Plan Validation Error" in error_message
    assert "'task_id' is a required property" in error_message # Assuming task_id is required

@patch('src.ai_whisperer.json_validator.subtask_schema', DUMMY_SUBTASK_SCHEMA)
def test_validate_subtask_valid():
    """Test validate_subtask with valid data."""
    is_valid, error_message = validate_subtask(VALID_SUBTASK_DATA)
    assert is_valid is True
    assert error_message is None

@patch('src.ai_whisperer.json_validator.subtask_schema', DUMMY_SUBTASK_SCHEMA)
def test_validate_subtask_invalid():
    """Test validate_subtask with invalid data (invalid status)."""
    is_valid, error_message = validate_subtask(INVALID_SUBTASK_DATA_INVALID_STATUS)
    assert is_valid is False
    assert "Subtask Validation Error" in error_message
    assert "'invalid_status' is not one of" in error_message # Assuming status is an enum

# Optional: Add tests for schema loading errors if needed
# @patch('src.ai_whisperer.json_validator.load_schema')
# def test_load_schema_file_not_found(mock_load_schema):
#     """Test load_schema with a non-existent file."""
#     mock_load_schema.side_effect = FileNotFoundError
#     with pytest.raises(RuntimeError, match="Schema file not found"):
#         load_schema("non_existent_schema.json")

# @patch('src.ai_whisperer.json_validator.load_schema')
# def test_load_schema_invalid_json(mock_load_schema):
#     """Test load_schema with an invalid JSON file."""
#     mock_load_schema.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 1)
#     with pytest.raises(RuntimeError, match="Error decoding schema file"):
#         load_schema("invalid_schema.json")