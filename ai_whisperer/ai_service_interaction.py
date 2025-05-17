import requests
from typing import Dict, Any, List, Generator, Optional # Import Optional
import json
import threading # Import threading
from unittest.mock import MagicMock
import logging

from .tools.tool_registry import ToolRegistry
from .exceptions import (
    OpenRouterAPIError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
    ConfigError,
)

logger = logging.getLogger(__name__)

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_API_URL = "https://openrouter.ai/api/v1/models"


class OpenRouterAPI:
    """
    Client for interacting with the OpenRouter API.
    Handles authentication and provides methods to access various API endpoints,
    including streaming chat completions.
    """

    def __init__(self, config: Dict[str, Any], shutdown_event: Optional[threading.Event] = None):
        """
        Initialize the OpenRouter API client with configuration.

        Args:
            config: The 'openrouter' section of the application configuration dictionary,
                   expected to contain 'api_key', 'model', 'cache' (optional), etc.
            shutdown_event: An optional threading.Event to signal shutdown.

        Raises:
            ConfigError: If required configuration keys are missing.
        """
        logger.debug(f"OpenRouterAPI __init__ received config type: {type(config)}")
        # logger.debug(f"OpenRouterAPI __init__ received config: {config}")  # Too verbose, remove or summarize

        if not isinstance(config, dict):
            raise ConfigError(f"Invalid 'openrouter' configuration: Expected a dictionary, got {type(config)}")

        self.openrouter_config = config
        self.shutdown_event = shutdown_event # Store the shutdown event

        required_keys = ["api_key", "model"]
        missing_keys = [
            key for key in required_keys if key not in self.openrouter_config or not self.openrouter_config[key]
        ]
        if missing_keys:
            raise ConfigError(
                f"Missing expected configuration key within 'openrouter' section: {', '.join(missing_keys)}"
            )

        self.api_key = self.openrouter_config["api_key"]
        # logger.debug(f"OpenRouterAPI __init__ self.api_key after setting: {self.api_key}")  # Too verbose, remove
        self.model = self.openrouter_config["model"]  # Now required
        self.params = self.openrouter_config.get("params", {})  # Default params
        # logger.debug(f"OpenRouterAPI __init__ self.params after setting: {self.params}")  # Too verbose, remove
        self.site_url = self.openrouter_config.get("site_url", "https://github.com/DeanoC/AIWhisperer")
        self.app_name = self.openrouter_config.get("app_name", "AIWhisperer")

        self.enable_cache = self.openrouter_config.get("cache", False)
        if self.enable_cache:
            self._cache_store = {}
        else:
            self._cache_store = None

        # Initialize attributes for token data
        self._last_input_tokens: int | None = None
        self._last_output_tokens: int | None = None

    @property
    def cache(self):
        """Exposes the internal cache store for inspection."""
        return self._cache_store

    def _generate_cache_key(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, Any] = None,
    ) -> str:
        """Generates a cache key for a given request."""
        key_parts = {
            "model": model,
            "messages": messages,
            "params": params,
            "tools": (tools if tools else "None"),  # Ensure consistent hashing for None
            "response_format": (response_format if response_format else "None"),
        }
        # Sort dicts for consistent key generation
        return json.dumps(key_parts, sort_keys=True)
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> tuple[int | None, int | None]:
        """
        Extracts input and output tokens from the API response data (from 'usage' field).
        Returns None for any missing fields.
        """
        usage = response_data.get("usage")
        if usage:
            input_tokens = usage.get("prompt_tokens")
            output_tokens = usage.get("completion_tokens")
            return input_tokens, output_tokens
        return None, None

    def get_generation_stats(self, generation_id: str) -> dict:
        """
        Fetches detailed generation stats (including native token counts and cost) from OpenRouter's /generation endpoint.
        """
        url = f"https://openrouter.ai/api/v1/generation?id={generation_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            raise OpenRouterAPIError(f"Failed to fetch generation stats: {response.status_code} {response.text}", status_code=response.status_code, response=response)
        return response.json()

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
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        try:
            response = requests.get(MODELS_API_URL, headers=headers, timeout=30)

            # Check for HTTP errors first
            response.raise_for_status()

            logger.debug(f"OpenRouter API list_models raw response type: {type(response.text)}")
            logger.debug(f"OpenRouter API list_models raw response content: <truncated, {len(response.text)} chars>")

            try:
                data = response.json()
                # Ensure the expected data structure exists
                if "data" not in data or not isinstance(data["data"], list):
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'data' array is missing or not a list.",
                        status_code=response.status_code,
                        response=response,
                    )

                # Add logging to inspect elements in data["data"]
                for i, item in enumerate(data["data"]):
                    logger.debug(f"Element {i} in data['data'] type: {type(item)}")
                    # logger.debug(f"Element {i} in data['data'] content: {str(item)[:200]}... <truncated>")

                return data["data"]

            except ValueError as e:
                raise OpenRouterAPIError(
                    f"Failed to decode JSON response: {e}", status_code=response.status_code, response=response
                ) from e
            except (KeyError, TypeError) as e:
                raise OpenRouterAPIError(
                    f"Unexpected response structure: {e}", status_code=response.status_code, response=response
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
                    f"Authentication failed: {error_message}", status_code=status_code, response=e.response
                ) from e
            elif status_code == 429:
                raise OpenRouterRateLimitError(
                    f"Rate limit exceeded: {error_message}", status_code=status_code, response=e.response
                ) from e
            else:
                raise OpenRouterAPIError(
                    f"API request failed: {error_message}", status_code=status_code, response=e.response
                ) from e

        except requests.exceptions.RequestException as e:
            raise OpenRouterConnectionError(
                f"Network error connecting to OpenRouter API: {e}", original_exception=e
            ) from e

    def call_chat_completion(
        self,
        model: str,
        params: Dict[str, Any] = None,
        messages_history: List[Dict[str, Any]] = None,
        prompt_text: str = None,
        system_prompt: str = None,
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, Any] = None,
        images: List[str] = None,
        pdfs: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Calls the OpenRouter Chat Completions API with advanced features (non-streaming).
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


        # Standard OpenAI-compatible logic:
        # If messages_history is provided and non-empty, use it as the messages array.
        # If not, build messages array from system_prompt and prompt_text.
        current_messages: List[Dict[str, Any]] = []
        if messages_history and len(messages_history) > 0:
            current_messages = list(messages_history)
        else:
            if system_prompt:
                current_messages.append({"role": "system", "content": system_prompt})
            # Only add user message if prompt_text is provided
            if prompt_text:
                user_content_parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt_text}]
                if images:
                    for image_data in images:
                        if not image_data.startswith("data:image"):
                            user_content_parts.append({"type": "image_url", "image_url": {"url": image_data, "detail": "auto"}})
                        else:
                            user_content_parts.append({"type": "image_url", "image_url": {"url": image_data, "detail": "auto"}})
                if pdfs:
                    for pdf_data in pdfs:
                        user_content_parts.append({"type": "file_url", "file_url": {"url": pdf_data, "media_type": "application/pdf"}})
                if len(user_content_parts) == 1 and user_content_parts[0]["type"] == "text":
                    current_messages.append({"role": "user", "content": user_content_parts[0]["text"]})
                else:
                    current_messages.append({"role": "user", "content": user_content_parts})

        # Merge default parameters with provided parameters
        if params is None:
            merged_params = dict(self.params)
        else:
            merged_params = {**self.params, **params}

        # Merge default parameters with provided parameters
        merged_params = {**self.params, **(params or {})}

        payload = {
            "model": model,
            "messages": current_messages,
        }
        if merged_params:
            payload.update(merged_params)
        # Only include tools if explicitly provided (most common usage style)
        actual_tools = None
        if tools is not None and tools:
            payload["tools"] = tools
            actual_tools = tools
        if response_format:
            payload["response_format"] = response_format

        # Caching logic
        cache_key = None
        if self.enable_cache and self._cache_store is not None:
            cache_key = self._generate_cache_key(model, current_messages, params, actual_tools, response_format)
            if cache_key in self._cache_store:
                logger.info(f"Returning cached response for model {model}.")
                cached_message_obj = self._cache_store[cache_key]
                return {"response": None, "message": cached_message_obj}

        try:
            timeout = self.openrouter_config.get("timeout_seconds", 60)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                timeout = 60  # Default fallback

            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)

            # Explicitly check for HTTP errors before attempting to process JSON
            if response.status_code >= 400:
                status_code = response.status_code
                error_text = response.text
                # Attempt to extract a more detailed error message from JSON if available
                error_details = error_text
                try:
                    if "application/json" in response.headers.get("Content-Type", ""):
                        error_data = response.json()
                        error_details = error_data.get("error", {}).get("message", error_text)
                except ValueError:
                    pass  # If JSON decoding fails, use the raw text

                error_message = f"OpenRouter API Error: {status_code} - {error_details}"
                if len(error_message) > 500:  # Truncate long messages for logging/exception
                    error_message = error_message[:497] + "..."

                logger.error(f"HTTPError in call_chat_completion: {error_message}", exc_info=True)

                if status_code == 401:
                    raise OpenRouterAuthError(
                        f"Authentication failed: {error_message}", status_code=status_code, response=response
                    )
                elif status_code == 429:
                    raise OpenRouterRateLimitError(
                        f"Rate limit exceeded: {error_message}", status_code=status_code, response=response
                    )
                else:
                    raise OpenRouterAPIError(
                        f"API request failed: {error_message}", status_code=status_code, response=response
                    )

            # If we reach here, the HTTP status is 2xx. Proceed to process the JSON response.
            try:
                data = response.json()

                # Extract and store cost and token data
                self._last_input_tokens, self._last_output_tokens = self._extract_token_usage(data)
                logger.debug(f"Extracted input_tokens: {self._last_input_tokens}, output_tokens: {self._last_output_tokens}")

                # Special handling for OpenRouter error objects (e.g., 502, 500, etc.)
                if "error" in data:
                    error_obj = data["error"]
                    error_code = error_obj.get("code")
                    error_message = error_obj.get("message", "Unknown error")
                    # Raise a specific exception for 502 and 500 errors
                    if error_code in (500, 502):
                        raise OpenRouterAPIError(
                            f"OpenRouter provider/internal error ({error_code}): {error_message}",
                            status_code=error_code,
                            response=response,
                        )
                    # Otherwise, raise a generic API error
                    raise OpenRouterAPIError(
                        f"OpenRouter API error ({error_code}): {error_message}",
                        status_code=error_code,
                        response=response,
                    )

                choices = data.get("choices")
                if not choices or not isinstance(choices, list) or len(choices) == 0:
                    logging.error(f"Response missing 'choices': {data}")
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'choices' array is missing, empty, or not an array.",
                        status_code=response.status_code,
                        response=response,
                    )

                message_obj = choices[0].get("message")
                if not message_obj or not isinstance(message_obj, dict):
                    raise OpenRouterAPIError(
                        "Unexpected response format: 'message' object is missing or not an object in the first choice.",
                        status_code=response.status_code,
                        response=response,
                    )

                # Handle potential tool_calls that are None but present
                if "tool_calls" in message_obj and message_obj["tool_calls"] is None:
                    pass

                if self.enable_cache and self._cache_store is not None and cache_key is not None:
                    self._cache_store[cache_key] = message_obj

                # Return both the full response and the message object for downstream use
                return {"response": data, "message": message_obj}

            except ValueError as e:
                logger.error(f"JSONDecodeError in call_chat_completion: {e}. Response text: {response.text[:500]}")
                raise OpenRouterAPIError(
                    f"Failed to decode JSON response: {e}. Response text: {response.text[:500]}",
                    status_code=response.status_code,
                    response=response,
                ) from e
            except (KeyError, IndexError, TypeError) as e:
                logger.error(
                    f"Data structure error in call_chat_completion: {e}. Response data: {data if 'data' in locals() else 'N/A'}"
                )
                raise OpenRouterAPIError(
                    f"Unexpected response structure: {e}. Response data: {data if 'data' in locals() else 'N/A'}",
                    status_code=response.status_code,
                    response=response,
                ) from e

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error in call_chat_completion: {e}", exc_info=True)
            raise OpenRouterConnectionError(
                f"Request to OpenRouter API timed out after {timeout} seconds: {e}",  # Include timeout in message
                original_exception=e,
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException in call_chat_completion: {e}", exc_info=True)
            raise OpenRouterConnectionError(
                f"Network error connecting to OpenRouter API: {e}", original_exception=e
            ) from e

    def stream_chat_completion(
        self,
        prompt_text: str,
        model: str,
        params: Dict[str, Any],
        system_prompt: str = None,
        tools: List[Dict[str, Any]] = None,
        response_format: Dict[str, Any] = None,
        images: List[str] = None,  # If supported by model and OpenRouter streaming
        pdfs: List[str] = None,  # If supported by model and OpenRouter streaming
        messages_history: List[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Initiates a streaming chat completion request to the OpenRouter API.
        It sends the prompt and parameters, then yields parsed data chunks as they are received from the API.

        Args:
            prompt_text: The user's primary text prompt.
            model: The model identifier.
            params: API parameters (e.g., temperature).
            system_prompt: Optional system message.
            tools: Optional list of tool definitions.
            response_format: Optional specification for structured output.
            images: Optional list of image data (ensure OpenRouter streaming supports this).
            pdfs: Optional list of PDF data (ensure OpenRouter streaming supports this).
            messages_history: Optional list of previous messages to continue a conversation.

        Yields:
            Dictionaries representing parsed Server-Sent Event (SSE) data chunks.

        Raises:
            OpenRouterAuthError: For authentication failures.
            OpenRouterRateLimitError: If rate limits are exceeded.
            OpenRouterConnectionError: For network issues.
            OpenRouterAPIError: For other API errors, including those occurring mid-stream.
            ConfigError: For configuration-related issues.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        current_messages: List[Dict[str, Any]]

        if messages_history:
            current_messages = list(messages_history)  # Make a copy
        else:
            current_messages = []
            if system_prompt:
                current_messages.append({"role": "system", "content": system_prompt})

            user_content_parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt_text}]

            if images:
                for image_data in images:
                    if not image_data.startswith("data:image"):
                        user_content_parts.append(
                            {"type": "image_url", "image_url": {"url": image_data, "detail": "auto"}}
                        )
                    else:
                        user_content_parts.append(
                            {"type": "image_url", "image_url": {"url": image_data, "detail": "auto"}}
                        )

            if pdfs:
                for pdf_data in pdfs:
                    user_content_parts.append({"type": "file", "file": {"url": pdf_data}})

            if len(user_content_parts) == 1 and user_content_parts[0]["type"] == "text":
                current_messages.append({"role": "user", "content": user_content_parts[0]["text"]})
            else:
                current_messages.append({"role": "user", "content": user_content_parts})

        # Merge default parameters with provided parameters (although params is already merged in call_chat_completion,
        # we do it here again for consistency and in case stream is called directly)
        merged_params = {**self.params, **params}

        # Get tool definitions from the registry
        tool_registry = ToolRegistry()
        registered_tools = tool_registry.get_all_tools()
        openrouter_tool_definitions = [tool.get_openrouter_tool_definition() for tool in registered_tools]


        payload = {
            "model": model,
            "messages": current_messages,
            **merged_params,  # Merge parameters directly into the payload
            "stream": True,  # Enable streaming
        }
        # Only include tools if messages_history is None
        include_tools = messages_history is None
        if include_tools:
            if tools is not None:
                if tools:
                    payload["tools"] = tools
            elif openrouter_tool_definitions:
                payload["tools"] = openrouter_tool_definitions
        if response_format:
            payload["response_format"] = response_format

        try:
            timeout = self.openrouter_config.get("timeout_seconds", 60)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                timeout = 60  # Default fallback

            logger.debug(f"OpenRouter API stream_chat_completion payload: <payload with {len(str(payload))} chars>")

            # Use stream=True for streaming responses
            response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=timeout)

            # Explicitly check for HTTP errors before attempting to process the stream
            if response.status_code >= 400:
                status_code = response.status_code
                error_text = response.text
                error_details = error_text
                try:
                    if "application/json" in response.headers.get("Content-Type", ""):
                        error_data = response.json()
                        error_details = error_data.get("error", {}).get("message", error_text)
                except ValueError:
                    pass

                error_message = f"OpenRouter API Error: {status_code} - {error_details}"
                if len(error_message) > 500:
                    error_message = error_message[:497] + "..."

                logger.error(f"HTTPError in stream_chat_completion: {error_message}", exc_info=True)

                if status_code == 401:
                    raise OpenRouterAuthError(
                        f"Authentication failed: {error_message}", status_code=status_code, response=response
                    )
                elif status_code == 429:
                    raise OpenRouterRateLimitError(
                        f"Rate limit exceeded: {error_message}", status_code=status_code, response=response
                    )
                else:
                    raise OpenRouterAPIError(
                        f"API request failed: {error_message}", status_code=status_code, response=response
                    )

            # Process the streaming response
            for line in response.iter_lines():
                if self.shutdown_event and self.shutdown_event.is_set():
                    logger.info("Shutdown event detected during stream. Breaking.")
                    break # Exit loop if shutdown is signaled

                if line:  # Filter out keep-alive newlines
                    if line.startswith(b"data: "):  # Check for byte string prefix
                        decoded_line = line.decode("utf-8")
                        json_str = decoded_line[len("data:") :].strip()
                        if json_str == "[DONE]":
                            break  # End of stream
                        try:
                            json_chunk = json.loads(json_str)
                            yield json_chunk
                        except json.JSONDecodeError as e:
                            logger.error(f"JSONDecodeError in stream_chat_completion: {e}. Invalid chunk: {json_str}")
                            raise OpenRouterAPIError(
                                f"Failed to decode JSON chunk from stream: {e}. Chunk: {json_str[:100]}...",
                                status_code=response.status_code,  # Use the initial response status code
                                response=response,
                            ) from e
                    # Ignore other lines like 'event: message' or comments
                    else:
                        logger.debug(f"Ignoring non-data line in stream: {line.decode('utf-8')[:100]}")

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error in stream_chat_completion: {e}", exc_info=True)
            raise OpenRouterConnectionError(
                f"Request to OpenRouter API timed out after {timeout} seconds: {e}", original_exception=e
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException during stream processing: {e}", exc_info=True)
            # This catches network errors that occur *during* the stream iteration
            raise OpenRouterConnectionError(
                f"Network error during OpenRouter API streaming: {e}", original_exception=e
            ) from e
        except (OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError, OpenRouterAPIError) as e:
            # Re-raise these specific custom exceptions directly if they were raised intentionally within the try block
            raise
        except Exception as e:
            # Catch any other unexpected errors during processing
            logger.error(f"Unexpected error during stream processing: {e}", exc_info=True)
            raise OpenRouterAPIError(
                f"Unexpected error during OpenRouter API streaming: {e}",
                status_code=(getattr(e, "response", MagicMock()).status_code if hasattr(e, "response") else None),
                response=getattr(e, "response", None),
            ) from e
