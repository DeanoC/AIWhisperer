#!/usr/bin/env python3
"""Quick comparison of current vs revised Alice prompts"""

import asyncio
import json
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.alice_prompt_testing.run_ab_tests import AliceABTestRunner


async def quick_compare():
    """Run a quick comparison of one test scenario"""
    runner = AliceABTestRunner()
    
    test_file = "test_workspace_status.txt"
    
    print("Testing CURRENT prompt...")
    runner.swap_prompts(use_revised=False)
    current_result = await runner.run_single_test(test_file, "current", "quick_current")
    
    print("\nTesting REVISED prompt...")
    runner.swap_prompts(use_revised=True)
    revised_result = await runner.run_single_test(test_file, "revised", "quick_revised")
    
    # Restore original
    runner.swap_prompts(use_revised=False)
    
    # Compare results
    print("\n=== COMPARISON ===")
    
    # Current prompt analysis
    if current_result['success']:
        current_response = current_result['results'][0]['response'] if current_result['results'] else ""
        current_metrics = current_result['metrics'][0] if current_result['metrics'] else {}
        
        print(f"\nCURRENT PROMPT:")
        print(f"- Response length: {len(current_response)} chars")
        print(f"- Word count: {current_metrics.get('word_count', 'N/A')}")
        print(f"- Has channels: {current_metrics.get('has_channels', False)}")
        print(f"- Channel compliance: {current_metrics.get('channel_count', 0)} channels")
        print(f"- Response preview: {current_response[:200]}...")
    else:
        print(f"\nCURRENT PROMPT: Failed - {current_result.get('error', 'Unknown error')}")
    
    # Revised prompt analysis
    if revised_result['success']:
        revised_response = revised_result['results'][0]['response'] if revised_result['results'] else ""
        revised_metrics = revised_result['metrics'][0] if revised_result['metrics'] else {}
        
        print(f"\nREVISED PROMPT:")
        print(f"- Response length: {len(revised_response)} chars")
        print(f"- Word count: {revised_metrics.get('word_count', 'N/A')}")
        print(f"- Has channels: {revised_metrics.get('has_channels', False)}")
        print(f"- Channel compliance: {revised_metrics.get('channel_count', 0)} channels")
        print(f"- Response preview: {revised_response[:200]}...")
    else:
        print(f"\nREVISED PROMPT: Failed - {revised_result.get('error', 'Unknown error')}")
    
    # Save comparison
    comparison = {
        "test_file": test_file,
        "current": current_result,
        "revised": revised_result
    }
    
    output_file = runner.results_dir / "quick_comparison.json"
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(quick_compare())