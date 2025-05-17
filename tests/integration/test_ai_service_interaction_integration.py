import pytest
from unittest.mock import patch, MagicMock
import json
from io import BytesIO
import requests
from ai_whisperer.state_management import StateManager # Import StateManager
from ai_whisperer.agent_handlers.ai_interaction import handle_ai_interaction # Import the handler
from ai_whisperer.execution_engine import ExecutionEngine # Import ExecutionEngine (or mock it)
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType # Import logging components

from ai_whisperer.ai_service_interaction import OpenRouterAPI, API_URL
from ai_whisperer.exceptions import (
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError,
)

# Mock configuration for testing
MOCK_CONFIG = {
    "api_key": "test_api_key",
    "model": "test_model",
    "params": {"temperature": 0.7},
    "site_url": "test_site_url",
    "app_name": "test_app_name",
    "cache": False,
    "timeout_seconds": 10,
}

# Mock response data for streaming
MOCK_STREAMING_CHUNKS = [
    b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{"role":"assistant","content":"{\\n  \\"description\\": \\"Mock streaming subtask description\\",\\n  \\"instructions\\": \\"Mock streaming subtask instructions\\",\\n  \\"input_artifacts\\": [],\\n  \\"output_artifacts\\": [],\\n  \\"constraints\\": [],\\n  \\"validation_criteria\\": [],\\n  \\"subtask_id\\": \\"mock-streaming-subtask-789\\",\\n  \\"task_id\\": \\""}}]}\n',
    b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{"content":"mock-streaming-task-012\\"\\n}"}}]}\n',
    b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{}}]}\n',  # Empty delta
    b"data: [DONE]\n",
]

# Mock response data for non-streaming
MOCK_NON_STREAMING_RESPONSE = {
    "id": "chatcmpl-xyz",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "test_model",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": '{\n  "description": "Mock subtask description",\n  "instructions": "Mock subtask instructions",\n  "input_artifacts": [],\n  "output_artifacts": [],\n  "constraints": [],\n  "validation_criteria": [],\n  "subtask_id": "mock-subtask-123",\n  "task_id": "mock-task-456"\n}',
            },
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
}


class MockResponse:
    """A mock class for requests.Response."""

    def __init__(self, status_code, json_data=None, text=None, headers=None, iter_lines_data=None):
        self.status_code = status_code
        self._json_data = json_data
        self._text = text
        self.headers = headers if headers is not None else {}
        self._iter_lines_data = iter_lines_data
        self.request = MagicMock()  # Add a mock request object

    def json(self):
        if self._json_data is not None:
            return self._json_data
        raise json.JSONDecodeError("No JSON data", "", 0)

    @property
    def text(self):
        return self._text if self._text is not None else json.dumps(self._json_data)

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(f"HTTP error {self.status_code}", response=self)

    def iter_lines(self):
        if self._iter_lines_data:
            for line in self._iter_lines_data:
                yield line
        else:
            yield from []  # Yield nothing if no data


