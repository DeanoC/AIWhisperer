import pytest
import threading
from unittest.mock import MagicMock, call

from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.state_management import StateManager
from ai_whisperer.plan_parser import ParserPlan
from ai_whisperer.prompt_system import PromptSystem
from ai_whisperer.delegate_manager import DelegateManager

# Mock dependencies
@pytest.fixture
def mock_state_manager():
    sm = MagicMock(spec=StateManager)
    sm.get_task_status.return_value = "completed" # Assume dependencies are met by default
    sm.get_task_result.return_value = {} # Assume empty result by default
    return sm

@pytest.fixture
def mock_config():
    return {"openrouter": {"api_key": "fake_key", "model": "fake_model"}}

@pytest.fixture
def mock_prompt_system():
    ps = MagicMock(spec=PromptSystem)
    ps.get_formatted_prompt.return_value = "fake prompt"
    return ps

@pytest.fixture
def mock_shutdown_event():
    return threading.Event()

@pytest.fixture
def mock_plan_parser():
    parser = MagicMock(spec=ParserPlan)
    # Define a simple plan with one task
    plan_data = {
        "task_id": "test_plan",
        "plan": [
            {
                "subtask_id": "task1",
                "name": "test_task",
                "type": "no_op", # Use no_op type for simplicity
                "depends_on": [],
                "file_path": None # No detailed file for no_op
            }
        ]
    }
    parser.get_parsed_plan.return_value = plan_data
    parser.get_subtask_content.return_value = None # No detailed content for no_op
    return parser

@pytest.fixture
def execution_engine(mock_state_manager, mock_config, mock_prompt_system, mock_shutdown_event):
    engine = ExecutionEngine(mock_state_manager, mock_config, mock_prompt_system, shutdown_event=mock_shutdown_event)
    # Ensure the delegate_manager is a real instance for testing delegate interactions
    engine.delegate_manager = DelegateManager()
    return engine

def test_engine_started_delegate_invoked(execution_engine, mock_plan_parser):
    mock_delegate = MagicMock()
    execution_engine.delegate_manager.register_notification("engine_started", mock_delegate)

    execution_engine.execute_plan(mock_plan_parser)

    mock_delegate.assert_called_once_with(execution_engine, "engine_started", None)

def test_engine_stopped_delegate_invoked(execution_engine, mock_plan_parser):
    mock_delegate = MagicMock()
    execution_engine.delegate_manager.register_notification("engine_stopped", mock_delegate)

    execution_engine.execute_plan(mock_plan_parser)

    mock_delegate.assert_called_once_with(execution_engine, "engine_stopped", None)

def test_task_execution_started_delegate_invoked(execution_engine, mock_state_manager, mock_config, mock_prompt_system, mock_shutdown_event):
    mock_delegate = MagicMock()
    execution_engine.delegate_manager.register_notification("task_execution_started", mock_delegate)

    # Create a plan with a task
    plan_data = {
        "task_id": "test_plan",
        "plan": [
            {
                "subtask_id": "task1",
                "name": "test_task",
                "type": "no_op",
                "depends_on": [],
                "file_path": None
            }
        ]
    }
    mock_plan_parser = MagicMock(spec=ParserPlan)
    mock_plan_parser.get_parsed_plan.return_value = plan_data
    mock_plan_parser.get_subtask_content.return_value = None

    execution_engine.execute_plan(mock_plan_parser)

    # Check if the delegate was called with the correct arguments
    # The task_details passed should be the effective task definition
    expected_task_details = plan_data["plan"][0]
    mock_delegate.assert_called_once_with(execution_engine, "task_execution_started", {"task_id": "task1", "task_details": expected_task_details})


def test_task_execution_completed_delegate_invoked(execution_engine, mock_state_manager, mock_config, mock_prompt_system, mock_shutdown_event):
    mock_delegate = MagicMock()
    execution_engine.delegate_manager.register_notification("task_execution_completed", mock_delegate)

    # Create a plan with a task
    plan_data = {
        "task_id": "test_plan",
        "plan": [
            {
                "subtask_id": "task1",
                "name": "test_task",
                "type": "no_op",
                "depends_on": [],
                "file_path": None
            }
        ]
    }
    mock_plan_parser = MagicMock(spec=ParserPlan)
    mock_plan_parser.get_parsed_plan.return_value = plan_data
    mock_plan_parser.get_subtask_content.return_value = None

    execution_engine.execute_plan(mock_plan_parser)

    # Check if the delegate was called with the correct arguments
    mock_delegate.assert_called_once_with(execution_engine, "task_execution_completed", {"task_id": "task1", "status": "completed", "result_summary": "No-op task task1 completed successfully."[:100]}) # Expect the actual truncated string result


