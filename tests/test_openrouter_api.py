import pytest
import requests
import requests_mock
from src.ai_whisperer.exceptions import APIError
# Import the actual function
from src.ai_whisperer.openrouter_api import call_openrouter

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = "test-api-key"
MODEL = "test-model/test-model"
PROMPT = "Test prompt"
PARAMS = {'temperature': 0.7}

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
        request_headers={'Authorization': f'Bearer {API_KEY}'}
    )

    response = call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)
    assert response == expected_response_content

    # Verify the request payload
    history = mock_requests.request_history
    assert len(history) == 1
    request = history[0]
    assert request.method == 'POST'
    assert request.url == API_URL
    assert request.headers['Authorization'] == f'Bearer {API_KEY}'
    assert request.json()['model'] == MODEL
    assert request.json()['messages'] == [{"role": "user", "content": PROMPT}]
    assert request.json()['temperature'] == PARAMS['temperature']

def test_call_openrouter_auth_error(mock_requests):
    """Test API call with authentication error (401)."""
    mock_requests.post(
        API_URL,
        json={"error": {"message": "Invalid API key"}},
        status_code=401
    )

    with pytest.raises(APIError, match=r"Authentication error \(401\)"):  # Use raw string
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_not_found_error(mock_requests):
    """Test API call with model not found error (404)."""
    mock_requests.post(
        API_URL,
        json={"error": {"message": "Model not found"}},
        status_code=404
    )

    with pytest.raises(APIError, match=r"Client error \(404\)"):  # Use raw string
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_server_error(mock_requests):
    """Test API call with server error (500)."""
    mock_requests.post(
        API_URL,
        json={"error": {"message": "Internal server error"}},
        status_code=500
    )

    with pytest.raises(APIError, match=r"Server error \(500\)"):  # Use raw string
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_connection_error(mock_requests):
    """Test API call with a connection error."""
    mock_requests.post(API_URL, exc=requests.exceptions.ConnectionError("Failed to connect"))

    with pytest.raises(APIError, match="Network error connecting to OpenRouter API"):
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_timeout_error(mock_requests):
    """Test API call with a timeout error."""
    mock_requests.post(API_URL, exc=requests.exceptions.Timeout("Request timed out"))

    with pytest.raises(APIError, match="Network error connecting to OpenRouter API"):
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_unexpected_response_format(mock_requests):
    """Test API call with unexpected successful response format."""
    # Missing 'choices' key
    mock_requests.post(
        API_URL,
        json={"message": "Something unexpected"},
        status_code=200
    )

    with pytest.raises(APIError, match="Unexpected response format from OpenRouter API"):
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_empty_choices(mock_requests):
    """Test API call with empty 'choices' list."""
    mock_requests.post(
        API_URL,
        json={"choices": [], "usage": {}},
        status_code=200
    )

    with pytest.raises(APIError, match="Unexpected response format from OpenRouter API: No choices returned"):
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_missing_message_in_choice(mock_requests):
    """Test API call with missing 'message' in the first choice."""
    mock_requests.post(
        API_URL,
        json={"choices": [{"no_message_here": "..."}], "usage": {}},
        status_code=200
    )

    with pytest.raises(APIError, match="Unexpected response format from OpenRouter API: Choice missing 'message' key"):
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)

def test_call_openrouter_missing_content_in_message(mock_requests):
    """Test API call with missing 'content' in the message."""
    mock_requests.post(
        API_URL,
        json={"choices": [{"message": {"no_content_here": "..."}}], "usage": {}},
        status_code=200
    )

    with pytest.raises(APIError, match="Unexpected response format from OpenRouter API: Message missing 'content' key"):
        call_openrouter(API_KEY, MODEL, PROMPT, PARAMS)
