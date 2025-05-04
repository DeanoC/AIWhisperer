import pytest
import requests
import requests_mock
# Import specific exceptions
from src.ai_whisperer.exceptions import (
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError # Import ConfigError for testing missing keys
)
# Import the actual function
from src.ai_whisperer.openrouter_api import call_openrouter

API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Define test config data
TEST_CONFIG = {
    'openrouter': {
        'api_key': "test-api-key",
        'model': "test-model/test-model",
        'params': {'temperature': 0.7},
        'site_url': "http://test-site.com",
        'app_name': "TestApp"
    }
}
PROMPT = "Test prompt"

@pytest.fixture
def mock_requests(requests_mock):
    """Fixture to provide requests_mock adapter."""
    return requests_mock

def test_call_openrouter_success(mock_requests):
    """Test successful API call."""
    expected_response_content = "Generated text response."
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"content": expected_response_content}}], "usage": {}},
        status_code=200,
        # Check for correct headers including Referer and Title
        request_headers={
            'Authorization': f'Bearer {TEST_CONFIG["openrouter"]["api_key"]}',
            'HTTP-Referer': TEST_CONFIG["openrouter"]["site_url"],
            'X-Title': TEST_CONFIG["openrouter"]["app_name"]}
    )

    # Pass the config dictionary
    response = call_openrouter(PROMPT, TEST_CONFIG)
    assert response == expected_response_content

    # Verify the request payload
    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.method == 'POST'
    assert request.url == API_URL
    assert request.headers['Authorization'] == f'Bearer {TEST_CONFIG["openrouter"]["api_key"]}'
    assert request.headers['HTTP-Referer'] == TEST_CONFIG["openrouter"]["site_url"]
    assert request.headers['X-Title'] == TEST_CONFIG["openrouter"]["app_name"]
    assert request.json()['model'] == TEST_CONFIG["openrouter"]["model"]
    assert request.json()['messages'] == [{"role": "user", "content": PROMPT}]
    assert request.json()['temperature'] == TEST_CONFIG["openrouter"]["params"]['temperature']

def test_call_openrouter_auth_error(mock_requests):
    """Test API call with authentication error (401)."""
    mock_requests.post(
        API_URL,
        json={"error": {"message": "Invalid API key"}},
        status_code=401
    )

    # Expect specific OpenRouterAuthError
    with pytest.raises(OpenRouterAuthError, match=r"Authentication failed: Invalid API key \(HTTP 401\)"):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_rate_limit_error(mock_requests):
    """Test API call with rate limit error (429)."""
    mock_requests.post(
        API_URL,
        json={"error": {"message": "Rate limit exceeded"}},
        status_code=429
    )

    # Expect specific OpenRouterRateLimitError
    with pytest.raises(OpenRouterRateLimitError, match=r"Rate limit exceeded: Rate limit exceeded \(HTTP 429\)"):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_not_found_error(mock_requests):
    """Test API call with model not found error (404)."""
    mock_requests.post(
        API_URL,
        json={"error": {"message": "Model not found"}},
        status_code=404
    )

    # Expect base OpenRouterAPIError for non-specific client errors
    with pytest.raises(OpenRouterAPIError, match=r"API request failed: Model not found \(HTTP 404\)"):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_server_error(mock_requests):
    """Test API call with server error (500)."""
    mock_requests.post(
        API_URL,
        json={"error": {"message": "Internal server error"}},
        status_code=500
    )

    # Expect base OpenRouterAPIError for server errors
    with pytest.raises(OpenRouterAPIError, match=r"API request failed: Internal server error \(HTTP 500\)"):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_connection_error(mock_requests):
    """Test API call with a connection error."""
    mock_requests.post(API_URL, exc=requests.exceptions.ConnectionError("Failed to connect"))

    # Expect specific OpenRouterConnectionError
    with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API: Failed to connect"):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_timeout_error(mock_requests):
    """Test API call with a timeout error."""
    mock_requests.post(API_URL, exc=requests.exceptions.Timeout("Request timed out"))

    # Expect specific OpenRouterConnectionError (as Timeout inherits from RequestException)
    with pytest.raises(OpenRouterConnectionError, match="Network error connecting to OpenRouter API: Request timed out"):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_unexpected_response_format_no_choices(mock_requests):
    """Test API call with unexpected successful response format (missing choices)."""
    mock_requests.post(
        API_URL,
        json={"message": "Something unexpected"},
        status_code=200
    )

    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'choices' array is missing, empty, or not an array."):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_unexpected_response_format_empty_choices(mock_requests):
    """Test API call with empty 'choices' list."""
    mock_requests.post(
        API_URL,
        json={"choices": [], "usage": {}},
        status_code=200
    )

    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'choices' array is missing, empty, or not an array."):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_unexpected_response_format_no_message(mock_requests):
    """Test API call with missing 'message' in the first choice."""
    mock_requests.post(
        API_URL,
        json={"choices": [{"no_message_here": "..."}], "usage": {}},
        status_code=200
    )

    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'message' object is missing or not an object in the first choice."):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_unexpected_response_format_no_content(mock_requests):
    """Test API call with missing 'content' in the message."""
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"no_content_here": "..."}}], "usage": {}},
        status_code=200
    )

    with pytest.raises(OpenRouterAPIError, match="Unexpected response format: 'content' key is missing in the message."):
        call_openrouter(PROMPT, TEST_CONFIG)

def test_call_openrouter_missing_config_key():
    """Test API call with missing essential key in config dict."""
    bad_config = {
        'openrouter': {
            # Missing 'api_key'
            'model': "test-model/test-model",
            'params': {'temperature': 0.7},
            'site_url': "http://test-site.com",
            'app_name': "TestApp"
        }
    }
    with pytest.raises(ConfigError, match="Missing expected configuration key: 'api_key'"):
        call_openrouter(PROMPT, bad_config)

def test_call_openrouter_missing_openrouter_section():
    """Test API call with missing 'openrouter' section in config dict."""
    bad_config = {
        # Missing 'openrouter' section entirely
        'prompts': {}
    }
    with pytest.raises(ConfigError, match="Missing expected configuration key: 'openrouter'"):
        call_openrouter(PROMPT, bad_config)
