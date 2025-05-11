import unittest
import json
import os
import tempfile
from unittest.mock import patch, mock_open

# Assuming the state management functions will be in a module,
# let's say `ai_whisperer.state_management`
# In a real scenario, these would be imported:
from src.ai_whisperer.state_management import (
    save_state,
    load_state,
    update_task_status,
    store_task_result,
    get_task_result,
    update_global_state,
    get_global_state,
)


class TestStateManagement(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file_path = os.path.join(self.temp_dir.name, "test_state.json")
        self.initial_state = {
            "tasks": {
                "task1": {"status": "pending", "result": {}},
                "task2": {"status": "in-progress", "result": {"data": "some_data"}},
            },
            "global_state": {"file_paths": ["/path/to/file1.txt"], "other_context": {"key": "value"}},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_state(self):
        save_state(self.initial_state, self.state_file_path)
        self.assertTrue(os.path.exists(self.state_file_path))
        loaded_state = load_state(self.state_file_path)
        self.assertEqual(loaded_state, self.initial_state)

    def test_load_state_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_state("non_existent_file.json")

    @patch("json.load")
    def test_load_state_corrupted_file(self, mock_json_load):
        mock_json_load.side_effect = json.JSONDecodeError("mock error", "doc", 0)
        # Create an empty file to simulate a corrupted one for loading
        with open(self.state_file_path, "w") as f:
            f.write("corrupted data")
        with self.assertRaises(IOError):
            load_state(self.state_file_path)

    @patch("os.replace")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_state_atomicity_failure(self, mock_file_open, mock_os_replace):
        mock_os_replace.side_effect = OSError("Failed to replace")
        temp_file_path = self.state_file_path + ".tmp"

        with self.assertRaises(IOError):
            save_state(self.initial_state, self.state_file_path)

        # Check that open was called for the temp file
        mock_file_open.assert_any_call(temp_file_path, "w")
        # Ensure the original file does not exist if replace failed and temp was removed
        # This part is tricky to test perfectly without more complex mocking of os.path.exists
        # and os.remove within the save_state function's error handling.
        # For now, we assert that os.replace was called, and an IOError was raised.
        mock_os_replace.assert_called_once_with(temp_file_path, self.state_file_path)

    def test_update_task_status(self):
        state = {}
        updated_state = update_task_status(state, "task1", "completed")
        self.assertEqual(updated_state["tasks"]["task1"]["status"], "completed")
        updated_state = update_task_status(updated_state, "task1", "failed")
        self.assertEqual(updated_state["tasks"]["task1"]["status"], "failed")
        updated_state = update_task_status(updated_state, "task2", "pending")
        self.assertEqual(updated_state["tasks"]["task2"]["status"], "pending")

    def test_store_task_result(self):
        state = {}
        result_data = {"output": "success", "value": 123}
        updated_state = store_task_result(state, "task1", result_data)
        self.assertEqual(updated_state["tasks"]["task1"]["result"], result_data)

    def test_get_task_result(self):
        result = get_task_result(self.initial_state, "task2")
        self.assertEqual(result, {"data": "some_data"})
        result_non_existent = get_task_result(self.initial_state, "task_non_existent")
        self.assertIsNone(result_non_existent)
        empty_state = {}
        result_empty_state = get_task_result(empty_state, "task1")
        self.assertIsNone(result_empty_state)

    def test_update_global_state(self):
        state = {}
        updated_state = update_global_state(state, "new_key", "new_value")
        self.assertEqual(updated_state["global_state"]["new_key"], "new_value")
        updated_state = update_global_state(updated_state, "file_paths", ["/new/path.txt"])
        self.assertEqual(updated_state["global_state"]["file_paths"], ["/new/path.txt"])

    def test_get_global_state(self):
        value = get_global_state(self.initial_state, "file_paths")
        self.assertEqual(value, ["/path/to/file1.txt"])
        value_non_existent = get_global_state(self.initial_state, "non_existent_key")
        self.assertIsNone(value_non_existent)
        empty_state = {}
        value_empty_state = get_global_state(empty_state, "key")
        self.assertIsNone(value_empty_state)

    def test_initial_state_structure_compliance(self):
        # Test if the initial state used in tests complies with the design
        self.assertIn("tasks", self.initial_state)
        self.assertIn("global_state", self.initial_state)
        if self.initial_state["tasks"]:
            first_task_id = list(self.initial_state["tasks"].keys())[0]
            first_task = self.initial_state["tasks"][first_task_id]
            self.assertIn("status", first_task)
            self.assertIn("result", first_task)
        if self.initial_state["global_state"]:
            self.assertIn("file_paths", self.initial_state["global_state"])
            self.assertIsInstance(self.initial_state["global_state"]["file_paths"], list)
            self.assertIn("other_context", self.initial_state["global_state"])
            self.assertIsInstance(self.initial_state["global_state"]["other_context"], dict)

    # Note: Testing file locking for concurrency (save_state, load_state)
    # is complex in unit tests and often requires integration-style tests
    # or very sophisticated mocking of file system operations and threading/multiprocessing.
    # The atomicity test for save_state (writing to .tmp then renaming) is a good step.


if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
