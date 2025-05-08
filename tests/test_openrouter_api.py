import pytest
import requests
from unittest.mock import patch, Mock

# Import specific exceptions
from src.ai_whisperer.exceptions import (
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError
)
# Import the actual class and constants
from src.ai_whisperer.openrouter_api import OpenRouterAPI, MODELS_API_URL, API_URL

# Define test config data
TEST_CONFIG_OPENROUTER_SECTION = {
    'api_key': "test-api-key",
    'model': "test-model/test-model",
    'params': {'temperature': 0.7, 'max_tokens': 1024},  # Added max_tokens here
    'site_url': "http://test-site.com",
    'app_name': "TestApp"
}

PROMPT = "Test prompt"
MESSAGES = [{"role": "user", "content": PROMPT}]

@pytest.fixture
def mock_requests(requests_mock):
    """Fixture to provide requests_mock adapter."""
    return requests_mock

# --- Test Cases ---

def test_openrouter_api_init_success():
    """Test successful initialization of OpenRouterAPI class."""
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    assert client.api_key == TEST_CONFIG_OPENROUTER_SECTION['api_key']
    assert client.model == TEST_CONFIG_OPENROUTER_SECTION['model']
    assert client.params == TEST_CONFIG_OPENROUTER_SECTION['params']
    assert client.site_url == TEST_CONFIG_OPENROUTER_SECTION['site_url']
    assert client.app_name == TEST_CONFIG_OPENROUTER_SECTION['app_name']

def test_openrouter_api_init_config_error():
    """Test OpenRouterAPI initialization with missing config raises ConfigError."""
    bad_config_section = {}
    with pytest.raises(ConfigError, match="Missing expected configuration key within 'openrouter' section: 'api_key'"):
        OpenRouterAPI(bad_config_section)

def test_chat_completion_success(mock_requests):
    """Test successful chat completion call."""
    expected_response_content = "Generated text response."
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"content": expected_response_content}}], "usage": {}},
        status_code=200,
        request_headers={
            'Authorization': f'Bearer {TEST_CONFIG_OPENROUTER_SECTION["api_key"]}',
            'HTTP-Referer': TEST_CONFIG_OPENROUTER_SECTION["site_url"],
            'X-Title': TEST_CONFIG_OPENROUTER_SECTION["app_name"]}
    )
    
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    response = client.call_chat_completion(
        prompt_text=PROMPT,
        model=client.model,
        params=client.params
    )
    assert response == expected_response_content

    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.method == 'POST'
    assert request.url == API_URL
    assert request.headers['Authorization'] == f'Bearer {TEST_CONFIG_OPENROUTER_SECTION["api_key"]}'
    assert request.headers['HTTP-Referer'] == TEST_CONFIG_OPENROUTER_SECTION["site_url"]
    assert request.headers['X-Title'] == TEST_CONFIG_OPENROUTER_SECTION["app_name"]
    assert request.json()['model'] == TEST_CONFIG_OPENROUTER_SECTION["model"]
    assert request.json()['messages'][0]['content'] == PROMPT
    assert request.json()['temperature'] == TEST_CONFIG_OPENROUTER_SECTION["params"]['temperature']
    assert request.json()['max_tokens'] == TEST_CONFIG_OPENROUTER_SECTION["params"]['max_tokens']  # Added this assertion
    
    # Reset history for next test
    mock_requests.reset()
    
    # Test with model override
    override_model = "different-model/test"
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"content": expected_response_content}}], "usage": {}},
        status_code=200
    )
    response = client.call_chat_completion(
        prompt_text=PROMPT,
        model=override_model,
        params=client.params
    )
    assert response == expected_response_content
    
    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.json()['model'] == override_model  # Should use the override model
    assert request.json()['temperature'] == TEST_CONFIG_OPENROUTER_SECTION["params"]['temperature']  # Default params
    
    # Reset history for next test
    mock_requests.reset()
    
    # Test with params override
    override_params = {'temperature': 0.2, 'max_tokens': 500}
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"content": expected_response_content}}], "usage": {}},
        status_code=200
    )
    response = client.call_chat_completion(
        prompt_text=PROMPT,
        model=client.model,
        params=override_params
    )
    assert response == expected_response_content
    
    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.json()['model'] == TEST_CONFIG_OPENROUTER_SECTION["model"]  # Default model
    assert request.json()['temperature'] == override_params['temperature']  # Override temp
    assert request.json()['max_tokens'] == override_params['max_tokens']  # Override max_tokens

def test_chat_completion_auth_error(mock_requests):
    """Test chat completion handles 401 authentication errors."""
    error_message = "Invalid API key"
    mock_requests.post(
        API_URL,
        json={"error": {"message": error_message}},
        status_code=401
    )
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAuthError, match=f"Authentication failed: {error_message}"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_rate_limit_error(mock_requests):
    """Test chat completion handles 429 rate limit errors."""
    error_message = "Rate limit exceeded"
    mock_requests.post(
        API_URL,
        json={"error": {"message": error_message}},
        status_code=429
    )
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterRateLimitError, match=f"Rate limit exceeded: {error_message}"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_not_found_error(mock_requests):
    """Test chat completion handles 404 errors (e.g., model not found)."""
    error_message = "Model not found"
    mock_requests.post(
        API_URL,
        json={"error": {"message": error_message}},
        status_code=404
    )
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match=f"API request failed: {error_message}"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_server_error(mock_requests):
    """Test chat completion handles 500 server errors."""
    error_message = "Internal server error"
    mock_requests.post(
        API_URL,
        json={"error": {"message": error_message}},
        status_code=500
    )
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match=f"API request failed: {error_message}"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_connection_error(mock_requests):
    """Test chat completion handles connection errors."""
    mock_requests.post(API_URL, exc=requests.exceptions.ConnectionError("Connection failed"))
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API: Connection failed"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_timeout_error(mock_requests):
    """Test chat completion handles timeout errors."""
    mock_requests.post(API_URL, exc=requests.exceptions.Timeout("Request timed out"))
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API: Request timed out"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_unexpected_response_format_no_choices(mock_requests):
    """Test chat completion handles unexpected response format (no 'choices')."""
    mock_requests.post(API_URL, json={"usage": {}}, status_code=200)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'choices' array is missing"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_unexpected_response_format_empty_choices(mock_requests):
    """Test chat completion handles unexpected response format (empty 'choices')."""
    mock_requests.post(API_URL, json={"choices": [], "usage": {}}, status_code=200)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'choices' array is missing"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_unexpected_response_format_no_message(mock_requests):
    """Test chat completion handles unexpected response format (no 'message' in choice)."""
    mock_requests.post(API_URL, json={"choices": [{"index": 0}], "usage": {}}, status_code=200)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'message' object is missing"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

