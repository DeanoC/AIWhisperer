# -*- coding: utf-8 -*-
"""Custom exception types for the AI Whisperer application."""
import requests # Import requests to potentially include response info in errors

class AIWhispererError(Exception):
    """Base class for all application-specific errors."""
    pass

class ConfigError(AIWhispererError):
    """Exception raised for errors in the configuration file (loading, parsing, validation)."""
    pass

# --- OpenRouter API Errors ---

class OpenRouterAPIError(AIWhispererError):
    """Base class for errors during interaction with the OpenRouter API.

    Attributes:
        status_code: The HTTP status code associated with the error, if available.
        response: The requests.Response object, if available.
    """
    def __init__(self, message: str, status_code: int | None = None, response: requests.Response | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response # Store the response for potential debugging

class OpenRouterAuthError(OpenRouterAPIError):
    """Raised for authentication errors (HTTP 401) with the OpenRouter API."""
    pass

class OpenRouterRateLimitError(OpenRouterAPIError):
    """Raised for rate limit errors (HTTP 429) with the OpenRouter API."""
    pass

class OpenRouterConnectionError(AIWhispererError):
    """Raised for network connection errors when trying to reach the OpenRouter API.

    Attributes:
        original_exception: The original exception that caused this error (e.g., requests.ConnectionError).
    """
    def __init__(self, message: str, original_exception: Exception | None = None):
        super().__init__(message)
        self.original_exception = original_exception


class ProcessingError(AIWhispererError):
    """Exception raised for errors during file processing (reading MD, writing YAML, etc.)."""
    pass
