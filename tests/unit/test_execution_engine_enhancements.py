import unittest
from unittest.mock import MagicMock, patch, call
import requests
import json # Added import for the json module

from src.ai_whisperer.execution_engine import ExecutionEngine, TaskExecutionError
from src.ai_whisperer.ai_service_interaction import OpenRouterAPI, OpenRouterAPIError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError, ConfigError
from src.ai_whisperer.state_management import StateManager
from src.ai_whisperer.monitoring import TerminalMonitor
from src.ai_whisperer.logging import LogMessage, LogLevel, ComponentType

class TestExecutionEngineEnhancements(unittest.TestCase):

    def setUp(self):
        """Set up mocks and ExecutionEngine instance before each test."""
        self.mock_state_manager = MagicMock(spec=StateManager)
        self.mock_monitor = MagicMock(spec=TerminalMonitor)
        self.mock_ai_service_interaction = MagicMock(spec=OpenRouterAPI)

        # Patch the OpenRouterAPI constructor within ExecutionEngine's scope
        # This is necessary because ExecutionEngine will instantiate OpenRouterAPI
        # when it's enhanced to handle ai_interaction tasks.
        # For now, we'll mock it directly in the test of _execute_single_task
        # as the current _execute_single_task doesn't instantiate it.
        # Once _execute_single_task is updated, this patch will be moved to setUp.

        # Provide a mock config dictionary
        self.mock_config = {}
        self.engine = ExecutionEngine(self.mock_state_manager, self.mock_monitor, self.mock_config)

    @patch('src.ai_whisperer.execution_engine.OpenRouterAPI')
    def test_execute_single_task_ai_interaction_success(self, MockOpenRouterAPI):
        """Test successful execution of an ai_interaction task."""
        # Configure the mocked AI service interaction
        mock_ai_instance = MockOpenRouterAPI.return_value
        mock_ai_instance.call_chat_completion.return_value = "AI generated response"

        # Simulate a task definition for AI interaction
        task_def = {
            "step_id": "task_ask_country",
            "agent_spec": {
                "type": "ai_interaction",
                "model": "test-model",
                "params": {"temperature": 0.7}
            },
            "instructions": "What is the capital of France?",
            "input_artifacts": [], # Assuming no input artifacts for simplicity in this test
            "depends_on": []
        }

        # Simulate StateManager returning no history
        self.mock_state_manager.get_task_result.return_value = None # No history for this simple case

        # Execute the task
        # The current _execute_single_task doesn't handle agent_spec.type,
        # so we'll need to manually simulate the expected logic for the test.
        # This test is written assuming the enhancement to _execute_single_task is in place.

        # Expected calls to StateManager and AIServiceInteraction
        expected_ai_call_args = {
            "prompt_text": task_def["instructions"],
            "model": task_def["agent_spec"]["model"],
            "params": task_def["agent_spec"]["params"],
            "system_prompt": None, # Assuming no system prompt in this task def
            "tools": None,
            "response_format": None,
            "images": None,
            "pdfs": None,
            "messages_history": [] # Empty history for the first turn
        }

        # Simulate the enhanced _execute_single_task logic
        task_id = task_def.get('step_id', 'unknown_task')
        self.mock_state_manager.set_task_state(task_id, "in-progress")
        self.mock_monitor.set_runner_status_info(f"In Progress: {task_id}")
        self.mock_monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_in_progress", f"Task {task_id} is in progress.", step_id=task_id))

        # Simulate fetching history (even if empty)
        conversation_history = self.mock_state_manager.get_task_result(task_id, result_key="conversation_history") or []

        # Simulate calling the AI service
        ai_response = mock_ai_instance.call_chat_completion(
            prompt_text=task_def["instructions"],
            model=task_def["agent_spec"]["model"],
            params=task_def["agent_spec"]["params"],
            system_prompt=None, # Need to determine how system prompt is handled
            tools=task_def["agent_spec"].get("tools"),
            response_format=task_def["agent_spec"].get("response_format"),
            images=task_def["agent_spec"].get("images"),
            pdfs=task_def["agent_spec"].get("pdfs"),
            messages_history=conversation_history
        )

        # Simulate processing the result and updating state
        result = ai_response # Assuming the response is the direct result for now
        self.mock_state_manager.set_task_state(task_id, "completed")
        self.mock_state_manager.store_task_result(task_id, result)
        self.mock_state_manager.save_state()
        self.mock_monitor.set_runner_status_info(f"Completed: {task_id}")
        self.mock_monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_completed", f"Task {task_id} completed successfully.", step_id=task_id, duration_ms=unittest.mock.ANY))


        # Assertions
        MockOpenRouterAPI.assert_called_once() # Verify OpenRouterAPI was instantiated
        mock_ai_instance.call_chat_completion.assert_called_once_with(**expected_ai_call_args)

        self.mock_state_manager.set_task_state.assert_any_call(task_id, "in-progress")
        self.mock_state_manager.set_task_state.assert_any_call(task_id, "completed")
        self.mock_state_manager.store_task_result.assert_called_once_with(task_id, "AI generated response")
        self.mock_state_manager.save_state.assert_called_once()

        self.mock_monitor.set_runner_status_info.assert_any_call(f"In Progress: {task_id}")
        self.mock_monitor.set_runner_status_info.assert_any_call(f"Completed: {task_id}")
        self.mock_monitor.add_log_message.assert_any_call(unittest.mock.ANY) # Check for log messages

    @patch('src.ai_whisperer.execution_engine.OpenRouterAPI')
    def test_execute_single_task_ai_interaction_api_error(self, MockOpenRouterAPI):
        """Test execution of an ai_interaction task that results in an API error."""
        mock_ai_instance = MockOpenRouterAPI.return_value
        # Simulate an API error
        mock_ai_instance.call_chat_completion.side_effect = OpenRouterAPIError("Simulated API Error", status_code=400, response=MagicMock())

        task_def = {
            "step_id": "task_api_error",
            "agent_spec": {
                "type": "ai_interaction",
                "model": "test-model"
            },
            "instructions": "Generate an error",
            "depends_on": []
        }

        self.mock_state_manager.get_task_result.return_value = None

        # Simulate the enhanced _execute_single_task logic
        task_id = task_def.get('step_id', 'unknown_task')
        self.mock_state_manager.set_task_state(task_id, "in-progress")
        self.mock_monitor.set_runner_status_info(f"In Progress: {task_id}")
        self.mock_monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_in_progress", f"Task {task_id} is in progress.", step_id=task_id))

        try:
            conversation_history = self.mock_state_manager.get_task_result(task_id, result_key="conversation_history") or []
            mock_ai_instance.call_chat_completion(
                prompt_text=task_def["instructions"],
                model=task_def["agent_spec"]["model"],
                params=task_def["agent_spec"].get("params", {}),
                system_prompt=None,
                tools=task_def["agent_spec"].get("tools"),
                response_format=task_def["agent_spec"].get("response_format"),
                images=task_def["agent_spec"].get("images"),
                pdfs=task_def["agent_spec"].get("pdfs"),
                messages_history=conversation_history
            )
        except OpenRouterAPIError as e:
            error_message = str(e)
            self.mock_state_manager.set_task_state(task_id, "failed", {"error": error_message})
            self.mock_monitor.set_runner_status_info(f"Failed: {task_id}")
            self.mock_monitor.add_log_message(LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "task_failed", f"Task {task_id} failed: {error_message}", step_id=task_id, duration_ms=unittest.mock.ANY, details={"error": error_message}))
        except Exception as e:
             # Catch any other unexpected error
            error_message = f"Unexpected error during execution of task {task_id}: {str(e)}"
            self.mock_state_manager.set_task_state(task_id, "failed", {"error": error_message})
            self.mock_monitor.set_runner_status_info(f"Failed: {task_id}")
            self.mock_monitor.add_log_message(LogMessage(LogLevel.CRITICAL, ComponentType.EXECUTION_ENGINE, "task_failed_unexpected", error_message, step_id=task_id, duration_ms=unittest.mock.ANY, details={"error": error_message, "traceback": unittest.mock.ANY}))


        # Assertions
        MockOpenRouterAPI.assert_called_once()
        mock_ai_instance.call_chat_completion.assert_called_once() # Check if it was called

        self.mock_state_manager.set_task_state.assert_any_call(task_id, "in-progress")
        self.mock_state_manager.set_task_state.assert_any_call(task_id, "failed", {"error": "Simulated API Error"})
        self.mock_state_manager.store_task_result.assert_not_called() # Result should not be stored on failure

        self.mock_monitor.set_runner_status_info.assert_any_call(f"In Progress: {task_id}")
        self.mock_monitor.set_runner_status_info.assert_any_call(f"Failed: {task_id}")
        self.mock_monitor.add_log_message.assert_any_call(unittest.mock.ANY) # Check for log messages

    @patch('src.ai_whisperer.execution_engine.OpenRouterAPI')
    def test_execute_single_task_ai_interaction_with_history(self, MockOpenRouterAPI):
        """Test execution of an ai_interaction task with conversation history."""
        mock_ai_instance = MockOpenRouterAPI.return_value
        mock_ai_instance.call_chat_completion.return_value = "AI response to second turn"

        task_def = {
            "step_id": "task_follow_up",
            "agent_spec": {
                "type": "ai_interaction",
                "model": "test-model"
            },
            "instructions": "What about its main landmark?",
            "depends_on": ["task_ask_country"] # Depends on the previous AI task
        }

        # Simulate StateManager returning previous conversation history
        previous_history = [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "Paris"}
        ]
        # StateManager stores results by task_id, and conversation history would be a specific key within that result
        self.mock_state_manager.get_task_result.return_value = previous_history # Simulate getting history

        # Simulate the enhanced _execute_single_task logic
        task_id = task_def.get('step_id', 'unknown_task')
        self.mock_state_manager.set_task_state(task_id, "in-progress")
        self.mock_monitor.set_runner_status_info(f"In Progress: {task_id}")
        self.mock_monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_in_progress", f"Task {task_id} is in progress.", step_id=task_id))

        # Simulate fetching history
        # In a real implementation, this would likely involve iterating through dependencies
        # and compiling history from their results. For this test, we directly provide it.
        conversation_history = self.mock_state_manager.get_task_result("task_ask_country", result_key="conversation_history") or []
        # Add the current user prompt to the history before sending to AI
        conversation_history.append({"role": "user", "content": task_def["instructions"]})


        # Simulate calling the AI service
        ai_response = mock_ai_instance.call_chat_completion(
            prompt_text=task_def["instructions"], # Note: prompt_text might be redundant if history is used
            model=task_def["agent_spec"]["model"],
            params=task_def["agent_spec"].get("params", {}),
            system_prompt=None,
            tools=task_def["agent_spec"].get("tools"),
            response_format=task_def["agent_spec"].get("response_format"),
            images=task_def["agent_spec"].get("images"),
            pdfs=task_def["agent_spec"].get("pdfs"),
            messages_history=conversation_history # Pass the compiled history
        )

        # Simulate processing the result and updating state
        result = ai_response
        # In a real implementation, the AI's response would also be added to the history
        updated_history = conversation_history + [{"role": "assistant", "content": result}]
        self.mock_state_manager.set_task_state(task_id, "completed")
        # Store both the result and the updated conversation history
        self.mock_state_manager.store_task_result(task_id, result)
        self.mock_state_manager.store_task_result(task_id, updated_history, result_key="conversation_history")
        self.mock_state_manager.save_state()
        self.mock_monitor.set_runner_status_info(f"Completed: {task_id}")
        self.mock_monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_completed", f"Task {task_id} completed successfully.", step_id=task_id, duration_ms=unittest.mock.ANY))


        # Assertions
        MockOpenRouterAPI.assert_called_once()
        # Verify call_chat_completion was called with the correct history
        expected_history_sent_to_ai = previous_history + [{"role": "user", "content": task_def["instructions"]}]
        mock_ai_instance.call_chat_completion.assert_called_once_with(
             prompt_text=task_def["instructions"],
             model=task_def["agent_spec"]["model"],
             params=task_def["agent_spec"].get("params", {}),
             system_prompt=None,
             tools=task_def["agent_spec"].get("tools"),
             response_format=task_def["agent_spec"].get("response_format"),
             images=task_def["agent_spec"].get("images"),
             pdfs=task_def["agent_spec"].get("pdfs"),
             messages_history=expected_history_sent_to_ai
        )

        self.mock_state_manager.set_task_state.assert_any_call(task_id, "in-progress")
        self.mock_state_manager.set_task_state.assert_any_call(task_id, "completed")
        self.mock_state_manager.store_task_result.assert_any_call(task_id, "AI response to second turn")
        self.mock_state_manager.store_task_result.assert_any_call(task_id, updated_history, result_key="conversation_history")
        self.mock_state_manager.save_state.assert_called_once()

        self.mock_monitor.set_runner_status_info.assert_any_call(f"In Progress: {task_id}")
        self.mock_monitor.set_runner_status_info.assert_any_call(f"Completed: {task_id}")
        self.mock_monitor.add_log_message.assert_any_call(unittest.mock.ANY) # Check for log messages


