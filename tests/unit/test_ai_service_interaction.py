import pytest
from unittest.mock import patch, MagicMock
import json
from io import BytesIO
import requests

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.ai_service import AIStreamChunk
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService, MODELS_API_URL, API_URL
from ai_whisperer.exceptions import (
    OpenRouterAIServiceError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError,
)

# Mock configuration for testing
MOCK_CONFIG = AIConfig(
    api_key="test_api_key",
    model_id="test_model",
    temperature=0.7,
    site_url="test_site_url",
    app_name="test_app_name",
    cache=False,
    timeout=10,
)
# Mock response data for streaming
MOCK_STREAMING_CHUNKS = [
    b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"}}]}\n',
    b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{"content":" world"}}]}\n',
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
            "message": {"role": "assistant", "content": "This is a non-streaming response."},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
}

# Mock response data for non-streaming with tool calls
MOCK_NON_STREAMING_TOOL_CALLS_RESPONSE = {
    "id": "chatcmpl-tool",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "test_model",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": '{"location": "London"}'},
                    }
                ],
            },
            "finish_reason": "tool_calls",
        }
    ],
    "usage": {"prompt_tokens": 15, "completion_tokens": 5, "total_tokens": 20},
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


class TestOpenRouterAIServiceUnit:

    @pytest.fixture
    def api_client(self):
        """Fixture to create an OpenRouterAIService instance with mock config."""
        return OpenRouterAIService(MOCK_CONFIG)

    def test_initialization_success(self):
        """Test successful initialization with valid config."""
        api = OpenRouterAIService(MOCK_CONFIG)
        assert api.api_key == "test_api_key"
        assert api.model == "test_model"
        assert api.site_url == "test_site_url"
        assert api.app_name == "test_app_name"
        # enable_cache is not an attribute of OpenRouterAIService

    def test_initialization_invalid_config_type(self):
        """Test initialization fails with invalid config type."""
        with pytest.raises(ConfigError, match="Invalid configuration: Expected AIConfig, got <class 'str'>"):
            OpenRouterAIService("invalid_config")

    @patch("requests.post")
    def test_call_chat_completion_success(self, mock_post, api_client):
        """Test successful non-streaming chat completion."""
        # Create mock tools directly
        expected_tools = [
            {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}}
        ]

        mock_response = MockResponse(200, json_data=MOCK_NON_STREAMING_RESPONSE)
        mock_post.return_value = mock_response

        prompt = "Hello AI"
        model = "test_model"
        params = {"temperature": 0.5}
        messages = [{"role": "user", "content": prompt}]
        response = api_client.call_chat_completion(
            messages=messages,
            model=model, 
            params=params, 
            tools=expected_tools)

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
                "temperature": 0.5,
                "tools": expected_tools
            },
            timeout=60,
        )
        assert response['message']['content'] == "This is a non-streaming response."

    @patch("requests.post")
    def test_call_chat_completion_with_history(self, mock_post, api_client):
        """Test non-streaming chat completion with message history."""
        # Tools are passed as parameters, not included in the payload when messages_history is provided

        mock_response = MockResponse(200, json_data=MOCK_NON_STREAMING_RESPONSE)
        mock_post.return_value = mock_response

        history = [{"role": "user", "content": "Previous message"}]
        prompt = "New message"
        model = "test_model"
        params = {"temperature": 0.5}
        # Combine history with new message
        messages = history + [{"role": "user", "content": prompt}]
        response = api_client.call_chat_completion(messages=messages, model=model, params=params)

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
                "messages": messages,  # Should include both history and new message
                "temperature": 0.5
            },
            timeout=60,
        )
        assert response['message']['content'] == "This is a non-streaming response."

    @patch("requests.post")
    def test_call_chat_completion_with_tool_calls(self, mock_post, api_client):
        """Test non-streaming chat completion returning tool calls."""
        # Create tools directly
        expected_tools = [
            {"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {}}}}
        ]

        mock_response = MockResponse(200, json_data=MOCK_NON_STREAMING_TOOL_CALLS_RESPONSE)
        mock_post.return_value = mock_response

        prompt = "What's the weather in London?"
        model = "test_model"
        params = {}
        messages = [{"role": "user", "content": prompt}]
        response = api_client.call_chat_completion(messages=messages, model=model, params=params, tools=expected_tools)

        # The response should be the full message object, not just content
        assert response["message"] == MOCK_NON_STREAMING_TOOL_CALLS_RESPONSE["choices"][0]["message"]

    @patch("requests.post")
    def test_call_chat_completion_auth_error(self, mock_post, api_client):
        """Test non-streaming chat completion authentication error (401)."""
        mock_response = MockResponse(401, text="Invalid API Key")
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterAuthError, match="Authentication failed"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    def test_call_chat_completion_rate_limit_error(self, mock_post, api_client):
        """Test non-streaming chat completion rate limit error (429)."""
        mock_response = MockResponse(429, text="Rate limit exceeded")
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterRateLimitError, match="Rate limit exceeded"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    def test_call_chat_completion_api_error(self, mock_post, api_client):
        """Test non-streaming chat completion generic API error (500)."""
        mock_response = MockResponse(500, text="Internal Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterAIServiceError, match="API error 500"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    def test_call_chat_completion_connection_error(self, mock_post, api_client):
        """Test non-streaming chat completion network connection error."""
        mock_post.side_effect = requests.exceptions.RequestException("Network unreachable")

        with pytest.raises(OpenRouterConnectionError, match="Network error:"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    def test_call_chat_completion_timeout_error(self, mock_post, api_client):
        """Test non-streaming chat completion timeout error."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(OpenRouterConnectionError, match="Network error:"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_success(self, mock_post, api_client):
        """Test successful streaming chat completion."""
        # Create tool definitions directly
        openrouter_tool_definitions = [
            {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}}
        ]

        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Stream this"
        model = "test_model"
        messages = [{"role": "user", "content": prompt}]

        stream_generator = api_client.stream_chat_completion(messages=messages,
                                                             tools=openrouter_tool_definitions,
                                                             )

        # Collect yielded chunks
        chunks = [chunk async for chunk in stream_generator]

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
                "tools": openrouter_tool_definitions,
                "temperature": 0.7,  # From MOCK_CONFIG["params"]
                "stream": True,  # Crucial for streaming
            },
            stream=True,  # Crucial for streaming
            timeout=60,
        )

        # Expected parsed chunks (excluding [DONE])
        expected_chunks = [
            AIStreamChunk(delta_content="Hello"),
            AIStreamChunk(delta_content=" world"),
            AIStreamChunk(delta_content=None),  # Empty delta from mock data
        ]
        assert chunks == expected_chunks

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_with_history(self, mock_post, api_client):
        """Test streaming chat completion with message history."""
        # Create tool definitions directly
        openrouter_tool_definitions = [
            {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}}
        ]

        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Stream this"
        model = "test_model"
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]

        stream_generator = api_client.stream_chat_completion(messages=messages,
                                                             tools=openrouter_tool_definitions,
                                                             )

        # Collect yielded chunks
        chunks = [chunk async for chunk in stream_generator]

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
                "messages": messages,
                "tools": openrouter_tool_definitions,
                "temperature": 0.7,  # From MOCK_CONFIG["params"]
                "stream": True,  # Crucial for streaming
            },
            stream=True,  # Crucial for streaming
            timeout=60,
        )

        # Expected parsed chunks (excluding [DONE])
        expected_chunks = [
            AIStreamChunk(delta_content="Hello"),
            AIStreamChunk(delta_content=" world"),
            AIStreamChunk(delta_content=None),  # Empty delta from mock data
        ]
        assert chunks == expected_chunks
    
    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_initial_auth_error(self, mock_post, api_client):
        """Test streaming chat completion initial authentication error (401)."""
        mock_response = MockResponse(401, text="Invalid API Key")
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterAuthError, match="Authentication failed"):
            # Need to iterate or call next() to trigger the request
            messages = [{"role": "user", "content": "prompt"}]
            [chunk async for chunk in api_client.stream_chat_completion(messages=messages, model="model", params={})]

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_initial_api_error(self, mock_post, api_client):
        """Test streaming chat completion initial generic API error (500)."""
        mock_response = MockResponse(500, text="Internal Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(OpenRouterAIServiceError, match="API error 500"):
            messages = [{"role": "user", "content": "prompt"}]
            [chunk async for chunk in api_client.stream_chat_completion(messages=messages, model="model", params={})]

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_initial_connection_error(self, mock_post, api_client):
        """Test streaming chat completion initial network connection error."""
        mock_post.side_effect = requests.exceptions.RequestException("Network unreachable")

        with pytest.raises(
            OpenRouterConnectionError, match="Streaming error:"
        ):
            messages = [{"role": "user", "content": "prompt"}]
            [chunk async for chunk in api_client.stream_chat_completion(messages=messages, model="model", params={})]

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_initial_timeout_error(self, mock_post, api_client):
        """Test streaming chat completion initial timeout error."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(OpenRouterConnectionError, match="Streaming error:"):
            messages = [{"role": "user", "content": "prompt"}]
            [chunk async for chunk in api_client.stream_chat_completion(messages=messages, model="model", params={})]


    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_mid_stream_error(self, mock_post, api_client):
        """Test streaming chat completion error occurring mid-stream."""
        # Create tool definitions directly
        openrouter_tool_definitions = [
            {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}}
        ]

        # Simulate a network error during iteration
        def iter_lines_with_error():
            yield b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"}}]}\n'
            raise requests.exceptions.RequestException("Mid-stream network error")

        mock_response = MockResponse(200)  # Status 200 initially
        mock_response.iter_lines = iter_lines_with_error  # Replace iter_lines with our generator
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "prompt"}]
        stream_generator = api_client.stream_chat_completion(messages=messages,
                                                             tools=openrouter_tool_definitions,
                                                             )

        # The first chunk should be yielded successfully
        first_chunk = await anext(stream_generator)
        assert first_chunk == AIStreamChunk(delta_content="Hello")

        # The next iteration should raise the error
        with pytest.raises(
            OpenRouterConnectionError, match="Streaming error:"
        ):
            await anext(stream_generator)


    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_invalid_json_chunk(self, mock_post, api_client):
        """Test streaming chat completion with an invalid JSON chunk."""

        invalid_chunks = [
            b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"}}]}\n',
            b"data: invalid json\n",  # Invalid JSON
            b"data: [DONE]\n",
        ]
        mock_response = MockResponse(200, iter_lines_data=invalid_chunks)
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "prompt"}]
        stream_generator = api_client.stream_chat_completion(messages=messages, model="model", params={})

        # The first chunk should be yielded successfully
        first_chunk = await anext(stream_generator)
        assert first_chunk == AIStreamChunk(delta_content="Hello")
        
        # The invalid JSON chunk is logged but not raised as an exception
        # The generator should complete without error (StopAsyncIteration)
        with pytest.raises(StopAsyncIteration):
            await anext(stream_generator)

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_non_data_lines(self, mock_post, api_client):
        """Test streaming chat completion ignores non-data lines."""

        chunks_with_comments = [
            b": comment\n",
            b"event: message\n",
            b'data: {"id":"chatcmpl-abc","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"}}]}\n',
            b"\n",  # Empty line
            b"data: [DONE]\n",
        ]
        mock_response = MockResponse(200, iter_lines_data=chunks_with_comments)
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "prompt"}]
        stream_generator = api_client.stream_chat_completion(messages=messages, model="model", params={})

        # Only the data line should be processed and yielded
        chunks = [chunk async for chunk in stream_generator]
        expected_chunks = AIStreamChunk(delta_content="Hello")

        assert chunks == [expected_chunks]

    @patch("requests.get")
    def test_list_models_success(self, mock_get, api_client):
        """Test successful list_models call."""
        mock_response_data = {"data": [{"id": "model-1", "name": "Model One"}, {"id": "model-2", "name": "Model Two"}]}
        mock_response = MockResponse(200, json_data=mock_response_data)
        mock_get.return_value = mock_response

        models = api_client.list_models()

        mock_get.assert_called_once_with(
            MODELS_API_URL,
            headers={"Authorization": "Bearer test_api_key", "Content-Type": "application/json"},
            timeout=30,
        )
        assert models == mock_response_data["data"]

    @patch("requests.get")
    def test_list_models_api_error(self, mock_get, api_client):
        """Test list_models API error (400)."""
        mock_response = MockResponse(400, text="Bad Request")
        mock_get.return_value = mock_response

        with pytest.raises(OpenRouterConnectionError, match="Failed to fetch models"):
            api_client.list_models()

    @patch("requests.get")
    def test_list_models_connection_error(self, mock_get, api_client):
        """Test list_models network connection error."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with pytest.raises(OpenRouterConnectionError, match="Failed to fetch models:"):
            api_client.list_models()

    @patch("requests.get")
    def test_list_models_invalid_response_format(self, mock_get, api_client):
        """Test list_models with unexpected response format."""
        mock_response_data = {"not_data_field": []}
        mock_response = MockResponse(200, json_data=mock_response_data)
        mock_get.return_value = mock_response

        # When "data" field is missing, it returns an empty list
        models = api_client.list_models()
        assert models == []


