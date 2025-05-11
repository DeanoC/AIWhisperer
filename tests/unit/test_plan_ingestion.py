import pytest
import json
import os
import shutil
import pytest
from pathlib import Path
from typing import Dict

from src.ai_whisperer.json_validator import set_schema_directory, get_schema_directory

# Import the new ParserPlan and exceptions
from src.ai_whisperer.plan_parser import (
    ParserPlan,
    PlanParsingError,
    PlanFileNotFoundError,
    PlanInvalidJSONError,
    PlanValidationError,
    SubtaskFileNotFoundError,
    SubtaskInvalidJSONError,
    SubtaskValidationError,
    PlanNotLoadedError,
)

# --- Test Data ---

VALID_SINGLE_FILE_PLAN_CONTENT = {
    "task_id": "task-123",
    "natural_language_goal": "Test the single file plan ingestion.",
    "input_hashes": {"requirements_md": "hash1", "config_yaml": "hash2", "prompt_file": "hash3"},
    "plan": [
        {
            "subtask_id": "subtask-001",
            "description": "First step: Generate code.",
            "instructions": ["Generate code according to requirements."],
            "input_artifacts": ["input.txt"],
            "output_artifacts": ["output.txt"],
            "constraints": ["Must be Python."],
            "validation_criteria": ["Runs without errors."],
            "type": "code_generation",
            "depends_on": [],
            "model_preference": None,
        },
        {
            "subtask_id": "subtask-002",
            "description": "Second step: Validate output.",
            "instructions": ["Validate the generated output."],
            "input_artifacts": ["output.txt"],
            "output_artifacts": [],
            "constraints": [],
            "validation_criteria": ["Output matches expected format."],
            "type": "validation",
            "depends_on": ["subtask-001"],
            "model_preference": None,
        },
    ]
}

VALID_OVERVIEW_PLAN_CONTENT = {
    "task_id": "task-overview-456",
    "natural_language_goal": "Test the overview plan ingestion.",
    "input_hashes": {"requirements_md": "hash_req", "config_yaml": "hash_config", "prompt_file": "hash_prompt"},
    "plan": [
        {
            "subtask_id": "step-o1",
            "file_path": "subtasks/subtask1.json",
            "depends_on": [],  # depends_on is still in overview plan step
            "type": "overview_step_type",  # Added required field
        },
        {
            "subtask_id": "step-o2",
            "file_path": "subtasks/subtask2.json",
            "depends_on": ["step-o1"],  # depends_on is still in overview plan step
            "type": "overview_step_type",  # Added required field
        },
    ],
}

VALID_SUBTASK_CONTENT_1 = {
    "subtask_id": "subtask-abc",
    "task_id": "task-overview-456",
    "description": "A subtask for testing overview.",  # Updated description
    "instructions": ["Do something specific for subtask 1."],  # Instructions as array
    "input_artifacts": [],  # Added required field
    "output_artifacts": [],  # Added required field
    "constraints": [],  # Added required field
    "validation_criteria": [],  # Added required field
    "type": "test_subtask",  # Added required field
    "depends_on": [],  # Added required field
    "model_preference": None,  # Added required field
}

VALID_SUBTASK_CONTENT_2 = {
    "subtask_id": "subtask-def",
    "task_id": "task-overview-456",
    "description": "Another subtask for testing overview.",  # Updated description
    "instructions": ["Do something specific for subtask 2."],  # Instructions as array
    "input_artifacts": [],  # Added required field
    "output_artifacts": [],  # Added required field
    "constraints": [],  # Added required field
    "validation_criteria": [],  # Added required field
    "type": "test_subtask",  # Added required field
    "depends_on": ["subtask-abc"],  # Added required field
    "model_preference": None,  # Added required field
}

# --- Fixtures ---


@pytest.fixture
def create_plan_file(tmp_path: Path):
    """Fixture to create a temporary plan file."""

    def _creator(filename: str, content: dict):
        file_path = tmp_path / filename
        file_path.write_text(json.dumps(content))
        return str(file_path)

    return _creator