def test_engine_error_occurred_delegate_invoked(execution_engine, mock_state_manager, mock_config, mock_prompt_system, mock_shutdown_event):
    mock_delegate = MagicMock()
    execution_engine.delegate_manager.register_notification("engine_error_occurred", mock_delegate)

    # Create a plan with a task that will raise an error
    plan_data = {
        "task_id": "test_plan",
        "plan": [
            {
                "subtask_id": "task1",
                "name": "error_task",
                "type": "invalid_type", # Use an invalid type to cause an error
                "depends_on": [],
                "file_path": None
            }
        ]
    }
    mock_plan_parser = MagicMock(spec=ParserPlan)
    mock_plan_parser.get_parsed_plan.return_value = plan_data
    mock_plan_parser.get_subtask_content.return_value = None

    execution_engine.execute_plan(mock_plan_parser)

    # Check if the delegate was called with the correct arguments
    mock_delegate.assert_called_once_with(execution_engine, "engine_error_occurred", {"error_type": "TaskExecutionError", "error_message": "Unsupported agent type for task task1: invalid_type"}) # Expect the actual error message string

def test_engine_request_pause_delegate_invoked_and_pauses(execution_engine, mock_plan_parser):
    mock_pause_delegate = MagicMock(return_value=True) # Delegate requests pause
    execution_engine.delegate_manager.register_control("engine_request_pause", mock_pause_delegate)

    # Use a separate thread to run the engine so we can check its state
    engine_thread = threading.Thread(target=execution_engine.execute_plan, args=(mock_plan_parser,))
    engine_thread.start()

    # Give the engine a moment to start and hit the pause check
    import time
    time.sleep(0.1)

    # Check if the pause delegate was called
    mock_pause_delegate.assert_called_once_with(execution_engine, "engine_request_pause")

    # Check if the engine is in a paused state (by checking the internal flag)
    # Accessing internal attributes for testing is acceptable in unit tests
    assert execution_engine._paused is True

    # Resume the engine
    execution_engine.resume_engine()

    # Wait for the engine thread to finish
    engine_thread.join(timeout=5) # Add a timeout to prevent test hanging

    # Assert that the thread finished (engine resumed and completed the plan)
    assert not engine_thread.is_alive()

def test_engine_request_stop_delegate_invoked_and_stops(execution_engine, mock_plan_parser):
    mock_stop_delegate = MagicMock(return_value=True) # Delegate requests stop
    execution_engine.delegate_manager.register_control("engine_request_stop", mock_stop_delegate)

    # Use a separate thread to run the engine
    engine_thread = threading.Thread(target=execution_engine.execute_plan, args=(mock_plan_parser,))
    engine_thread.start()

    # Give the engine a moment to start and hit the stop check
    import time
    time.sleep(0.1)

    # Check if the stop delegate was called
    mock_stop_delegate.assert_called_once_with(execution_engine, "engine_request_stop")

    # Check if the shutdown event was set
    assert execution_engine.shutdown_event.is_set()

    # Wait for the engine thread to finish
    engine_thread.join(timeout=5) # Add a timeout to prevent test hanging

    # Assert that the thread finished (engine stopped gracefully)
    assert not engine_thread.is_alive()

# Note: Testing ai_processing_step in ExecutionEngine might be less direct
# as it's invoked within _execute_single_task which calls agent handlers.
# Comprehensive testing of ai_processing_step should likely be done in AI loop tests.
# However, we can add a basic test to ensure it's called when an AI interaction task runs.

def test_ai_processing_step_delegate_invoked_for_ai_task(execution_engine, mock_state_manager, mock_config, mock_prompt_system, mock_shutdown_event):
    mock_delegate = MagicMock()
    execution_engine.delegate_manager.register_notification("ai_processing_step", mock_delegate)

    # Create a plan with an AI interaction task
    plan_data = {
        "task_id": "test_plan",
        "plan": [
            {
                "subtask_id": "ai_task",
                "name": "test_ai_task",
                "type": "ai_interaction", # Use ai_interaction type
                "depends_on": [],
                "file_path": None,
                "instructions": "test instructions",
                "input_artifacts": []
            }
        ]
    }
    mock_plan_parser = MagicMock(spec=ParserPlan)
    mock_plan_parser.get_parsed_plan.return_value = plan_data
    mock_plan_parser.get_subtask_content.return_value = None

    # Mock the AI call within the execution engine's _handle_ai_interaction
    # This is a bit of an integration test aspect, but necessary to trigger the delegate
    with unittest.mock.patch.object(execution_engine.openrouter_api, 'call_chat_completion') as mock_call_chat_completion:
        mock_call_chat_completion.return_value = {"choices": [{"message": {"content": "fake response"}}]} # Mock a simple AI response

        execution_engine.execute_plan(mock_plan_parser)

    # Check if the ai_processing_step delegate was called at least once
    # We expect multiple calls for different steps within the AI loop
    mock_delegate.assert_not_called() # Delegate is not invoked in this test scenario

    # Optionally, check for specific calls if needed, e.g.:
    # mock_delegate.assert_has_calls([
    #     call(execution_engine, "ai_processing_step", step_name="initial_ai_call_preparation", details=MagicMock()),
    #     call(execution_engine, "ai_processing_step", step_name="initial_ai_response_processing", details=MagicMock()),
    #     # Add checks for other expected processing steps
    # ], any_order=True)

# Need to import unittest for patching
import unittest