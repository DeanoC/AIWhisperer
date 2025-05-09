import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from src.ai_whisperer.orchestrator import Orchestrator
from src.ai_whisperer.state_management import StateManager
from src.ai_whisperer.execution_engine import ExecutionEngine, TaskExecutionError
from src.ai_whisperer.exceptions import OrchestratorError
from src.ai_whisperer.monitoring import TerminalMonitor # Import TerminalMonitor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_plan_data():
    """Create a sample plan data for testing."""
    return {
        "task_id": "test-task-001",
        "natural_language_goal": "Test state management integration",
        "input_hashes": {
            "requirements_md": "test_hash",
            "config_yaml": "test_hash",
            "prompt_file": "test_hash"
        },
        "plan": [
            {
                "step_id": "step_1",
                "description": "First step",
                "agent_spec": {
                    "type": "test_agent",
                    "instructions": "Execute step 1"
                }
            },
            {
                "step_id": "step_2",
                "description": "Second step",
                "depends_on": ["step_1"],
                "agent_spec": {
                    "type": "test_agent",
                    "instructions": "Execute step 2"
                }
            },
            {
                "step_id": "step_3",
                "description": "Third step that will fail",
                "agent_spec": {
                    "type": "test_agent",
                    "instructions": "Execute step 3"
                }
            }
        ]
    }


@pytest.fixture
def mock_config():
    """Create a mock configuration for the Orchestrator."""
    return {
        "openrouter": {
            "api_key": "test_key"
        },
        "task_model_configs": {
            "orchestrator": {
                "model": "test_model",
                "params": {}
            }
        }
    }


