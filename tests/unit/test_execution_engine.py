


from unittest.mock import MagicMock, call, patch, AsyncMock
import pytest
import uuid
from ai_whisperer.execution_engine import ExecutionEngine, TaskExecutionError
from ai_whisperer.plan_parser import ParserPlan
from ai_whisperer.prompt_system import PromptSystem
import threading


@pytest.fixture

def engine_fixture():
    mock_state_manager = MagicMock()
    patcher = patch.object(ExecutionEngine, "_execute_single_task", new_callable=AsyncMock)
    mock_execute_single_task = patcher.start()
    def cleanup():
        patcher.stop()
    import atexit
    atexit.register(cleanup)
    mock_config = {"openrouter": {"api_key": "dummy", "model": "test-model", "params": {}}}
    mock_prompt_system = MagicMock(spec=PromptSystem)
    mock_delegate_manager = MagicMock()
    mock_delegate_manager.invoke_control = AsyncMock(return_value=False)
    mock_delegate_manager.invoke_notification = AsyncMock()
    mock_shutdown_event = MagicMock(spec=threading.Event)
    mock_shutdown_event.is_set.return_value = False
    engine = ExecutionEngine(mock_state_manager, config=mock_config, prompt_system=mock_prompt_system, delegate_manager=mock_delegate_manager, shutdown_event=mock_shutdown_event)
    return {
        "engine": engine,
        "mock_state_manager": mock_state_manager,
        "mock_execute_single_task": mock_execute_single_task,
        "mock_prompt_system": mock_prompt_system,
        "mock_delegate_manager": mock_delegate_manager,
        "mock_shutdown_event": mock_shutdown_event,
    }

def _get_sample_plan(num_tasks=2, add_failing_task=False, add_dependent_task=False):
    plan = {"task_id": str(uuid.uuid4()), "natural_language_goal": "Test plan", "input_hashes": {}, "plan": []}
    for i in range(num_tasks):
        task_id = f"task_{i+1}"
        step = {
            "subtask_id": task_id,
            "description": f"This is task {i+1}",
            "agent_spec": {"type": "test_agent", "instructions": "do something"},
        }
        if add_dependent_task and i == num_tasks - 1:
            step["depends_on"] = ["task_1"]
        plan["plan"].append(step)
    if add_failing_task:
        plan["plan"].append({
            "subtask_id": "task_that_fails",
            "description": "This task will fail",
            "agent_spec": {"type": "failing_agent", "instructions": "fail"},
        })
    return plan


