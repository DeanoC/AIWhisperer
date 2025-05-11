import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

# from src.ai_whisperer.orchestrator import Orchestrator
from src.ai_whisperer.state_management import StateManager
from src.ai_whisperer.execution_engine import ExecutionEngine, TaskExecutionError
from src.ai_whisperer.exceptions import OrchestratorError
from src.ai_whisperer.monitoring import TerminalMonitor  # Import TerminalMonitor
from src.ai_whisperer.plan_parser import ParserPlan


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_overview_plan_data():
    """Create a sample plan data for testing."""
    return {
        "task_id": "test-task-001",
        "natural_language_goal": "Test state management integration",
        "input_hashes": {"requirements_md": "test_hash", "config_yaml": "test_hash", "prompt_file": "test_hash"},
        "plan": [
            {
                "subtask_id": "step_1",
                "file_path": "path/to/step_1.json",
                "description": "First step",
            },
            {
                "subtask_id": "step_2",
                "file_path": "path/to/step_2.json",
                "description": "Second step",
            },
            {
                "subtask_id": "step_3",
                "file_path": "path/to/step_3.json",
                "description": "Third step that will fail",
            },
        ],
    }


@pytest.fixture
def mock_config():
    """Create a mock configuration for the Orchestrator."""
    return {
        "openrouter": {"api_key": "test_key", "model": "test_model"},
        "task_model_configs": {"orchestrator": {"model": "test_model", "params": {}}},
    }


