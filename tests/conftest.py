import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
import pytest
import json


@pytest.fixture
def simple_country_plan():
    """Loads the simple country test plan."""
    plan_path = "./tests/simple_run_test_country/overview_simple_run_test_country_aiwhisperer_config.json"
    with open(plan_path, "r") as f:
        return json.load(f)
