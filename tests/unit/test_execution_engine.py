import unittest
from unittest.mock import MagicMock, call, patch
import uuid

from src.ai_whisperer.execution_engine import ExecutionEngine, TaskExecutionError
from src.ai_whisperer.monitoring import TerminalMonitor # Import TerminalMonitor


class TestExecutionEngine(unittest.TestCase):

    def setUp(self):
        self.mock_state_manager = MagicMock()
        # self.engine = ExecutionEngine(self.mock_state_manager)
        # Patch the _execute_single_task for most tests to control its behavior
        # For specific tests (like failure), we might let the original run or mock differently
        patcher = patch.object(ExecutionEngine, '_execute_single_task', autospec=True)
        self.mock_execute_single_task = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Create a mock monitor for the ExecutionEngine
        self.mock_monitor = MagicMock(spec=TerminalMonitor)
        self.engine = ExecutionEngine(self.mock_state_manager, monitor=self.mock_monitor)


    def _get_sample_plan(self, num_tasks=2, add_failing_task=False, add_dependent_task=False):
        plan = {
            "task_id": str(uuid.uuid4()),
            "natural_language_goal": "Test plan",
            "input_hashes": {},
            "plan": []
        }
        for i in range(num_tasks):
            task_id = f"task_{i+1}"
            step = {
                "step_id": task_id,
                "description": f"This is task {i+1}",
                "agent_spec": {"type": "test_agent", "instructions": "do something"}
            }
            if add_dependent_task and i == num_tasks -1 : # Make the last task dependent on the first
                step["depends_on"] = ["task_1"]
            plan["plan"].append(step)

        if add_failing_task:
            plan["plan"].append({
                "step_id": "task_that_fails",
                "description": "This task will fail",
                "agent_spec": {"type": "failing_agent", "instructions": "fail"}
            })
        return plan

    def test_initialization(self):
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.state_manager, self.mock_state_manager)

    def test_execute_empty_plan(self):
        empty_plan = {"plan": []}
        self.engine.execute_plan(empty_plan)
        self.mock_state_manager.set_task_state.assert_not_called()
        self.mock_execute_single_task.assert_not_called()

    def test_execute_plan_none(self):
        with self.assertRaises(ValueError) as cm:
            self.engine.execute_plan(None)
        self.assertEqual(str(cm.exception), "Plan data cannot be None.")
        self.mock_state_manager.set_task_state.assert_not_called()
        self.mock_execute_single_task.assert_not_called()

    def test_execute_simple_sequential_plan(self):
        sample_plan = self._get_sample_plan(num_tasks=2)
        task1_def = sample_plan["plan"][0]
        task2_def = sample_plan["plan"][1]

        self.mock_execute_single_task.side_effect = [
            "Result of task_1",
            "Result of task_2"
        ]

        self.engine.execute_plan(sample_plan)

        # Check task execution calls
        self.mock_execute_single_task.assert_any_call(self.engine, task1_def)
        self.mock_execute_single_task.assert_any_call(self.engine, task2_def)
        self.assertEqual(self.mock_execute_single_task.call_count, 2)
        
        # Check state manager interactions
        expected_state_calls = [
            call.set_task_state("task_1", "pending"),
            call.set_task_state("task_1", "in-progress"),
            call.set_task_state("task_1", "completed"),
            call.save_state(),
            call.store_task_result("task_1", "Result of task_1"),
            call.set_task_state("task_2", "pending"),
            call.set_task_state("task_2", "in-progress"),
            call.set_task_state("task_2", "completed"),
            call.save_state(),
            call.store_task_result("task_2", "Result of task_2"),
        ]
        self.mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)


    def test_get_task_status(self):
        self.mock_state_manager.get_task_status.return_value = "completed"
        status = self.engine.get_task_status("task_123")
        self.mock_state_manager.get_task_status.assert_called_once_with("task_123")
        self.assertEqual(status, "completed")

    def test_get_task_status_not_found(self):
        self.mock_state_manager.get_task_status.return_value = None # Or raise specific exception
        status = self.engine.get_task_status("task_non_existent")
        self.mock_state_manager.get_task_status.assert_called_once_with("task_non_existent")
        self.assertIsNone(status)

    def test_get_task_result(self):
        self.mock_state_manager.get_task_result.return_value = {"data": "some_result"}
        result = self.engine.get_task_result("task_456")
        self.mock_state_manager.get_task_result.assert_called_once_with("task_456")
        self.assertEqual(result, {"data": "some_result"})

    def test_get_task_result_not_found_or_not_completed(self):
        self.mock_state_manager.get_task_result.return_value = None # Or raise specific exception
        result = self.engine.get_task_result("task_not_done")
        self.mock_state_manager.get_task_result.assert_called_once_with("task_not_done")
        self.assertIsNone(result)

    def test_execute_plan_with_task_failure(self):
        # This test uses the original _execute_single_task from the placeholder
        # to simulate an actual TaskExecutionError
        # Create a mock monitor for this specific instance
        mock_monitor_for_failure_test = MagicMock(spec=TerminalMonitor)
        engine_with_real_failure_logic = ExecutionEngine(self.mock_state_manager, monitor=mock_monitor_for_failure_test)

        sample_plan = self._get_sample_plan(num_tasks=1, add_failing_task=True)
        # plan: task_1, task_that_fails
        
        task1_def = sample_plan["plan"][0]
        failing_task_def = sample_plan["plan"][1]

        # Mock the behavior of _execute_single_task for this instance
        def side_effect_for_failure_test(self_arg, task_def_arg):
            if task_def_arg['step_id'] == "task_that_fails":
                raise TaskExecutionError("Intentional failure for task_that_fails")
            # Simulate successful execution for task_1 if it's not the failing task
            if task_def_arg['step_id'] == "task_1":
                 return f"Result of {task_def_arg['step_id']}"
            # This part should ideally not be reached if the failing task is handled above
            # but as a fallback or for other tasks, return a default result
            return f"Result of {task_def_arg['step_id']}"

        self.mock_execute_single_task.side_effect = side_effect_for_failure_test
        
        engine_with_real_failure_logic.execute_plan(sample_plan)

        # Check state manager calls for the failing task
        # Check state manager calls for the failing task
        expected_state_calls_for_failure = [
            call.set_task_state("task_1", "pending"),
            call.set_task_state("task_1", "in-progress"),
            call.set_task_state("task_1", "completed"),
            call.save_state(),
            call.store_task_result("task_1", "Result of task_1"),
            call.set_task_state("task_that_fails", "pending"),
            call.set_task_state("task_that_fails", "in-progress"),
            call.set_task_state("task_that_fails", "failed", {"error": "Intentional failure for task_that_fails"}),
        ]
        self.mock_state_manager.assert_has_calls(expected_state_calls_for_failure, any_order=False)
        self.mock_state_manager.store_task_result.assert_any_call("task_1", "Result of task_1")
        # Ensure result was not stored for the failing task
        for sm_call in self.mock_state_manager.store_task_result.call_args_list:
            self.assertNotEqual(sm_call[0][0], "task_that_fails")


    def test_execute_plan_with_dependency_met(self):
        sample_plan = self._get_sample_plan(num_tasks=2, add_dependent_task=True) # task_2 depends on task_1
        task1_def = sample_plan["plan"][0]
        task2_def = sample_plan["plan"][1]

        self.mock_execute_single_task.side_effect = [
            "Result of task_1",
            "Result of task_2"
        ]
        self.mock_state_manager.get_task_status.return_value = "completed" # Assume task_1 completes

        self.engine.execute_plan(sample_plan)

        self.mock_state_manager.get_task_status.assert_called_once_with("task_1")
        self.mock_execute_single_task.assert_any_call(self.engine, task1_def)
        self.mock_execute_single_task.assert_any_call(self.engine, task2_def)
        self.assertEqual(self.mock_execute_single_task.call_count, 2)

        expected_state_calls = [
            call.set_task_state("task_1", "pending"),
            call.set_task_state("task_1", "in-progress"),
            call.set_task_state("task_1", "completed"),
            call.save_state(),
            call.store_task_result("task_1", "Result of task_1"),
            call.set_task_state("task_2", "pending"),
            call.get_task_status("task_1"),
            # get_task_status("task_1") is called by the engine here
            call.set_task_state("task_2", "in-progress"),
            call.set_task_state("task_2", "completed"),
            call.save_state(),
            call.store_task_result("task_2", "Result of task_2"),
        ]
        self.mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)


    def test_execute_plan_with_dependency_not_met(self):
        sample_plan = self._get_sample_plan(num_tasks=2, add_dependent_task=True) # task_2 depends on task_1
        task1_def = sample_plan["plan"][0]
        # task2_def = sample_plan["plan"][1] # Will be skipped

        self.mock_execute_single_task.return_value = "Result of task_1" # Only task_1 will execute
        
        # Simulate task_1 not completing (e.g., it's 'failed' or 'in-progress')
        self.mock_state_manager.get_task_status.return_value = "failed" 

        self.engine.execute_plan(sample_plan)

        self.mock_state_manager.get_task_status.assert_called_once_with("task_1")
        # Only task_1 should be attempted
        self.mock_execute_single_task.assert_called_once_with(self.engine, task1_def)
        
        expected_state_calls = [
            call.set_task_state("task_1", "pending"),
            call.set_task_state("task_1", "in-progress"),
            call.set_task_state("task_1", "completed"), # Mocked _execute_single_task returns success for task_1
            call.save_state(),
            call.store_task_result("task_1", "Result of task_1"),
            call.set_task_state("task_2", "pending"),
            call.get_task_status("task_1"),
            # get_task_status("task_1") is called by the engine here, returns "failed"
            call.set_task_state("task_2", "skipped", {"reason": "Dependency task_1 not met. Status: failed"}),
        ]
        self.mock_state_manager.assert_has_calls(expected_state_calls, any_order=False)

    # Placeholder for conditional logic tests if the design evolves
    # def test_conditional_branching(self):
    #     # This would require a more complex plan structure and state manager interaction
    #     # For now, this is a placeholder based on "conditional logic" in the design doc.
    #     self.skipTest("Conditional logic testing not yet fully defined/implemented.")
    #     pass

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)