class TestOpenRouterAPIIntegration:
    @pytest.fixture(autouse=True)
    def clear_tool_registry(self):
        # Ensure ToolRegistry is cleared before each test to avoid cross-test contamination
        from ai_whisperer.tools.tool_registry import ToolRegistry
        ToolRegistry().reload_tools()


    @pytest.fixture
    def api_client(self):
        """Fixture to create an OpenRouterAPI instance with mock config."""
        return OpenRouterAPI(MOCK_CONFIG)

    @patch("requests.post")
    def test_integration_non_streaming_success(self, mock_post, api_client):
        """Test end-to-end mocked non-streaming call."""
        mock_response = MockResponse(200, json_data=MOCK_NON_STREAMING_RESPONSE)
        mock_post.return_value = mock_response

        prompt = "Integration test prompt"
        model = "test_model"
        params = {"temperature": 0.5}
        response = api_client.call_chat_completion(
            model=model,
            params=params,
            prompt_text=prompt
        )

        mock_post.assert_called_once_with(
            API_URL,
            headers={
                "Authorization": "Bearer test_api_key",
                "Content-Type": "application/json",
                "HTTP-Referer": "test_site_url",
                "X-Title": "test_app_name",
            },
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.5},
            timeout=10,
        )
        # Assert the new OpenRouterAPI return structure
        assert isinstance(response, dict)
        assert "message" in response
        assert response["message"]["role"] == "assistant"
        assert response["message"]["content"] == '{\n  "description": "Mock subtask description",\n  "instructions": "Mock subtask instructions",\n  "input_artifacts": [],\n  "output_artifacts": [],\n  "constraints": [],\n  "validation_criteria": [],\n  "subtask_id": "mock-subtask-123",\n  "task_id": "mock-task-456"\n}'

    # The following tests mock the API call and are useful once stream_chat_completion is added
    @patch("requests.post")
    def test_integration_streaming_success_mocked(self, mock_post, api_client):
        """Test end-to-end mocked streaming call (will pass once implemented)."""
        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Integration streaming test prompt"
        model = "test_model"
        params = {"temperature": 0.9}

        stream_generator = api_client.stream_chat_completion(prompt, model, params)
        chunks = list(stream_generator)
        expected_chunks = [
            {
                "id": "chatcmpl-abc",
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": '{\n  "description": "Mock streaming subtask description",\n  "instructions": "Mock streaming subtask instructions",\n  "input_artifacts": [],\n  "output_artifacts": [],\n  "constraints": [],\n  "validation_criteria": [],\n  "subtask_id": "mock-streaming-subtask-789",\n  "task_id": "',
                        },
                    }
                ],
            },
            {"id": "chatcmpl-abc", "choices": [{"index": 0, "delta": {"content": 'mock-streaming-task-012"\n}'}}]},
            {"id": "chatcmpl-abc", "choices": [{"index": 0, "delta": {}}]},
        ]
        assert chunks == expected_chunks

        # mock_post.assert_called_once_with( # This assertion is tricky with streaming, as the call is made, then iterated.
        # We're testing the outcome (chunks) more than the exact call details here,
        # as those are covered by unit tests.
        # If specific call verification is needed for integration, it might require a more complex setup
        # or focusing on the fact that the mock_post was called at all if that's sufficient.
        # For now, the functional outcome (correct chunks) is the primary integration concern.
        # If we want to assert the call, we need to ensure the generator is consumed *before* this assertion.
        # The list(stream_generator) above does consume it.
        mock_post.assert_called_once_with(
            API_URL,
            headers={
                "Authorization": "Bearer test_api_key",
                "Content-Type": "application/json",
                "HTTP-Referer": "test_site_url",
                "X-Title": "test_app_name",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "stream": True,  # Crucial for streaming
            },
            stream=True,  # Crucial for streaming
            timeout=10,
        )

    @patch("requests.post")
    def test_integration_auth_error(self, mock_post, api_client):
        """Test integration with mocked authentication error (401)."""
        mock_response = MockResponse(401, text="Invalid API Key")
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterAuthError, match="Authentication failed"):
            api_client.call_chat_completion(
                model="model",
                params={},
                prompt_text="prompt"
            )

        with pytest.raises(OpenRouterAuthError, match="Authentication failed"):
            list(api_client.stream_chat_completion("prompt", "model", {}))

    @patch("requests.post")
    def test_integration_network_error(self, mock_post, api_client):
        """Test integration with mocked network connection error."""
        mock_post.side_effect = requests.exceptions.RequestException("Simulated network unreachable")

        with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API"):
            api_client.call_chat_completion(
                model="model",
                params={},
                prompt_text="prompt"
            )

        with pytest.raises(
            OpenRouterConnectionError,
            match="Network error during OpenRouter API streaming: Simulated network unreachable",
        ):
            list(api_client.stream_chat_completion("prompt", "model", {}))

    @patch("requests.post")
    def test_integration_service_side_error(self, mock_post, api_client):
        """Test integration with mocked service-side error (500)."""
        mock_response = MockResponse(500, text="Simulated Internal Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterAPIError, match="API request failed"):
            api_client.call_chat_completion(
                model="model",
                params={},
                prompt_text="prompt"
            )

        with pytest.raises(OpenRouterAPIError, match="API request failed"):
            list(api_client.stream_chat_completion("prompt", "model", {}))

    def test_integration_initialization_with_config(self):
        """Test integration of module initialization with a mock config."""
        # This test doesn't need to mock requests.post, just verifies
        # that the OpenRouterAPI can be instantiated with a config dict.
        try:
            api = OpenRouterAPI(MOCK_CONFIG)
            assert isinstance(api, OpenRouterAPI)
            assert api.api_key == MOCK_CONFIG["api_key"]
            assert api.model == MOCK_CONFIG["model"]
        except Exception as e:
            pytest.fail(f"Initialization with mock config failed: {e}")


    @patch("requests.post")
    @patch("ai_whisperer.state_management.StateManager") # Mock StateManagement
    @patch("ai_whisperer.execution_engine.ExecutionEngine") # Mock ExecutionEngine
    def test_integration_cost_token_capture(self, mock_execution_engine_class, mock_state_management_class, mock_post):
        """Test end-to-end capture and storage of cost/token data."""
        # Mock the StateManagement instance
        mock_state_management = MagicMock()
        mock_state_management_class.return_value = mock_state_management

        # Mock the ExecutionEngine instance and its attributes
        mock_engine = mock_execution_engine_class.return_value
        mock_engine.state_manager = mock_state_management
        mock_engine.config = MOCK_CONFIG.copy() # Use a copy of the existing mock config
        mock_engine.config['logger'] = MagicMock() # Add a mock logger to the config
        mock_engine.config['global_runner_default_prompt_content'] = "This is a mock default prompt." # Add a mock default prompt
        mock_engine.monitor = MagicMock() # Mock the monitor

        mock_engine.openrouter_api = MagicMock() # Mock the OpenRouterAPI instance
        # Ensure shutdown_event.is_set() returns False
        mock_engine.shutdown_event = MagicMock(is_set=MagicMock(return_value=False))

        # Mock AI service response with usage data (simulate streaming chunk)
        mock_stream_chunk = {
            "choices": [
                {
                    "delta": {
                        "content": "This is a mock AI response."
                    }
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 75, "total_tokens": 125},
        }
        # Configure the mock openrouter_api to yield the mock chunk
        mock_engine.openrouter_api.stream_chat_completion.return_value = iter([mock_stream_chunk])

        # Create a mock task definition
        task_id = "mock-task-cost-token-123"
        mock_task_definition = {
            "type": "ai_interaction",
            "instructions": "Perform a test interaction.",
            "input_artifacts": [],
            "output_artifacts": ["output.txt"],
            "task_id": task_id,
        }

        # Create a mock prompt_system
        mock_prompt_system = MagicMock()

        # Simulate AI interaction by calling the handler with the required prompt_system argument
        handle_ai_interaction(mock_engine, mock_task_definition, mock_prompt_system)

        # Access and verify state management
        # Assert that store_conversation_turn was called for the assistant message with usage_info
        # We need to check the calls to store_conversation_turn. There should be two calls: one for user, one for assistant.
        # We are interested in the assistant turn.

        # Find the assistant turn call
        assistant_turn_call = None
        for call_args, call_kwargs in mock_state_management.store_conversation_turn.call_args_list:
            called_task_id, turn_data = call_args
            if called_task_id == task_id and turn_data.get("role") == "assistant":
                assistant_turn_call = turn_data
                break

        assert assistant_turn_call is not None, "store_conversation_turn was not called for the assistant turn"

        assert assistant_turn_call["role"] == "assistant"
        assert assistant_turn_call["content"] == "This is a mock AI response."
        assert "usage_info" in assistant_turn_call
        assert assistant_turn_call["usage_info"]["prompt_tokens"] == 50
        assert assistant_turn_call["usage_info"]["completion_tokens"] == 75
        assert assistant_turn_call["usage_info"]["total_tokens"] == 125