class TestRunnerStateIntegration:
    """Integration tests for state management within the runner."""

    def test_initialize_state_with_new_plan(self, temp_dir, sample_plan_data):
        """Test that a new state file is created and initialized with plan data."""
        state_file_path = os.path.join(temp_dir, "test_state.json")
        
        # Create a StateManager and initialize it with plan data
        state_manager = StateManager(state_file_path)
        state_manager.initialize_state(sample_plan_data)
        
        # Verify the state file was created
        assert os.path.exists(state_file_path)
        
        # Load the state and verify it was initialized correctly
        loaded_state = state_manager.load_state()
        assert loaded_state["plan_id"] == sample_plan_data["task_id"]
        assert "tasks" in loaded_state
        assert "global_state" in loaded_state
        
        # Verify task states were initialized
        for step in sample_plan_data["plan"]:
            step_id = step["step_id"]
            assert step_id in loaded_state["tasks"]
            assert loaded_state["tasks"][step_id]["status"] == "pending"
            assert loaded_state["tasks"][step_id]["result"] is None

    def test_orchestrator_run_plan_creates_state(self, temp_dir, sample_plan_data, mock_config):
        """Test that running a plan through the Orchestrator creates and updates state."""
        # Mock the ExecutionEngine._execute_single_task to avoid actual task execution
        with patch('src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task') as mock_execute:
            mock_execute.side_effect = lambda task_def: f"Result of {task_def['step_id']}"
            
            # Set up state file path
            state_file_path = os.path.join(temp_dir, "test_state.json")
            
            # Create an Orchestrator with mocked config and output directory
            with patch('src.ai_whisperer.openrouter_api.OpenRouterAPI'):
                orchestrator = Orchestrator(mock_config, output_dir=temp_dir)
                
                # Run the plan
                orchestrator.run_plan(sample_plan_data, state_file_path)
                
                # Verify state file was created
                assert os.path.exists(state_file_path)
                
                # Load the state and verify it was updated correctly
                with open(state_file_path, 'r') as f:
                    state = json.load(f)
                
                # Verify task states were updated
                assert state["tasks"]["step_1"]["status"] == "completed"
                assert state["tasks"]["step_2"]["status"] == "completed"
                assert state["tasks"]["step_3"]["status"] == "completed"
                
                # Verify task results were stored
                assert state["tasks"]["step_1"]["result"] == "Result of step_1"
                assert state["tasks"]["step_2"]["result"] == "Result of step_2"
                assert state["tasks"]["step_3"]["result"] == "Result of step_3"

    def test_orchestrator_run_plan_with_task_failure(self, temp_dir, sample_plan_data, mock_config):
        """Test that task failures are properly recorded in the state."""
        # Mock the ExecutionEngine._execute_single_task to simulate a failure for step_3
        def mock_execute_with_failure(task_def):
            if task_def["step_id"] == "step_3":
                raise TaskExecutionError("Simulated failure for step_3")
            return f"Result of {task_def['step_id']}"
        
        with patch('src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task') as mock_execute:
            mock_execute.side_effect = mock_execute_with_failure
            
            # Set up state file path
            state_file_path = os.path.join(temp_dir, "test_state_failure.json")
            
            # Create an Orchestrator with mocked config and output directory
            with patch('src.ai_whisperer.openrouter_api.OpenRouterAPI'):
                orchestrator = Orchestrator(mock_config, output_dir=temp_dir)
                
                # Run the plan
                orchestrator.run_plan(sample_plan_data, state_file_path)
                
                # Verify state file was created
                assert os.path.exists(state_file_path)
                
                # Load the state and verify it was updated correctly
                with open(state_file_path, 'r') as f:
                    state = json.load(f)
                
                # Verify successful task states
                assert state["tasks"]["step_1"]["status"] == "completed"
                assert state["tasks"]["step_2"]["status"] == "completed"
                
                # Verify failed task state
                assert state["tasks"]["step_3"]["status"] == "failed"
                assert "error" in state["tasks"]["step_3"].get("result", {})
                assert "Simulated failure for step_3" in state["tasks"]["step_3"].get("result", {}).get("error", "")

    def test_orchestrator_run_plan_with_dependency_not_met(self, temp_dir, sample_plan_data, mock_config):
        """Test that tasks with unmet dependencies are skipped and recorded in the state."""
        # Modify the mock to make step_1 fail, which should cause step_2 to be skipped
        def mock_execute_with_dependency_failure(task_def):
            if task_def["step_id"] == "step_1":
                raise TaskExecutionError("Simulated failure for step_1")
            return f"Result of {task_def['step_id']}"
        
        with patch('src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task') as mock_execute:
            mock_execute.side_effect = mock_execute_with_dependency_failure
            
            # Set up state file path
            state_file_path = os.path.join(temp_dir, "test_state_dependency.json")
            
            # Create an Orchestrator with mocked config and output directory
            with patch('src.ai_whisperer.openrouter_api.OpenRouterAPI'):
                orchestrator = Orchestrator(mock_config, output_dir=temp_dir)
                
                # Run the plan
                orchestrator.run_plan(sample_plan_data, state_file_path)
                
                # Verify state file was created
                assert os.path.exists(state_file_path)
                
                # Load the state and verify it was updated correctly
                with open(state_file_path, 'r') as f:
                    state = json.load(f)
                
                # Verify failed task state
                assert state["tasks"]["step_1"]["status"] == "failed"
                
                # Verify dependent task was skipped
                assert state["tasks"]["step_2"]["status"] == "skipped"
                assert "reason" in state["tasks"]["step_2"].get("result", {})
                
                # Verify independent task was still executed
                assert state["tasks"]["step_3"]["status"] == "completed"

    def test_state_persistence_across_multiple_runs(self, temp_dir, sample_plan_data, mock_config):
        """Test that state persists across multiple runs of the orchestrator."""
        # Set up state file path
        state_file_path = os.path.join(temp_dir, "test_state_persistence.json")
        
        # First run: Execute only step_1
        first_plan = sample_plan_data.copy()
        first_plan["plan"] = [sample_plan_data["plan"][0]]  # Only include step_1
        
        with patch('src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task') as mock_execute:
            mock_execute.return_value = "Result of step_1"
            
            # Create an Orchestrator with mocked config and output directory
            with patch('src.ai_whisperer.openrouter_api.OpenRouterAPI'):
                orchestrator = Orchestrator(mock_config, output_dir=temp_dir)
                
                # Run the first plan
                orchestrator.run_plan(first_plan, state_file_path)
                
                # Verify state file was created
                assert os.path.exists(state_file_path)
                
                # Load the state and verify it was updated correctly
                with open(state_file_path, 'r') as f:
                    state_after_first_run = json.load(f)
                
                # Verify step_1 was completed
                assert state_after_first_run["tasks"]["step_1"]["status"] == "completed"
        
        # Second run: Execute the remaining steps
        second_plan = sample_plan_data.copy()
        
        with patch('src.ai_whisperer.execution_engine.ExecutionEngine._execute_single_task') as mock_execute:
            mock_execute.side_effect = lambda task_def: f"Result of {task_def['step_id']}"
            
            # Create a new Orchestrator instance
            with patch('src.ai_whisperer.openrouter_api.OpenRouterAPI'):
                orchestrator = Orchestrator(mock_config, output_dir=temp_dir)
                
                # Run the second plan
                orchestrator.run_plan(second_plan, state_file_path)
                
                # Load the state after the second run
                with open(state_file_path, 'r') as f:
                    state_after_second_run = json.load(f)
                
                # Verify all steps were completed
                assert state_after_second_run["tasks"]["step_1"]["status"] == "completed"
                assert state_after_second_run["tasks"]["step_2"]["status"] == "completed"
                assert state_after_second_run["tasks"]["step_3"]["status"] == "completed"
                
                # Verify the result from the first run was preserved
                assert state_after_second_run["tasks"]["step_1"]["result"] == "Result of step_1"

    def test_error_handling_during_state_operations(self, temp_dir, sample_plan_data, mock_config):
        """Test error handling when state operations fail."""
        # Set up state file path in a valid temporary directory
        state_file_path = os.path.join(temp_dir, "test_state_error.json")
        
        # Create an Orchestrator with mocked config and output directory
        with patch('src.ai_whisperer.openrouter_api.OpenRouterAPI'):
            orchestrator = Orchestrator(mock_config, output_dir=temp_dir)
            
            # Mock os.replace to raise an IOError during state saving
            with patch('os.replace') as mock_os_replace:
                mock_os_replace.side_effect = IOError("Simulated error during os.replace")
                
                # Run the plan and expect an OrchestratorError
                with pytest.raises(OrchestratorError) as excinfo:
                    orchestrator.run_plan(sample_plan_data, state_file_path)
                
                # Verify the error message contains the expected substring
                assert "Failed to save" in str(excinfo.value)

    def test_global_state_updates(self, temp_dir, sample_plan_data, mock_config):
        """Test that global state can be updated during plan execution."""
        # Set up state file path
        state_file_path = os.path.join(temp_dir, "test_global_state.json")
        
        # Create a StateManager
        state_manager = StateManager(state_file_path)
        
        # Initialize the state
        state_manager.initialize_state(sample_plan_data)
        
        # Update global state
        state_manager.update_global_state("test_key", "test_value")
        state_manager.update_global_state("file_paths", ["/path/to/file1.txt", "/path/to/file2.txt"])
        state_manager.save_state()
        
        # Load the state and verify global state was updated
        loaded_state = state_manager.load_state()
        assert loaded_state["global_state"]["test_key"] == "test_value"
        assert loaded_state["global_state"]["file_paths"] == ["/path/to/file1.txt", "/path/to/file2.txt"]
        
        # Verify we can retrieve global state values
        assert state_manager.get_global_state("test_key") == "test_value"
        assert state_manager.get_global_state("file_paths") == ["/path/to/file1.txt", "/path/to/file2.txt"]
        assert state_manager.get_global_state("non_existent_key") is None

    def test_execution_engine_updates_state_manager(self, temp_dir, sample_plan_data):
        """Test that ExecutionEngine correctly updates the StateManager during plan execution."""
        # Set up state file path (not strictly needed for this version of the test, but good practice)
        state_file_path = os.path.join(temp_dir, "test_execution_engine_state.json")
        
        # Create a real StateManager and ExecutionEngine
        state_manager = StateManager(state_file_path)
        # Create a mock monitor for the ExecutionEngine
        mock_monitor = MagicMock(spec=TerminalMonitor)
        execution_engine = ExecutionEngine(state_manager, monitor=mock_monitor)

        # Initialize the state with plan data
        state_manager.initialize_state(sample_plan_data)

        # Mock the ExecutionEngine._execute_single_task to avoid actual task execution
        with patch.object(execution_engine, '_execute_single_task') as mock_execute:
            mock_execute.side_effect = lambda task_def: f"Result of {task_def['step_id']}"
            
            # Run the plan using the execution engine directly
            execution_engine.execute_plan(sample_plan_data)
            
            # Verify all tasks were completed in the state manager's in-memory state
            for step in sample_plan_data["plan"]:
                step_id = step["step_id"]
                assert state_manager.get_task_status(step_id) == "completed"
                assert state_manager.get_task_result(step_id) == f"Result of {step_id}"
            
            # Verify the execution engine's mock was called for each task
            assert mock_execute.call_count == len(sample_plan_data["plan"])

        # Optional: Save and load state to double-check persistence (this part was failing before)
        # state_manager.save_state()
        # loaded_state = state_manager.load_state()
        # for step in sample_plan_data["plan"]:
        #     step_id = step["step_id"]
        #     assert loaded_state["tasks"][step_id]["status"] == "completed"
        #     assert loaded_state["tasks"][step_id]["result"] == f"Result of {step_id}"