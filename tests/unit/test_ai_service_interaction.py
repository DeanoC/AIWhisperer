import pytest
from unittest.mock import patch, MagicMock
import json
from io import BytesIO
import pytest
from unittest.mock import patch, MagicMock
import json
from io import BytesIO
import requests

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.ai_service import AIStreamChunk
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService, MODELS_API_URL, API_URL
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.tools.tool_registry import ToolRegistry, get_tool_registry # Import ToolRegistry
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
class MockTool(AITool):
    @property
    def name(self):
        return "mock_tool_1"
    @property
    def description(self):
        return "Mock tool 1 description"
    @property
    def parameters(self):
        return {"type": "object", "properties": {}}
    @property
    def get_ai_prompt_instructions(self):
        return "Use mock_tool_1 to perform the mock operation."
    @property
    def execute(self, **kwargs):
        return "Mock tool 1 executed."
    @property
    def parameters_schema(self):
        return {"type": "object", "properties": {}}

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
        assert api.enable_cache is False
        assert api.cache is None

    def test_initialization_invalid_config_type(self):
        """Test initialization fails with invalid config type."""
        with pytest.raises(ConfigError, match="Invalid configuration: Expected AIConfig, got <class 'str'>"):
            OpenRouterAIService("invalid_config")

    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    def test_call_chat_completion_success(self, mock_post, mock_tool_registry, api_client):
        """Test successful non-streaming chat completion."""
        # Configure the mock ToolRegistry to return a predictable list of tools
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [
            MagicMock(get_openrouter_tool_definition=lambda: {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}})
        ]
        expected_tools = [tool.get_openrouter_tool_definition() for tool in mock_tool_registry_instance.get_all_tools.return_value]

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
                "max_tokens": None,
                "tools": expected_tools
            },
            timeout=60,
        )
        assert response['message']['content'] == "This is a non-streaming response."

    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    def test_call_chat_completion_with_history(self, mock_post, mock_tool_registry, api_client):
        """Test non-streaming chat completion with message history."""
        # Configure the mock ToolRegistry (needed for the API call logic, but tools won't be in payload with history)
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [
            MagicMock(get_openrouter_tool_definition=lambda: {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}})
        ]
        # expected_tools are NOT included in the payload when messages_history is provided

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
                "temperature": 0.5,
                "max_tokens": None
            },
            timeout=60,
        )
        assert response['message']['content'] == "This is a non-streaming response."

    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    def test_call_chat_completion_with_tool_calls(self, mock_post, mock_tool_registry, api_client):
        """Test non-streaming chat completion returning tool calls."""
        # Configure the mock ToolRegistry (needed for the API call logic, but not asserted here)
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [
            MagicMock(get_openrouter_tool_definition=lambda: {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}})
        ]
        # No assertion on tools here as the response is what's being checked

        mock_response = MockResponse(200, json_data=MOCK_NON_STREAMING_TOOL_CALLS_RESPONSE)
        mock_post.return_value = mock_response

        prompt = "What's the weather in London?"
        model = "test_model"
        params = {}
        messages = [{"role": "user", "content": prompt}]
        response = api_client.call_chat_completion(messages=messages, model=model, params=params, tools=[tool.get_openrouter_tool_definition() for tool in mock_tool_registry_instance.get_all_tools.return_value])

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

        with pytest.raises(OpenRouterAIServiceError, match="API request failed"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    def test_call_chat_completion_connection_error(self, mock_post, api_client):
        """Test non-streaming chat completion network connection error."""
        mock_post.side_effect = requests.exceptions.RequestException("Network unreachable")

        with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    def test_call_chat_completion_timeout_error(self, mock_post, api_client):
        """Test non-streaming chat completion timeout error."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(OpenRouterConnectionError, match="Request to OpenRouter API timed out"):
            api_client.call_chat_completion(messages=[{"role": "user", "content": "prompt"}], model="model", params={})

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_success(self, mock_post, api_client):
        """Test successful streaming chat completion."""
        testTool = MockTool()

        get_tool_registry().reset_tools()  # Reset tools to ensure a clean state
        get_tool_registry().register_tool(testTool)  # Register the mock tool

        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Stream this"
        model = "test_model"
        messages = [{"role": "user", "content": prompt}]
        # Get tool definitions from the registry
        tool_registry = ToolRegistry()
        registered_tools = tool_registry.get_all_tools()
        openrouter_tool_definitions = [tool.get_openrouter_tool_definition() for tool in registered_tools]

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
                "max_tokens": None,  # Not specified in the mock, but can be included
                "stream": True,  # Crucial for streaming
            },
            stream=True,  # Crucial for streaming
            timeout=60,
        )

        # Expected parsed chunks (excluding [DONE])
        expected_chunks = [
            AIStreamChunk(delta_content="Hello"),
            AIStreamChunk(delta_content=" world"),   
        ]
        assert chunks == expected_chunks

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_with_history(self, mock_post, api_client):
        """Test streaming chat completion with message history."""
        testTool = MockTool()

        get_tool_registry().reset_tools()  # Reset tools to ensure a clean state
        get_tool_registry().register_tool(testTool)  # Register the mock tool

        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Stream this"
        model = "test_model"
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        # Get tool definitions from the registry
        tool_registry = ToolRegistry()
        registered_tools = tool_registry.get_all_tools()
        openrouter_tool_definitions = [tool.get_openrouter_tool_definition() for tool in registered_tools]

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
                "max_tokens": None,  # Not specified in the mock, but can be included
                "stream": True,  # Crucial for streaming
            },
            stream=True,  # Crucial for streaming
            timeout=60,
        )

        # Expected parsed chunks (excluding [DONE])
        expected_chunks = [
            AIStreamChunk(delta_content="Hello"),
            AIStreamChunk(delta_content=" world"),   
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

        with pytest.raises(OpenRouterAIServiceError, match="API request failed"):
            messages = [{"role": "user", "content": "prompt"}]
            [chunk async for chunk in api_client.stream_chat_completion(messages=messages, model="model", params={})]

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_initial_connection_error(self, mock_post, api_client):
        """Test streaming chat completion initial network connection error."""
        mock_post.side_effect = requests.exceptions.RequestException("Network unreachable")

        with pytest.raises(
            OpenRouterConnectionError, match="Network error during OpenRouter API streaming: Network unreachable"
        ):
            messages = [{"role": "user", "content": "prompt"}]
            [chunk async for chunk in api_client.stream_chat_completion(messages=messages, model="model", params={})]

    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_initial_timeout_error(self, mock_post, api_client):
        """Test streaming chat completion initial timeout error."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(OpenRouterConnectionError, match="Request to OpenRouter API timed out"):
            messages = [{"role": "user", "content": "prompt"}]
            [chunk async for chunk in api_client.stream_chat_completion(messages=messages, model="model", params={})]


    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_mid_stream_error(self, mock_post, api_client):
        """Test streaming chat completion error occurring mid-stream."""
        testTool = MockTool()
        get_tool_registry().reset_tools()  # Reset tools to ensure a clean state
        get_tool_registry().register_tool(testTool)  # Register the mock tool

        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Stream this"
        model = "test_model"
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        # Get tool definitions from the registry
        tool_registry = ToolRegistry()
        registered_tools = tool_registry.get_all_tools()
        openrouter_tool_definitions = [tool.get_openrouter_tool_definition() for tool in registered_tools]

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
            OpenRouterConnectionError, match="Network error during OpenRouter API streaming: Mid-stream network error"
        ):
            await anext(stream_generator)


    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_invalid_json_chunk(self, mock_post, mock_tool_registry, api_client):
        """Test streaming chat completion with an invalid JSON chunk."""
        # Configure the mock ToolRegistry (needed for the API call logic, but not asserted here)
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [
            MagicMock(get_openrouter_tool_definition=lambda: {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}})
        ]
        # No assertion on tools here as the response is what's being checked

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
        

        # The next iteration should raise a JSON decode error wrapped in OpenRouterAIServiceError
        with pytest.raises(
            OpenRouterAIServiceError,
            match="Failed to decode JSON chunk from stream: Expecting value: line 1 column 1 \\(char 0\\). Chunk: invalid json...",
        ):
            await anext(stream_generator)

    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry")  # Patch ToolRegistry
    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_non_data_lines(self, mock_post, mock_tool_registry, api_client):
        """Test streaming chat completion ignores non-data lines."""
        # Configure the mock ToolRegistry (needed for the API call logic, but not asserted here)
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [
            MagicMock(get_openrouter_tool_definition=lambda: {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}})
        ]
        # No assertion on tools here as the response is what's being checked

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

        with pytest.raises(OpenRouterAIServiceError, match="API request failed"):
            api_client.list_models()

    @patch("requests.get")
    def test_list_models_connection_error(self, mock_get, api_client):
        """Test list_models network connection error."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API"):
            api_client.list_models()

    @patch("requests.get")
    def test_list_models_invalid_response_format(self, mock_get, api_client):
        """Test list_models with unexpected response format."""
        mock_response_data = {"not_data_field": []}
        mock_response = MockResponse(200, json_data=mock_response_data)
        mock_get.return_value = mock_response

        with pytest.raises(OpenRouterAIServiceError, match="Unexpected response format"):
            api_client.list_models()

    def test_cache_disabled(self, api_client):
        """Test that cache is None when disabled."""
        assert api_client.cache is None

    def test_cache_enabled(self):
        """Test that cache is a dict when enabled."""
        config = AIConfig(
            api_key=MOCK_CONFIG.api_key,
            model_id=MOCK_CONFIG.model_id,
            temperature=MOCK_CONFIG.temperature,
            site_url=MOCK_CONFIG.site_url,
            app_name=MOCK_CONFIG.app_name,
            cache=True,
            timeout=MOCK_CONFIG.timeout
        )
        api = OpenRouterAIService(config)
        assert isinstance(api.cache, dict)


    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    def test_call_chat_completion_cache_hit(self, mock_post, mock_tool_registry):
        """Test cache hit for non-streaming call."""
        # Define the expected tool definition as a dictionary
        expected_tool_definition = {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}}
        expected_tools = [expected_tool_definition] # Use a list of dictionaries

        # Configure the mock ToolRegistry to return the expected tool definition
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [MagicMock(get_openrouter_tool_definition=lambda: expected_tool_definition)]


        config = AIConfig(
            api_key=MOCK_CONFIG.api_key,
            model_id=MOCK_CONFIG.model_id,
            temperature=MOCK_CONFIG.temperature,
            site_url=MOCK_CONFIG.site_url,
            app_name=MOCK_CONFIG.app_name,
            cache=True,
            timeout=MOCK_CONFIG.timeout
        )
        api = OpenRouterAIService(config)

        # Populate cache with a key that includes tools (using the dictionary list)
        cache_key = api._generate_cache_key("test_model", [{"role": "user", "content": "Cached prompt"}], {}, expected_tools)
        api._cache_store[cache_key] = {"role": "assistant", "content": "Cached response"}

        # Call with the same parameters, including tools (which will be added by the API class)
        # Mock the response for the internal call within call_chat_completion when cache is enabled
        # This mock is actually not needed for a cache hit test, but keeping it doesn't hurt.
        mock_response = MockResponse(200, json_data={"choices": [{"message": {"content": "Cached response"}}]})
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Cached prompt"}]
        response = api.call_chat_completion(messages=messages, model="test_model", params={}, tools=expected_tools)

        # requests.post should NOT have been called
        mock_post.assert_not_called()
        assert response['message']['content'] == "Cached response"


    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    def test_call_chat_completion_cache_miss(self, mock_post, mock_tool_registry):
        """Test cache miss for non-streaming call."""
        # Define the expected tool definition as a dictionary
        expected_tool_definition = {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}}
        expected_tools = [expected_tool_definition] # Use a list of dictionaries

        # Configure the mock ToolRegistry to return the expected tool definition
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [MagicMock(get_openrouter_tool_definition=lambda: expected_tool_definition)]

        config = AIConfig(
            api_key=MOCK_CONFIG.api_key,
            model_id=MOCK_CONFIG.model_id,
            temperature=MOCK_CONFIG.temperature,
            site_url=MOCK_CONFIG.site_url,
            app_name=MOCK_CONFIG.app_name,
            cache=True,
            timeout=MOCK_CONFIG.timeout
        )
        api = OpenRouterAIService(config)

        mock_response = MockResponse(200, json_data=MOCK_NON_STREAMING_RESPONSE)
        mock_post.return_value = mock_response

        prompt = "Uncached prompt"
        model = "test_model"
        params = {}
        messages = [{"role": "user", "content": prompt}]
        response = api.call_chat_completion(messages=messages, model=model, params=params, tools=expected_tools)


        # requests.post should have been called
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
                "temperature": 0.7,
                "max_tokens": None,
                "tools": expected_tools
            },
            timeout=60,
        )
        assert response['message']['content'] == "This is a non-streaming response."

        # Verify cache was populated with a key that includes tools
        cache_key = api._generate_cache_key(model, [{"role": "user", "content": prompt}], params, expected_tools)
        assert cache_key in api._cache_store
        assert api._cache_store[cache_key] == MOCK_NON_STREAMING_RESPONSE["choices"][0]["message"]


    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_cache_disabled(self, mock_post, mock_tool_registry):
        """Test that streaming calls do not use cache when disabled."""
        # Configure the mock ToolRegistry (needed for the API call logic, but not asserted here)
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [
            MagicMock(get_openrouter_tool_definition=lambda: {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}})
        ]
        # No assertion on tools here as the response is what's being checked
        api = OpenRouterAIService(MOCK_CONFIG)  # Cache is False by default

        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Stream this"
        model = "test_model"
        messages = [{"role": "user", "content": prompt}]
        stream_generator = api.stream_chat_completion(
            model=model, 
            messages=messages)

        [chunk async for chunk in stream_generator]  # Consume the generator

        # requests.post should have been called
        mock_post.assert_called_once()
        assert api.cache is None  # Cache should still be None

    @patch("ai_whisperer.ai_service.openrouter_ai_service.ToolRegistry") # Patch ToolRegistry
    @patch("requests.post")
    @pytest.mark.asyncio
    async def test_stream_chat_completion_cache_enabled_no_caching(self, mock_post, mock_tool_registry):
        """Test that streaming calls do not use or populate cache even when enabled."""
        # Configure the mock ToolRegistry (needed for the API call logic, but not asserted here)
        mock_tool_registry_instance = mock_tool_registry.return_value
        mock_tool_registry_instance.get_all_tools.return_value = [
            MagicMock(get_openrouter_tool_definition=lambda: {"type": "function", "function": {"name": "mock_tool_1", "description": "Mock tool 1", "parameters": {"type": "object", "properties": {}}}})
        ]
        # No assertion on tools here as the response is what's being checked

        config = AIConfig(
            api_key=MOCK_CONFIG.api_key,
            model_id=MOCK_CONFIG.model_id,
            temperature=MOCK_CONFIG.temperature,
            site_url=MOCK_CONFIG.site_url,
            app_name=MOCK_CONFIG.app_name,
            cache=True,
            timeout=MOCK_CONFIG.timeout
        )
        api = OpenRouterAIService(config)

        mock_response = MockResponse(200, iter_lines_data=MOCK_STREAMING_CHUNKS)
        mock_post.return_value = mock_response

        prompt = "Stream this"
        model = "test_model"
        params = {}
        messages = [{"role": "user", "content": prompt}]
        stream_generator = api.stream_chat_completion(messages=messages, model=model, params=params)

        [chunk async for chunk in stream_generator]  # Consume the generator

        # requests.post should have been called
        mock_post.assert_called_once()
        assert isinstance(api.cache, dict)  # Cache should exist
        assert len(api.cache) == 0  # Cache should be empty

