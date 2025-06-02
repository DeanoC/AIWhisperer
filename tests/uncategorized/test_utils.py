import pytest
import logging

# Import the actual functions
from ai_whisperer.utils.helpers import setup_logging


# Basic test for logging setup - more complex tests could mock logging calls
def test_setup_logging_runs_without_error():
    """Test that setup_logging runs without raising exceptions."""
    try:
        setup_logging()
        # Check if a basic configuration might have been applied (optional)
        # assert logging.getLogger().hasHandlers() # This might be too specific depending on implementation
    except Exception as e:
        pytest.fail(f"setup_logging raised an exception: {e}")
