import unittest
from unittest.mock import MagicMock, call, patch
import uuid

from ai_whisperer.execution_engine import ExecutionEngine, TaskExecutionError
from ai_whisperer.plan_parser import ParserPlan  # Import ParserPlan
from ai_whisperer.prompt_system import PromptSystem # Import PromptSystem


class TestExecutionEngine(unittest.TestCase):

    def setUp(self):
        self.mock_state_manager = MagicMock()
        patcher = patch.object(ExecutionEngine, "_execute_single_task", autospec=True)
        self.mock_execute_single_task = patcher.start()
        self.addCleanup(patcher.stop)
        import threading # Import threading
        self.mock_config = {"openrouter": {"api_key": "dummy", "model": "test-model", "params": {}}}
        import threading # Import threading
        self.mock_config = {"openrouter": {"api_key": "dummy", "model": "test-model", "params": {}}}
        self.mock_prompt_system = MagicMock(spec=PromptSystem) # Create a mock PromptSystem
        self.mock_delegate_manager = MagicMock() # Create a mock DelegateManager
        # Ensure pause/stop controls are not triggered in these unit tests
        self.mock_delegate_manager.invoke_control.return_value = False
        self.mock_shutdown_event = MagicMock(spec=threading.Event) # Create a mock shutdown event
        self.mock_shutdown_event.is_set.return_value = False # Default to not set
        self.engine = ExecutionEngine(self.mock_state_manager, config=self.mock_config, prompt_system=self.mock_prompt_system, delegate_manager=self.mock_delegate_manager, shutdown_event=self.mock_shutdown_event) # Add mock_prompt_system, mock_delegate_manager, and mock_shutdown_event

    def _get_sample_plan(self, num_tasks=2, add_failing_task=False, add_dependent_task=False):
        plan = {"task_id": str(uuid.uuid4()), "natural_language_goal": "Test plan", "input_hashes": {}, "plan": []}
        for i in range(num_tasks):
            task_id = f"task_{i+1}"
            step = {
                "subtask_id": task_id,
                "description": f"This is task {i+1}",
                "agent_spec": {"type": "test_agent", "instructions": "do something"},
            }
            if add_dependent_task and i == num_tasks - 1:  # Make the last task dependent on the first
                step["depends_on"] = ["task_1"]
            plan["plan"].append(step)

        if add_failing_task:
            plan["plan"].append(
                {
                    "subtask_id": "task_that_fails",
                    "description": "This task will fail",
                    "agent_spec": {"type": "failing_agent", "instructions": "fail"},
                }
            )
        return plan

    def test_initialization(self):
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.state_manager, self.mock_state_manager)

    @patch("ai_whisperer.execution_engine.ParserPlan")
    def test_execute_empty_plan(self, MockParserPlan):
        empty_plan_data = {"plan": []}
        mock_parser_instance = MagicMock(spec=ParserPlan)
        mock_parser_instance.get_parsed_plan.return_value = empty_plan_data
        MockParserPlan.return_value = mock_parser_instance
        self.engine.execute_plan(mock_parser_instance)
        self.mock_state_manager.set_task_state.assert_not_called()
        self.mock_execute_single_task.assert_not_called()

    @patch("ai_whisperer.execution_engine.ParserPlan")
    def test_execute_plan_none(self, MockParserPlan):
        with self.assertRaises(ValueError) as cm:
            self.engine.execute_plan(None)
        self.assertEqual(str(cm.exception), "Plan parser cannot be None.")
        self.mock_state_manager.set_task_state.assert_not_called()
        self.mock_execute_single_task.assert_not_called()
        MockParserPlan.assert_not_called()

    @patch("ai_whisperer.execution_engine.ParserPlan")  # Patch ParserPlan
    def test_execute_simple_sequential_plan(self, MockParserPlan):
        sample_plan_data = self._get_sample_plan(num_tasks=2)
        task1_def = sample_plan_data["plan"][0]
        task2_def = sample_plan_data["plan"][1]

        mock_parser_instance = MagicMock(spec=ParserPlan)
        mock_parser_instance.get_parsed_plan.return_value = sample_plan_data
        MockParserPlan.return_value = mock_parser_instance

        # Set the mock to return the expected results for each task
        self.mock_execute_single_task.side_effect = ["Result of task_1", "Result of task_2"]

        self.engine.execute_plan(mock_parser_instance)

        self.mock_execute_single_task.assert_any_call(self.engine, task1_def)
        self.mock_execute_single_task.assert_any_call(self.engine, task2_def)
        self.assertEqual(self.mock_execute_single_task.call_count, 2)

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
        self.mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)

    def test_get_task_status(self):
        self.mock_state_manager.get_task_status.return_value = "completed"
        status = self.engine.get_task_status("task_123")
        self.mock_state_manager.get_task_status.assert_called_once_with("task_123")
        self.assertEqual(status, "completed")

    def test_get_task_status_not_found(self):
        self.mock_state_manager.get_task_status.return_value = None  # Or raise specific exception
        status = self.engine.get_task_status("task_non_existent")
        self.mock_state_manager.get_task_status.assert_called_once_with("task_non_existent")
        self.assertIsNone(status)

    def test_get_task_result(self):
        self.mock_state_manager.get_task_result.return_value = {"data": "some_result"}
        result = self.engine.get_task_result("task_456")
        self.mock_state_manager.get_task_result.assert_called_once_with("task_456")
        self.assertEqual(result, {"data": "some_result"})

    def test_get_task_result_not_found_or_not_completed(self):
        self.mock_state_manager.get_task_result.return_value = None  # Or raise specific exception
        result = self.engine.get_task_result("task_not_done")
        self.mock_state_manager.get_task_result.assert_called_once_with("task_not_done")
        self.assertIsNone(result)

    @patch("ai_whisperer.execution_engine.ParserPlan")  # Patch ParserPlan
    def test_execute_plan_with_task_failure(self, MockParserPlan):
        # This test mocks _execute_single_task to simulate a TaskExecutionError
        sample_plan_data = self._get_sample_plan(num_tasks=1, add_failing_task=True)
        # plan: task_1, task_that_fails

        task1_def = sample_plan_data["plan"][0]
        failing_task_def = sample_plan_data["plan"][1]

        mock_parser_instance = MagicMock(spec=ParserPlan)  # Create a mock ParserPlan instance
        mock_parser_instance.get_parsed_plan.return_value = sample_plan_data  # Revert to mocking get_parsed_plan
        MockParserPlan.return_value = mock_parser_instance  # Ensure the engine gets this mock

        # Set the mock: first call returns result, second call raises TaskExecutionError
        def side_effect(engine, task_def):
            if task_def["subtask_id"] == "task_1":
                return "Result of task_1"
            elif task_def["subtask_id"] == "task_that_fails":
                raise TaskExecutionError("Intentional failure for task_that_fails")
        self.mock_execute_single_task.side_effect = side_effect

        self.engine.execute_plan(mock_parser_instance)

        # Check state manager calls for both tasks
        expected_state_calls_for_failure = [
            call.set_task_state("task_1", "pending"),
            call.set_task_state("task_1", "in-progress"),
            call.set_task_state("task_1", "completed"),
            call.store_task_result("task_1", "Result of task_1"),
            call.save_state(),
            call.set_task_state("task_that_fails", "pending"),
            call.set_task_state("task_that_fails", "in-progress"),
            call.set_task_state("task_that_fails", "failed", {"error": "Intentional failure for task_that_fails"}),
            call.save_state(),
        ]
        self.mock_state_manager.assert_has_calls(expected_state_calls_for_failure, any_order=False)
        self.mock_state_manager.store_task_result.assert_any_call("task_1", "Result of task_1")
        # Ensure result for the failing task is a failure dict
        found = False
        for sm_call in self.mock_state_manager.store_task_result.call_args_list:
            if sm_call[0][0] == "task_that_fails":
                found = True
                failure_result = sm_call[0][1]
                self.assertIsInstance(failure_result, dict)
                self.assertEqual(failure_result["status"], "failed")
                self.assertEqual(failure_result["error"], "Intentional failure for task_that_fails")
        self.assertTrue(found, "store_task_result was not called for the failing task")

    @patch("ai_whisperer.execution_engine.ParserPlan")  # Patch ParserPlan
    def test_execute_plan_with_dependency_met(self, MockParserPlan):
        sample_plan_data = self._get_sample_plan(num_tasks=2, add_dependent_task=True)  # task_2 depends on task_1
        task1_def = sample_plan_data["plan"][0]
        task2_def = sample_plan_data["plan"][1]

        mock_parser_instance = MagicMock(spec=ParserPlan)  # Create a mock ParserPlan instance
        mock_parser_instance.get_parsed_plan.return_value = sample_plan_data  # Revert to mocking get_parsed_plan
        MockParserPlan.return_value = mock_parser_instance  # Ensure the engine gets this mock

        self.mock_state_manager.get_task_status.return_value = "completed"

        # Set the mock to return the expected results for each task
        self.mock_execute_single_task.side_effect = ["Result of task_1", "Result of task_2"]

        self.engine.execute_plan(mock_parser_instance)

        self.mock_state_manager.get_task_status.assert_called_once_with("task_1")
        self.mock_execute_single_task.assert_any_call(self.engine, task1_def)
        self.mock_execute_single_task.assert_any_call(self.engine, task2_def)
        self.assertEqual(self.mock_execute_single_task.call_count, 2)

        expected_state_calls = [
            call.set_task_state("task_1", "pending"),
            call.set_task_state("task_1", "in-progress"),
            call.set_task_state("task_1", "completed"),
            call.store_task_result("task_1", "Result of task_1"),
            call.save_state(),
            call.set_task_state("task_2", "pending"),
            call.get_task_status("task_1"),
            # get_task_status("task_1") is called by the engine here
            call.set_task_state("task_2", "in-progress"),
            call.set_task_state("task_2", "completed"),
            call.store_task_result("task_2", "Result of task_2"),
            call.save_state(),
        ]
        self.mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)

    @patch("ai_whisperer.execution_engine.ParserPlan")  # Patch ParserPlan
    def test_execute_plan_with_dependency_not_met(self, MockParserPlan):
        sample_plan_data = self._get_sample_plan(num_tasks=2, add_dependent_task=True)  # task_2 depends on task_1
        task1_def = sample_plan_data["plan"][0]
        # task2_def = sample_plan_data["plan"][1] # Will be skipped

        mock_parser_instance = MagicMock(spec=ParserPlan)  # Create a mock ParserPlan instance
        mock_parser_instance.get_parsed_plan.return_value = sample_plan_data  # Revert to mocking get_parsed_plan
        MockParserPlan.return_value = mock_parser_instance  # Ensure the engine gets this mock

        self.mock_state_manager.get_task_status.return_value = "failed"

        # Only the first task will be executed
        self.mock_execute_single_task.side_effect = ["Result of task_1"]

        self.engine.execute_plan(mock_parser_instance)

        self.mock_state_manager.get_task_status.assert_called_once_with("task_1")
        # Only task_1 should be attempted
        self.mock_execute_single_task.assert_called_once_with(self.engine, task1_def)

        expected_state_calls = [
            call.set_task_state("task_1", "pending"),
            call.set_task_state("task_1", "in-progress"),
            call.set_task_state("task_1", "completed"),  # Mocked _execute_single_task returns success for task_1
            call.store_task_result("task_1", "Result of task_1"),
            call.save_state(),
            call.set_task_state("task_2", "pending"),
            call.get_task_status("task_1"),
            # get_task_status("task_1") is called by the engine here, returns "failed"
            call.set_task_state("task_2", "skipped", {"reason": "Dependency task_1 not met. Status: failed"}),
        ]
        self.mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)
