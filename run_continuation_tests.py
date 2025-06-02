#!/usr/bin/env python3
"""
Run continuation system regression tests.

This script runs comprehensive tests of the agent continuation system,
including multi-tool execution and explicit continuation signals.
"""

import sys
import subprocess
import json
from pathlib import Path
import argparse
from datetime import datetime


def run_json_batch_test(script_path: str, verbose: bool = False) -> bool:
    """Run a JSON batch test script."""
    print(f"\n{'='*60}")
    print(f"Running: {script_path}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    cmd = [
        sys.executable, "-m", "ai_whisperer.batch.batch_client",
        script_path
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"\nTest FAILED with return code: {result.returncode}")
            return False
        else:
            print(f"\nTest PASSED")
            return True
            
    except Exception as e:
        print(f"Error running test: {e}")
        return False


def run_text_batch_test(script_path: str, config_path: str = "config.yaml") -> bool:
    """Run a text batch test script."""
    print(f"\n{'='*60}")
    print(f"Running: {script_path}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    cmd = [
        sys.executable, "-m", "ai_whisperer.cli",
        script_path,
        "--config", config_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"\nTest FAILED with return code: {result.returncode}")
            return False
        else:
            print(f"\nTest PASSED")
            return True
            
    except Exception as e:
        print(f"Error running test: {e}")
        return False


def analyze_test_results(log_file: str = None):
    """Analyze test results from logs."""
    print(f"\n{'='*60}")
    print("Test Analysis")
    print(f"{'='*60}\n")
    
    # Key patterns to look for
    patterns = {
        "Multi-tool execution": "SINGLE_TOOL_MODEL_ERROR",
        "Continuation decisions": "CONTINUATION STRATEGY DECISION:",
        "Explicit signals": "Explicit continuation signal:",
        "Safety limits": "Safety limits reached",
        "Tool executions": "EXECUTING TOOLS: Found",
    }
    
    if log_file and Path(log_file).exists():
        with open(log_file, 'r') as f:
            log_content = f.read()
            
        for name, pattern in patterns.items():
            count = log_content.count(pattern)
            print(f"{name}: {count} occurrences")
    else:
        print("No log file specified or file not found")
        print("Check logs/aiwhisperer_server.log for detailed information")


def main():
    parser = argparse.ArgumentParser(description="Run agent continuation system tests")
    parser.add_argument(
        "--test",
        choices=["regression", "quick", "all"],
        default="all",
        help="Which test to run"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze test results from logs"
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file for analysis"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path(".WHISPER").exists():
        print("ERROR: Must run from an AIWhisperer project directory (no .WHISPER found)")
        sys.exit(1)
    
    results = []
    
    if args.test in ["regression", "all"]:
        # Run comprehensive regression test
        if Path("scripts/test_continuation_regression.json").exists():
            success = run_json_batch_test(
                "scripts/test_continuation_regression.json",
                verbose=args.verbose
            )
            results.append(("Regression Test", success))
        else:
            print("WARNING: Regression test script not found")
    
    if args.test in ["quick", "all"]:
        # Run quick text test
        if Path("test_continuation_quick.txt").exists():
            success = run_text_batch_test("test_continuation_quick.txt")
            results.append(("Quick Test", success))
        else:
            print("WARNING: Quick test script not found")
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
    
    # Analyze if requested
    if args.analyze:
        analyze_test_results(args.log_file)
    
    # Exit with appropriate code
    all_passed = all(success for _, success in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()