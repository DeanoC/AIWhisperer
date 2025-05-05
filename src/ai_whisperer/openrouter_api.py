import requests
from typing import Dict, Any, List
from .exceptions import (
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError
)

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_API_URL = "https://openrouter.ai/api/v1/models"

class OpenRouterAPI:
    """
    Client for interacting with the OpenRouter API.
    Handles authentication and provides methods to access various API endpoints.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OpenRouter API client with configuration.

        Args:
            config: The 'openrouter' section of the application configuration dictionary,
                   expected to contain 'api_key', 'model', etc.

        Raises:
            ConfigError: If required configuration keys are missing.
        """
        try:
            self.openrouter_config = config  # Use the passed dict directly
            self.api_key = self.openrouter_config['api_key']
            self.model = self.openrouter_config.get('model')
            self.params = self.openrouter_config.get('params', {})
            self.site_url = self.openrouter_config.get('site_url', 'https://github.com/yourusername/AIWhisperer')
            self.app_name = self.openrouter_config.get('app_name', 'AIWhisperer')
        except KeyError as e:
            raise ConfigError(f"Missing expected configuration key within 'openrouter' section: {e}") from e
        except Exception as e:
            raise ConfigError(f"Error initializing OpenRouterAPI from config: {e}") from e
    
    def list_models(self) -> List[str]:
        """
        Retrieves a list of available model IDs from the OpenRouter API.
        
        Returns:
            A list of model ID strings that can be used with the OpenRouter API.
            
        Raises:
            OpenRouterConnectionError: If there's a network issue connecting to the API.
            OpenRouterAuthError: If authentication fails (HTTP 401).
            OpenRouterRateLimitError: If rate limits are exceeded (HTTP 429).
            OpenRouterAPIError: For other API-related errors.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.get(MODELS_API_URL, headers=headers, timeout=30)
            response.raise_for_status()
            
            try:
                data = response.json()
                # Ensure the expected data structure exists
                if "data" not in data or not isinstance(data["data"], list):
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'data' array is missing or not a list.", 
                        status_code=response.status_code, 
                        response=response
                    )
                
                # Extract model IDs from the response
                model_ids = [model["id"] for model in data["data"] if "id" in model]
                return model_ids
                
            except ValueError as e:
                raise OpenRouterAPIError(
                    f"Failed to decode JSON response: {e}", 
                    status_code=response.status_code, 
                    response=response
                ) from e
            except (KeyError, TypeError) as e:
                raise OpenRouterAPIError(
                    f"Unexpected response structure: {e}", 
                    status_code=response.status_code, 
                    response=response
                ) from e
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_message = f"HTTP error {status_code}"
            try:
                error_data = e.response.json()
                error_details = error_data.get("error", {}).get("message", e.response.text)
                error_message = f"{error_details} (HTTP {status_code})"
            except ValueError:
                error_details = e.response.text
                error_message = f"Non-JSON error response (HTTP {status_code}): {error_details[:100]}..."

            if status_code == 401:
                raise OpenRouterAuthError(
                    f"Authentication failed: {error_message}", 
                    status_code=status_code, 
                    response=e.response
                ) from e
            elif status_code == 429:
                raise OpenRouterRateLimitError(
                    f"Rate limit exceeded: {error_message}", 
                    status_code=status_code, 
                    response=e.response
                ) from e
            else:
                raise OpenRouterAPIError(
                    f"API request failed: {error_message}", 
                    status_code=status_code, 
                    response=e.response
                ) from e
                
        except requests.exceptions.RequestException as e:
            raise OpenRouterConnectionError(
                f"Network error connecting to OpenRouter API: {e}", 
                original_exception=e
            ) from e
    
    def call_chat_completion(self, prompt_text: str, model: str = None, params: Dict[str, Any] = None) -> str:
        """
        Calls the OpenRouter Chat Completions API with the provided prompt.
        
        Args:
            prompt_text: The user's prompt content.
            model: Optional model override. If not provided, uses the model from config.
            params: Optional parameters override. If provided, these parameters will be
                   merged with (and take precedence over) the default parameters from config.
            
        Returns:
            The content string from the 'message' object in the API response's first choice.
            
        Raises:
            OpenRouterConnectionError: If there's a network issue connecting to the API.
            OpenRouterAuthError: If authentication fails (HTTP 401).
            OpenRouterRateLimitError: If rate limits are exceeded (HTTP 429).
            OpenRouterAPIError: For other API-related errors.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }
        
        # Use provided model or fall back to config
        model_to_use = model if model is not None else self.model
        
        # Start with default params from config
        request_params = dict(self.params)
        
        # Update with override params if provided
        if params:
            request_params.update(params)

        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            **request_params
        }

        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            try:
                data = response.json()
                choices = data.get('choices')
                if not choices or not isinstance(choices, list) or len(choices) == 0:
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'choices' array is missing, empty, or not an array.",
                        status_code=response.status_code, 
                        response=response
                    )

                message = choices[0].get('message')
                if not message or not isinstance(message, dict):
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'message' object is missing or not an object in the first choice.",
                        status_code=response.status_code,
                        response=response
                    )

                content = message.get('content')
                if content is None:
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'content' key is missing in the message.",
                        status_code=response.status_code,
                        response=response
                    )

                return str(content)

            except ValueError as e:
                raise OpenRouterAPIError(
                    f"Failed to decode JSON response: {e}",
                    status_code=response.status_code,
                    response=response
                ) from e
            except (KeyError, IndexError, TypeError) as e:
                raise OpenRouterAPIError(
                    f"Unexpected response structure: {e}",
                    status_code=response.status_code,
                    response=response
                ) from e

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
                raise OpenRouterAuthError(
                    f"Authentication failed: {error_message}",
                    status_code=status_code,
                    response=e.response
                ) from e
            elif status_code == 429:
                raise OpenRouterRateLimitError(
                    f"Rate limit exceeded: {error_message}",
                    status_code=status_code,
                    response=e.response
                ) from e
            else:
                raise OpenRouterAPIError(
                    f"API request failed: {error_message}",
                    status_code=status_code,
                    response=e.response
                ) from e

        except requests.exceptions.RequestException as e:
            raise OpenRouterConnectionError(
                f"Network error connecting to OpenRouter API: {e}",
                original_exception=e
            ) from e


# Keep the original call_openrouter function for backward compatibility
def call_openrouter(prompt_text: str, config: Dict[str, Any], model: str = None, params: Dict[str, Any] = None) -> str:
    """
    Calls the OpenRouter Chat Completions API using configuration settings.
    
    This is a backward-compatibility wrapper around the OpenRouterAPI class.

    Args:
        prompt_text: The user's prompt content.
        config: The application configuration dictionary.
        model: Optional model override. If not provided, uses the model from config.
        params: Optional parameters override. If provided, these parameters will
               be merged with (and take precedence over) the default parameters from config.

    Returns:
        The content string from the 'message' object in the API response's first choice.

    Raises:
        ConfigError: If required configuration keys are missing.
        OpenRouterConnectionError: If there's a network issue connecting to the API.
        OpenRouterAuthError: If authentication fails (HTTP 401).
        OpenRouterRateLimitError: If rate limits are exceeded (HTTP 429).
        OpenRouterAPIError: For other API-related errors.
    """
    # Create an instance of OpenRouterAPI and delegate the call
    client = OpenRouterAPI(config)
    return client.call_chat_completion(prompt_text=prompt_text, model=model, params=params)
