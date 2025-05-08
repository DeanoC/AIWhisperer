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
                   expected to contain 'api_key', 'model', 'cache' (optional), etc.

        Raises:
            ConfigError: If required configuration keys are missing.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"OpenRouterAPI __init__ received config type: {type(config)}")
        logger.debug(f"OpenRouterAPI __init__ received config: {config}")

        if not isinstance(config, dict):
            raise ConfigError(f"Invalid 'openrouter' configuration: Expected a dictionary, got {type(config)}")

        self.openrouter_config = config
        
        required_keys = ['api_key', 'model']
        missing_keys = [key for key in required_keys if key not in self.openrouter_config or not self.openrouter_config[key]]
        if missing_keys:
            raise ConfigError(f"Missing expected configuration key within 'openrouter' section: {', '.join(missing_keys)}")

        self.api_key = self.openrouter_config['api_key']
        self.model = self.openrouter_config['model'] # Now required
        self.params = self.openrouter_config.get('params', {}) # Default params
        self.site_url = self.openrouter_config.get('site_url', 'https://github.com/DeanoC/AIWhisperer')
        self.app_name = self.openrouter_config.get('app_name', 'AIWhisperer')
        
        self.enable_cache = self.openrouter_config.get('cache', False)
        if self.enable_cache:
            self._cache_store = {}
        else:
            self._cache_store = None

    @property
    def cache(self):
        """Exposes the internal cache store for inspection."""
        return self._cache_store

    def _generate_cache_key(self, model: str, messages: List[Dict[str, Any]], params: Dict[str, Any], tools: List[Dict[str, Any]] = None, response_format: Dict[str, Any] = None) -> str:
        """Generates a cache key for a given request."""
        import json
        key_parts = {
            "model": model,
            "messages": messages,
            "params": params,
            "tools": tools if tools else "None", # Ensure consistent hashing for None
            "response_format": response_format if response_format else "None"
        }
        # Sort dicts for consistent key generation
        return json.dumps(key_parts, sort_keys=True)

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of available models with detailed metadata from the OpenRouter API.
        
        Returns:
            A list of dictionaries, where each dictionary contains detailed information
            about a model.
            
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

            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"OpenRouter API list_models raw response type: {type(response.text)}")
            logger.debug(f"OpenRouter API list_models raw response content: {response.text[:500]}") # Log first 500 chars
            
            try:
                data = response.json()
                # Ensure the expected data structure exists
                if "data" not in data or not isinstance(data["data"], list):
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'data' array is missing or not a list.",
                        status_code=response.status_code,
                        response=response
                    )
                
                # Extract detailed model information from the response
                # Extract only the model IDs from the response
                # Extract detailed model information from the response
                # The API call should return all the data for all the models
                
                # Add logging to inspect elements in data["data"]
                for i, item in enumerate(data["data"]):
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Element {i} in data['data'] type: {type(item)}")
                    logger.debug(f"Element {i} in data['data'] content: {item}")

                return data["data"]
                
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
    
    def call_chat_completion(
        self,
        prompt_text: str,
        model: str,
        params: Dict[str, Any],
        system_prompt: str = None,
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, Any] = None,
        images: List[str] = None,
        pdfs: List[str] = None,
        # For tool usage, the calling code will manage history.
        # This function can be called iteratively.
        # If `messages_history` is provided, it's used instead of constructing from prompt_text.
        messages_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calls the OpenRouter Chat Completions API with advanced features.
        Handles a single turn or continues a conversation if messages_history is provided.

        Args:
            prompt_text: The user's primary text prompt (used if messages_history is None).
            model: The model identifier.
            params: API parameters (e.g., temperature).
            system_prompt: Optional system message (used if messages_history is None and it's the first turn).
            tools: Optional list of tool definitions.
            response_format: Optional specification for structured output (e.g., JSON schema).
            images: Optional list of image URLs or base64 encoded image data (used with prompt_text).
            pdfs: Optional list of base64 encoded PDF data (used with prompt_text).
            messages_history: Optional list of previous messages to continue a conversation.
                              If provided, prompt_text, system_prompt, images, pdfs are ignored for message construction.

        Returns:
            The 'message' object from the API response's first choice,
            which may include 'content', 'tool_calls', or 'file_annotations'.

        Raises:
            OpenRouterConnectionError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterAPIError.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        current_messages: List[Dict[str, Any]]

        if messages_history:
            current_messages = list(messages_history) # Make a copy
        else:
            current_messages = []
            if system_prompt:
                current_messages.append({"role": "system", "content": system_prompt})

            user_content_parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt_text}]

            if images:
                for image_data in images:
                    # Basic check if it's a base64 string or URL
                    # A more robust check might be needed for production
                    if not image_data.startswith("data:image"): # Assuming URLs don't start with data:image
                         # It's a URL
                        user_content_parts.append({"type": "image_url", "image_url": {"url": image_data, "detail": "auto"}})
                    else: # It's base64
                        user_content_parts.append({"type": "image_url", "image_url": {"url": image_data, "detail": "auto"}})
            
            if pdfs:
                for pdf_data in pdfs: # Assuming pdf_data is already a base64 data URI
                    user_content_parts.append({"type": "file", "file": {"url": pdf_data}})

            # If only text is present, OpenRouter expects content as a string, not a list.
            if len(user_content_parts) == 1 and user_content_parts[0]["type"] == "text":
                current_messages.append({"role": "user", "content": user_content_parts[0]["text"]})
            else:
                current_messages.append({"role": "user", "content": user_content_parts})
        
        payload = {
            "model": model,
            "messages": current_messages,
            **params
        }

        if tools:
            payload["tools"] = tools
        
        if response_format:
            payload["response_format"] = response_format

        # Caching logic
        cache_key = None
        if self.enable_cache and self._cache_store is not None:
            # For caching, ensure messages_history is part of the key if used,
            # otherwise use the constructed current_messages.
            cache_key = self._generate_cache_key(model, current_messages, params, tools, response_format)
            if cache_key in self._cache_store:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Returning cached response for model {model}.")
                cached_message_obj = self._cache_store[cache_key]
                # Apply the same logic as for a fresh response to return content or full object
                if cached_message_obj.get('content') is not None and cached_message_obj.get('tool_calls') is None:
                    return cached_message_obj.get('content')
                else:
                    return cached_message_obj

        try:
            timeout = self.openrouter_config.get('timeout_seconds', 60)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                timeout = 60 # Default fallback
            
            import logging # Ensure logger is available
            logger = logging.getLogger(__name__)
            logger.debug(f"OpenRouter API call_chat_completion payload: {payload}")

            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)

            # Explicitly check for HTTP errors before attempting to process JSON
            if response.status_code >= 400:
                status_code = response.status_code
                error_text = response.text
                # Attempt to extract a more detailed error message from JSON if available
                error_details = error_text
                try:
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        error_data = response.json()
                        error_details = error_data.get("error", {}).get("message", error_text)
                except ValueError:
                    pass # If JSON decoding fails, use the raw text

                error_message = f"OpenRouter API Error: {status_code} - {error_details}"
                if len(error_message) > 500: # Truncate long messages for logging/exception
                     error_message = error_message[:497] + "..."

                logger.error(f"HTTPError in call_chat_completion: {error_message}", exc_info=True)

                if status_code == 401:
                    raise OpenRouterAuthError(
                        f"Authentication failed: {error_message}",
                        status_code=status_code,
                        response=response
                    )
                elif status_code == 429:
                    raise OpenRouterRateLimitError(
                        f"Rate limit exceeded: {error_message}",
                        status_code=status_code,
                        response=response
                    )
                else:
                    raise OpenRouterAPIError(
                        f"API request failed: {error_message}",
                        status_code=status_code,
                        response=response
                    )

            # If we reach here, the HTTP status is 2xx. Proceed to process the JSON response.
            try:
                data = response.json()
                logger.debug(f"OpenRouter API call_chat_completion response data: {data}")
                choices = data.get('choices')
                if not choices or not isinstance(choices, list) or len(choices) == 0:
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'choices' array is missing, empty, or not an array.",
                        status_code=response.status_code,
                        response=response
                    )

                message_obj = choices[0].get('message')
                if not message_obj or not isinstance(message_obj, dict):
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'message' object is missing or not an object in the first choice.",
                        status_code=response.status_code,
                        response=response
                    )

                # Handle potential tool_calls that are None but present
                if "tool_calls" in message_obj and message_obj["tool_calls"] is None:
                    # Some models might return "tool_calls": null instead of omitting it.
                    # We can remove it for consistency if it's null, or ensure downstream handles it.
                    # For now, let's keep it as is, as the model returned it.
                    pass

                if self.enable_cache and self._cache_store is not None and cache_key is not None:
                    self._cache_store[cache_key] = message_obj

                # Return only the content for simple text responses,
                # otherwise return the full message object (e.g., for tool calls)
                if message_obj.get('content') is not None and message_obj.get('tool_calls') is None:
                    return message_obj.get('content')
                else:
                    return message_obj

            except ValueError as e:
                logger.error(f"JSONDecodeError in call_chat_completion: {e}. Response text: {response.text[:500]}")
                raise OpenRouterAPIError(
                    f"Failed to decode JSON response: {e}. Response text: {response.text[:500]}",
                    status_code=response.status_code,
                    response=response
                ) from e
            except (KeyError, IndexError, TypeError) as e:
                logger.error(f"Data structure error in call_chat_completion: {e}. Response data: {data if 'data' in locals() else 'N/A'}")
                raise OpenRouterAPIError(
                    f"Unexpected response structure: {e}. Response data: {data if 'data' in locals() else 'N/A'}",
                    status_code=response.status_code,
                    response=response
                ) from e

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error in call_chat_completion: {e}", exc_info=True)
            raise OpenRouterConnectionError(
                f"Request to OpenRouter API timed out after {timeout} seconds: {e}", # Include timeout in message
                original_exception=e
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException in call_chat_completion: {e}", exc_info=True)
            raise OpenRouterConnectionError(
                f"Network error connecting to OpenRouter API: {e}",
                original_exception=e
            ) from e