@pytest.fixture
def create_overview_plan_with_subtasks(tmp_path: Path, request):
    """Fixture to create a temporary overview plan and its subtasks, and set schema directory."""
    original_schema_dir = get_schema_directory()
    schema_temp_dir = tmp_path / "schemas"
    schema_temp_dir.mkdir()

    # Copy schema files to the temporary directory
    source_schema_dir = os.path.join(os.path.dirname(__file__), "../../src/ai_whisperer/schemas")
    shutil.copy(os.path.join(source_schema_dir, "subinitial_plan_schema.json"), schema_temp_dir)
    shutil.copy(os.path.join(source_schema_dir, "initial_plan_schema.json"), schema_temp_dir)

    # Set the schema directory for the validator
    set_schema_directory(str(schema_temp_dir))

    def _creator(overview_filename: str, overview_content: dict, subtask_dir: str, subtasks: Dict[str, dict]):
        overview_file_path = tmp_path / overview_filename
        subtask_dir_path = tmp_path / subtask_dir
        subtask_dir_path.mkdir()

        # Update overview content with correct relative paths
        updated_overview_content = overview_content.copy()
        updated_plan_steps = []
        for step in overview_content.get("plan", []):
            updated_step = step.copy()
            if "file_path" in updated_step:
                # Ensure file_path is relative to the overview file's directory
                updated_step["file_path"] = os.path.join(subtask_dir, os.path.basename(updated_step["file_path"]))
            updated_plan_steps.append(updated_step)
        updated_overview_content["plan"] = updated_plan_steps

        overview_file_path.write_text(json.dumps(updated_overview_content))

        for subtask_filename, subtask_content in subtasks.items():
            subtask_file_path = subtask_dir_path / subtask_filename
            subtask_file_path.write_text(json.dumps(subtask_content))

        return str(overview_file_path)

    # Add a finalizer to reset the schema directory after the test
    request.addfinalizer(lambda: set_schema_directory(original_schema_dir))

    return _creator


# --- Test Cases for ParserPlan ---


def test_parser_plan_not_loaded_init():
    """Test that accessing data before loading raises PlanNotLoadedError."""
    parser = ParserPlan()
    with pytest.raises(PlanNotLoadedError, match="Plan data has not been loaded. Call a load method first."):
        parser.get_parsed_plan()
    with pytest.raises(PlanNotLoadedError, match="Plan data has not been loaded. Call a load method first."):
        parser.get_all_steps()
    # get_task_dependencies is removed
    with pytest.raises(PlanNotLoadedError, match="Plan data has not been loaded. Call a load method first."):
        parser.get_subtask_content("some_subtask_id")


# --- Tests for load_single_file_plan ---


def test_load_single_file_plan_success(create_plan_file):
    """Test successful loading of a valid single-file plan."""
    plan_path = create_plan_file("single_plan.json", VALID_SINGLE_FILE_PLAN_CONTENT)
    parser = ParserPlan()
    parser.load_single_file_plan(plan_path)
    assert parser.get_parsed_plan() == VALID_SINGLE_FILE_PLAN_CONTENT
    assert parser.get_all_steps() == VALID_SINGLE_FILE_PLAN_CONTENT["plan"]
    # get_task_dependencies is removed, no assertion needed
    assert parser.get_subtask_content("subtask-001") is None  # Single file plan doesn't have embedded subtasks


def test_load_single_file_plan_file_not_found():
    """Test loading a non-existent single-file plan."""
    parser = ParserPlan()
    with pytest.raises(PlanFileNotFoundError, match="Plan file not found: .*non_existent_plan.json"):
        parser.load_single_file_plan("non_existent_plan.json")


def test_load_single_file_plan_malformed_json(tmp_path):
    """Test loading a single-file plan with malformed JSON."""
    malformed_content = '{"task_id": "task-malformed", "plan": ['
    malformed_plan_path = tmp_path / "malformed_plan.json"
    malformed_plan_path.write_text(malformed_content)
    parser = ParserPlan()
    with pytest.raises(PlanInvalidJSONError, match="Malformed JSON"):
        parser.load_single_file_plan(str(malformed_plan_path))


def test_load_single_file_plan_missing_top_level_field(create_plan_file):
    """Test single-file plan with missing required top-level field."""
    invalid_content = VALID_SINGLE_FILE_PLAN_CONTENT.copy()
    del invalid_content["task_id"]
    plan_path = create_plan_file("invalid_plan.json", invalid_content)
    parser = ParserPlan()
    with pytest.raises(PlanValidationError, match="'task_id' is a required property"):
        parser.load_single_file_plan(plan_path)


