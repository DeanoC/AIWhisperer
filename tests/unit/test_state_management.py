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
from src.ai_whisperer.state_management import StateManager


class TestStateManagement(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file_path = os.path.join(self.temp_dir.name, "test_state.json")
        self.state_manager = StateManager(self.state_file_path)
        self.initial_state_data = {
            "tasks": {
                "task1": {"status": "pending", "result": {}},
                "task2": {"status": "in-progress", "result": {"data": "some_data"}},
            },
            "global_state": {"file_paths": ["/path/to/file1.txt"], "other_context": {"key": "value"}},
        }
        # Initialize the state manager's state for tests that need it pre-populated
        self.state_manager.state = self.initial_state_data.copy()


    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_state(self):
        self.state_manager.save_state()
        self.assertTrue(os.path.exists(self.state_file_path))
        loaded_state_manager = StateManager(self.state_file_path)
        loaded_state = loaded_state_manager.load_state()
        self.assertEqual(loaded_state, self.initial_state_data)

    def test_load_state_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            StateManager("non_existent_file.json").load_state()

    @patch("json.load")
    def test_load_state_corrupted_file(self, mock_json_load):
        mock_json_load.side_effect = json.JSONDecodeError("mock error", "doc", 0)
        # Create an empty file to simulate a corrupted one for loading
        with open(self.state_file_path, "w") as f:
            f.write("corrupted data")
        state_manager = StateManager(self.state_file_path)
        with self.assertRaises(IOError):
            state_manager.load_state()

    @patch("os.replace")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_state_atomicity_failure(self, mock_file_open, mock_os_replace):
        mock_os_replace.side_effect = OSError("Failed to replace")
        temp_file_path = self.state_file_path + ".tmp"

        with self.assertRaises(IOError):
            self.state_manager.save_state()

        # Check that open was called for the temp file
        mock_file_open.assert_any_call(temp_file_path, "w")
        # Ensure the original file does not exist if replace failed and temp was removed
        # This part is tricky to test perfectly without more complex mocking of os.path.exists
        # and os.remove within the save_state function's error handling.
        # For now, we assert that os.replace was called, and an IOError was raised.
        mock_os_replace.assert_called_once_with(temp_file_path, self.state_file_path)

    def test_update_task_status(self):
        task_id = "task1"
        self.state_manager.set_task_state(task_id, "completed")
        self.assertEqual(self.state_manager.get_task_status(task_id), "completed")
        self.state_manager.set_task_state(task_id, "failed")
        self.assertEqual(self.state_manager.get_task_status(task_id), "failed")
        task_id_new = "task3"
        self.state_manager.set_task_state(task_id_new, "in-progress")
        self.assertEqual(self.state_manager.get_task_status(task_id_new), "in-progress")


    def test_store_task_result(self):
        task_id = "task1"
        result_data = {"output": "success", "value": 123}
        self.state_manager.store_task_result(task_id, result_data)
        self.assertEqual(self.state_manager.get_task_result(task_id), result_data)

    def test_get_task_result(self):
        result = self.state_manager.get_task_result("task2")
        self.assertEqual(result, {"data": "some_data"})
        result_non_existent = self.state_manager.get_task_result("task_non_existent")
        self.assertIsNone(result_non_existent)
        empty_state_manager = StateManager(self.state_file_path + "_empty")
        result_empty_state = empty_state_manager.get_task_result("task1")
        self.assertIsNone(result_empty_state)

    def test_update_global_state(self):
        self.state_manager.update_global_state("new_key", "new_value")
        self.assertEqual(self.state_manager.get_global_state("new_key"), "new_value")
        self.state_manager.update_global_state("file_paths", ["/new/path.txt"])
        self.assertEqual(self.state_manager.get_global_state("file_paths"), ["/new/path.txt"])

    def test_get_global_state(self):
        value = self.state_manager.get_global_state("file_paths")
        self.assertEqual(value, ["/path/to/file1.txt"])
        value_non_existent = self.state_manager.get_global_state("non_existent_key")
        self.assertIsNone(value_non_existent)
        empty_state_manager = StateManager(self.state_file_path + "_empty")
        value_empty_state = empty_state_manager.get_global_state("key")
        self.assertIsNone(value_empty_state)

    def test_initial_state_structure_compliance(self):
        # Test if the initial state used in tests complies with the design
        self.assertIn("tasks", self.state_manager.state)
        self.assertIn("global_state", self.state_manager.state)
        if self.state_manager.state["tasks"]:
            first_task_id = list(self.state_manager.state["tasks"].keys())[0]
            first_task = self.state_manager.state["tasks"][first_task_id]
            self.assertIn("status", first_task)
            self.assertIn("result", first_task)
        if self.state_manager.state["global_state"]:
            self.assertIn("file_paths", self.state_manager.state["global_state"])
            self.assertIsInstance(self.state_manager.state["global_state"]["file_paths"], list)
            self.assertIn("other_context", self.state_manager.state["global_state"])
            self.assertIsInstance(self.state_manager.state["global_state"]["other_context"], dict)

    def test_store_ai_message_interaction_with_usage_info(self):
        task_id = "task1"
        ai_message_content = "This is the AI response."
        usage_info = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost": 0.0003,
            "completion_tokens_details": {},
            "prompt_tokens_details": {}
        }
        timestamp = "2025-05-11T18:30:05.123456Z"

        ai_message_turn = {
            "role": "assistant",
            "content": ai_message_content,
            "timestamp": timestamp,
            "usage_info": usage_info
        }

        # Assuming task1 is already initialized in self.state_manager.state
        self.state_manager.store_conversation_turn(task_id, ai_message_turn)

        # Assert that the state contains the message with usage info
        conversation_history = self.state_manager.get_conversation_history(task_id)
        self.assertEqual(len(conversation_history), 1)

        stored_message = conversation_history[0]
        self.assertEqual(stored_message["role"], "assistant")
        self.assertEqual(stored_message["content"], ai_message_content)
        self.assertEqual(stored_message["timestamp"], timestamp)
        self.assertIn("usage_info", stored_message)
        self.assertEqual(stored_message["usage_info"], usage_info)

    def test_store_user_message_interaction_with_timestamp(self):
        task_id = "task1"
        user_message_content = "This is the user prompt."
        timestamp = "2025-05-11T18:29:59.987654Z"

        user_message_turn = {
            "role": "user",
            "content": user_message_content,
            "timestamp": timestamp
        }

        # Assuming task1 is already initialized in self.state_manager.state
        self.state_manager.store_conversation_turn(task_id, user_message_turn)

        # Assert that the state contains the message with timestamp but no usage info
        conversation_history = self.state_manager.get_conversation_history(task_id)
        self.assertEqual(len(conversation_history), 1)

        stored_message = conversation_history[0]
        self.assertEqual(stored_message["role"], "user")
        self.assertEqual(stored_message["content"], user_message_content)
        self.assertEqual(stored_message["timestamp"], timestamp)
        self.assertNotIn("usage_info", stored_message)
