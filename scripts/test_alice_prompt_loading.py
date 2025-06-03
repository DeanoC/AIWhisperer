#!/usr/bin/env python3
"""
Test Alice's prompt loading to diagnose why she's not using her system prompt.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_whisperer.prompt_system import PromptSystem
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.utils.path import PathManager
from ai_whisperer.core.config import load_config

def test_alice_prompt():
    """Test loading Alice's prompt."""
    print("Testing Alice's Prompt Loading")
    print("=" * 50)
    
    # Initialize PathManager first
    config = load_config("config/main.yaml")
    
    # Initialize components
    tool_registry = ToolRegistry()
    prompt_system = PromptSystem(tool_registry)
    
    # Get prompts directory
    prompts_dir = project_root / "prompts" / "agents"
    agent_registry = AgentRegistry(str(prompts_dir))
    
    # Get Alice's info
    alice_info = agent_registry.get_agent("A")
    if not alice_info:
        print("ERROR: Alice not found in agent registry!")
        return
    
    print(f"Agent ID: A")
    print(f"Name: {alice_info.name}")
    print(f"Prompt file: {alice_info.prompt_file}")
    
    # Try to load prompt the same way the session manager does
    prompt_name = alice_info.prompt_file
    if prompt_name.endswith('.prompt.md'):
        prompt_name = prompt_name[:-10]  # Remove '.prompt.md'
    elif prompt_name.endswith('.md'):
        prompt_name = prompt_name[:-3]  # Remove '.md'
    
    print(f"\nTrying to load prompt: agents/{prompt_name}")
    
    try:
        # Enable continuation feature
        prompt_system.enable_feature('continuation_protocol')
        
        # Load prompt
        prompt = prompt_system.get_formatted_prompt("agents", prompt_name, include_tools=False)
        
        print(f"\nPrompt loaded successfully!")
        print(f"Length: {len(prompt)} characters")
        print(f"\nFirst 500 characters:")
        print("-" * 50)
        print(prompt[:500])
        print("-" * 50)
        
        # Check if it's the expected Alice prompt
        if "Alice the Assistant" in prompt:
            print("\n✓ Correct Alice prompt loaded!")
        else:
            print("\n✗ WARNING: This doesn't look like Alice's prompt!")
            
    except Exception as e:
        print(f"\nERROR loading prompt: {e}")
        import traceback
        traceback.print_exc()
    
    # Also try direct file read
    print("\n\nDirect file read test:")
    prompt_path = prompts_dir / alice_info.prompt_file
    if prompt_path.exists():
        with open(prompt_path, 'r') as f:
            content = f.read()
        print(f"✓ File exists and readable")
        print(f"Length: {len(content)} characters")
        print(f"First line: {content.split('\\n')[0]}")
    else:
        print(f"✗ File not found: {prompt_path}")

if __name__ == "__main__":
    test_alice_prompt()