def test_initialization(engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    assert engine is not None
    assert engine.state_manager == mock_state_manager


@patch("ai_whisperer.execution_engine.ParserPlan")
@pytest.mark.asyncio
async def test_execute_empty_plan(MockParserPlan, engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_execute_single_task = engine_fixture["mock_execute_single_task"]
    empty_plan_data = {"plan": []}
    mock_parser_instance = MagicMock(spec=ParserPlan)
    mock_parser_instance.get_parsed_plan.return_value = empty_plan_data
    MockParserPlan.return_value = mock_parser_instance
    await engine.execute_plan(mock_parser_instance)
    mock_state_manager.set_task_state.assert_not_called()
    mock_execute_single_task.assert_not_called()


@patch("ai_whisperer.execution_engine.ParserPlan")
@pytest.mark.asyncio
async def test_execute_plan_none(MockParserPlan, engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_execute_single_task = engine_fixture["mock_execute_single_task"]
    with pytest.raises(ValueError) as cm:
        await engine.execute_plan(None)
    assert str(cm.value) == "Plan parser cannot be None."
    mock_state_manager.set_task_state.assert_not_called()
    mock_execute_single_task.assert_not_called()
    MockParserPlan.assert_not_called()


@patch("ai_whisperer.execution_engine.ParserPlan")
@pytest.mark.asyncio
async def test_execute_simple_sequential_plan(MockParserPlan, engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_execute_single_task = engine_fixture["mock_execute_single_task"]
    sample_plan_data = _get_sample_plan(num_tasks=2)
    task1_def = sample_plan_data["plan"][0]
    task2_def = sample_plan_data["plan"][1]
    mock_parser_instance = MagicMock(spec=ParserPlan)
    mock_parser_instance.get_parsed_plan.return_value = sample_plan_data
    MockParserPlan.return_value = mock_parser_instance
    mock_execute_single_task.side_effect = ["Result of task_1", "Result of task_2"]
    await engine.execute_plan(mock_parser_instance)
    mock_execute_single_task.assert_any_call(task1_def, mock_parser_instance)
    mock_execute_single_task.assert_any_call(task2_def, mock_parser_instance)
    assert mock_execute_single_task.call_count == 2
    expected_state_calls = [
        call.set_task_state("task_1", "pending"),
        call.set_task_state("task_1", "in-progress"),
        call.set_task_state("task_1", "completed"),
        call.store_task_result("task_1", "Result of task_1"),
        call.save_state(),
        call.set_task_state("task_2", "pending"),
        call.set_task_state("task_2", "in-progress"),
        call.set_task_state("task_2", "completed"),
        call.store_task_result("task_2", "Result of task_2"),
        call.save_state(),
    ]
    mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)


def test_get_task_status(engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_state_manager.get_task_status.return_value = "completed"
    status = engine.get_task_status("task_123")
    mock_state_manager.get_task_status.assert_called_once_with("task_123")
    assert status == "completed"


def test_get_task_status_not_found(engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_state_manager.get_task_status.return_value = None
    status = engine.get_task_status("task_non_existent")
    mock_state_manager.get_task_status.assert_called_once_with("task_non_existent")
    assert status is None


def test_get_task_result(engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_state_manager.get_task_result.return_value = {"data": "some_result"}
    result = engine.get_task_result("task_456")
    mock_state_manager.get_task_result.assert_called_once_with("task_456")
    assert result == {"data": "some_result"}


def test_get_task_result_not_found_or_not_completed(engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_state_manager.get_task_result.return_value = None
    result = engine.get_task_result("task_not_done")
    mock_state_manager.get_task_result.assert_called_once_with("task_not_done")
    assert result is None


@patch("ai_whisperer.execution_engine.ParserPlan")
@pytest.mark.asyncio
async def test_execute_plan_with_task_failure(MockParserPlan, engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_execute_single_task = engine_fixture["mock_execute_single_task"]
    sample_plan_data = _get_sample_plan(num_tasks=1, add_failing_task=True)
    task1_def = sample_plan_data["plan"][0]
    failing_task_def = sample_plan_data["plan"][1]
    mock_parser_instance = MagicMock(spec=ParserPlan)
    mock_parser_instance.get_parsed_plan.return_value = sample_plan_data
    MockParserPlan.return_value = mock_parser_instance
    def side_effect(task_def, plan_parser_arg):
        if task_def["subtask_id"] == "task_1":
            return "Result of task_1"
        elif task_def["subtask_id"] == "task_that_fails":
            raise TaskExecutionError("Intentional failure for task_that_fails")
    mock_execute_single_task.side_effect = side_effect
    await engine.execute_plan(mock_parser_instance)
    expected_state_calls_for_failure = [
        call.set_task_state("task_1", "pending"),
        call.set_task_state("task_1", "in-progress"),
        call.set_task_state("task_1", "completed"),
        call.store_task_result("task_1", "Result of task_1"),
        call.save_state(),
        call.set_task_state("task_that_fails", "pending"),
        call.set_task_state("task_that_fails", "in-progress"),
        call.set_task_state("task_that_fails", "failed", {"error": "Intentional failure for task_that_fails"}),
        call.store_task_result("task_that_fails", {"status": "failed", "error": "Intentional failure for task_that_fails", "error_details": None}),
        call.save_state(),
    ]
    mock_state_manager.assert_has_calls(expected_state_calls_for_failure, any_order=False)
    mock_state_manager.store_task_result.assert_any_call("task_1", "Result of task_1")
    found = False
    for sm_call in mock_state_manager.store_task_result.call_args_list:
        if sm_call[0][0] == "task_that_fails":
            found = True
            failure_result = sm_call[0][1]
            assert isinstance(failure_result, dict)
            assert failure_result["status"] == "failed"
            assert failure_result["error"] == "Intentional failure for task_that_fails"
            assert failure_result["error_details"] is None
    assert found, "store_task_result was not called for the failing task"


@patch("ai_whisperer.execution_engine.ParserPlan")
@pytest.mark.asyncio
async def test_execute_plan_with_dependency_met(MockParserPlan, engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_execute_single_task = engine_fixture["mock_execute_single_task"]
    sample_plan_data = _get_sample_plan(num_tasks=2, add_dependent_task=True)
    task1_def = sample_plan_data["plan"][0]
    task2_def = sample_plan_data["plan"][1]
    mock_parser_instance = MagicMock(spec=ParserPlan)
    mock_parser_instance.get_parsed_plan.return_value = sample_plan_data
    MockParserPlan.return_value = mock_parser_instance
    mock_state_manager.get_task_status.return_value = "completed"
    mock_execute_single_task.side_effect = ["Result of task_1", "Result of task_2"]
    await engine.execute_plan(mock_parser_instance)
    mock_state_manager.get_task_status.assert_called_once_with("task_1")
    mock_execute_single_task.assert_any_call(task1_def, mock_parser_instance)
    mock_execute_single_task.assert_any_call(task2_def, mock_parser_instance)
    assert mock_execute_single_task.call_count == 2
    expected_state_calls = [
        call.set_task_state("task_1", "pending"),
        call.set_task_state("task_1", "in-progress"),
        call.set_task_state("task_1", "completed"),
        call.store_task_result("task_1", "Result of task_1"),
        call.save_state(),
        call.set_task_state("task_2", "pending"),
        call.get_task_status("task_1"),
        call.set_task_state("task_2", "in-progress"),
        call.set_task_state("task_2", "completed"),
        call.store_task_result("task_2", "Result of task_2"),
        call.save_state(),
    ]
    mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)


@patch("ai_whisperer.execution_engine.ParserPlan")
@pytest.mark.asyncio
async def test_execute_plan_with_dependency_not_met(MockParserPlan, engine_fixture):
    engine = engine_fixture["engine"]
    mock_state_manager = engine_fixture["mock_state_manager"]
    mock_execute_single_task = engine_fixture["mock_execute_single_task"]
    sample_plan_data = _get_sample_plan(num_tasks=2, add_dependent_task=True)
    task1_def = sample_plan_data["plan"][0]
    mock_parser_instance = MagicMock(spec=ParserPlan)
    mock_parser_instance.get_parsed_plan.return_value = sample_plan_data
    MockParserPlan.return_value = mock_parser_instance
    mock_state_manager.get_task_status.return_value = "failed"
    mock_execute_single_task.side_effect = ["Result of task_1"]
    await engine.execute_plan(mock_parser_instance)
    mock_state_manager.get_task_status.assert_called_once_with("task_1")
    mock_execute_single_task.assert_called_once_with(task1_def, mock_parser_instance)
    expected_state_calls = [
        call.set_task_state("task_1", "pending"),
        call.set_task_state("task_1", "in-progress"),
        call.set_task_state("task_1", "completed"),
        call.store_task_result("task_1", "Result of task_1"),
        call.save_state(),
        call.set_task_state("task_2", "pending"),
        call.get_task_status("task_1"),
        call.set_task_state("task_2", "skipped", {"reason": "Dependency task_1 not met. Status: failed"}),
    ]
    mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)
