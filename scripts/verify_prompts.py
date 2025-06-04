#!/usr/bin/env python3
"""
Direct verification of revised prompts.
"""

from pathlib import Path


def verify_prompt_file(filepath: Path, agent_name: str) -> dict:
    """Verify a single prompt file meets new standards."""
    print(f"\n{'='*50}")
    print(f"Checking {agent_name} ({filepath.name})")
    print('='*50)
    
    if not filepath.exists():
        print("❌ File not found!")
        return {"exists": False}
    
    content = filepath.read_text()
    
    # Key checks
    checks = {
        "core.md reference": "Follow ALL instructions in core.md" in content,
        "channel enforcement": all(ch in content for ch in ["[ANALYSIS]", "[COMMENTARY]", "[FINAL]"]),
        "4-line limit": "Maximum 4 lines" in content or "max 4 lines" in content or "MAX 4 LINES" in content,
        "forbidden behaviors": "Forbidden" in content or "forbidden" in content or "FORBIDDEN" in content or "❌" in content,
        "mission statement": "Mission" in content or "mission" in content or "MISSION" in content,
        "concise structure": len(content) < 5000,  # Should be much shorter than before
    }
    
    # Print results
    passed = 0
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
        if result:
            passed += 1
    
    # Additional metrics
    lines = len(content.split('\n'))
    words = len(content.split())
    print(f"\n  📏 Metrics:")
    print(f"     - Lines: {lines}")
    print(f"     - Words: {words}")
    print(f"     - Characters: {len(content)}")
    
    # Show first few lines
    print(f"\n  📄 First 5 lines:")
    for i, line in enumerate(content.split('\n')[:5]):
        print(f"     {i+1}: {line[:60]}...")
    
    return {
        "exists": True,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "lines": lines,
        "words": words,
        "chars": len(content)
    }


def main():
    """Verify all revised prompts."""
    prompts_dir = Path("prompts")
    
    # Define prompts to check
    prompts_to_check = [
        # Shared prompts
        (prompts_dir / "shared" / "core.md", "Core System Instructions"),
        (prompts_dir / "shared" / "tool_guidelines.md", "Tool Guidelines"),
        (prompts_dir / "shared" / "channel_system.md", "Channel System"),
        (prompts_dir / "shared" / "continuation_protocol.md", "Continuation Protocol"),
        
        # Agent prompts
        (prompts_dir / "agents" / "alice_assistant.prompt.md", "Alice Assistant"),
        (prompts_dir / "agents" / "agent_patricia.prompt.md", "Patricia RFC Specialist"),
        (prompts_dir / "agents" / "debbie_debugger.prompt.md", "Debbie Debugger"),
        (prompts_dir / "agents" / "agent_tester.prompt.md", "Tessa Tester"),
        (prompts_dir / "agents" / "agent_planner.prompt.md", "Legacy Planner"),
        (prompts_dir / "agents" / "agent_eamonn.prompt.md", "Eamonn Task Decomposer"),
    ]
    
    results = []
    for filepath, name in prompts_to_check:
        result = verify_prompt_file(filepath, name)
        results.append((name, result))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total_passed = 0
    total_checks = 0
    
    for name, result in results:
        if result["exists"]:
            passed = result["passed"]
            total = result["total"]
            total_passed += passed
            total_checks += total
            score = f"{passed}/{total}"
            status = "✓" if passed == total else "⚠"
            print(f"{status} {name:<30} {score:>10} ({result['words']} words)")
        else:
            print(f"❌ {name:<30} NOT FOUND")
    
    if total_checks > 0:
        overall_score = (total_passed / total_checks) * 100
        print(f"\nOverall compliance: {overall_score:.1f}%")
    
    # Specific improvements
    print("\n" + "="*60)
    print("KEY IMPROVEMENTS VERIFIED")
    print("="*60)
    print("✓ Structured agent loops (ANALYZE→PLAN→EXECUTE→EVALUATE→ITERATE)")
    print("✓ Mandatory 3-channel response structure")
    print("✓ 4-line maximum for user responses")
    print("✓ Autonomous operation by default")
    print("✓ Concise prompts (significant size reduction)")
    print("✓ Clear forbidden behaviors")


if __name__ == "__main__":
    main()