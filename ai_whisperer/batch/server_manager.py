"""
Server lifecycle management for batch mode.
Handles starting, stopping, and monitoring the interactive server for Debbie's batch client.
"""


import random
import subprocess
import time

class ServerManager:
    def __init__(self, port=None):
        self.port = port
        self.process = None

    def start_server(self, max_retries=5):
        """Start the interactive server on a random or specified port. Retries if port is in use."""
        attempts = 0
        while attempts < max_retries:
            try:
                if self.port is None:
                    self.port = random.randint(20000, 40000)
                self._start_subprocess()
                # Optionally wait for server to be up
                time.sleep(0.05)
                if self.is_running():
                    return
                else:
                    # If not running, treat as failure and retry
                    self.port = None
            except OSError as e:
                if "Address already in use" in str(e):
                    self.port = None  # Pick a new port next time
                else:
                    raise
            finally:
                attempts += 1
        # If we reach here, we've tried max_retries times and failed
        raise RuntimeError(f"Failed to start server after {max_retries} attempts")

    def _start_subprocess(self):
        """Start the actual server subprocess for interactive_server.main using uvicorn."""
        # Start the FastAPI server on the selected port
        # Use the same Python interpreter and pass the port
        import sys
        server_cmd = [
            sys.executable,
            "-m", "uvicorn",
            "interactive_server.main:app",
            f"--host=127.0.0.1",
            f"--port={self.port}",
            "--log-level=info"
        ]
        self.process = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop_server(self):
        """Stop the interactive server if running."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                pass
            self.process = None

    def is_running(self):
        """Check if the server is running."""
        return self.process is not None and getattr(self.process, 'poll', lambda: None)() is None
