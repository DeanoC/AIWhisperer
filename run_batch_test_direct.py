#!/usr/bin/env python3
"""Direct batch test runner that properly passes dry_run parameter."""

import asyncio
import sys
from ai_whisperer.batch.batch_client import BatchClient

async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_batch_test_direct.py <script_file>")
        sys.exit(1)
    
    script_file = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    print(f"Running batch script: {script_file}")
    print(f"Dry run: {dry_run}")
    
    try:
        client = BatchClient(script_file, dry_run=dry_run)
        await client.run()
        print("\nBatch execution completed successfully")
    except Exception as e:
        print(f"\nBatch execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())