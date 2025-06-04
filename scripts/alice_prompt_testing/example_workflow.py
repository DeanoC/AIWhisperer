#!/usr/bin/env python3
"""
Example workflow script demonstrating the complete A/B testing process.

This script:
1. Sets up the testing environment
2. Runs a small A/B test
3. Evaluates results with Debbie
4. Displays a summary
"""

import asyncio
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


async def run_example_workflow():
    """Run the complete example workflow."""
    print("=== Alice Prompt A/B Testing Example Workflow ===\n")
    
    # Step 1: Setup
    print("Step 1: Setting up metrics integration...")
    result = subprocess.run([
        sys.executable, 
        "scripts/alice_prompt_testing/setup_metrics_integration.py"
    ], cwd=PROJECT_ROOT, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Setup failed: {result.stderr}")
        return
    print("✓ Setup complete\n")
    
    # Step 2: Check for revised prompt
    revised_prompt = PROJECT_ROOT / "prompts" / "agents" / "alice_assistant_revised.prompt.md"
    if not revised_prompt.exists():
        print("! No revised prompt found. Using the template created by setup.")
        print(f"  Edit {revised_prompt} to add your improvements.\n")
    
    # Step 3: Run A/B tests (just 1 iteration for demo)
    print("Step 2: Running A/B tests (1 iteration for demo)...")
    test_runner = "scripts/alice_prompt_testing/run_ab_tests.py"
    
    # Import and run directly to capture results
    from run_ab_tests import AliceABTestRunner
    
    runner = AliceABTestRunner()
    results = await runner.run_all_tests(iterations=1)
    
    # Find the latest results file
    results_dir = Path(__file__).parent / "results"
    result_files = sorted(results_dir.glob("ab_test_results_*.json"))
    if not result_files:
        print("No results files found!")
        return
    
    latest_results = result_files[-1]
    print(f"✓ Test results saved to: {latest_results}\n")
    
    # Step 4: Quick analysis (without Debbie for demo)
    print("Step 3: Analyzing results...")
    with open(latest_results, 'r') as f:
        test_results = json.load(f)
    
    # Simple analysis
    current_results = [r for r in test_results if r["prompt_version"] == "current"]
    revised_results = [r for r in test_results if r["prompt_version"] == "revised"]
    
    print("\n=== Quick Analysis ===")
    print(f"Tests run: {len(test_results)}")
    print(f"Current prompt: {len(current_results)} tests")
    print(f"Revised prompt: {len(revised_results)} tests")
    
    # Check for channel usage
    def has_channels(results):
        """Check if responses use channel structure."""
        count = 0
        for result in results:
            if result.get("success"):
                responses = result.get("results", [])
                for r in responses:
                    if "[FINAL]" in r.get("response", ""):
                        count += 1
                        break
        return count
    
    current_channels = has_channels(current_results)
    revised_channels = has_channels(revised_results)
    
    print(f"\nChannel usage:")
    print(f"  Current: {current_channels}/{len(current_results)} tests")
    print(f"  Revised: {revised_channels}/{len(revised_results)} tests")
    
    # Step 5: Recommendations
    print("\n=== Next Steps ===")
    print("1. Review the test results in detail:")
    print(f"   cat {latest_results} | python -m json.tool | less")
    print("\n2. Run Debbie's evaluation for detailed analysis:")
    print(f"   python scripts/alice_prompt_testing/evaluate_with_debbie.py {latest_results}")
    print("\n3. Run a full test with more iterations:")
    print("   python scripts/alice_prompt_testing/run_ab_tests.py --iterations 5")
    print("\n4. Iterate on your revised prompt based on the feedback")
    
    # Step 6: Show example improvements
    print("\n=== Example Prompt Improvements ===")
    print("Based on common issues, consider these improvements:")
    print("1. Add explicit instruction to ALWAYS use response channels")
    print("2. Add 'Skip preambles like \"I'll help you...\"'")
    print("3. Emphasize 'Use tools immediately without asking'")
    print("4. Add 'Complete all steps before responding'")
    print("5. Include specific examples of good vs bad responses")


def main():
    """Main entry point."""
    try:
        asyncio.run(run_example_workflow())
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
    except Exception as e:
        print(f"\nError during workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()