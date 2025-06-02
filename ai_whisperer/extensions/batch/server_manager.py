"""
Server lifecycle management for batch mode.
Handles starting, stopping, and monitoring the interactive server for Debbie's batch client.
"""

import random
import subprocess
import time
import socket
class ServerManager:
    def __init__(self, port=None):
        self.port = port
        self.process = None

    def start_server(self, max_retries=5):
        """Start the interactive server on a random or specified port. Retries if port is in use."""
        print("🚀 Starting batch mode server...")
        attempts = 0
        while attempts < max_retries:
            try:
                if self.port is None:
                    self.port = random.randint(20000, 40000)
                print(f"   📡 Attempting to start server on port {self.port}")
                self._start_subprocess()
                # Wait for server to initialize properly
                time.sleep(2.0)  # Interactive server needs time to initialize
                if self.is_running():
                    print(f"   ✅ Batch server started successfully on port {self.port}")
                    print(f"   📁 Server logs: logs/aiwhisperer_server_batch_{self.port}.log")
                    print(f"   🌐 Server URL: http://127.0.0.1:{self.port}")
                    return
                else:
                    # If not running, treat as failure and retry
                    print(f"   ❌ Server failed to start on port {self.port}, retrying...")
                    self.port = None
            except OSError as e:
                if "Address already in use" in str(e):
                    print(f"   ⚠️ Port {self.port} already in use, trying another port...")
                    self.port = None  # Pick a new port next time
                else:
                    raise
            finally:
                attempts += 1
        # If we reach here, we've tried max_retries times and failed
        raise RuntimeError(f"Failed to start server after {max_retries} attempts")

    def _start_subprocess(self):
        """Start the actual server subprocess using interactive_server.main directly."""
        # Start the interactive server using its main module
        # This ensures proper initialization and argument parsing
        import sys
        import os
        
        print(f"   🔧 Starting subprocess with Python: {sys.executable}")
        print(f"   🔧 Port: {self.port}")
        
        # Set environment variable for port-specific logging
        env = os.environ.copy()
        env['AIWHISPERER_BATCH_PORT'] = str(self.port)
        
        server_cmd = [
            sys.executable,
            "-m", "interactive_server.main",
            f"--host=127.0.0.1",
            f"--port={self.port}"
        ]
        
        print(f"   🔧 Command: {' '.join(server_cmd)}")
        print(f"   🔧 Environment AIWHISPERER_BATCH_PORT: {env.get('AIWHISPERER_BATCH_PORT')}")
        
        try:
            self.process = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            print(f"   🔧 Subprocess started with PID: {self.process.pid}")
            
            # Wait for server to be ready
            if not self._wait_for_server_ready():
                self.stop_server()
                raise RuntimeError(f"Server failed to start on port {self.port}")
                
        except Exception as e:
            print(f"   ❌ Failed to start subprocess: {e}")
            raise

    def stop_server(self):
        """Stop the interactive server if running."""
        if self.process:
            print(f"🛑 Stopping batch server on port {self.port}")
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
                print(f"   ✅ Batch server stopped successfully")
            except Exception as e:
                print(f"   ⚠️ Error stopping server: {e}")
            self.process = None

    def is_running(self):
        """Check if the server is running."""
        return self.process is not None and getattr(self.process, 'poll', lambda: None)() is None

    def _wait_for_server_ready(self, timeout_seconds: int = 10) -> bool:
        """Wait for the server to be ready to accept connections."""
        print(f"   ⏳ Waiting for server to be ready on port {self.port}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                # Try to connect to the server port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', self.port))
                sock.close()
                
                if result == 0:
                    print(f"   ✅ Server is ready on port {self.port}")
                    return True
                    
            except Exception:
                pass
                
            time.sleep(0.5)
        
        print(f"   ❌ Server not ready after {timeout_seconds} seconds")
        return False
