import pytest
import json
from unittest.mock import mock_open, patch

# Assume the plan ingestion logic will be in a module like this:
# from ai_whisperer.plan_ingestion import PlanIngestion, PlanValidationError

# For now, let's define placeholder classes and functions to write tests against.
# These would be replaced by actual implementations later.

class PlanValidationError(Exception):
    pass

class PlanIngestion:
    def __init__(self, plan_json_content: str):
        try:
            self.plan_data = json.loads(plan_json_content)
        except json.JSONDecodeError as e:
            raise PlanValidationError(f"Malformed JSON: {e}")
        self._validate_plan_structure()
        self._validate_subtask_references() # Placeholder for subtask validation

    def _validate_plan_structure(self):
        required_top_level_fields = ["task_id", "natural_language_goal", "input_hashes", "plan"]
        for field in required_top_level_fields:
            if field not in self.plan_data:
                raise PlanValidationError(f"Missing required top-level field: {field}")

        if not isinstance(self.plan_data["plan"], list):
            raise PlanValidationError("'plan' field must be a list.")

        required_step_fields = ["step_id", "description", "agent_spec"] # depends_on is optional
        required_agent_spec_fields = ["type", "instructions"]

        for i, step in enumerate(self.plan_data["plan"]):
            for field in required_step_fields:
                if field not in step:
                    raise PlanValidationError(f"Step {i} missing required field: {field}")
            
            agent_spec = step.get("agent_spec", {})
            for field in required_agent_spec_fields:
                if field not in agent_spec:
                    raise PlanValidationError(f"Step {i} agent_spec missing required field: {field}")
            
            # Validate input_hashes structure
            input_hashes = self.plan_data.get("input_hashes", {})
            required_input_hashes_fields = ["requirements_md", "config_yaml", "prompt_file"]
            for field in required_input_hashes_fields:
                if field not in input_hashes:
                    raise PlanValidationError(f"Missing required field in input_hashes: {field}")


    def _validate_subtask_references(self):
        # This method would typically load and validate subtask JSON files.
        # For unit tests, we'll mock this behavior.
        # According to design doc:
        # - The runner will read the subtask files referenced in the `file_path` of each step.
        # - The subtask files will be validated against their actual structure.
        # - The validation will check for the presence of required fields like `description`, 
        #   `depends_on`, `agent_spec`, `step_id`, `task_id`, and `subtask_id`.
        # - The `agent_spec` will be checked to ensure it has `type`, `input_artifacts`, 
        #   `output_artifacts`, `instructions`, `constraints`, and `validation_criteria`.
        #
        # The subtask_schema.json has:
        # "required": ["subtask_id", "task_id", "name", "description", "instructions"]
        pass # Actual implementation would involve file I/O and further validation.

    def get_parsed_plan(self):
        return self.plan_data

    def get_task_dependencies(self):
        dependencies = {}
        for step in self.plan_data.get("plan", []):
            dependencies[step["step_id"]] = step.get("depends_on", [])
        return dependencies

# --- Test Cases ---

VALID_PLAN_CONTENT = {
    "task_id": "task-123",
    "natural_language_goal": "Test the plan ingestion.",
    "overall_context": "This is a test.",
    "input_hashes": {
        "requirements_md": "hash1",
        "config_yaml": "hash2",
        "prompt_file": "hash3"
    },
    "plan": [
        {
            "step_id": "step-001",
            "description": "First step",
            "depends_on": [],
            "agent_spec": {
                "type": "code_generation",
                "input_artifacts": ["input.txt"],
                "output_artifacts": ["output.txt"],
                "instructions": ["Generate code."],
                "constraints": ["Must be Python."],
                "validation_criteria": ["Runs without errors."]
            }
        },
        {
            "step_id": "step-002",
            "description": "Second step",
            "depends_on": ["step-001"],
            "agent_spec": {
                "type": "validation",
                "instructions": ["Validate output."]
            }
        }
    ]
}

VALID_SUBTASK_CONTENT = {
    "subtask_id": "subtask-abc",
    "task_id": "task-123",
    "name": "Sample Subtask",
    "description": "A subtask for testing.",
    "instructions": "Do something specific for this subtask."
}


