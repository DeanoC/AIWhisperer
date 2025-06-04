#!/usr/bin/env python3
"""
Run regression tests for tool execution flow.

This script tests fundamental tool calling patterns to ensure:
1. Tools are executed when requested
2. Tool results are processed and shown to users
3. No empty messages or continuation issues
4. The conversation completes properly
"""
import subprocess
import json
import sys
import time
from pathlib import Path


def run_conversation_test(conversation_file, test_name, expected_patterns):
    """Run a conversation replay test and check for expected patterns."""
    print(f"\n{'='*60}")
    print(f"Running test: {test_name}")
    print(f"Conversation: {conversation_file}")
    print(f"{'='*60}")
    
    # Run the conversation replay
    cmd = [
        sys.executable, "-m", "ai_whisperer.interfaces.cli.main",
        "--config", "config/main.yaml",
        "replay", conversation_file,
        "--timeout", "10"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Check for expected patterns
        success = True
        for pattern in expected_patterns:
            if pattern in output:
                print(f"✅ Found expected: {pattern}")
            else:
                print(f"❌ Missing expected: {pattern}")
                success = False
        
        # Check for error patterns that indicate issues
        error_patterns = [
            "MSG[6] role=user content=",  # Empty user message
            "MSG[7] role=user content=",  # Another empty message
            "Error executing tool",
            "tool_calls\": []",  # Empty tool calls when we expect them
        ]
        
        for pattern in error_patterns:
            if pattern in output and "content=" in pattern and "content=\n" in output:
                print(f"❌ Found error pattern: empty user message")
                success = False
            elif pattern in output and pattern != "content=":
                # More detailed check for actual errors
                lines = output.split('\n')
                for i, line in enumerate(lines):
                    if pattern in line:
                        # Check context
                        context_start = max(0, i-2)
                        context_end = min(len(lines), i+3)
                        context = '\n'.join(lines[context_start:context_end])
                        if "Error executing tool" in pattern or ("tool_calls\": []" in pattern and "fetch_url" in context):
                            print(f"❌ Found error pattern: {pattern}")
                            print(f"   Context: {context[:200]}...")
                            success = False
        
        # Save output for debugging
        output_file = f"test_results/tool_regression_{Path(conversation_file).stem}_{int(time.time())}.log"
        Path("test_results").mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(output)
        
        if success:
            print(f"\n✅ Test PASSED: {test_name}")
        else:
            print(f"\n❌ Test FAILED: {test_name}")
            print(f"   Full output saved to: {output_file}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"❌ Test TIMEOUT: {test_name}")
        return False
    except Exception as e:
        print(f"❌ Test ERROR: {test_name} - {e}")
        return False


def main():
    """Run all tool regression tests."""
    print("Tool Execution Regression Tests")
    print("=" * 60)
    
    tests = [
        {
            "file": "scripts/conversations/test_tool_execution.txt",
            "name": "Read File Tool Test",
            "patterns": [
                "🔧 EXECUTING TOOL 1/1: read_file",
                "🔧 TOOL CALLS COMPLETED:",
                "🔧 Tool results processed and final response generated",
                "AIWhisperer",  # Should see content from README
                "[FINAL]"
            ]
        },
        {
            "file": "scripts/conversations/test_fetch_github.txt", 
            "name": "Fetch URL Tool Test",
            "patterns": [
                "🔧 EXECUTING TOOL 1/1: fetch_url",
                "🔧 TOOL CALLS COMPLETED:",
                "🔧 Tool results processed and final response generated",
                "AI Whisperer",  # Should see content from GitHub
                "[FINAL]"
            ]
        }
    ]
    
    # Check if conversation files exist
    for test in tests:
        if not Path(test["file"]).exists():
            print(f"Warning: Test file not found: {test['file']}")
            # Create it if it doesn't exist
            Path(test["file"]).parent.mkdir(parents=True, exist_ok=True)
            if "read" in test["file"].lower():
                content = "Please read the file README.md and tell me what this project is about"
            else:
                content = "Can you show me the readme from https://github.com/DeanoC/AIWhisperer"
            Path(test["file"]).write_text(content)
            print(f"Created test file: {test['file']}")
    
    # Run tests
    results = []
    for test in tests:
        success = run_conversation_test(test["file"], test["name"], test["patterns"])
        results.append((test["name"], success))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Exit with error code if any tests failed
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()