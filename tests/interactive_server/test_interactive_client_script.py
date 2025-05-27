import subprocess
import sys
import os
import pathlib
import pytest

SCRIPT_DIR = pathlib.Path(__file__).parent.parent.parent / "project_dev"
CLIENT = SCRIPT_DIR / "interactive_client.py"

@pytest.mark.parametrize("script_file", [
    "interactive_client_script_example.txt",
    "interactive_client_script_example.json",
])
def test_interactive_client_script(script_file, tmp_path):
    script_path = SCRIPT_DIR / script_file
    log_path = tmp_path / f"{script_file}.log"
    # Start the server externally before running this test, or use the fixture if available
    result = subprocess.run([
        sys.executable, str(CLIENT),
        "--script", str(script_path),
        "--log", str(log_path)
    ], capture_output=True, text=True, timeout=30)
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)
    assert result.returncode == 0
    assert log_path.exists()
    # Optionally, check log contents for expected server responses
