#!/usr/bin/env python3
"""
Simple test to verify prompt compliance with new standards.
Tests channel usage, conciseness, and autonomous behavior.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.interfaces.cli.main import main as cli_main
from ai_whisperer.core.config import load_config


def create_test_conversations():
    """Create test conversation files."""
    test_dir = Path("test_conversations")
    test_dir.mkdir(exist_ok=True)
    
    tests = {
        "alice_conciseness.txt": [
            "What tools do I have available?",
            "List the files in my workspace"
        ],
        "alice_switching.txt": [
            "I need to create an RFC for a new feature"
        ],
        "patricia_immediate.txt": [
            "switch to patricia",
            "I want to add dark mode to the application"
        ],
        "debbie_monitoring.txt": [
            "switch to debbie", 
            "Check the session health"
        ]
    }
    
    created_files = []
    for filename, messages in tests.items():
        filepath = test_dir / filename
        with open(filepath, 'w') as f:
            f.write('\n'.join(messages))
        created_files.append(filepath)
    
    return created_files


def analyze_conversation_output(output_file: Path) -> dict:
    """Analyze the output of a conversation replay."""
    if not output_file.exists():
        return {"error": "Output file not found"}
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    # Look for channel markers
    has_analysis = "[ANALYSIS]" in content
    has_commentary = "[COMMENTARY]" in content  
    has_final = "[FINAL]" in content
    
    # Extract FINAL content
    final_content = ""
    if has_final:
        import re
        final_matches = re.findall(r'\[FINAL\](.*?)(?:\[/FINAL\]|\[ANALYSIS\]|\[COMMENTARY\]|$)', content, re.DOTALL)
        if final_matches:
            final_content = final_matches[-1].strip()
    
    # Count lines in final
    final_lines = len([l for l in final_content.split('\n') if l.strip()]) if final_content else 0
    
    # Check for forbidden phrases
    forbidden = ["I'll help you", "Let me", "Great!", "Certainly!", "I'd be happy to"]
    violations = [p for p in forbidden if p.lower() in content.lower()]
    
    return {
        "has_channels": has_analysis or has_commentary or has_final,
        "has_all_channels": has_analysis and has_commentary and has_final,
        "final_lines": final_lines,
        "final_within_limit": final_lines <= 4,
        "violations": violations,
        "total_length": len(content),
        "word_count": len(content.split())
    }


async def run_conversation_test(conversation_file: Path, config_path: str = "config/main.yaml"):
    """Run a conversation replay test."""
    print(f"\nTesting: {conversation_file.name}")
    
    # Run conversation replay
    output_file = conversation_file.with_suffix('.output.txt')
    
    # We need to run this through the CLI
    import subprocess
    cmd = [
        sys.executable, "-m", "ai_whisperer.interfaces.cli.main",
        "--config", config_path,
        "replay", str(conversation_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Save output
        with open(output_file, 'w') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write(f"\n\nERROR OUTPUT:\n{result.stderr}")
        
        # Analyze results
        analysis = analyze_conversation_output(output_file)
        
        return {
            "test": conversation_file.name,
            "success": result.returncode == 0,
            "analysis": analysis
        }
        
    except subprocess.TimeoutExpired:
        return {
            "test": conversation_file.name,
            "success": False,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "test": conversation_file.name,
            "success": False,
            "error": str(e)
        }


async def main():
    """Run all tests."""
    print("Creating test conversations...")
    test_files = create_test_conversations()
    
    print("\nRunning prompt compliance tests...")
    results = []
    
    for test_file in test_files:
        result = await run_conversation_test(test_file)
        results.append(result)
        
        # Print immediate feedback
        if result["success"] and "analysis" in result:
            a = result["analysis"]
            channels_status = 'YES' if a['has_all_channels'] else ('PARTIAL' if a['has_channels'] else 'NO')
            print(f"  ✓ Channels: {channels_status}")
            lines_status = 'YES' if a['final_within_limit'] else f"NO ({a['final_lines']} lines)"
            print(f"  ✓ Final ≤4 lines: {lines_status}")
            violations_status = 'YES' if not a['violations'] else 'NO: ' + ', '.join(a['violations'])
            print(f"  ✓ No violations: {violations_status}")
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    successful = [r for r in results if r["success"]]
    if successful:
        channel_compliance = sum(1 for r in successful if r["analysis"]["has_all_channels"]) / len(successful) * 100
        line_compliance = sum(1 for r in successful if r["analysis"]["final_within_limit"]) / len(successful) * 100
        no_violations = sum(1 for r in successful if not r["analysis"]["violations"]) / len(successful) * 100
        
        print(f"Channel Compliance: {channel_compliance:.0f}%")
        print(f"Line Limit Compliance: {line_compliance:.0f}%")
        print(f"No Violations: {no_violations:.0f}%")
    else:
        print("No successful tests to analyze")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(f"prompt_test_results_{timestamp}.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    # Clean up
    print("\nCleaning up test files...")
    for test_file in test_files:
        test_file.unlink()
        output_file = test_file.with_suffix('.output.txt')
        if output_file.exists():
            output_file.unlink()
    Path("test_conversations").rmdir()


if __name__ == "__main__":
    asyncio.run(main())