class TestAIServiceInteractionEnhancements(unittest.TestCase):

    def setUp(self):
        """Set up mocks and OpenRouterAPI instance before each test."""
        self.mock_config = {
            "api_key": "fake_api_key",
            "model": "test-model",
            "params": {"temperature": 0.5},
            "site_url": "http://test.com",
            "app_name": "TestApp",
            "timeout_seconds": 10,
            "cache": False # Disable cache for most tests
        }
        self.api = OpenRouterAPI(self.mock_config)

    @patch('requests.post')
    def test_call_chat_completion_success_text(self, mock_post):
        """Test successful call_chat_completion with a simple text response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hello, world!"}}]
        }
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Say hello"
        model = "test-model"
        params = {"temperature": 0.7}

        result = self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer fake_api_key",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://test.com",
                "X-Title": "TestApp",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            },
            timeout=10
        )
        self.assertEqual(result, "Hello, world!")

    @patch('requests.post')
    def test_call_chat_completion_success_tool_calls(self, mock_post):
        """Test successful call_chat_completion with tool calls in the response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": '{"location": "Paris"}'}
                    }
                ]
            }}]
        }
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "What's the weather in Paris?"
        model = "test-model"
        params = {}
        tools = [{"type": "function", "function": {"name": "get_weather", "description": "Gets weather", "parameters": {}}}]

        result = self.api.call_chat_completion(prompt, model, params, tools=tools)

        mock_post.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=unittest.mock.ANY, # Headers are tested in other cases
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "tools": tools
            },
            timeout=10
        )
        self.assertIsInstance(result, dict)
        self.assertIn("tool_calls", result)
        self.assertIsNone(result.get("content"))
        self.assertEqual(len(result["tool_calls"]), 1)
        self.assertEqual(result["tool_calls"][0]["function"]["name"], "get_weather")

    @patch('requests.post')
    def test_call_chat_completion_api_error(self, mock_post):
        """Test call_chat_completion handling of API errors (e.g., 400)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": {"message": "Bad request format"}}'
        mock_response.json.return_value = {"error": {"message": "Bad request format"}}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Invalid request"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterAPIError, "OpenRouter API Error: 400 - Bad request format"):
            self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_chat_completion_auth_error(self, mock_post):
        """Test call_chat_completion handling of authentication errors (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": {"message": "Invalid API key"}}'
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Test auth"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterAuthError, "Authentication failed: OpenRouter API Error: 401 - Invalid API key"):
            self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_chat_completion_rate_limit_error(self, mock_post):
        """Test call_chat_completion handling of rate limit errors (429)."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"error": {"message": "Rate limit exceeded"}}'
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_response.headers = {'Content-Type': 'application/json', 'Retry-After': '60'}
        mock_post.return_value = mock_response

        prompt = "Test rate limit"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterRateLimitError, "Rate limit exceeded: OpenRouter API Error: 429 - Rate limit exceeded"):
            self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_chat_completion_network_error(self, mock_post):
        """Test call_chat_completion handling of network errors."""
        mock_post.side_effect = requests.exceptions.RequestException("Simulated network error")

        prompt = "Test network error"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterConnectionError, "Network error connecting to OpenRouter API: Simulated network error"):
            self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_chat_completion_timeout_error(self, mock_post):
        """Test call_chat_completion handling of timeout errors."""
        mock_post.side_effect = requests.exceptions.Timeout("Simulated timeout")

        prompt = "Test timeout"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterConnectionError, "Request to OpenRouter API timed out after 10 seconds: Simulated timeout"):
            self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_chat_completion_invalid_json_response(self, mock_post):
        """Test call_chat_completion handling of non-JSON or invalid JSON responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "This is not JSON"
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_response.headers = {'Content-Type': 'text/plain'} # Simulate non-JSON content type
        mock_post.return_value = mock_response

        prompt = "Test invalid json"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterAPIError, "Failed to decode JSON response"):
             self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_chat_completion_unexpected_response_structure(self, mock_post):
        """Test call_chat_completion handling of unexpected JSON structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not_choices": []} # Missing 'choices' key
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Test unexpected structure"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterAPIError, "Unexpected response format: 'choices' array is missing, empty, or not an array."):
             self.api.call_chat_completion(prompt, model, params)

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_call_chat_completion_with_history(self, mock_post):
        """Test call_chat_completion with conversation history."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Response to turn 2"}}]
        }
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "What about its main landmark?"
        model = "test-model"
        params = {}
        history = [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "Paris"}
        ]

        self.api.call_chat_completion(prompt, model, params, messages_history=history)

        expected_messages = history + [{"role": "user", "content": prompt}]

        mock_post.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=unittest.mock.ANY,
            json={
                "model": model,
                "messages": expected_messages,
                **params
            },
            timeout=10
        )

    @patch('requests.post')
    def test_call_chat_completion_with_system_prompt(self, mock_post):
        """Test call_chat_completion with a system prompt (first turn)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Acknowledged."}}]
        }
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Start the task."
        model = "test-model"
        params = {}
        system_prompt = "You are a helpful assistant."

        self.api.call_chat_completion(prompt, model, params, system_prompt=system_prompt)

        expected_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        mock_post.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=unittest.mock.ANY,
            json={
                "model": model,
                "messages": expected_messages,
                **params
            },
            timeout=10
        )

    @patch('requests.post')
    def test_call_chat_completion_with_images(self, mock_post):
        """Test call_chat_completion with image data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Description of image."}}]
        }
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Describe this image."
        model = "test-model"
        params = {}
        images = ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="] # 1x1 transparent pixel base64

        self.api.call_chat_completion(prompt, model, params, images=images)

        expected_messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": images[0], "detail": "auto"}}
            ]}
        ]

        mock_post.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=unittest.mock.ANY,
            json={
                "model": model,
                "messages": expected_messages,
                **params
            },
            timeout=10
        )

    @patch('requests.post')
    def test_call_chat_completion_with_pdfs(self, mock_post):
        """Test call_chat_completion with PDF data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Summary of PDF."}}]
        }
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Summarize this document."
        model = "test-model"
        params = {}
        pdfs = ["data:application/pdf;base64,JVBERi0xLjMKJcKl..." ] # Dummy base64 PDF data

        self.api.call_chat_completion(prompt, model, params, pdfs=pdfs)

        expected_messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "file", "file": {"url": pdfs[0]}}
            ]}
        ]

        mock_post.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=unittest.mock.ANY,
            json={
                "model": model,
                "messages": expected_messages,
                **params
            },
            timeout=10
        )

    @patch('requests.post')
    def test_call_chat_completion_with_cache_enabled(self, mock_post):
        """Test call_chat_completion with caching enabled."""
        # Enable cache for this test
        self.api.openrouter_config['cache'] = True
        self.api._cache_store = {} # Reset cache

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Cached response."}}]
        }
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Cache test"
        model = "test-model"
        params = {"temperature": 0.1}

        # First call - should hit the API and cache the response
        result1 = self.api.call_chat_completion(prompt, model, params)
        mock_post.assert_called_once()
        self.assertEqual(result1, "Cached response.")
        self.assertEqual(len(self.api.cache), 1)

        # Reset mock to check if API is called again
        mock_post.reset_mock()

        # Second call with the same parameters - should return from cache
        result2 = self.api.call_chat_completion(prompt, model, params)
        mock_post.assert_not_called() # API should NOT be called
        self.assertEqual(result2, "Cached response.")
        self.assertEqual(len(self.api.cache), 1) # Cache size should remain 1

        # Call with different parameters - should hit the API and add to cache
        mock_post.return_value = mock_response # Ensure mock returns a response
        result3 = self.api.call_chat_completion("Different prompt", model, params)
        mock_post.assert_called_once() # API should be called
        self.assertEqual(result3, "Cached response.")
        self.assertEqual(len(self.api.cache), 2) # Cache size should be 2

    @patch('requests.post')
    def test_stream_chat_completion_success(self, mock_post):
        """Test successful stream_chat_completion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulate streaming data chunks
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"role": "assistant"}}]}',
            b'',
            b'data: {"choices": [{"delta": {"content": "Hello,"}}]}',
            b'',
            b'data: {"choices": [{"delta": {"content": " world!"}}]}',
            b'',
            b'data: [DONE]',
            b''
        ]
        mock_response.headers = {'Content-Type': 'text/event-stream'}
        mock_post.return_value = mock_response

        prompt = "Stream test"
        model = "test-model"
        params = {}

        chunks = list(self.api.stream_chat_completion(prompt, model, params))

        mock_post.assert_called_once_with(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=unittest.mock.ANY,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                **params,
                "stream": True
            },
            stream=True,
            timeout=10
        )

        # Check the parsed chunks
        self.assertEqual(len(chunks), 3) # Should yield 3 data chunks before DONE
        self.assertEqual(chunks[0], {"choices": [{"delta": {"role": "assistant"}}]})
        self.assertEqual(chunks[1], {"choices": [{"delta": {"content": "Hello,"}}]})
        self.assertEqual(chunks[2], {"choices": [{"delta": {"content": " world!"}}]})

    @patch('requests.post')
    def test_stream_chat_completion_api_error(self, mock_post):
        """Test stream_chat_completion handling of API errors before streaming starts."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": {"message": "Bad stream request"}}'
        mock_response.json.return_value = {"error": {"message": "Bad stream request"}}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_post.return_value = mock_response

        prompt = "Test stream error"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterAPIError, "OpenRouter API Error: 400 - Bad stream request"):
            # Iterating over the generator will trigger the request and error
            list(self.api.stream_chat_completion(prompt, model, params))

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_stream_chat_completion_network_error(self, mock_post):
        """Test stream_chat_completion handling of network errors."""
        mock_post.side_effect = requests.exceptions.RequestException("Simulated stream network error")

        prompt = "Test stream network error"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterConnectionError, "Network error connecting to OpenRouter API: Simulated stream network error"):
            list(self.api.stream_chat_completion(prompt, model, params))

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_stream_chat_completion_timeout_error(self, mock_post):
        """Test stream_chat_completion handling of timeout errors."""
        mock_post.side_effect = requests.exceptions.Timeout("Simulated stream timeout")

        prompt = "Test stream timeout"
        model = "test-model"
        params = {}

        with self.assertRaisesRegex(OpenRouterConnectionError, "Request to OpenRouter API timed out after 10 seconds: Simulated stream timeout"):
            list(self.api.stream_chat_completion(prompt, model, params))

        mock_post.assert_called_once()

    @patch('requests.post')
    def test_stream_chat_completion_invalid_json_chunk(self, mock_post):
        """Test stream_chat_completion handling of invalid JSON in a data chunk."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"role": "assistant"}}]}',
            b'',
            b'data: This is not JSON', # Invalid chunk
            b'',
            b'data: [DONE]',
            b''
        ]
        mock_response.headers = {'Content-Type': 'text/event-stream'}
        mock_post.return_value = mock_response

        prompt = "Test invalid stream json"
        model = "test-model"
        params = {}

        # The generator should yield the first valid chunk, then raise an error on the invalid one
        generator = self.api.stream_chat_completion(prompt, model, params)

        # Get the first valid chunk
        first_chunk = next(generator)
        self.assertEqual(first_chunk, {"choices": [{"delta": {"role": "assistant"}}]})

        # Expect an API error when trying to process the invalid chunk
        with self.assertRaisesRegex(OpenRouterAPIError, "Failed to decode JSON from stream chunk"):
            next(generator) # Attempt to get the next chunk

        mock_post.assert_called_once()

    @patch('requests.get')
    def test_list_models_success(self, mock_get):
        """Test successful list_models call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "model-1", "name": "Model One"},
                {"id": "model-2", "name": "Model Two"}
            ]
        }
        mock_response.text = json.dumps(mock_response.json.return_value) # Ensure text is available for logging
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_response

        models = self.api.list_models()

        mock_get.assert_called_once_with(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": "Bearer fake_api_key",
                "Content-Type": "application/json",
            },
            timeout=30
        )
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["id"], "model-1")
        self.assertEqual(models[1]["id"], "model-2")

    @patch('requests.get')
    def test_list_models_api_error(self, mock_get):
        """Test list_models handling of API errors (e.g., 400)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": {"message": "Bad models request"}}'
        mock_response.json.return_value = {"error": {"message": "Bad models request"}}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(OpenRouterAPIError, "API request failed: Bad models request \(HTTP 400\)"):
            self.api.list_models()

        mock_get.assert_called_once()

    @patch('requests.get')
    def test_list_models_auth_error(self, mock_get):
        """Test list_models handling of authentication errors (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": {"message": "Invalid models API key"}}'
        mock_response.json.return_value = {"error": {"message": "Invalid models API key"}}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(OpenRouterAuthError, "Authentication failed: Invalid models API key \(HTTP 401\)"):
            self.api.list_models()

        mock_get.assert_called_once()

    @patch('requests.get')
    def test_list_models_rate_limit_error(self, mock_get):
        """Test list_models handling of rate limit errors (429)."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"error": {"message": "Models rate limit exceeded"}}'
        mock_response.json.return_value = {"error": {"message": "Models rate limit exceeded"}}
        mock_response.headers = {'Content-Type': 'application/json', 'Retry-After': '60'}
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(OpenRouterRateLimitError, "Rate limit exceeded: Models rate limit exceeded \(HTTP 429\)"):
            self.api.list_models()

        mock_get.assert_called_once()

    @patch('requests.get')
    def test_list_models_network_error(self, mock_get):
        """Test list_models handling of network errors."""
        mock_get.side_effect = requests.exceptions.RequestException("Simulated models network error")

        with self.assertRaisesRegex(OpenRouterConnectionError, "Network error connecting to OpenRouter API: Simulated models network error"):
            self.api.list_models()

        mock_get.assert_called_once()

    @patch('requests.get')
    def test_list_models_invalid_json_response(self, mock_get):
        """Test list_models handling of non-JSON or invalid JSON responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "This is not JSON"
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(OpenRouterAPIError, "Failed to decode JSON response"):
             self.api.list_models()

        mock_get.assert_called_once()

    @patch('requests.get')
    def test_list_models_unexpected_response_structure(self, mock_get):
        """Test list_models handling of unexpected JSON structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not_data": []} # Missing 'data' key
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(OpenRouterAPIError, "Unexpected response format: 'data' array is missing or not a list."):
             self.api.list_models()

        mock_get.assert_called_once()

    def test_openrouterapi_init_missing_api_key(self):
        """Test OpenRouterAPI initialization with missing api_key."""
        config = {"model": "test-model"}
        with self.assertRaisesRegex(ConfigError, "Missing expected configuration key within 'openrouter' section: api_key"):
            OpenRouterAPI(config)

    def test_openrouterapi_init_missing_model(self):
        """Test OpenRouterAPI initialization with missing model."""
        config = {"api_key": "fake_key"}
        with self.assertRaisesRegex(ConfigError, "Missing expected configuration key within 'openrouter' section: model"):
            OpenRouterAPI(config)

    def test_openrouterapi_init_invalid_config_type(self):
        """Test OpenRouterAPI initialization with invalid config type."""
        config = "not a dict"
        with self.assertRaisesRegex(ConfigError, "Invalid 'openrouter' configuration: Expected a dictionary, got <class 'str'>"):
            OpenRouterAPI(config)


if __name__ == '__main__':
    unittest.main()