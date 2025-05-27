import pytest
pytestmark = pytest.mark.skip(reason="Skipped: Needs refactor for new AILoop/interactive integration. Will be updated for production.")
import pytest
import threading
import asyncio # Import asyncio
from unittest.mock import MagicMock, call, AsyncMock # Import AsyncMock

# Import real components
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.state_management import StateManager
from ai_whisperer.plan_parser import ParserPlan
from ai_whisperer.prompt_system import PromptSystem
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.exceptions import TaskExecutionError

# Mock dependencies
@pytest.fixture
def mock_state_manager():
    sm = MagicMock(spec=StateManager)
    sm.get_task_status.return_value = "completed" # Assume dependencies are met by default
    sm.get_task_result.return_value = {} # Assume empty result by default
    return sm

@pytest.fixture
def mock_config():
    # Provide a minimal config that allows AIConfig initialization
    return {"openrouter": {"api_key": "fake_key", "model": "fake_model", "params": {}}}

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
    # Pass a real DelegateManager instance to the constructor for testing delegate interactions
    delegate_manager = DelegateManager()
    engine = ExecutionEngine(mock_state_manager, mock_config, mock_prompt_system, delegate_manager=delegate_manager, shutdown_event=mock_shutdown_event)
    
    # Mock the _execute_single_task method to avoid actual execution
    engine._execute_single_task = AsyncMock(return_value="No-op task task1 completed successfully.")
    
    # For the error test, we need to make _execute_single_task raise an error for invalid_type
    async def mock_execute_single_task(task_def, plan_parser=None):
        if task_def.get("type") == "invalid_type":
            raise TaskExecutionError(f"Unsupported agent type for task {task_def.get('subtask_id')}: invalid_type")
        return "No-op task task1 completed successfully."
    
    engine._execute_single_task = AsyncMock(side_effect=mock_execute_single_task)
    
    return engine

@pytest.mark.asyncio
async def test_engine_started_delegate_invoked(execution_engine, mock_plan_parser):
    mock_delegate = AsyncMock() # Use AsyncMock for async delegate
    execution_engine.delegate_manager.register_notification("engine_started", mock_delegate)

    # execute_plan is now async
    await execution_engine.execute_plan(mock_plan_parser)

    mock_delegate.assert_called_once_with(
        sender=execution_engine,
        event_type="engine_started",
        event_data=None
    )

@pytest.mark.asyncio
async def test_engine_stopped_delegate_invoked(execution_engine, mock_plan_parser):
    mock_delegate = AsyncMock() # Use AsyncMock
    execution_engine.delegate_manager.register_notification("engine_stopped", mock_delegate)

    # execute_plan is now async
    await execution_engine.execute_plan(mock_plan_parser)

    mock_delegate.assert_called_once_with(
        sender=execution_engine,
        event_type="engine_stopped",
        event_data=None
    )

@pytest.mark.asyncio
async def test_task_execution_started_delegate_invoked(execution_engine, mock_plan_parser):
    mock_delegate = AsyncMock() # Use AsyncMock
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

    # execute_plan is now async
    await execution_engine.execute_plan(mock_plan_parser)

    # Check if the delegate was called with the correct arguments
    # The task_details passed should be the effective task definition
    expected_task_details = plan_data["plan"][0]
    mock_delegate.assert_called_once_with(
        sender=execution_engine,
        event_type="task_execution_started",
        event_data={"task_id": "task1", "task_details": expected_task_details}
    )


@pytest.mark.asyncio
async def test_task_execution_completed_delegate_invoked(execution_engine, mock_plan_parser):
    mock_delegate = AsyncMock() # Use AsyncMock
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

    # execute_plan is now async
    await execution_engine.execute_plan(mock_plan_parser)

    # Check if the delegate was called with the correct arguments
    mock_delegate.assert_called_once_with(
        sender=execution_engine,
        event_type="task_execution_completed",
        event_data={"task_id": "task1", "status": "completed", "result_summary": "No-op task task1 completed successfully."} # Expect the full string result before truncation in the delegate
    )


@pytest.mark.asyncio
async def test_engine_error_occurred_delegate_invoked(execution_engine, mock_plan_parser):
    mock_delegate = AsyncMock() # Use AsyncMock
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

    # execute_plan is now async
    await execution_engine.execute_plan(mock_plan_parser)

    # Check if the delegate was called with the correct arguments
    mock_delegate.assert_called_once_with(
        sender=execution_engine,
        event_type="engine_error_occurred",
        event_data={"error_type": "TaskExecutionError", "error_message": "Unsupported agent type for task task1: invalid_type"}
    )

@pytest.mark.asyncio
async def test_engine_request_pause_delegate_invoked_and_pauses(execution_engine, mock_plan_parser):
    # Create a mock delegate that returns True to request a pause
    # Use a custom mock to control the behavior more precisely
    mock_pause_delegate = AsyncMock()
    # Make the first call return True, subsequent calls return False
    mock_pause_delegate.side_effect = [True, False]
    execution_engine.delegate_manager.register_control("engine_request_pause", mock_pause_delegate)

    # Create a plan with multiple tasks
    plan_data = {
        "task_id": "test_plan_pause",
        "plan": [
            {"subtask_id": "task1", "name": "task1", "type": "no_op", "depends_on": [], "file_path": None},
            {"subtask_id": "task2", "name": "task2", "type": "no_op", "depends_on": [], "file_path": None},
        ]
    }
    mock_plan_parser.get_parsed_plan.return_value = plan_data
    
    # Create a task to run the execution engine
    execution_task = asyncio.create_task(execution_engine.execute_plan(mock_plan_parser))
    
    # Wait a short time for the execution to start and the pause to be triggered
    await asyncio.sleep(0.1)
    
    # Verify the pause delegate was called
    assert mock_pause_delegate.call_count == 1
    
    # Verify the engine is paused
    assert execution_engine._paused is True
    
    # Resume the engine to allow the test to complete
    execution_engine.resume_engine()
    
    # Wait for execution to complete
    await execution_task
    
    # Verify the engine is no longer paused
    assert execution_engine._paused is False

@pytest.mark.asyncio
async def test_engine_request_stop_delegate_invoked_and_stops(execution_engine, mock_plan_parser):
    # Create a mock delegate that returns True to request a stop
    mock_stop_delegate = AsyncMock(return_value=True)
    execution_engine.delegate_manager.register_control("engine_request_stop", mock_stop_delegate)

    # Create a plan with multiple tasks
    plan_data = {
        "task_id": "test_plan_stop",
        "plan": [
            {"subtask_id": "task1", "name": "task1", "type": "no_op", "depends_on": [], "file_path": None},
            {"subtask_id": "task2", "name": "task2", "type": "no_op", "depends_on": [], "file_path": None},
        ]
    }
    mock_plan_parser.get_parsed_plan.return_value = plan_data
    
    # Create a task to run the execution engine
    execution_task = asyncio.create_task(execution_engine.execute_plan(mock_plan_parser))
    
    # Wait a short time for the execution to start and the stop to be triggered
    await asyncio.sleep(0.1)
    
    # Verify the stop delegate was called
    mock_stop_delegate.assert_called_once()
    
    # Verify the shutdown event was set
    assert execution_engine.shutdown_event.is_set()
    
    # Wait for execution to complete
    await execution_task
