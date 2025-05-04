import requests
from .exceptions import APIError

API_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter(api_key: str, model: str, prompt_text: str, params: dict) -> str:
    """
    Calls the OpenRouter Chat Completions API.

    Args:
        api_key: The OpenRouter API key.
        model: The model identifier (e.g., 'google/gemini-flash-1.5').
        prompt_text: The user's prompt content.
        params: Additional parameters for the API call (e.g., temperature).

    Returns:
        The content of the message from the API response.

    Raises:
        APIError: If there's an issue with the API call or response.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        **params # Add any extra parameters like temperature, max_tokens etc.
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60) # Added timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        # Process successful response
        try:
            data = response.json()
            if not data.get('choices'):
                raise APIError("Unexpected response format from OpenRouter API: No choices returned")
            if not data['choices'][0].get('message'):
                 raise APIError("Unexpected response format from OpenRouter API: Choice missing 'message' key")
            if 'content' not in data['choices'][0]['message']:
                 raise APIError("Unexpected response format from OpenRouter API: Message missing 'content' key")

            return data['choices'][0]['message']['content']

        except (ValueError, KeyError, IndexError) as e: # Catch JSON decoding errors or missing keys/indices
            raise APIError(f"Unexpected response format from OpenRouter API: {e}") from e

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_message = f"HTTP error {status_code}"
        try:
            # Try to get more specific error from response body
            error_details = e.response.json().get('error', {}).get('message', e.response.text)
            error_message = f"{error_details} ({status_code})"
        except ValueError: # If response is not JSON
            error_details = e.response.text
            error_message = f"{error_details[:100]}... ({status_code})" # Truncate long non-JSON errors

        if 400 <= status_code < 500:
            if status_code == 401:
                 raise APIError(f"Authentication error ({status_code}): Check your API key.") from e
            else:
                 raise APIError(f"Client error ({status_code}): {error_message}") from e
        elif 500 <= status_code < 600:
            raise APIError(f"Server error ({status_code}): {error_message}") from e
        else:
            raise APIError(f"Unhandled HTTP error: {error_message}") from e

    except requests.exceptions.RequestException as e:
        # Catch connection errors, timeouts, etc.
        raise APIError(f"Network error connecting to OpenRouter API: {e}") from e
