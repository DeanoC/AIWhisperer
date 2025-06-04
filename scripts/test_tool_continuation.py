#!/usr/bin/env python3
"""
Test tool continuation behavior - specifically when Alice fetches GitHub repos.
This test verifies whether tool results are properly sent back to the AI.
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
import subprocess


def analyze_output(output: str) -> dict:
    """Analyze the conversation output to understand what happened."""
    lines = output.split('\n')
    
    analysis = {
        "total_lines": len(lines),
        "alice_responses": [],
        "tool_calls": [],
        "continuations": [],
        "errors": [],
        "github_content_shown": False
    }
    
    current_response = None
    in_alice_response = False
    
    for i, line in enumerate(lines):
        # Track Alice responses
        if "Alice the AI Assistant" in line:
            if current_response:
                analysis["alice_responses"].append(current_response)
            current_response = {
                "start_line": i,
                "content": [],
                "has_analysis": False,
                "has_commentary": False,
                "has_final": False,
                "mentions_repos": False
            }
            in_alice_response = True
        elif in_alice_response and line.strip() == "":
            in_alice_response = False
            if current_response:
                analysis["alice_responses"].append(current_response)
                current_response = None
        elif in_alice_response and current_response:
            current_response["content"].append(line)
            if "[ANALYSIS]" in line:
                current_response["has_analysis"] = True
            if "[COMMENTARY]" in line:
                current_response["has_commentary"] = True
            if "[FINAL]" in line:
                current_response["has_final"] = True
            if any(word in line.lower() for word in ["repository", "repositories", "repos", "AIWhisperer"]):
                current_response["mentions_repos"] = True
        
        # Track tool calls
        if "fetch_url" in line:
            analysis["tool_calls"].append({
                "line": i,
                "content": line
            })
        
        # Track continuations
        if "continuation" in line.lower() or "continue" in line.lower():
            analysis["continuations"].append({
                "line": i,
                "content": line
            })
        
        # Check if GitHub content was shown
        if "AIWhisperer" in line or "DeanoC" in line:
            analysis["github_content_shown"] = True
        
        # Track errors
        if "error" in line.lower() or "failed" in line.lower():
            analysis["errors"].append({
                "line": i,
                "content": line
            })
    
    # Add final response if exists
    if current_response:
        analysis["alice_responses"].append(current_response)
    
    return analysis


def print_analysis(analysis: dict):
    """Print the analysis in a readable format."""
    print("\n" + "="*60)
    print("CONVERSATION ANALYSIS")
    print("="*60)
    
    print(f"\nTotal Alice responses: {len(analysis['alice_responses'])}")
    print(f"Tool calls found: {len(analysis['tool_calls'])}")
    print(f"Continuation mentions: {len(analysis['continuations'])}")
    print(f"Errors found: {len(analysis['errors'])}")
    print(f"GitHub content shown: {analysis['github_content_shown']}")
    
    print("\n--- ALICE RESPONSES ---")
    for i, resp in enumerate(analysis['alice_responses']):
        print(f"\nResponse {i+1} (line {resp['start_line']}):")
        print(f"  Has channels: A={resp['has_analysis']}, C={resp['has_commentary']}, F={resp['has_final']}")
        print(f"  Mentions repos: {resp['mentions_repos']}")
        print(f"  Preview: {resp['content'][0][:100] if resp['content'] else 'empty'}...")
    
    print("\n--- TOOL CALLS ---")
    for tc in analysis['tool_calls']:
        print(f"  Line {tc['line']}: {tc['content'][:100]}...")
    
    print("\n--- KEY FINDING ---")
    # Check if Alice got the tool results
    last_response_mentions_repos = False
    if analysis['alice_responses']:
        last_resp = analysis['alice_responses'][-1]
        last_response_mentions_repos = last_resp['mentions_repos']
    
    if len(analysis['tool_calls']) > 0 and not analysis['github_content_shown']:
        print("❌ ISSUE CONFIRMED: fetch_url was called but GitHub content was never shown!")
        print("   Alice never received the tool results back.")
    elif analysis['github_content_shown']:
        print("✅ GitHub content was displayed")
    else:
        print("⚠️  No fetch_url call or GitHub content found")


async def run_test():
    """Run the conversation replay test."""
    print("Running conversation replay test...")
    
    # Run the conversation
    cmd = [
        sys.executable, "-m", "ai_whisperer.interfaces.cli.main",
        "--config", "config/main.yaml",
        "replay", "scripts/test_github_fetch.txt"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"test_results/github_fetch_test_{timestamp}.txt")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)
        
        print(f"\nOutput saved to: {output_file}")
        
        # Analyze the output
        analysis = analyze_output(result.stdout)
        
        # Save analysis
        analysis_file = Path(f"test_results/github_fetch_analysis_{timestamp}.json")
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"Analysis saved to: {analysis_file}")
        
        # Print analysis
        print_analysis(analysis)
        
        return analysis
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 60 seconds")
        return None
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return None


async def main():
    """Run the test and report results."""
    print("Testing tool continuation behavior...")
    print("Scenario: Alice fetches GitHub repos with fetch_url")
    
    analysis = await run_test()
    
    if analysis:
        # Determine if the issue is confirmed
        if len(analysis['tool_calls']) > 0 and not analysis['github_content_shown']:
            print("\n" + "="*60)
            print("ISSUE CONFIRMED")
            print("="*60)
            print("The tool was called but results were never shown to the user.")
            print("This confirms that tool results are not being sent back to the AI")
            print("after execution when continuation is not triggered.")
            return False
        else:
            print("\n" + "="*60)
            print("TEST PASSED")
            print("="*60)
            return True
    else:
        print("\nTest could not complete")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)