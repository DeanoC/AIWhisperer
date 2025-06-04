#!/usr/bin/env python3
"""
Quick diagnostic script to test continuation protocol compliance.

Usage:
    python scripts/test_continuation_compliance.py [--model MODEL]
"""
import subprocess
import json
import sys
import re
from pathlib import Path
import argparse


def extract_continuation_signal(text: str) -> dict:
    """Extract continuation JSON from response text."""
    # Look for JSON objects containing "continuation"
    json_pattern = r'\{[^{}]*"continuation"[^{}]*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            data = json.loads(match)
            if 'continuation' in data:
                return data['continuation']
        except json.JSONDecodeError:
            continue
    
    return None


def run_test(prompt: str, config: str = "config/main.yaml", timeout: int = 10) -> dict:
    """Run a single test and return results."""
    # Create temporary test file
    test_file = Path("temp_continuation_test.txt")
    test_file.write_text(prompt)
    
    try:
        # Run conversation replay
        result = subprocess.run(
            [
                sys.executable, "-m", "ai_whisperer.interfaces.cli.main",
                "--config", config,
                "replay", str(test_file),
                "--timeout", str(timeout)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Extract model name
        model_match = re.search(r"Starting OpenRouter stream for model: (.+)", output)
        model_name = model_match.group(1) if model_match else "Unknown"
        
        # Look for continuation signal
        continuation = extract_continuation_signal(output)
        
        # Check if response was generated
        has_final = "[FINAL]" in output
        
        # Check for tool usage
        has_tools = "TOOL CALLS COMPLETED" in output or "EXECUTING TOOL" in output
        
        return {
            "prompt": prompt,
            "model": model_name,
            "has_response": has_final,
            "has_tools": has_tools,
            "has_continuation": continuation is not None,
            "continuation": continuation,
            "output_sample": output[-500:] if len(output) > 500 else output  # Last 500 chars
        }
        
    finally:
        test_file.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Test continuation protocol compliance")
    parser.add_argument("--model", help="Model to test (requires config file)")
    parser.add_argument("--config", default="config/main.yaml", help="Config file to use")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()
    
    # Test cases
    test_cases = [
        ("Simple intro", "Who are you?"),
        ("Simple math", "What is 2+2?"),
        ("Read file", "What's in the README.md file?"),
        ("List files", "List the Python files in the current directory"),
    ]
    
    print("=== Continuation Protocol Compliance Test ===")
    print(f"Config: {args.config}")
    print("=" * 60)
    
    results = []
    for test_name, prompt in test_cases:
        print(f"\nTesting: {test_name}")
        print(f"Prompt: {prompt}")
        
        result = run_test(prompt, args.config)
        results.append(result)
        
        # Display results
        print(f"Model: {result['model']}")
        print(f"Response generated: {'✅' if result['has_response'] else '❌'}")
        print(f"Tools used: {'✅' if result['has_tools'] else '❌'}")
        print(f"Continuation signal: {'✅' if result['has_continuation'] else '❌'}")
        
        if result['has_continuation']:
            cont = result['continuation']
            print(f"  Status: {cont.get('status', 'N/A')}")
            print(f"  Reason: {cont.get('reason', 'N/A')}")
        else:
            print("  ⚠️  NO CONTINUATION SIGNAL FOUND")
            if args.verbose:
                print("\nLast part of output:")
                print("-" * 40)
                print(result['output_sample'])
                print("-" * 40)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    compliant = sum(1 for r in results if r['has_continuation'])
    total = len(results)
    
    if compliant == total:
        print(f"✅ Model is COMPLIANT: {compliant}/{total} tests passed")
    else:
        print(f"❌ Model is NOT COMPLIANT: {compliant}/{total} tests passed")
        print("\nFailed tests:")
        for r in results:
            if not r['has_continuation']:
                print(f"  - {r['prompt']}")
    
    # Return exit code based on compliance
    sys.exit(0 if compliant == total else 1)


if __name__ == "__main__":
    main()