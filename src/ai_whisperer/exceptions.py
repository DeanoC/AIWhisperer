# -*- coding: utf-8 -*-
"""Custom exception types for the AI Whisperer application."""
import requests  # Import requests to potentially include response info in errors
import jsonschema  # Import jsonschema for validation error handling


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
        self.response = response  # Store the response for potential debugging


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


# --- Orchestrator Errors ---


class OrchestratorError(AIWhispererError):
    """Base class for errors specific to the Orchestrator."""

    pass

class PlanNotLoadedError(OrchestratorError):
    """Exception raised when a plan is expected but has not been loaded."""
    pass

class HashMismatchError(OrchestratorError):
    """Error raised when input hashes in the API response do not match calculated hashes."""

    def __init__(self, expected_hashes: dict, received_hashes: dict):
        self.expected_hashes = expected_hashes
        self.received_hashes = received_hashes
        message = f"Input hash mismatch detected.\n" f"  Expected: {expected_hashes}\n" f"  Received: {received_hashes}"
        super().__init__(message)


class YAMLValidationError(AIWhispererError):
    """Custom exception for YAML validation errors."""

    def __init__(self, validation_errors: list):
        # Ensure validation_errors is a list of ValidationError objects
        if not isinstance(validation_errors, list) or not all(
            isinstance(err, jsonschema.exceptions.ValidationError) for err in validation_errors
        ):
            message = "Invalid input for YAMLValidationError. Expected a list of ValidationError objects."
            super().__init__(message)
            return

        # Format the error messages from the validation errors
        error_details = "\n".join(
            [
                f"- {e.message} (path: {' -> '.join(map(str, e.path)) if e.path else 'N/A'})\n"
                f"  Schema path: {' -> '.join(map(str, e.schema_path)) if e.schema_path else 'N/A'}"
                for e in validation_errors
            ]
        )
        message = f"YAML validation failed:\n{error_details}"
        super().__init__(message)


class PromptError(OrchestratorError):
    """Errors related to loading or processing prompt files."""

    pass


class OrchestrationError(AIWhispererError):
    """Exception raised for errors during the orchestration process."""

    pass


class TaskExecutionError(AIWhispererError):
    """Exception raised for errors during the execution of a task."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details


class ToolNotFound(AIWhispererError):
    """Exception raised when a requested tool is not found in the registry."""
    pass

class FileRestrictionError(AIWhispererError):
    """Exception raised when a file operation is restricted."""
    pass

# --- Add the missing exceptions ---


class SubtaskGenerationError(AIWhispererError):
    """Exception raised for errors during the subtask generation process."""

    pass


class SchemaValidationError(AIWhispererError):
    """Exception raised when generated data fails schema validation."""

class PromptNotFoundError(AIWhispererError):
    """Exception raised when a prompt is not found in the resolution hierarchy."""
    pass
