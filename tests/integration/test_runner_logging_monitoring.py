import pytest
import logging
import threading
from unittest.mock import MagicMock, patch

from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType
from src.ai_whisperer.commands import RunCommand
from dataclasses import dataclass, field
from typing import List, Dict, Any


# Define simple data classes for mocking state
@dataclass
class StepState:
    subtask_id: str
    status: str
    result: Any = None


@dataclass
class PlanState:
    plan_id: str
    status: str
    steps: List[StepState] = field(default_factory=list)
    global_state: Dict[str, Any] = field(default_factory=dict)


# Configure logging to capture messages during tests
@pytest.fixture(scope="function")
def caplog_aiwhisperer(caplog):
    """Fixture to capture logs from the ai_whisperer logger."""
    caplog.set_level(logging.DEBUG, logger="ai_whisperer")
    return caplog


def create_simple_test_plan():
    """Creates a simple mock plan for testing."""
    # This structure should mimic the actual plan structure used by the ExecutionEngine
    # For integration tests, we might need a more realistic plan structure
    # For now, a simplified dictionary representation might suffice if the ExecutionEngine
    # can work with it or if we mock the parts that interact with the plan structure.
    # A more robust approach would be to use the actual Plan and Step classes if available.

    # Assuming a simplified plan structure for now.
    # If Plan/Step classes are needed, we'd import and use them.
    plan = {
        "plan_id": "test_plan_123",
        "description": "A simple plan for logging/monitoring integration tests",
        "steps": [
            {"subtask_id": "step_1_start", "description": "Starting step", "agent_spec": {"type": "dummy_start"}},
            {
                "subtask_id": "step_2_process",
                "description": "Processing step with simulated AI interaction",
                "agent_spec": {"type": "dummy_process"},
            },
            {
                "step_3_end": {
                    "subtask_id": "step_3_end",
                    "description": "Ending step",
                    "agent_spec": {"type": "dummy_end"},
                }
            },
        ],
    }
    return plan


# Mock the ExecutionEngine and StateManager interactions for controlled testing
# In a true integration test, we might instantiate these classes and
# mock their dependencies (like AI service calls, file ops, terminal ops)
# rather than the classes themselves.
# For this task, focusing on logging/monitoring interaction with runner/state,
# mocking the core engine/manager might be acceptable to isolate the test scope.


@patch("src.ai_whisperer.execution_engine.ExecutionEngine")
@patch("src.ai_whisperer.state_management.StateManager")
def test_runner_logs_and_state_updates_on_step_execution(MockExecutionEngine, MockStateManager, caplog_aiwhisperer):
    """
    Tests that logging and state management are updated correctly during step execution.
    """
    # Setup mocks
    mock_state_manager_instance = MockStateManager.return_value
    mock_execution_engine_instance = MockExecutionEngine.return_value

    # Simulate a simple plan and its state
    test_plan = create_simple_test_plan()
    mock_state_manager_instance.get_plan_state.return_value = PlanState(
        plan_id=test_plan["plan_id"],
        status="Running",
        steps=[
            StepState(subtask_id="step_1_start", status="Completed"),
            StepState(subtask_id="step_2_process", status="Running"),
            StepState(subtask_id="step_3_end", status="Pending"),
        ],
    )
    mock_state_manager_instance.get_step_state.side_effect = lambda subtask_id: next(
        (s for s in mock_state_manager_instance.get_plan_state.return_value.steps if s.subtask_id == subtask_id), None
    )

    # Simulate the execution engine running a step
    # In a real scenario, the ExecutionEngine would call StateManager methods
    # and trigger logging. Here, we simulate those calls directly for testing.

    # Simulate step start
    subtask_id_to_test = "step_2_process"
    mock_state_manager_instance.update_step_state(subtask_id_to_test, "Running")
    # Simulate logging the step start event
    logging.getLogger("ai_whisperer").info(
        LogMessage(
            level=LogLevel.INFO,
            component=ComponentType.EXECUTION_ENGINE,
            action="step_execution_started",
            event_summary=f"Starting execution of step '{subtask_id_to_test}'.",  # Use event_summary
            subtask_id=subtask_id_to_test,
            state_before="Pending",  # Assuming it was pending before running
            state_after="Running",
        ).to_dict()  # Assuming LogMessage has a to_dict method for logging extra
    )

    # Simulate some activity within the step (e.g., AI interaction)
    logging.getLogger("ai_whisperer").debug(
        LogMessage(
            level=LogLevel.DEBUG,
            component=ComponentType.AI_SERVICE,
            action="api_request_sent",
            event_summary="Sent request to LLM.",  # Use event_summary
            subtask_id=subtask_id_to_test,
            details={"model": "test-model"},
        ).to_dict()
    )

    # Simulate step completion
    mock_state_manager_instance.update_step_state(subtask_id_to_test, "Completed")
    # Simulate logging the step completion event
    logging.getLogger("ai_whisperer").info(
        LogMessage(
            level=LogLevel.INFO,
            component=ComponentType.EXECUTION_ENGINE,
            action="step_execution_succeeded",
            event_summary=f"Step '{subtask_id_to_test}' completed successfully.",  # Use event_summary
            subtask_id=subtask_id_to_test,
            state_before="Running",
            state_after="Completed",
            duration_ms=100.0,  # Example duration
        ).to_dict()
    )

    # Assertions for State Management updates
    mock_state_manager_instance.update_step_state.assert_any_call(subtask_id_to_test, "Running")
    mock_state_manager_instance.update_step_state.assert_any_call(subtask_id_to_test, "Completed")
    # Note: In a real integration test, we'd check the actual state object returned
    # by StateManager methods, not just that the mock methods were called.
    # This requires instantiating StateManager and potentially mocking its storage.

    # Assertions for Logging output
    # Check for specific log messages and their content
    log_messages = [record.message for record in caplog_aiwhisperer.records]

    assert any(f"Starting execution of step '{subtask_id_to_test}'" in msg for msg in log_messages)
    assert any("Sent request to LLM." in msg for msg in log_messages)
    assert any(f"Step '{subtask_id_to_test}' completed successfully." in msg for msg in log_messages)

    # More detailed assertions checking LogMessage structure and content
    # This requires parsing the logged message string back into a LogMessage or checking the 'extra' dict
    # Assuming the LogMessage.to_dict() is used and captured in record.message (which might not be the case,
    # logging handlers usually format the message. We might need a custom test handler or parse the formatted string).
    # A better approach is to check the `record.as_dict()` if using JsonFormatter or check `record.__dict__` for extra fields.

    # Let's refine assertions to check the captured log records directly
    step_start_log = next(
        (
            record
            for record in caplog_aiwhisperer.records
            if f"Starting execution of step '{subtask_id_to_test}'" in record.message
        ),
        None,
    )
    assert step_start_log is not None
    # Check extra fields if they are captured by caplog (requires specific caplog configuration or custom handler)
    # For now, let's check basic message content and level
    assert step_start_log.levelname == "INFO"

    ai_interaction_log = next(
        (record for record in caplog_aiwhisperer.records if "Sent request to LLM." in record.message), None
    )
    assert ai_interaction_log is not None
    assert ai_interaction_log.levelname == "DEBUG"

    step_completion_log = next(
        (
            record
            for record in caplog_aiwhisperer.records
            if f"Step '{subtask_id_to_test}' completed successfully." in record.message
        ),
        None,
    )
    assert step_completion_log is not None
    assert step_completion_log.levelname == "INFO"


