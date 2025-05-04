import requests
from typing import Dict, Any
from .exceptions import (
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError
)

API_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_openrouter(prompt_text: str, config: Dict[str, Any]) -> str:
    """
    Calls the OpenRouter Chat Completions API using configuration settings.

    Extracts API key, model, parameters, site URL, and app name from the
    provided configuration dictionary. Sets appropriate headers, including
    Authorization, HTTP-Referer, and X-Title.

    Handles various API errors by raising specific custom exceptions.

    Args:
        prompt_text: The user's prompt content.
        config: The application configuration dictionary, expected to contain
                'openrouter': {
                    'api_key': str,
                    'model': str,
                    'params': dict (optional),
                    'site_url': str (optional, defaults used if missing),
                    'app_name': str (optional, defaults used if missing)
                }.

    Returns:
        The content string from the 'message' object in the API response's first choice.

    Raises:
        ConfigError: If required configuration keys ('openrouter', 'api_key', 'model',
                     'site_url', 'app_name') are missing within the passed config dict.
                     Note: 'api_key' presence is usually ensured by load_config.
        OpenRouterConnectionError: If there's a network issue (connection, timeout)
                                   connecting to the API.
        OpenRouterAuthError: If authentication fails (HTTP 401).
        OpenRouterRateLimitError: If rate limits are exceeded (HTTP 429).
        OpenRouterAPIError: For other API-related errors (e.g., bad request,
                            server error, unexpected response format).
    """
    try:
        openrouter_config = config['openrouter']
        api_key = openrouter_config['api_key']
        model = openrouter_config['model']
        params = openrouter_config.get('params', {})
        site_url = openrouter_config['site_url']
        app_name = openrouter_config['app_name']
    except KeyError as e:
        raise ConfigError(f"Missing expected configuration key: {e}") from e

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": site_url,
        "X-Title": app_name,
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        **params
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        try:
            data = response.json()
            choices = data.get('choices')
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                raise OpenRouterAPIError("Unexpected response format: 'choices' array is missing, empty, or not an array.", status_code=response.status_code, response=response)

            message = choices[0].get('message')
            if not message or not isinstance(message, dict):
                raise OpenRouterAPIError("Unexpected response format: 'message' object is missing or not an object in the first choice.", status_code=response.status_code, response=response)

            content = message.get('content')
            if content is None:
                raise OpenRouterAPIError("Unexpected response format: 'content' key is missing in the message.", status_code=response.status_code, response=response)

            return str(content)

        except ValueError as e:
            raise OpenRouterAPIError(f"Failed to decode JSON response: {e}", status_code=response.status_code, response=response) from e
        except (KeyError, IndexError, TypeError) as e:
            raise OpenRouterAPIError(f"Unexpected response structure: {e}", status_code=response.status_code, response=response) from e

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_message = f"HTTP error {status_code}"
        try:
            error_data = e.response.json()
            error_details = error_data.get('error', {}).get('message', e.response.text)
            error_message = f"{error_details} (HTTP {status_code})"
        except ValueError:
            error_details = e.response.text
            error_message = f"Non-JSON error response (HTTP {status_code}): {error_details[:100]}..."

        if status_code == 401:
            raise OpenRouterAuthError(f"Authentication failed: {error_message}", status_code=status_code, response=e.response) from e
        elif status_code == 429:
            raise OpenRouterRateLimitError(f"Rate limit exceeded: {error_message}", status_code=status_code, response=e.response) from e
        else:
            raise OpenRouterAPIError(f"API request failed: {error_message}", status_code=status_code, response=e.response) from e

    except requests.exceptions.RequestException as e:
        raise OpenRouterConnectionError(f"Network error connecting to OpenRouter API: {e}", original_exception=e) from e
