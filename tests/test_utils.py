import pytest
import logging
from rich.console import Console

# Import the actual functions
from src.ai_whisperer.utils import setup_logging, setup_rich_output


def test_setup_rich_output_returns_console():
    """Test that setup_rich_output returns a Console instance."""
    console = setup_rich_output()
    assert isinstance(console, Console)


# Basic test for logging setup - more complex tests could mock logging calls
def test_setup_logging_runs_without_error():
    """Test that setup_logging runs without raising exceptions."""
    try:
        setup_logging()
        # Check if a basic configuration might have been applied (optional)
        # assert logging.getLogger().hasHandlers() # This might be too specific depending on implementation
    except Exception as e:
        pytest.fail(f"setup_logging raised an exception: {e}")