@patch("src.ai_whisperer.execution_engine.ExecutionEngine")
@patch("src.ai_whisperer.state_management.StateManager")
def test_runner_logs_and_state_updates_on_user_interaction(MockExecutionEngine, MockStateManager, caplog_aiwhisperer):
    """
    Tests that logging and state management are updated correctly on simulated user interactions.
    """
    mock_state_manager_instance = MockStateManager.return_value
    mock_execution_engine_instance = MockExecutionEngine.return_value

    test_plan = create_simple_test_plan()
    mock_state_manager_instance.get_plan_state.return_value = PlanState(
        plan_id=test_plan["plan_id"], status="Running", steps=[StepState(subtask_id="step_to_pause", status="Running")]
    )
    mock_state_manager_instance.get_step_state.side_effect = lambda subtask_id: next(
        (s for s in mock_state_manager_instance.get_plan_state.return_value.steps if s.subtask_id == subtask_id), None
    )

    subtask_id_to_interact = "step_to_pause"

    # Simulate user pausing execution
    # In a real scenario, a UI component would call a method on the runner/engine
    # which would then update state and log. We simulate the state/log updates directly.
    mock_state_manager_instance.update_plan_state("Paused")
    mock_state_manager_instance.update_step_state(subtask_id_to_interact, "Paused")
    logging.getLogger("ai_whisperer").info(
        LogMessage(
            level=LogLevel.INFO,
            component=ComponentType.USER_INTERACTION,
            action="execution_pause_requested",
            event_summary="User requested to pause execution.",  # Use event_summary
            subtask_id=subtask_id_to_interact,
            state_before="Running",
            state_after="Paused",
        ).to_dict()
    )

    # Simulate user resuming execution
    mock_state_manager_instance.update_plan_state("Running")
    mock_state_manager_instance.update_step_state(subtask_id_to_interact, "Running")
    logging.getLogger("ai_whisperer").info(
        LogMessage(
            level=LogLevel.INFO,
            component=ComponentType.USER_INTERACTION,
            action="execution_resume_requested",
            event_summary="User requested to resume execution.",  # Use event_summary
            subtask_id=subtask_id_to_interact,
            state_before="Paused",
            state_after="Running",
        ).to_dict()
    )

    # Simulate user canceling execution
    mock_state_manager_instance.update_plan_state("Cancelled")
    mock_state_manager_instance.update_step_state(subtask_id_to_interact, "Cancelled")
    logging.getLogger("ai_whisperer").info(
        LogMessage(
            level=LogLevel.INFO,
            component=ComponentType.USER_INTERACTION,
            action="execution_cancel_requested",
            event_summary="User requested to cancel execution.",  # Use event_summary
            subtask_id=subtask_id_to_interact,
            state_before="Running",  # Could be Running or Paused
            state_after="Cancelled",
        ).to_dict()
    )

    # Simulate user adding context
    logging.getLogger("ai_whisperer").info(
        LogMessage(
            level=LogLevel.INFO,
            component=ComponentType.USER_INTERACTION,
            action="context_added_by_user",
            event_summary="User provided additional context.",  # Use event_summary
            subtask_id=subtask_id_to_interact,
            details={"context_summary": "Some context"},
        ).to_dict()
    )

    # Assertions for State Management updates
    mock_state_manager_instance.update_plan_state.assert_any_call("Paused")
    mock_state_manager_instance.update_step_state.assert_any_call(subtask_id_to_interact, "Paused")
    mock_state_manager_instance.update_plan_state.assert_any_call("Running")
    mock_state_manager_instance.update_step_state.assert_any_call(subtask_id_to_interact, "Running")
    mock_state_manager_instance.update_plan_state.assert_any_call("Cancelled")
    mock_state_manager_instance.update_step_state.assert_any_call(subtask_id_to_interact, "Cancelled")

    # Assertions for Logging output
    log_messages = [record.message for record in caplog_aiwhisperer.records]

    assert any("User requested to pause execution." in msg for msg in log_messages)
    assert any("User requested to resume execution." in msg for msg in log_messages)
    assert any("User requested to cancel execution." in msg for msg in log_messages)
    assert any("User provided additional context." in msg for msg in log_messages)

    # More detailed assertions checking LogMessage structure and content
    pause_log = next(
        (record for record in caplog_aiwhisperer.records if "User requested to pause execution." in record.message),
        None,
    )
    assert pause_log is not None
    assert pause_log.levelname == "INFO"

    resume_log = next(
        (record for record in caplog_aiwhisperer.records if "User requested to resume execution." in record.message),
        None,
    )
    assert resume_log is not None
    assert resume_log.levelname == "INFO"

    cancel_log = next(
        (record for record in caplog_aiwhisperer.records if "User requested to cancel execution." in record.message),
        None,
    )
    assert cancel_log is not None
    assert cancel_log.levelname == "INFO"

    context_log = next(
        (record for record in caplog_aiwhisperer.records if "User provided additional context." in record.message), None
    )
    assert context_log is not None
    assert context_log.levelname == "INFO"
    # Further checks on 'extra' dict for component, action, subtask_id, state_before, state_after, details
    # This requires caplog to capture 'extra' or parsing the message if using JsonFormatter.
    # Assuming caplog captures extra for now or that the message format includes key info.
    # If not, a custom test handler would be needed to collect structured log data.


