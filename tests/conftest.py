import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
import pytest
import json

# Ensure logging is set up before any tests run
from ai_whisperer.logging_custom import setup_basic_logging

def pytest_configure(config):
    setup_basic_logging()

# Helper for checking exception types in mock calls
# This should ideally be in conftest.py or a shared test utility file
# For now, adding it here for self-containment in this diff.
# In a real scenario, you'd add this to conftest.py
if not hasattr(pytest, 'helpers'):
    class PytestHelpers:
        def assert_exception_type(self, expected_type):
            class ExceptionTypeMatcher:
                def __eq__(self, other):
                    return isinstance(other, expected_type)

                def __repr__(self):
                    return f"<instance of {expected_type.__name__}>"
            return ExceptionTypeMatcher()
    pytest.helpers = PytestHelpers()