def test_load_single_file_plan_missing_required_input_hashes_field(create_plan_file):
    """Test single-file plan with missing required input_hashes field."""
    invalid_content = json.loads(json.dumps(VALID_SINGLE_FILE_PLAN_CONTENT))
    del invalid_content["input_hashes"]["requirements_md"]
    plan_path = create_plan_file("invalid_plan.json", invalid_content)
    parser = ParserPlan()
    with pytest.raises(PlanValidationError, match="'requirements_md' is a required property"):
        parser.load_single_file_plan(plan_path)


def test_load_single_file_plan_plan_not_a_list(create_plan_file):
    """Test single-file plan where 'plan' is not a list."""
    invalid_content = VALID_SINGLE_FILE_PLAN_CONTENT.copy()
    invalid_content["plan"] = {"not_a": "list"}
    plan_path = create_plan_file("invalid_plan.json", invalid_content)
    parser = ParserPlan()
    with pytest.raises(PlanValidationError, match=".* is not of type 'array'"):
        parser.load_single_file_plan(plan_path)


# Test for missing required subtask fields in single-file plan
def test_load_single_file_plan_missing_required_subtask_field(create_plan_file):
    """Test single-file plan with a step missing a required subtask field."""
    invalid_content = json.loads(json.dumps(VALID_SINGLE_FILE_PLAN_CONTENT))
    # Remove a required field from the first subtask
    del invalid_content["plan"][0]["description"]
    plan_path = create_plan_file("invalid_single_subtask.json", invalid_content)
    parser = ParserPlan()

    # Expecting PlanValidationError because load_single_file_plan now validates steps
    with pytest.raises(PlanValidationError, match="'description' is a required property"):
        parser.load_single_file_plan(plan_path)


# Test for extra properties in single-file plan steps due to additionalProperties: false
def test_load_single_file_plan_extra_property_in_subtask(create_plan_file):
    """Test single-file plan with an extra property in a step."""
    invalid_content = json.loads(json.dumps(VALID_SINGLE_FILE_PLAN_CONTENT))
    # Add an extra property to the first subtask
    invalid_content["plan"][0]["extra_property"] = "should be removed"
    plan_path = create_plan_file("invalid_single_extra.json", invalid_content)
    parser = ParserPlan()
    # Expecting SubtaskValidationError because load_single_file_plan now validates steps
    with pytest.raises(PlanValidationError, match="Additional properties are not allowed"):
        parser.load_single_file_plan(plan_path)


# --- Tests for load_overview_plan ---


def test_load_overview_plan_success(create_overview_plan_with_subtasks):
    """Test successful loading of a valid overview plan with subtasks."""
    overview_path = create_overview_plan_with_subtasks(
        "overview_plan.json",
        VALID_OVERVIEW_PLAN_CONTENT,
        "subtasks",
        {"subtask1.json": VALID_SUBTASK_CONTENT_1, "subtask2.json": VALID_SUBTASK_CONTENT_2},
    )
    parser = ParserPlan()
    parser.load_overview_plan(overview_path)
    parsed_plan = parser.get_parsed_plan()

    assert parsed_plan["task_id"] == VALID_OVERVIEW_PLAN_CONTENT["task_id"]
    assert len(parsed_plan["plan"]) == 2
    assert "loaded_subtasks" in parsed_plan
    assert len(parsed_plan["loaded_subtasks"]) == 2
    assert parsed_plan["loaded_subtasks"]["step-o1"] == VALID_SUBTASK_CONTENT_1
    assert parsed_plan["loaded_subtasks"]["step-o2"] == VALID_SUBTASK_CONTENT_2

    assert parser.get_all_steps() == parsed_plan["plan"]
    # get_task_dependencies is removed, no assertion needed
    assert parser.get_subtask_content("step-o1") == VALID_SUBTASK_CONTENT_1
    assert parser.get_subtask_content("step-o2") == VALID_SUBTASK_CONTENT_2
    assert parser.get_subtask_content("non-existent-step") is None


def test_load_overview_plan_file_not_found():
    """Test loading a non-existent overview plan."""
    parser = ParserPlan()
    with pytest.raises(PlanFileNotFoundError, match="Overview plan file not found: .*non_existent_overview.json"):
        parser.load_overview_plan("non_existent_overview.json")


def test_load_overview_plan_malformed_json(tmp_path):
    """Test loading an overview plan with malformed JSON."""
    malformed_content = '{"task_id": "task-malformed-overview", "plan": ['
    malformed_plan_path = tmp_path / "malformed_overview.json"
    malformed_plan_path.write_text(malformed_content)
    parser = ParserPlan()
    with pytest.raises(PlanInvalidJSONError, match="Malformed JSON"):
        parser.load_overview_plan(str(malformed_plan_path))