def test_successful_plan_ingestion():
    plan_str = json.dumps(VALID_PLAN_CONTENT)
    ingestion = PlanIngestion(plan_str)
    assert ingestion.get_parsed_plan() == VALID_PLAN_CONTENT

def test_malformed_json():
    malformed_plan_str = '{"task_id": "task-123", "plan": [}' # Missing closing brace and quotes
    with pytest.raises(PlanValidationError, match="Malformed JSON"):
        PlanIngestion(malformed_plan_str)

def test_missing_required_top_level_field():
    invalid_plan = VALID_PLAN_CONTENT.copy()
    del invalid_plan["task_id"]
    plan_str = json.dumps(invalid_plan)
    with pytest.raises(PlanValidationError, match="Missing required top-level field: task_id"):
        PlanIngestion(plan_str)

def test_missing_required_input_hashes_field():
    invalid_plan = json.loads(json.dumps(VALID_PLAN_CONTENT)) # Deep copy
    del invalid_plan["input_hashes"]["requirements_md"]
    plan_str = json.dumps(invalid_plan)
    with pytest.raises(PlanValidationError, match="Missing required field in input_hashes: requirements_md"):
        PlanIngestion(plan_str)

def test_plan_not_a_list():
    invalid_plan = VALID_PLAN_CONTENT.copy()
    invalid_plan["plan"] = {"not_a": "list"}
    plan_str = json.dumps(invalid_plan)
    with pytest.raises(PlanValidationError, match="'plan' field must be a list."):
        PlanIngestion(plan_str)

def test_missing_required_step_field():
    invalid_plan = json.loads(json.dumps(VALID_PLAN_CONTENT)) # Deep copy
    del invalid_plan["plan"][0]["step_id"]
    plan_str = json.dumps(invalid_plan)
    with pytest.raises(PlanValidationError, match="Step 0 missing required field: step_id"):
        PlanIngestion(plan_str)

def test_missing_required_agent_spec_field():
    invalid_plan = json.loads(json.dumps(VALID_PLAN_CONTENT)) # Deep copy
    del invalid_plan["plan"][0]["agent_spec"]["type"]
    plan_str = json.dumps(invalid_plan)
    with pytest.raises(PlanValidationError, match="Step 0 agent_spec missing required field: type"):
        PlanIngestion(plan_str)

def test_get_task_dependencies():
    plan_str = json.dumps(VALID_PLAN_CONTENT)
    ingestion = PlanIngestion(plan_str)
    expected_dependencies = {
        "step-001": [],
        "step-002": ["step-001"]
    }
    assert ingestion.get_task_dependencies() == expected_dependencies

def test_plan_with_no_dependencies():
    plan_content = {
        "task_id": "task-nodep",
        "natural_language_goal": "Test no deps.",
        "input_hashes": {
            "requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"
        },
        "plan": [
            {
                "step_id": "step-a",
                "description": "Step A",
                "agent_spec": {"type": "generic", "instructions": ["Do A"]}
            }
        ]
    }
    plan_str = json.dumps(plan_content)
    ingestion = PlanIngestion(plan_str)
    assert ingestion.get_task_dependencies() == {"step-a": []}

@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
def test_subtask_validation_success(mock_json_load, mock_file_open):
    """
    This test simulates the scenario where subtask files are referenced and validated.
    The actual validation logic for subtasks would be more complex.
    """
    plan_with_subtask_ref = {
        "task_id": "task-sub",
        "natural_language_goal": "Test subtask ref.",
        "input_hashes": {
            "requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"
        },
        "plan": [
            {
                "step_id": "step-s1",
                "description": "Step with subtask",
                "file_path": "path/to/subtask1.json", # Design doc mentions file_path for subtasks
                "agent_spec": {"type": "subtask_runner", "instructions": ["Run subtask"]}
            }
        ]
    }
    
    # Mock PlanIngestion to include subtask validation logic
    class PlanIngestionWithSubtaskValidation(PlanIngestion):
        def _validate_subtask_references(self):
            for step in self.plan_data.get("plan", []):
                if "file_path" in step:
                    # Simulate reading and validating the subtask file
                    # In a real scenario, you'd open(step["file_path"])
                    # and json.load() it, then validate against subtask_schema.json
                    mock_file_open.return_value # Ensure open was called
                    mock_json_load.return_value = VALID_SUBTASK_CONTENT # Simulate loaded content
                    
                    subtask_content = mock_json_load() # Simulate loading
                    required_subtask_fields = ["subtask_id", "task_id", "name", "description", "instructions"]
                    for field in required_subtask_fields:
                        if field not in subtask_content:
                            raise PlanValidationError(f"Subtask {step['file_path']} missing field: {field}")
    
    plan_str = json.dumps(plan_with_subtask_ref)
    ingestion = PlanIngestionWithSubtaskValidation(plan_str) # No error expected
    assert ingestion.get_parsed_plan()["plan"][0]["file_path"] == "path/to/subtask1.json"


