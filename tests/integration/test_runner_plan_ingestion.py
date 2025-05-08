import pytest
import json
from unittest.mock import mock_open, patch

# Assume the runner and plan ingestion logic will be structured something like this.
# These are placeholders for the purpose of writing integration tests.

# Placeholder for PlanIngestion from the unit tests, assuming it would be in a similar location
class PlanValidationError(Exception):
    pass

class PlanIngestion:
    def __init__(self, plan_json_content: str):
        try:
            self.plan_data = json.loads(plan_json_content)
        except json.JSONDecodeError as e:
            raise PlanValidationError(f"Malformed JSON: {e}")
        self._validate_plan_structure()
        self._validate_subtask_references()

    def _validate_plan_structure(self):
        required_top_level_fields = ["task_id", "natural_language_goal", "input_hashes", "plan"]
        for field in required_top_level_fields:
            if field not in self.plan_data:
                raise PlanValidationError(f"Missing required top-level field: {field}")

        if not isinstance(self.plan_data["plan"], list):
            raise PlanValidationError("'plan' field must be a list.")

        required_step_fields = ["step_id", "description", "agent_spec"]
        required_agent_spec_fields = ["type", "instructions"]

        for i, step in enumerate(self.plan_data["plan"]):
            for field in required_step_fields:
                if field not in step:
                    raise PlanValidationError(f"Step {i} missing required field: {field}")
            
            agent_spec = step.get("agent_spec", {})
            for field in required_agent_spec_fields:
                if field not in agent_spec:
                    raise PlanValidationError(f"Step {i} agent_spec missing required field: {field}")

            input_hashes = self.plan_data.get("input_hashes", {})
            required_input_hashes_fields = ["requirements_md", "config_yaml", "prompt_file"]
            for field in required_input_hashes_fields:
                if field not in input_hashes:
                    raise PlanValidationError(f"Missing required field in input_hashes: {field}")

    def _validate_subtask_references(self):
        # In a real scenario, this would involve file I/O.
        # For integration tests, we might mock the file system or use temp files.
        # This simplified version assumes subtask data is somehow available or mocked.
        for step in self.plan_data.get("plan", []):
            if "file_path" in step: # Indicates a subtask reference
                # Simulate loading and validating subtask (simplified)
                # This part would be more complex in real integration.
                # Here, we assume if file_path exists, it's a subtask to be "handled".
                # The actual validation of subtask content is unit-tested elsewhere.
                pass


    def get_parsed_plan(self):
        return self.plan_data

    def get_steps(self):
        return self.plan_data.get("plan", [])

# Placeholder for a Runner class
class Runner:
    def __init__(self, plan_file_path: str):
        self.plan_file_path = plan_file_path
        self.plan_ingestion = None
        self.parsed_plan = None

    def load_and_parse_plan(self):
        # In a real runner, this would read the file content
        # For this test, we'll assume the content is passed directly or mocked
        try:
            # Simulating file read for structure
            with open(self.plan_file_path, 'r') as f:
                plan_content_str = f.read()
            self.plan_ingestion = PlanIngestion(plan_content_str)
            self.parsed_plan = self.plan_ingestion.get_parsed_plan()
            return True
        except FileNotFoundError:
            # print(f"Error: Plan file not found at {self.plan_file_path}")
            raise PlanValidationError(f"Plan file not found: {self.plan_file_path}")
        except PlanValidationError as e:
            # print(f"Error validating plan: {e}")
            raise # Re-raise the validation error to be caught by tests
        except Exception as e:
            # print(f"An unexpected error occurred during plan loading: {e}")
            raise PlanValidationError(f"Unexpected error loading plan: {e}")


    def get_executable_steps(self):
        if not self.parsed_plan:
            return []
        # This is a simplified representation. Real step execution would be more complex.
        return self.plan_ingestion.get_steps()

# --- Test Data ---

VALID_PLAN_FOR_RUNNER = {
    "task_id": "runner-task-001",
    "natural_language_goal": "Test runner plan ingestion.",
    "overall_context": "Integration testing context.",
    "input_hashes": {
        "requirements_md": "r_hash",
        "config_yaml": "c_hash",
        "prompt_file": "p_hash"
    },
    "plan": [
        {
            "step_id": "r_step_1",
            "description": "Runner step 1",
            "depends_on": [],
            "agent_spec": {
                "type": "initialization",
                "instructions": ["Initialize system for runner."]
            }
        },
        {
            "step_id": "r_step_2",
            "description": "Runner step 2, references a subtask",
            "file_path": "dummy/subtask_for_runner.json", # Path to a subtask file
            "depends_on": ["r_step_1"],
            "agent_spec": {
                "type": "execute_subtask",
                "instructions": ["Execute the referenced subtask."]
            }
        }
    ]
}

VALID_SUBTASK_FOR_RUNNER = {
    "subtask_id": "runner-subtask-xyz",
    "task_id": "runner-task-001", # Should match parent task_id
    "name": "Subtask for Runner Test",
    "description": "A subtask to be 'executed' by the runner.",
    "instructions": "Perform subtask actions."
}

MALFORMED_JSON_PLAN_STR = '{"task_id": "malformed-01", "plan": [error}'

# --- Integration Test Cases ---

