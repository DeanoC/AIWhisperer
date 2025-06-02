#!/usr/bin/env python3
"""
Entry point for batch mode execution.
Usage: python -m ai_whisperer.batch.batch_client <script_path>
"""
import sys
import asyncio
from .batch_client import BatchClient


def main():
    """Main entry point for batch client"""
    if len(sys.argv) < 2:
        print("Usage: python -m ai_whisperer.batch.batch_client <script_path>", file=sys.stderr)
        print("Example: python -m ai_whisperer.batch.batch_client scripts/test.json", file=sys.stderr)
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    try:
        client = BatchClient(script_path, dry_run=False)
        asyncio.run(client.run())
    except Exception as e:
        print(f"Batch execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()