def test_load_overview_plan_missing_top_level_field(create_plan_file):
    """Test overview plan with missing required top-level field."""
    invalid_content = VALID_OVERVIEW_PLAN_CONTENT.copy()
    del invalid_content["task_id"]
    plan_path = create_plan_file("invalid_overview.json", invalid_content)
    parser = ParserPlan()
    with pytest.raises(PlanValidationError, match="'task_id' is a required property"):
        parser.load_overview_plan(plan_path)


def test_load_overview_plan_plan_not_a_list(create_plan_file):
    """Test overview plan where 'plan' is not a list."""
    invalid_content = VALID_OVERVIEW_PLAN_CONTENT.copy()
    invalid_content["plan"] = {"not_a": "list"}
    plan_path = create_plan_file("invalid_overview.json", invalid_content)
    parser = ParserPlan()
    with pytest.raises(PlanValidationError, match=".* is not of type 'array'"):
        parser.load_overview_plan(plan_path)


def test_load_overview_plan_missing_required_step_field(create_plan_file):
    """Test overview plan with missing required step field."""
    invalid_content = json.loads(json.dumps(VALID_OVERVIEW_PLAN_CONTENT))
    del invalid_content["plan"][0]["subtask_id"]
    plan_path = create_plan_file("invalid_overview.json", invalid_content)
    parser = ParserPlan()
    with pytest.raises(PlanValidationError, match="'subtask_id' is a required property"):
        parser.load_overview_plan(plan_path)
def test_load_overview_plan_subtask_file_not_found(create_overview_plan_with_subtasks, tmp_path):
    """Test overview plan referencing a non-existent subtask file."""
    overview_content = {
        "task_id": "task-sub-missing",
        "natural_language_goal": "Test missing subtask.",
        "input_hashes": {"requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"},
        "plan": [
            {
                "subtask_id": "step-m1",
                "description": "Step with missing subtask",
                "file_path": "subtasks/missing_subtask.json",  # This file won't be created
                "depends_on": [],
                "agent_spec": {"type": "subtask_runner"},
            }
        ],
    }
    overview_path = create_overview_plan_with_subtasks(
        "overview_missing_subtask.json", overview_content, "subtasks", {}  # No subtasks created
    )
    parser = ParserPlan()
    with pytest.raises(SubtaskFileNotFoundError, match="Step file not found:\s*.*missing_subtask.json\s*\(at index \d+\)"):
        parser.load_overview_plan(overview_path)


def test_load_overview_plan_subtask_malformed_json(create_overview_plan_with_subtasks):
    """Test overview plan referencing a subtask with malformed JSON."""
    # Provide syntactically valid but semantically incorrect JSON to trigger validation error
    invalid_subtask_content = {}  # Empty object is valid JSON but fails schema validation
    overview_path = create_overview_plan_with_subtasks(
        "overview_invalid_subtask_content.json",
        VALID_OVERVIEW_PLAN_CONTENT,
        "subtasks",
        {
            "subtask1.json": VALID_SUBTASK_CONTENT_1,
            "subtask2.json": invalid_subtask_content,
        },  # subtask2 has invalid content
    )
    parser = ParserPlan()
    # Expecting SubtaskValidationError due to schema violation
    with pytest.raises(SubtaskValidationError, match="Subtask validation failed for\s*.*subtask\d+\.json\s*\(referenced in step '.*'\):\s*.*"):
        parser.load_overview_plan(overview_path)


def test_load_overview_plan_subtask_validation_error(create_overview_plan_with_subtasks):
    """Test overview plan referencing a subtask that fails schema validation."""
    invalid_subtask_content = VALID_SUBTASK_CONTENT_1.copy()
    del invalid_subtask_content["description"]  # Missing required field 'description'
    overview_path = create_overview_plan_with_subtasks(
        "overview_invalid_subtask.json",
        VALID_OVERVIEW_PLAN_CONTENT,
        "subtasks",
        {"subtask1.json": invalid_subtask_content, "subtask2.json": VALID_SUBTASK_CONTENT_2},  # subtask1 is invalid
    )
    parser = ParserPlan()
    with pytest.raises(SubtaskValidationError, match="Subtask validation failed for .*subtask1.json"):
        parser.load_overview_plan(overview_path)


