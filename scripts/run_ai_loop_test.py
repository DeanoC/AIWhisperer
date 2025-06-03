#!/usr/bin/env python3
"""
Run the per-agent AI loops test using Debbie and conversation replay.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_whisperer.interfaces.cli.main import main


def run_test():
    """Run the per-agent AI loops test conversation."""
    # Set up arguments for conversation replay
    sys.argv = [
        "ai_whisperer",
        "--config", "config/main.yaml",
        "replay",
        "scripts/conversations/test_per_agent_ai_loops.txt"
    ]
    
    print("="*60)
    print("Testing Per-Agent AI Loops")
    print("="*60)
    print("\nThis test will:")
    print("1. Start with Debbie and inspect AI loop configurations")
    print("2. Switch to Alice and verify she uses the default model")
    print("3. Switch to Eamonn and verify he uses Claude-3-Opus")
    print("4. Return to Debbie for final verification")
    print("\nStarting test...\n")
    
    # Run the conversation replay
    main()


if __name__ == "__main__":
    run_test()