@patch('builtins.open', new_callable=mock_open)
@patch('json.load')
def test_subtask_validation_missing_field(mock_json_load, mock_file_open):
    plan_with_subtask_ref = {
        "task_id": "task-sub-fail",
        "natural_language_goal": "Test subtask ref fail.",
        "input_hashes": {
            "requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"
        },
        "plan": [
            {
                "step_id": "step-s2",
                "description": "Step with invalid subtask",
                "file_path": "path/to/invalid_subtask.json",
                "agent_spec": {"type": "subtask_runner", "instructions": ["Run invalid subtask"]}
            }
        ]
    }
    
    invalid_subtask_content = VALID_SUBTASK_CONTENT.copy()
    del invalid_subtask_content["name"] # Missing 'name'

    class PlanIngestionWithSubtaskValidation(PlanIngestion):
        def _validate_subtask_references(self):
            for step in self.plan_data.get("plan", []):
                if "file_path" in step:
                    mock_file_open.return_value
                    mock_json_load.return_value = invalid_subtask_content
                    
                    subtask_content = mock_json_load()
                    required_subtask_fields = ["subtask_id", "task_id", "name", "description", "instructions"]
                    for field in required_subtask_fields:
                        if field not in subtask_content:
                            raise PlanValidationError(f"Subtask {step['file_path']} missing field: {field}")

    plan_str = json.dumps(plan_with_subtask_ref)
    with pytest.raises(PlanValidationError, match="Subtask path/to/invalid_subtask.json missing field: name"):
        PlanIngestionWithSubtaskValidation(plan_str)

def test_empty_plan_array():
    plan_content = {
        "task_id": "task-empty-plan",
        "natural_language_goal": "Test empty plan array.",
        "input_hashes": {
            "requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"
        },
        "plan": [] # Empty plan
    }
    plan_str = json.dumps(plan_content)
    ingestion = PlanIngestion(plan_str) # Should not raise error for empty plan array itself
    assert ingestion.get_parsed_plan()["plan"] == []
    assert ingestion.get_task_dependencies() == {}

def test_plan_with_optional_fields_missing():
    plan_content = {
        "task_id": "task-optional",
        "natural_language_goal": "Test optional fields.",
        "input_hashes": {
            "requirements_md": "h1", "config_yaml": "h2", "prompt_file": "h3"
        },
        "plan": [
            {
                "step_id": "step-opt1",
                "description": "Step with minimal agent_spec",
                # depends_on is missing (optional)
                "agent_spec": {
                    "type": "minimal_type",
                    "instructions": ["Minimal instructions"]
                    # input_artifacts, output_artifacts, constraints, validation_criteria are missing (optional)
                }
            }
        ]
    }
    plan_str = json.dumps(plan_content)
    ingestion = PlanIngestion(plan_str) # Should not raise error
    parsed_plan = ingestion.get_parsed_plan()
    assert "depends_on" not in parsed_plan["plan"][0]
    agent_spec = parsed_plan["plan"][0]["agent_spec"]
    assert "input_artifacts" not in agent_spec
    assert "output_artifacts" not in agent_spec
    assert "constraints" not in agent_spec
    assert "validation_criteria" not in agent_spec

# Placeholder for where the actual PlanIngestion and PlanValidationError would be imported from
# from ai_whisperer.plan_ingestion import PlanIngestion, PlanValidationError