class TestRunnerStateIntegration:
    """Integration tests for state management within the runner."""

    def test_initialize_state_with_new_plan(self, temp_dir, sample_overview_plan_data):
        """Test that a new state file is created and initialized with plan data."""
        state_file_path = os.path.join(temp_dir, "test_state.json")

        # Create a temporary directory for the subtasks
        subtask_dir = os.path.join(temp_dir, "subtasks")
        os.makedirs(subtask_dir)

        # Create individual subtask JSON files that conform to the subtask schema
        for subtask in sample_overview_plan_data["plan"]:
            subtask_filepath = os.path.join(subtask_dir, f"{subtask['subtask_id']}.json")
            subtask_data = {
                "description": subtask["description"],
                "instructions": ["Follow the instructions for this subtask."],
                "input_artifacts": ["artifact1", "artifact2"],
                "output_artifacts": ["output1", "output2"],
                "constraints": ["Constraint 1", "Constraint 2"],
                "validation_criteria": ["Validation 1", "Validation 2"],
                "subtask_id": subtask["subtask_id"],
                "task_id": sample_overview_plan_data["task_id"],
                "type": "no_op"  # Ensure type is set to "no_op"
            }
            with open(subtask_filepath, "w") as f:
                json.dump(subtask_data, f)
            subtask["file_path"] = subtask_filepath  # Update the file_path in the plan

        # Create a StateManager and initialize it with plan data
        state_manager = StateManager(state_file_path)
        state_manager.initialize_state(sample_overview_plan_data)

        # Verify the state file was created
        assert os.path.exists(state_file_path)

        # Load the state and verify it was initialized correctly
        loaded_state = state_manager.load_state()
        assert loaded_state["plan_id"] == sample_overview_plan_data["task_id"]
        assert "tasks" in loaded_state
        assert "global_state" in loaded_state

        # Verify task states were initialized
        for step in sample_overview_plan_data["plan"]:
            subtask_id = step["subtask_id"]
            assert subtask_id in loaded_state["tasks"]
            assert loaded_state["tasks"][subtask_id]["status"] == "pending"
            assert loaded_state["tasks"][subtask_id]["result"] is None

    def test_orchestrator_run_plan_creates_state_with_overview(self, temp_dir, sample_overview_plan_data, mock_config):
        """Test that running a plan through the Orchestrator creates and updates state using an overview plan."""
        # Create a temporary directory for the overview plan and subtasks
        overview_dir = os.path.join(temp_dir, "overview_plan")
        os.makedirs(overview_dir)

        # Create the overview JSON file
        overview_data = {
            "task_id": sample_overview_plan_data["task_id"],
            "natural_language_goal": sample_overview_plan_data["natural_language_goal"],
            "input_hashes": {
                "requirements_md": sample_overview_plan_data["input_hashes"].get("requirements_md"),
                "config_yaml": sample_overview_plan_data["input_hashes"].get("config_yaml"),
                "prompt_file": sample_overview_plan_data["input_hashes"].get("prompt_file")
            },
            "plan": []  # This will be populated with paths to subtask files
        }

        # Create individual subtask JSON files that conform to the subtask schema
        for subtask_data in sample_overview_plan_data["plan"]:
            subtask_filename = f"subtask_{subtask_data['subtask_id']}.json"
            subtask_filepath = os.path.join(overview_dir, subtask_filename)

            subtask_content = {
                "description": subtask_data["description"],
                "instructions": ["Follow the instructions for this subtask."],
                "input_artifacts": ["artifact1", "artifact2"],
                "output_artifacts": ["output1", "output2"],
                "constraints": ["Constraint 1", "Constraint 2"],
                "validation_criteria": ["Validation 1", "Validation 2"],
                "subtask_id": subtask_data["subtask_id"],
                "task_id": sample_overview_plan_data["task_id"],
                "type": "no_op"  # Ensure type is set to "no_op"
            }

            with open(subtask_filepath, "w") as f:
                json.dump(subtask_content, f)

            overview_data["plan"].append({
                "subtask_id": subtask_data["subtask_id"],
                "file_path": subtask_filename,
                "type": "no_op"  # Ensure type is set to "no_op"
            })

        # Write the overview JSON file
        overview_filepath = os.path.join(overview_dir, "overview.json")
        with open(overview_filepath, "w") as f:
            json.dump(overview_data, f, indent=4)

        # Set up state file path
        state_file_path = os.path.join(temp_dir, "test_state.json")

        # Create an Orchestrator with mocked config and output directory
        with patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI"):
            orchestrator = Orchestrator(mock_config, output_dir=temp_dir)

            # Create a ParserPlan instance and load the overview plan
            parser = ParserPlan()
            parser.load_overview_plan(overview_filepath)

            # Run the plan with the parser
            orchestrator.run_plan(parser, state_file_path)

            # Verify state file was created
            assert os.path.exists(state_file_path)

            # Load the state after the run and verify it was updated correctly
            state_manager_after_run = StateManager(state_file_path)
            state = state_manager_after_run.load_state()

            # Verify task states were updated (ExecutionEngine should handle this)
            assert state["tasks"]["step_1"]["status"] == "completed"
            assert state["tasks"]["step_2"]["status"] == "completed"
            assert state["tasks"]["step_3"]["status"] == "completed"

    def test_orchestrator_run_plan_with_task_failure_overview(self, temp_dir, sample_overview_plan_data, mock_config):
        """Test that running a plan with a failing task through the Orchestrator records failure in state using an overview plan."""
        # Create a temporary directory for the overview plan and subtasks
        overview_dir = os.path.join(temp_dir, "overview_plan_failure")
        os.makedirs(overview_dir)

        # Create the overview JSON file
        overview_data = {
            "task_id": sample_overview_plan_data["task_id"],
            "natural_language_goal": sample_overview_plan_data["natural_language_goal"],
            "input_hashes": sample_overview_plan_data["input_hashes"],
            "plan": [],  # This will be populated with paths to subtask files
        }

        # Create individual subtask JSON files that conform to the subtask schema
        for subtask_data in sample_overview_plan_data["plan"]:
            subtask_filename = f"subtask_{subtask_data['subtask_id']}.json"
            subtask_filepath = os.path.join(overview_dir, subtask_filename)

            subtask_content = {
                "description": subtask_data["description"],
                "instructions": ["Follow the instructions for this subtask."],
                "input_artifacts": ["artifact1", "artifact2"],
                "output_artifacts": ["output1", "output2"],
                "constraints": ["Constraint 1", "Constraint 2"],
                "validation_criteria": ["Validation 1", "Validation 2"],
                "subtask_id": subtask_data["subtask_id"],
                "task_id": sample_overview_plan_data["task_id"],
                "type": "no_op"  # Ensure type is set to "no_op"
            }

            with open(subtask_filepath, "w") as f:
                json.dump(subtask_content, f)

            overview_data["plan"].append({
                "subtask_id": subtask_data["subtask_id"],
                "file_path": subtask_filename,
                "type": "no_op"  # Ensure type is set to "no_op"
            })

        # Write the overview JSON file
        overview_filepath = os.path.join(overview_dir, "overview.json")
        with open(overview_filepath, "w") as f:
            json.dump(overview_data, f)

        # Set up state file path
        state_file_path = os.path.join(temp_dir, "test_state_failure.json")

        # Mock the ExecutionEngine._execute_single_task to simulate a failure for step_3
        # We need to mock this because the real ExecutionEngine would try to execute the task.
        with patch("src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task") as mock_execute:

            def side_effect_with_failure(task_def):
                task_id = task_def["subtask_id"]
                if task_id == "step_3":
                    error_message = "Simulated failure for step_3"
                    # In a real scenario, ExecutionEngine would update state to failed
                    # We simulate that here by raising the exception that ExecutionEngine catches
                    raise TaskExecutionError(error_message)
                else:
                    # Simulate successful execution for other tasks
                    return {"result": f"Result of {task_id}"}

            mock_execute.side_effect = side_effect_with_failure

            # Create an Orchestrator with mocked config and output directory
            with patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI"):
                orchestrator = Orchestrator(mock_config, output_dir=temp_dir)

                # Create a ParserPlan instance and load the overview plan
                parser = ParserPlan()
                parser.load_overview_plan(overview_filepath)

                # Run the plan with the parser
                orchestrator.run_plan(parser, state_file_path)

                # Verify state file was created
                assert os.path.exists(state_file_path)

                # Load the state after the run and verify it was updated correctly
                state_manager_after_run = StateManager(state_file_path)
                state = state_manager_after_run.load_state()

                # Verify successful task states
                assert state["tasks"]["step_1"]["status"] == "completed"
                assert state["tasks"]["step_2"]["status"] == "completed"

                # Verify failed task state
                assert state["tasks"]["step_3"]["status"] == "failed"
                assert "error" in state["tasks"]["step_3"].get("result", {})
                assert "Simulated failure for step_3" in state["tasks"]["step_3"].get("result", {}).get("error", "")

    def test_state_persistence_across_multiple_runs_overview(self, temp_dir, sample_overview_plan_data, mock_config):
        """Test that state persists across multiple runs of the Orchestrator using an overview plan."""
        state_file_path = os.path.join(temp_dir, "test_state_persistence.json")

        # Create a temporary directory for the overview plan and subtasks for the first run
        overview_dir_1 = os.path.join(temp_dir, "overview_plan_run_1")
        os.makedirs(overview_dir_1)

        # Create the overview JSON file for the first run (only step_1)
        first_plan_data = sample_overview_plan_data.copy()
        first_plan_data["plan"] = [sample_overview_plan_data["plan"][0]]  # Only include step_1

        overview_data_1 = {
            "task_id": first_plan_data["task_id"],
            "natural_language_goal": first_plan_data["natural_language_goal"],
            "input_hashes": first_plan_data["input_hashes"],
            "plan": [],
        }

        subtask_filename_1 = f"subtask_{first_plan_data["plan"][0]["subtask_id"]}.json"
        subtask_filepath_1 = os.path.join(overview_dir_1, subtask_filename_1)
        subtask_content_1 = {
            "description": first_plan_data["plan"][0]["description"],
            "instructions": ["Follow the instructions for this subtask."],
            "input_artifacts": ["artifact1", "artifact2"],
            "output_artifacts": ["output1", "output2"],
            "constraints": ["Constraint 1", "Constraint 2"],
            "validation_criteria": ["Validation 1", "Validation 2"],
            "subtask_id": first_plan_data["plan"][0]["subtask_id"],
            "task_id": first_plan_data["task_id"],
            "type": "no_op"  # Ensure type is set to "no_op"
        }
        with open(subtask_filepath_1, "w") as f:
            json.dump(subtask_content_1, f)

        overview_data_1["plan"].append({
            "subtask_id": first_plan_data["plan"][0]["subtask_id"],
            "file_path": subtask_filepath_1,  # Use absolute path as required by schema
            "type": "no_op"  # Ensure type is set to "no_op"
        })

        overview_filepath_1 = os.path.join(overview_dir_1, "overview.json")
        with open(overview_filepath_1, "w") as f:
            json.dump(overview_data_1, f)

        # Use ParserPlan for loading and validation
        parser_1 = ParserPlan()
        parser_1.load_overview_plan(overview_filepath_1)

        # Mock the ExecutionEngine._execute_single_task for the first run
        with patch("src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task") as mock_execute_1:
            mock_execute_1.side_effect = lambda task_def: f"Result of {task_def["subtask_id"]}"

            # Create an Orchestrator for the first run
            with patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI"):
                orchestrator_1 = Orchestrator(mock_config, output_dir=temp_dir)

                # Run the plan
                orchestrator_1.run_plan(parser_1, state_file_path)

                # Verify state file was created
                assert os.path.exists(state_file_path)

                # Load the state after the first run
                state_manager_after_first_run = StateManager(state_file_path)
                state_after_first_run = state_manager_after_first_run.load_state()

                # Verify step_1 was completed
                assert state_after_first_run["tasks"]["step_1"]["status"] == "completed"
                assert state_after_first_run["tasks"]["step_1"]["result"] == "Result of step_1"

        # Second run: Execute the remaining steps
        # Create a temporary directory for the overview plan and subtasks for the second run
        overview_dir_2 = os.path.join(temp_dir, "overview_plan_run_2")
        os.makedirs(overview_dir_2)

        second_plan_data = sample_overview_plan_data.copy()

        overview_data_2 = {
            "task_id": second_plan_data["task_id"],
            "natural_language_goal": second_plan_data["natural_language_goal"],
            "input_hashes": second_plan_data["input_hashes"],
            "plan": [],
        }

        # Create individual subtask JSON files for the second run
        for subtask_data in second_plan_data["plan"]:
            subtask_filename = f"subtask_{subtask_data["subtask_id"]}.json"
            subtask_filepath = os.path.join(overview_dir_2, subtask_filename)
            subtask_content = {
                "description": subtask_data["description"],
                "instructions": ["Follow the instructions for this subtask."],
                "input_artifacts": ["artifact1", "artifact2"],
                "output_artifacts": ["output1", "output2"],
                "constraints": ["Constraint 1", "Constraint 2"],
                "validation_criteria": ["Validation 1", "Validation 2"],
                "subtask_id": subtask_data["subtask_id"],
                "task_id": second_plan_data["task_id"],
                "type": "no_op"  # Ensure type is set to "no_op"
            }
            with open(subtask_filepath, "w") as f:
                json.dump(subtask_content, f)

            # Append the absolute path to the overview plan
            overview_data_2["plan"].append({
                "subtask_id": subtask_data["subtask_id"],
                "file_path": subtask_filepath,  # Use absolute path as required by schema
                "type": "no_op"  # Ensure type is set to "no_op"
            })

        overview_filepath_2 = os.path.join(overview_dir_2, "overview.json")
        with open(overview_filepath_2, "w") as f:
            json.dump(overview_data_2, f)

        # Use ParserPlan for loading and validation
        parser_2 = ParserPlan()
        parser_2.load_overview_plan(overview_filepath_2)

        # Mock the ExecutionEngine._execute_single_task for the second run
        with patch("src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task") as mock_execute_2:
            mock_execute_2.side_effect = lambda task_def: f"Result of {task_def["subtask_id"]}"

            # Create a new Orchestrator instance for the second run, loading the existing state
            with patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI"):
                orchestrator_2 = Orchestrator(mock_config, output_dir=temp_dir)

                # Run the plan with the parser
                orchestrator_2.run_plan(parser_2, state_file_path)

        # Load the state after the second run
        state_manager_after_second_run = StateManager(state_file_path)
        state_after_second_run = state_manager_after_second_run.load_state()

        # Verify all steps were completed
        assert state_after_second_run["tasks"]["step_1"]["status"] == "completed"
        assert state_after_second_run["tasks"]["step_2"]["status"] == "completed"
        assert state_after_second_run["tasks"]["step_3"]["status"] == "completed"

        # Verify the result from the first run was preserved
        assert state_after_second_run["tasks"]["step_1"]["result"] == "Result of step_1"

    def test_orchestrator_run_plan_state_save_error_handling_overview(self, temp_dir, sample_overview_plan_data, mock_config):
        """Test that Orchestrator correctly handles state save errors during plan execution using an overview plan."""
        # Create a temporary directory for the overview plan and subtasks
        overview_dir = os.path.join(temp_dir, "overview_plan_save_error")
        os.makedirs(overview_dir)

        # Create the overview JSON file
        overview_data = {
            "task_id": sample_overview_plan_data["task_id"],
            "natural_language_goal": sample_overview_plan_data["natural_language_goal"],
            "input_hashes": sample_overview_plan_data["input_hashes"],
            "plan": [],  # This will be populated with paths to subtask files
        }

        # Create individual subtask JSON files that conform to the subtask schema
        for subtask_data in sample_overview_plan_data["plan"]:
            subtask_filename = f"subtask_{subtask_data["subtask_id"]}.json"
            subtask_filepath = os.path.join(overview_dir, subtask_filename)

            subtask_content = {
                "description": subtask_data["description"],
                "instructions": ["Follow the instructions for this subtask."],
                "input_artifacts": ["artifact1", "artifact2"],
                "output_artifacts": ["output1", "output2"],
                "constraints": ["Constraint 1", "Constraint 2"],
                "validation_criteria": ["Validation 1", "Validation 2"],
                "subtask_id": subtask_data["subtask_id"],
                "task_id": sample_overview_plan_data["task_id"],
                "type": "no_op"  # Ensure type is set to "no_op"
            }

            with open(subtask_filepath, "w") as f:
                json.dump(subtask_content, f)

            overview_data["plan"].append({
                "subtask_id": subtask_data["subtask_id"],
                "file_path": subtask_filename,
                "type": "no_op"  # Ensure type is set to "no_op"
            })

        # Write the overview JSON file
        overview_filepath = os.path.join(overview_dir, "overview.json")
        with open(overview_filepath, "w") as f:
            json.dump(overview_data, f)

        # Set up state file path
        state_file_path = os.path.join(temp_dir, "test_state_save_error.json")

        # Mock os.replace to raise an IOError during state saving
        with patch("os.replace") as mock_os_replace:
            mock_os_replace.side_effect = IOError("Simulated error during os.replace")

            # Create an Orchestrator with mocked config and output directory
            with patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI"):
                orchestrator = Orchestrator(mock_config, output_dir=temp_dir)

                # Create a ParserPlan instance and load the overview plan
                parser = ParserPlan()
                parser.load_overview_plan(overview_filepath)

                # Run the plan and expect an OrchestratorError due to save failure
                with pytest.raises(OrchestratorError) as excinfo:
                    orchestrator.run_plan(parser, state_file_path)

                # Verify the error message contains the expected substring
                assert "Failed to save" in str(excinfo.value)
                assert "Simulated error during os.replace" in str(excinfo.value)

    def test_global_state_updates(self, temp_dir, sample_overview_plan_data):
        """Test that global state can be updated in the StateManager."""
        state_file_path = os.path.join(temp_dir, "test_global_state.json")

        # Create a StateManager
        state_manager = StateManager(state_file_path)

        # Initialize the state
        state_manager.initialize_state(sample_overview_plan_data)

        # Update global state
        state_manager.update_global_state("test_key", "test_value")
        state_manager.update_global_state("file_paths", ["/path/to/file1.txt", "/path/to/file2.txt"])
        state_manager.save_state()

        # Load the state and verify global state was updated
        loaded_state = state_manager.load_state()
        assert loaded_state["global_state"]["test_key"] == "test_value"
        assert loaded_state["global_state"]["file_paths"] == ["/path/to/file1.txt", "/path/to/file2.txt"]
        assert state_manager.get_global_state("non_existent_key") is None

    def test_execution_engine_updates_state_manager_overview(self, temp_dir, sample_overview_plan_data, mock_config):
        """Test that ExecutionEngine correctly updates the StateManager during plan execution using an overview plan."""
        state_file_path = os.path.join(temp_dir, "test_execution_engine_state.json")

        # Create a temporary directory for the overview plan and subtasks
        overview_dir = os.path.join(temp_dir, "overview_plan_ee")
        os.makedirs(overview_dir)

        # Create the overview JSON file
        overview_data = {
            "task_id": sample_overview_plan_data["task_id"],
            "natural_language_goal": sample_overview_plan_data["natural_language_goal"],
            "input_hashes": sample_overview_plan_data["input_hashes"],
            "plan": [],  # This will be populated with paths to subtask files
        }

        # Create individual subtask JSON files that conform to the subtask schema
        for subtask_data in sample_overview_plan_data["plan"]:
            subtask_filename = f"subtask_{subtask_data['subtask_id']}.json"
            subtask_filepath = os.path.join(overview_dir, subtask_filename)

            subtask_content = {
                "description": subtask_data["description"],
                "instructions": ["Follow the instructions for this subtask."],
                "input_artifacts": ["artifact1", "artifact2"],
                "output_artifacts": ["output1", "output2"],
                "constraints": ["Constraint 1", "Constraint 2"],
                "validation_criteria": ["Validation 1", "Validation 2"],
                "subtask_id": subtask_data["subtask_id"],
                "task_id": sample_overview_plan_data["task_id"],
                "type": "no_op"  # Ensure type is set to "no_op"
            }

            with open(subtask_filepath, "w") as f:
                json.dump(subtask_content, f)

            overview_data["plan"].append({
                "subtask_id": subtask_data["subtask_id"],
                "file_path": subtask_filename,
                "type": "no_op"  # Ensure type is set to "no_op"
            })

        # Write the overview JSON file
        overview_filepath = os.path.join(overview_dir, "overview.json")
        with open(overview_filepath, "w") as f:
            json.dump(overview_data, f)

        # Create a real StateManager and ExecutionEngine
        state_manager = StateManager(state_file_path)
        mock_monitor = MagicMock(spec=TerminalMonitor)
        execution_engine = ExecutionEngine(state_manager, monitor=mock_monitor, config=mock_config)

        # Mock the ExecutionEngine._execute_single_task to simulate task completion
        # We need to mock this because the real ExecutionEngine would try to execute the task.
        with patch.object(execution_engine, "_execute_single_task") as mock_execute:
            mock_execute.side_effect = lambda task_def: {"result": f"Result of {task_def['subtask_id']}"}

            # Create a ParserPlan instance and load the overview plan
            parser = ParserPlan()
            parser.load_overview_plan(overview_filepath)

            # Execute the plan using the execution engine
            execution_engine.execute_plan(parser)

            # Verify the execution engine's mock was called for each task
            assert mock_execute.call_count == len(sample_overview_plan_data["plan"])

        # Load the state after execution and verify it was updated correctly
        state_manager_after_run = StateManager(state_file_path)
        state = state_manager_after_run.load_state()

        # Verify all tasks were completed in the state manager's in-memory state
        for step in sample_overview_plan_data["plan"]:
            subtask_id = step["subtask_id"]
            assert state["tasks"][subtask_id]["status"] == "completed"
            assert state["tasks"][subtask_id]["result"] is not None  # Check that result is stored
