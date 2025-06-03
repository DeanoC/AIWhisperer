#!/usr/bin/env python3
"""Fix import paths in Agent E tools."""

import os
import re

# Tools to fix
agent_e_tools = [
    'decompose_plan_tool.py',
    'analyze_dependencies_tool.py', 
    'format_for_external_agent_tool.py',
    'update_task_status_tool.py',
    'validate_external_agent_tool.py',
    'recommend_external_agent_tool.py',
    'parse_external_result_tool.py'
]

tools_dir = '/home/deano/projects/AIWhisperer/ai_whisperer/tools'

# Import replacements
replacements = [
    (r'from \.\.agents\.', 'from ..extensions.agents.'),
    (r'from \.\.agents import', 'from ..extensions.agents import'),
]

for tool_file in agent_e_tools:
    file_path = os.path.join(tools_dir, tool_file)
    if os.path.exists(file_path):
        print(f"Fixing imports in {tool_file}...")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        if content != original:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  ✅ Fixed imports in {tool_file}")
        else:
            print(f"  ℹ️  No changes needed in {tool_file}")
    else:
        print(f"  ❌ File not found: {tool_file}")

print("\nDone!")