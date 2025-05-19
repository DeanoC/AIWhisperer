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