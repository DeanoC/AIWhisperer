#!/usr/bin/env python3
"""
Direct batch test runner to reproduce chat bugs.
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from ai_whisperer.extensions.conversation_replay.conversation_client import ConversationClient


async def main():
    script_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/test_chat_bugs.json"
    
    print(f"Running batch test: {script_path}")
    
    # Updated to use ConversationClient
    # Note: This script needs to be updated for the new conversation replay architecture
    print("This script needs to be updated for the new conversation replay architecture")
    # client = ConversationClient(script_path, dry_run=False)
    # await client.run()


if __name__ == "__main__":
    asyncio.run(main())