# --- Tests for data access after loading ---


def test_data_access_after_single_file_load(create_plan_file):
    """Test accessing data after successful single-file load."""
    plan_path = create_plan_file("single_plan.json", VALID_SINGLE_FILE_PLAN_CONTENT)
    parser = ParserPlan()
    parser.load_single_file_plan(plan_path)
    # These should not raise PlanNotLoadedError
    parser.get_parsed_plan()
    parser.get_all_steps()
    # get_task_dependencies is removed, no assertion needed


def test_data_access_after_overview_load(create_overview_plan_with_subtasks):
    """Test accessing data after successful overview load."""
    overview_path = create_overview_plan_with_subtasks(
        "overview_plan.json",
        VALID_OVERVIEW_PLAN_CONTENT,
        "subtasks",
        {"subtask1.json": VALID_SUBTASK_CONTENT_1, "subtask2.json": VALID_SUBTASK_CONTENT_2},
    )
    parser = ParserPlan()
    parser.load_overview_plan(overview_path)
    # These should not raise PlanNotLoadedError
    parser.get_parsed_plan()
    parser.get_all_steps()
    # get_task_dependencies is removed, no assertion needed
    parser.get_subtask_content("step-o1")
    parser.get_subtask_content("step-o2")
    parser.get_subtask_content("non-existent-step")


# --- Additional Tests ---

# Removed test_plan_with_no_dependencies_single_file as get_task_dependencies is removed
# Removed test_empty_plan_array_single_file as get_task_dependencies is removed


def test_plan_with_optional_fields_missing_single_file(create_plan_file):
    """Test single-file plan with optional fields missing."""
    plan_content = {
        "task_id": "task-optional",
        "natural_language_goal": "Test optional fields.",
        "input_hashes": {"requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"},
        "plan": [
            {
                "subtask_id": "subtask-opt1",  # Added required field
                "description": "Step with minimal fields.",  # Added required field
                "instructions": ["Minimal instructions."],  # Added required field
                "input_artifacts": [],  # Added required field
                "output_artifacts": [],  # Added required field
                "constraints": [],  # Added required field
                "validation_criteria": [],  # Added required field
                "type": "minimal_step",  # Added required field
                "depends_on": [],  # Added required field
                "model_preference": None,  # Added required field
            }
        ],
    }
    plan_path = create_plan_file("optional_fields_plan.json", plan_content)
    parser = ParserPlan()
    parser.load_single_file_plan(plan_path)
    # Assert that the plan was loaded without validation errors
    assert parser.get_parsed_plan() == plan_content
    assert parser.get_all_steps() == plan_content["plan"]


# Test for overview plan with optional fields missing in subtasks
def test_overview_plan_with_optional_subtask_fields_missing(create_overview_plan_with_subtasks):
    """Test overview plan referencing subtasks with optional fields missing."""
    subtask_content_minimal = {
        "subtask_id": "subtask-minimal",
        "task_id": "task-overview-optional",
        "description": "Minimal subtask.",
        "instructions": ["Do minimal work."],
        "input_artifacts": [],
        "output_artifacts": [],
        "constraints": [],
        "validation_criteria": [],
        "type": "minimal_subtask_type",  # Added required field
        "depends_on": [],  # Added required field
        "model_preference": None,  # Added required field
    }
    overview_content = {
        "task_id": "task-overview-optional",
        "natural_language_goal": "Test optional subtask fields.",
        "input_hashes": {"requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"},
        "plan": [
            {
                "subtask_id": "step-min1",
                "description": "Step with minimal subtask",
                "file_path": "subtasks/minimal_subtask.json",
                "depends_on": [],
                "agent_spec": {"type": "subtask_runner"},
            }
        ],
    }
    overview_path = create_overview_plan_with_subtasks(
        "overview_optional_subtask.json",
        overview_content,
        "subtasks",
        {"minimal_subtask.json": subtask_content_minimal},
    )
    parser = ParserPlan()
    parser.load_overview_plan(overview_path)
    # Assert that the overview plan and subtask were loaded without validation errors
    parsed_plan = parser.get_parsed_plan()
    assert parsed_plan["task_id"] == overview_content["task_id"]
    assert len(parsed_plan["plan"]) == 1
    assert parsed_plan["loaded_subtasks"]["step-min1"] == subtask_content_minimal
