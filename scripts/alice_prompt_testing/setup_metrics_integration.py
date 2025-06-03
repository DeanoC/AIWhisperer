#!/usr/bin/env python3
"""
Setup script for integrating prompt metrics tool with the testing framework.

This script:
1. Ensures the prompt_metrics_tool is properly registered
2. Creates necessary directories for metrics storage
3. Provides utilities for metrics collection
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_metrics_integration():
    """Set up the prompt metrics tool integration."""
    
    # Create metrics directory
    metrics_dir = PROJECT_ROOT / "metrics"
    metrics_dir.mkdir(exist_ok=True)
    print(f"✓ Created metrics directory: {metrics_dir}")
    
    # Check if prompt_metrics_tool exists in correct location
    tool_path = PROJECT_ROOT / "ai_whisperer" / "tools" / "prompt_metrics_tool.py"
    if not tool_path.exists():
        print(f"✗ Error: prompt_metrics_tool.py not found at {tool_path}")
        return False
    else:
        print(f"✓ Found prompt_metrics_tool.py at {tool_path}")
    
    # Check tool registration
    tool_sets_path = PROJECT_ROOT / "ai_whisperer" / "tools" / "tool_sets.yaml"
    if tool_sets_path.exists():
        import yaml
        with open(tool_sets_path, 'r') as f:
            tool_sets = yaml.safe_load(f)
        
        # Check if prompt_metrics is in any tool set
        found = False
        for set_name, tools in tool_sets.items():
            if "prompt_metrics" in tools:
                found = True
                print(f"✓ prompt_metrics tool found in tool set: {set_name}")
                break
        
        if not found:
            print("⚠ Warning: prompt_metrics not found in any tool set")
            print("  You may need to add it to tool_sets.yaml for agents to use it")
    
    # Create initial metrics files
    prompt_metrics_file = metrics_dir / "prompt_metrics.json"
    tool_metrics_file = metrics_dir / "tool_metrics.json"
    
    for file_path, desc in [(prompt_metrics_file, "prompt metrics"), (tool_metrics_file, "tool metrics")]:
        if not file_path.exists():
            with open(file_path, 'w') as f:
                json.dump({}, f)
            print(f"✓ Created {desc} file: {file_path}")
        else:
            print(f"✓ {desc.capitalize()} file already exists: {file_path}")
    
    # Create a sample revised prompt for testing
    prompts_dir = PROJECT_ROOT / "prompts" / "agents"
    revised_prompt_path = prompts_dir / "alice_assistant_revised.prompt.md"
    
    if not revised_prompt_path.exists():
        print(f"\n⚠ Note: No revised prompt found at {revised_prompt_path}")
        print("  You'll need to create this file with your improved Alice prompt")
        print("  for A/B testing to work properly.")
        
        # Create a template
        template = """You are Alice the Assistant, a friendly and knowledgeable AI helper for the AIWhisperer system.

## Response Channels
ALWAYS structure your responses using these channels:

- **[ANALYSIS]** - Your reasoning process (hidden from user)
- **[COMMENTARY]** - Technical details and tool outputs  
- **[FINAL]** - Concise user-facing response

## Core Principles
1. **Be Concise** - Skip preambles. Get straight to the point.
2. **Be Autonomous** - Use tools immediately. Don't ask permission.
3. **Be Thorough** - Complete tasks fully before responding.

## Your Role
- Welcome users and explain AIWhisperer features
- Guide users to appropriate specialized agents
- Provide coding assistance and troubleshooting help
- Use tools proactively to answer questions

## Available Agents
When users need specialized help, switch immediately:
- **Patricia (p)**: RFC creation and planning
- **Tessa (t)**: Test generation and strategy
- **Debbie (d)**: Debugging and diagnostics
- **Eamonn (e)**: Task decomposition for external AI

## Task Execution
1. Analyze the request
2. Use relevant tools WITHOUT asking
3. Continue until task is COMPLETE
4. Report results concisely

Remember: Actions speak louder than explanations. DO rather than describe."""
        
        with open(revised_prompt_path, 'w') as f:
            f.write(template)
        print(f"\n✓ Created template revised prompt at: {revised_prompt_path}")
        print("  Please customize this prompt with your improvements!")
    else:
        print(f"\n✓ Revised prompt already exists at: {revised_prompt_path}")
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Customize the revised Alice prompt if needed")
    print("2. Run A/B tests: python run_ab_tests.py")
    print("3. Evaluate results: python evaluate_with_debbie.py <results_file>")
    
    return True


def check_tool_registration():
    """Check if prompt_metrics tool is properly registered."""
    try:
        from ai_whisperer.tools.tool_registry import ToolRegistry
        registry = ToolRegistry()
        
        # Try to get the tool
        if hasattr(registry, 'get_tool'):
            tool = registry.get_tool('prompt_metrics')
            if tool:
                print("✓ prompt_metrics tool is registered in ToolRegistry")
                return True
        
        print("✗ prompt_metrics tool not found in ToolRegistry")
        return False
        
    except Exception as e:
        print(f"✗ Error checking tool registration: {e}")
        return False


def add_to_tool_sets():
    """Add prompt_metrics to appropriate tool sets."""
    tool_sets_path = PROJECT_ROOT / "ai_whisperer" / "tools" / "tool_sets.yaml"
    
    if not tool_sets_path.exists():
        print(f"✗ tool_sets.yaml not found at {tool_sets_path}")
        return False
    
    import yaml
    
    with open(tool_sets_path, 'r') as f:
        tool_sets = yaml.safe_load(f)
    
    # Add to analysis and alice tool sets
    modified = False
    
    if "analysis" in tool_sets and "prompt_metrics" not in tool_sets["analysis"]:
        tool_sets["analysis"].append("prompt_metrics")
        modified = True
        print("✓ Added prompt_metrics to 'analysis' tool set")
    
    if "alice" in tool_sets and "prompt_metrics" not in tool_sets["alice"]:
        tool_sets["alice"].append("prompt_metrics") 
        modified = True
        print("✓ Added prompt_metrics to 'alice' tool set")
    
    if "debbie" in tool_sets and "prompt_metrics" not in tool_sets["debbie"]:
        tool_sets["debbie"].append("prompt_metrics")
        modified = True
        print("✓ Added prompt_metrics to 'debbie' tool set")
    
    if modified:
        # Create backup
        backup_path = tool_sets_path.with_suffix('.yaml.backup')
        import shutil
        shutil.copy(tool_sets_path, backup_path)
        print(f"✓ Created backup at {backup_path}")
        
        # Write updated tool sets
        with open(tool_sets_path, 'w') as f:
            yaml.dump(tool_sets, f, default_flow_style=False, sort_keys=False)
        print(f"✓ Updated {tool_sets_path}")
    else:
        print("✓ prompt_metrics already in all necessary tool sets")
    
    return True


if __name__ == "__main__":
    print("=== Setting up Prompt Metrics Integration ===\n")
    
    # Run setup
    if setup_metrics_integration():
        print("\n=== Checking Tool Registration ===")
        check_tool_registration()
        
        print("\n=== Updating Tool Sets ===")
        add_to_tool_sets()
        
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)