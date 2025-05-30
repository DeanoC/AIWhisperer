"""
Integration test for batch mode: runs the CLI with a real script, server, and OpenRouter AI connection.
"""

import os
import subprocess
import time
import pytest
from ai_whisperer.config import load_config

BATCH_SCRIPT = "tests/data/example_batch_script.txt"
CONFIG_PATH = "config.yaml"
CLI_ENTRY = "ai_whisperer.cli"

@pytest.mark.integration
def test_batch_mode_e2e(monkeypatch):

    # Load config to ensure .env and API key are loaded for the test process
    config = load_config(CONFIG_PATH)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    assert api_key, "OPENROUTER_API_KEY must be set in environment/.env for this test."

    # Start the server in a subprocess (if not auto-started by CLI)
    # (Assume CLI starts server if not running)

    # Run the CLI with the batch script
    cmd = [
        "python", "-m", CLI_ENTRY, BATCH_SCRIPT, "--config", CONFIG_PATH
    ]
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = api_key
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        stdout, stderr = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise AssertionError("Batch mode CLI did not complete in 60 seconds.")

    # Output for debugging
    print("STDOUT:\n", stdout.decode())
    print("STDERR:\n", stderr.decode())

    # Check for expected output (AI response, success message, etc.)
    assert proc.returncode == 0, f"CLI exited with code {proc.returncode}"
    assert b"Debbie" in stdout or b"batch complete" in stdout.lower(), "Expected batch output not found."
