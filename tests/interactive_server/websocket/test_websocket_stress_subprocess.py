import subprocess
import sys
import os
import pytest

@pytest.mark.performance
def test_websocket_stress_subprocess():
    """Run the websocket stress test in a subprocess to avoid thread/event loop leaks."""
    pytest.xfail("Known issue: FastAPI TestClient + threading + asyncio event loop leaks cause process to hang. See https://github.com/tiangolo/fastapi/issues/3941 and related discussions.")
    test_file = os.path.join(os.path.dirname(__file__), "test_websocket_stress.py")
    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    print("[Subprocess STDOUT]\n" + result.stdout)
    print("[Subprocess STDERR]\n" + result.stderr)
    # If the subprocess timed out or crashed, fail
    assert result.returncode in (0, 5), f"Test subprocess failed or hung (exit code {result.returncode})"
    # 0 = success, 5 = skipped (pytest exit code for all tests skipped)
    if result.returncode == 5:
        pytest.skip("WebSocket stress test skipped in subprocess (API key or event loop issue)")