# Further tests could include:
# - Testing error scenarios and verifying error logging and state updates (e.g., step failure).
# - Testing a plan with multiple steps and verifying the sequence of logs and state changes.
# - Testing the interaction between different components' logs (e.g., ExecutionEngine step log followed by AI_SERVICE logs).
# - If the terminal monitoring view logic is testable separately, add tests for that.
# - If the plan structure is more complex, use actual Plan/Step objects and potentially mock their dependencies.

@patch('threading.Thread.start')
@patch('src.ai_whisperer.plan_runner.PlanRunner')
@patch('src.ai_whisperer.commands.load_config')
@patch('src.ai_whisperer.commands.ParserPlan')
def test_monitor_thread_not_started_without_option(mock_parser_plan, mock_load_config, mock_plan_runner, mock_thread_start):
    """
    Tests that the monitor thread is not started when the --monitor option is not used.
    """
    mock_load_config.return_value = {} # Return a mock config dictionary
    mock_parser_plan.return_value.get_parsed_plan.return_value = {"plan_id": "mock_plan"} # Return a mock plan dictionary
    run_command_instance = RunCommand(config_path="dummy_config_path", plan_file="dummy_plan_path", state_file="dummy_state_path", monitor=False)
    run_command_instance.execute()
    mock_thread_start.assert_not_called()

@patch('threading.Thread.start')
@patch('src.ai_whisperer.plan_runner.PlanRunner')
@patch('src.ai_whisperer.commands.load_config')
@patch('src.ai_whisperer.commands.ParserPlan')
def test_monitor_thread_started_with_option(mock_parser_plan, mock_load_config, mock_plan_runner, mock_thread_start):
    """
    Tests that the monitor thread is started when the --monitor option is used.
    """
    mock_load_config.return_value = {} # Return a mock config dictionary
    mock_parser_plan.return_value.get_parsed_plan.return_value = {"plan_id": "mock_plan"} # Return a mock plan dictionary
    run_command_instance = RunCommand(config_path="dummy_config_path", plan_file="dummy_plan_path", state_file="dummy_state_path", monitor=True)
    run_command_instance.execute()
    mock_thread_start.assert_called_once()
