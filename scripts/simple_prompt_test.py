#!/usr/bin/env python3
"""
Simple direct test of the revised prompts.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.prompt_system import PromptSystem
from ai_whisperer.core.config import load_config
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.utils.path import PathManager


def test_prompt_loading():
    """Test that revised prompts load correctly."""
    print("Testing prompt loading...")
    
    # Load config
    config = load_config("config/main.yaml")
    
    # Initialize components
    prompt_system = PromptSystem(PROJECT_ROOT / "prompts")
    agent_registry = AgentRegistry(PROJECT_ROOT / "prompts")
    
    # Test each agent
    agents_to_test = ["A", "P", "D", "T", "E"]
    
    for agent_id in agents_to_test:
        print(f"\nTesting Agent {agent_id}:")
        
        # Get agent config
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            print(f"  ✗ No agent found")
            continue
        
        # Load prompt
        prompt = prompt_system.get_agent_prompt(agent_id)
        if not prompt:
            print(f"  ✗ No prompt found")
            continue
        
        # Check for key improvements
        checks = {
            "Has core.md reference": "Follow ALL instructions in core.md" in prompt,
            "Has channel rules": "[ANALYSIS]" in prompt and "[COMMENTARY]" in prompt and "[FINAL]" in prompt,
            "Has 4-line limit": "Maximum 4 lines" in prompt or "Max 4 lines" in prompt,
            "Has forbidden behaviors": "❌" in prompt or "FORBIDDEN" in prompt or "forbidden" in prompt,
        }
        
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}")
        
        # Show prompt length
        print(f"  📏 Prompt length: {len(prompt)} chars, {len(prompt.split())} words")


def test_channel_extraction():
    """Test channel extraction from sample responses."""
    print("\n\nTesting channel extraction...")
    
    sample_response = """[ANALYSIS]
User wants to list files. I'll use list_directory tool.

[COMMENTARY]
list_directory(path=".")
Found 5 files: main.py, config.json, README.md, test.py, utils.py

[FINAL]
Found 5 files in your workspace:
main.py, config.json, README.md, test.py, utils.py"""
    
    # Extract channels
    import re
    
    channels = {}
    channel_pattern = r'\[(\w+)\]\s*(.*?)(?=\[|$)'
    matches = re.findall(channel_pattern, sample_response, re.DOTALL)
    
    for channel, content in matches:
        channels[channel] = content.strip()
    
    print("\nExtracted channels:")
    for channel, content in channels.items():
        lines = len([l for l in content.split('\n') if l.strip()])
        print(f"  [{channel}]: {lines} lines")
    
    # Check compliance
    print("\nCompliance check:")
    print(f"  ✓ Has all channels: {all(ch in channels for ch in ['ANALYSIS', 'COMMENTARY', 'FINAL'])}")
    final_lines = len([l for l in channels.get('FINAL', '').split('\n') if l.strip()])
    print(f"  ✓ FINAL ≤ 4 lines: {final_lines <= 4} ({final_lines} lines)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("PROMPT REVISION VERIFICATION")
    print("=" * 60)
    
    test_prompt_loading()
    test_channel_extraction()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Run interactive session to test real agent behavior")
    print("2. Use conversation replay for systematic testing")
    print("3. Monitor channel compliance and response length")
    print("=" * 60)


if __name__ == "__main__":
    main()