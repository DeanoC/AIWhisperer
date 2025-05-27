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

    # Check log contents for expected server responses
    found_message_id = False
    found_final_chunk = False
    found_hello = False
    found_weather = False
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if '"messageId"' in line:
                found_message_id = True
            if '"AIMessageChunkNotification"' in line and '"isFinal": true' in line:
                found_final_chunk = True
            if 'Hello, AI!' in line:
                found_hello = True
            if 'What is the weather?' in line:
                found_weather = True
    assert found_message_id, "No messageId found in log (sendUserMessage response missing)"
    assert found_final_chunk, "No final AIMessageChunkNotification found in log"
    assert found_hello, "Expected user message 'Hello, AI!' not found in log"
    assert found_weather, "Expected user message 'What is the weather?' not found in log"
