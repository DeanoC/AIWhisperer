#!/usr/bin/env python3
"""
Run batch test using existing server on port 8000.
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from ai_whisperer.extensions.batch.client import BatchClient


async def main():
    script_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/test_chat_bugs.json"
    
    print(f"Running batch test: {script_path}")
    print("Using existing server on port 8000...")
    
    # Create client with existing server URI
    client = BatchClient(script_path, server_port=8000, ws_uri="ws://localhost:8000/ws", dry_run=False)
    
    # Prevent it from trying to start a new server
    client.server_manager.port = 8000
    client.server_manager.process = None  # Fake process to skip startup
    
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())