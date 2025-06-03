#!/usr/bin/env python3
"""Add **kwargs support to Agent E tools execute methods."""

import os
import re

# Tools to fix
agent_e_tools = [
    'analyze_dependencies_tool.py', 
    'format_for_external_agent_tool.py',
    'update_task_status_tool.py',
    'validate_external_agent_tool.py',
    'recommend_external_agent_tool.py',
    'parse_external_result_tool.py'
]

tools_dir = '/home/deano/projects/AIWhisperer/ai_whisperer/tools'

for tool_file in agent_e_tools:
    file_path = os.path.join(tools_dir, tool_file)
    if os.path.exists(file_path):
        print(f"Checking {tool_file}...")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Look for execute method without **kwargs
        pattern = r'def execute\(self, arguments: Dict\[str, Any\]\) -> str:'
        replacement = 'def execute(self, arguments: Dict[str, Any], **kwargs) -> str:'
        
        if re.search(pattern, content) and ', **kwargs)' not in content:
            content = re.sub(pattern, replacement, content)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  ✅ Added **kwargs to {tool_file}")
        else:
            print(f"  ℹ️  No changes needed in {tool_file} (already has **kwargs or not found)")
    else:
        print(f"  ❌ File not found: {tool_file}")

print("\nDone!")