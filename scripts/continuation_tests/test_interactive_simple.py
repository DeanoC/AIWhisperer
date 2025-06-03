#!/usr/bin/env python3
"""Test interactive server directly to bypass batch client issues"""

import asyncio
import subprocess
import time

async def test_interactive():
    # Start server
    print("Starting interactive server...")
    server = subprocess.Popen(
        ["python", "-m", "interactive_server.main", "--config", "config/main.yaml", "--port", "9999"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server
    time.sleep(5)
    
    try:
        print("\nServer started. You can now test manually:")
        print("1. Open a new terminal")
        print("2. Run: python -m ai_whisperer.interfaces.cli.main --config config/main.yaml")
        print("3. Type your messages to test continuation")
        print("\nPress Ctrl+C when done testing")
        
        # Keep server running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.terminate()
        server.wait()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(test_interactive())