def test_chat_completion_unexpected_response_format_no_content(mock_requests):
    """Test chat completion handles unexpected response format (no 'content' in message)."""
    mock_requests.post(API_URL, json={"choices": [{"message": {"role": "assistant"}}], "usage": {}}, status_code=200)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'content' key is missing"):
        client.call_chat_completion(prompt_text=PROMPT, model=client.model, params=client.params)

# --- list_models Tests ---

def test_list_models_success(mock_requests):
    """Test successful call to list_models."""
    expected_models = [{"id": "model1"}, {"id": "model2"}]
    mock_requests.get(MODELS_API_URL, json={"data": expected_models}, status_code=200)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    models = client.list_models()
    assert models == expected_models
    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.method == 'GET'
    assert request.url == MODELS_API_URL

def test_list_models_auth_error(mock_requests):
    """Test list_models handles 401 (though unlikely as it's unauthenticated)."""
    error_message = "Auth error on models endpoint"
    mock_requests.get(MODELS_API_URL, json={"error": {"message": error_message}}, status_code=401)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAuthError, match=f"Authentication failed: {error_message}"):
        client.list_models()

def test_list_models_rate_limit_error(mock_requests):
    """Test list_models handles 429 rate limit errors."""
    error_message = "Rate limit exceeded"
    mock_requests.get(MODELS_API_URL, json={"error": {"message": error_message}}, status_code=429)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterRateLimitError, match=f"Rate limit exceeded: {error_message}"):
        client.list_models()

def test_list_models_server_error(mock_requests):
    """Test list_models handles 500 server errors."""
    error_message = "Server unavailable"
    mock_requests.get(MODELS_API_URL, json={"error": {"message": error_message}}, status_code=500)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match=f"API request failed: {error_message}"):
        client.list_models()

def test_list_models_connection_error(mock_requests):
    """Test list_models handles connection errors."""
    mock_requests.get(MODELS_API_URL, exc=requests.exceptions.ConnectionError("Cannot connect"))
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API: Cannot connect"):
        client.list_models()

def test_list_models_invalid_json(mock_requests):
    """Test list_models handles invalid JSON response."""
    mock_requests.get(MODELS_API_URL, text="not json", status_code=200)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match="Failed to decode JSON response"):
        client.list_models()

def test_list_models_empty_data(mock_requests):
    """Test list_models handles response with missing 'data' key."""
    mock_requests.get(MODELS_API_URL, json={"info": "some info"}, status_code=200)
    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'data' array is missing"):
        client.list_models()

# --- call_openrouter (backward compatibility) Tests --- # Refactored

def test_call_openrouter_success_refactored(mock_requests):
    """Test successful API call using the OpenRouterAPI class (Refactored)."""
    expected_response_content = "Generated text response."
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"content": expected_response_content}}], "usage": {}},
        status_code=200
    )

    client = OpenRouterAPI(TEST_CONFIG_OPENROUTER_SECTION)
    response = client.call_chat_completion(
        prompt_text=PROMPT,
        model=client.model,
        params=client.params
    )
    assert response == expected_response_content

    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.json()['model'] == TEST_CONFIG_OPENROUTER_SECTION['model']
    assert request.json()['temperature'] == TEST_CONFIG_OPENROUTER_SECTION['params']['temperature']
    assert request.json()['max_tokens'] == TEST_CONFIG_OPENROUTER_SECTION['params']['max_tokens']

    # Reset history
    mock_requests.reset()

    # Test with model override
    override_model = "different-model/test"
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"content": expected_response_content}}], "usage": {}},
        status_code=200
    )
    response = client.call_chat_completion(
        prompt_text=PROMPT,
        model=override_model,
        params=client.params
    )
    assert response == expected_response_content

    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.json()['model'] == override_model
    # Ensure default params are still sent when only model is overridden
    assert request.json()['temperature'] == TEST_CONFIG_OPENROUTER_SECTION['params']['temperature']
    assert request.json()['max_tokens'] == TEST_CONFIG_OPENROUTER_SECTION['params']['max_tokens']

    # Reset history
    mock_requests.reset()

    # Test with params override
    override_params = {'temperature': 0.3, 'top_p': 0.9, 'max_tokens': 512} # Ensure max_tokens override is tested
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"content": expected_response_content}}], "usage": {}},
        status_code=200
    )
    response = client.call_chat_completion(
        prompt_text=PROMPT,
        model=client.model, # Pass default model
        params=override_params
    )
    assert response == expected_response_content

    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.json()['model'] == TEST_CONFIG_OPENROUTER_SECTION['model'] # Default model
    assert request.json()['temperature'] == override_params['temperature']
    assert request.json()['top_p'] == override_params['top_p']
    assert request.json()['max_tokens'] == override_params['max_tokens'] # Check overridden max_tokens

