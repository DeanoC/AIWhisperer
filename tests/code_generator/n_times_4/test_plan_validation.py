import os
import shutil
import pytest
from pathlib import Path
import subprocess

PLAN_DIR = Path(__file__).parent
PLAN_JSON = PLAN_DIR / "overview_n_times_4.json"
OUTPUT_FILE = PLAN_DIR / "output" / "n_times_4.py"
RUN_SCRIPT = PLAN_DIR / "run_plan.ps1"

@pytest.fixture(autouse=True)
def clean_output():
    output_dir = PLAN_DIR / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)
    yield
    # Clean up after test
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_plan_passes_if_output_file_present():
    # Create the output file
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text("def n_times_4(x):\n    return x * 4\n")
    # Run the plan using the PowerShell script
    result = subprocess.run([
        "powershell.exe", "-NoProfile", "-Command", str(RUN_SCRIPT), str(PLAN_JSON)
    ], capture_output=True, text=True)
    # The process should exit with zero code if validation passes
    assert result.returncode == 0, f"Expected success, got exit code {result.returncode}. Output: {result.stdout}\n{result.stderr}"
    assert "passed" in result.stdout.lower() or "success" in result.stdout.lower(), f"Expected success message. Output: {result.stdout}\n{result.stderr}"