@patch('builtins.open', new_callable=mock_open)
def test_runner_successfully_loads_valid_plan(mock_file):
    plan_content_str = json.dumps(VALID_PLAN_FOR_RUNNER)
    # Configure mock_open to simulate reading the plan file and then subtask files
    # The first call to open is for the main plan.
    # Subsequent calls could be for subtasks if _validate_subtask_references did I/O.
    
    # Side effect for multiple open calls: first for plan, then for subtask
    mock_file.side_effect = [
        mock_open(read_data=plan_content_str).return_value,  # For main plan
        mock_open(read_data=json.dumps(VALID_SUBTASK_FOR_RUNNER)).return_value # For subtask
    ]

    runner = Runner("dummy_plan.json")
    
    # Patch PlanIngestion's _validate_subtask_references to simulate subtask loading
    # This is a bit of a hybrid approach for testing the integration point.
    # A full integration might involve actually creating temp files.
    def mock_validate_subtasks(self_ingestion):
        for step in self_ingestion.plan_data.get("plan", []):
            if "file_path" in step:
                # Simulate opening and "validating" the subtask file
                # This assumes the mock_open is set up to provide subtask content next
                with open(step["file_path"], 'r') as sf: # This call will use the 2nd mock_open
                    subtask_data = json.load(sf)
                # Basic check, real validation is in subtask validator's own tests
                if "subtask_id" not in subtask_data:
                    raise PlanValidationError(f"Mock subtask missing subtask_id: {step['file_path']}")

    with patch.object(PlanIngestion, '_validate_subtask_references', mock_validate_subtasks):
        assert runner.load_and_parse_plan() is True
        assert runner.parsed_plan is not None
        assert runner.parsed_plan["task_id"] == "runner-task-001"
        executable_steps = runner.get_executable_steps()
        assert len(executable_steps) == 2
        assert executable_steps[0]["step_id"] == "r_step_1"
        assert executable_steps[1]["file_path"] == "dummy/subtask_for_runner.json"

    # Check that open was called for the plan and the subtask
    assert mock_file.call_count == 2
    mock_file.assert_any_call("dummy_plan.json", 'r')
    mock_file.assert_any_call("dummy/subtask_for_runner.json", 'r')


@patch('builtins.open', new_callable=mock_open)
def test_runner_handles_malformed_plan_json(mock_file):
    mock_file.return_value = mock_open(read_data=MALFORMED_JSON_PLAN_STR).return_value
    runner = Runner("malformed_plan.json")
    with pytest.raises(PlanValidationError, match="Malformed JSON"):
        runner.load_and_parse_plan()

@patch('builtins.open', new_callable=mock_open)
def test_runner_handles_plan_with_missing_top_level_field(mock_file):
    invalid_plan_data = VALID_PLAN_FOR_RUNNER.copy()
    del invalid_plan_data["task_id"]
    mock_file.return_value = mock_open(read_data=json.dumps(invalid_plan_data)).return_value
    
    runner = Runner("invalid_plan_missing_field.json")
    with pytest.raises(PlanValidationError, match="Missing required top-level field: task_id"):
        runner.load_and_parse_plan()

@patch('builtins.open', new_callable=mock_open)
def test_runner_handles_plan_file_not_found(mock_file):
    mock_file.side_effect = FileNotFoundError("File not found for runner test")
    runner = Runner("non_existent_plan.json")
    with pytest.raises(PlanValidationError, match="Plan file not found: non_existent_plan.json"):
        runner.load_and_parse_plan()


@patch('builtins.open', new_callable=mock_open)
def test_runner_handles_subtask_file_validation_error(mock_file):
    plan_referencing_invalid_subtask = json.loads(json.dumps(VALID_PLAN_FOR_RUNNER)) # deep copy
    
    malformed_subtask_content = '{"subtask_id": "sub-err", "name": "bad json' # malformed

    # First open is for the main plan, second for the subtask file
    mock_file.side_effect = [
        mock_open(read_data=json.dumps(plan_referencing_invalid_subtask)).return_value,
        mock_open(read_data=malformed_subtask_content).return_value 
    ]

    runner = Runner("plan_with_bad_subtask.json")

    # We need to patch the PlanIngestion's subtask validation to simulate the error
    # based on the content of the mocked subtask file.
    def failing_mock_validate_subtasks(self_ingestion):
        for step in self_ingestion.plan_data.get("plan", []):
            if "file_path" in step:
                # This simulates the PlanIngestion trying to load the subtask
                try:
                    with open(step["file_path"], 'r') as sf: # This uses the 2nd mock_open
                        json.load(sf) # This will fail due to malformed_subtask_content
                except json.JSONDecodeError as e:
                    raise PlanValidationError(f"Subtask {step['file_path']} is malformed: {e}")

    with patch.object(PlanIngestion, '_validate_subtask_references', failing_mock_validate_subtasks):
        with pytest.raises(PlanValidationError, match="Subtask dummy/subtask_for_runner.json is malformed"):
            runner.load_and_parse_plan()
    
    assert mock_file.call_count == 2 # plan + subtask attempted


def test_runner_integration_with_empty_plan_array():
    empty_plan_content = {
        "task_id": "runner-empty-002",
        "natural_language_goal": "Test runner with empty plan array.",
        "overall_context": "Integration context for empty plan.",
        "input_hashes": {"requirements_md": "rh", "config_yaml": "ch", "prompt_file": "ph"},
        "plan": []
    }
    plan_str = json.dumps(empty_plan_content)

    with patch('builtins.open', mock_open(read_data=plan_str)) as mock_file_open:
        runner = Runner("empty_plan_for_runner.json")
        assert runner.load_and_parse_plan() is True
        assert runner.parsed_plan["plan"] == []
        assert runner.get_executable_steps() == []
        mock_file_open.assert_called_once_with("empty_plan_for_runner.json", 'r')

# Placeholder for actual imports if these classes were in separate modules
# from ai_whisperer.runner import Runner
# from ai_whisperer.plan_ingestion import PlanIngestion, PlanValidationError