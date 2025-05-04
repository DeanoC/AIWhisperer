# -*- coding: utf-8 -*-
"""Custom exception types for the AI Whisperer application."""

class AIWhispererError(Exception):
    """Base class for all application-specific errors."""
    pass

class ConfigError(AIWhispererError):
    """Exception raised for errors in the configuration file (loading, parsing, validation)."""
    pass

class APIError(AIWhispererError):
    """Exception raised for errors during interaction with the OpenRouter API."""
    pass

class ProcessingError(AIWhispererError):
    """Exception raised for errors during file processing (reading MD, writing YAML, etc.)."""
    pass
