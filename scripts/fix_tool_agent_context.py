#!/usr/bin/env python3
"""Fix tools to accept agent context parameters via **kwargs"""

import os
import re
from pathlib import Path

def fix_tool_execute_method(file_path):
    """Fix a tool file to accept **kwargs in execute method"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match execute method with Dict[str, Any] argument
    pattern = r'def execute\(self, arguments: Dict\[str, Any\]\) -> str:'
    
    if not re.search(pattern, content):
        print(f"  ✓ {file_path.name} - Already fixed or different signature")
        return False
    
    # Replace the method signature
    new_signature = 'def execute(self, arguments: Dict[str, Any] = None, **kwargs) -> str:'
    content = re.sub(pattern, new_signature, content)
    
    # Find the execute method and add agent context handling at the beginning
    # This is a bit complex but we need to insert after the docstring
    lines = content.split('\n')
    new_lines = []
    in_execute = False
    docstring_ended = False
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Check if we're starting the execute method
        if 'def execute(self, arguments:' in line and '**kwargs' in line:
            in_execute = True
            docstring_ended = False
            continue
            
        # If we're in execute method
        if in_execute and not inserted:
            # Skip empty lines at the start
            if line.strip() == '':
                continue
                
            # Skip docstring
            if '"""' in line:
                if line.count('"""') == 2:  # Single line docstring
                    docstring_ended = True
                elif docstring_ended:  # End of multi-line docstring
                    docstring_ended = True
                else:  # Start of multi-line docstring
                    docstring_ended = False
                continue
                
            # If we've passed the docstring and this is code, insert our handling
            if docstring_ended and line.strip() and not line.strip().startswith('"""'):
                # Get the indentation of the current line
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                
                # Insert agent context handling
                context_handling = [
                    f'{indent_str}# Handle both arguments dict and kwargs patterns',
                    f'{indent_str}if arguments is None:',
                    f'{indent_str}    arguments = {{}}',
                    f'{indent_str}',
                    f'{indent_str}# Merge kwargs into arguments, excluding agent context params',
                    f'{indent_str}for key, value in kwargs.items():',
                    f'{indent_str}    if not key.startswith("_"):  # Skip agent context params',
                    f'{indent_str}        arguments[key] = value',
                    f'{indent_str}',
                ]
                
                # Insert before the current line
                new_lines = new_lines[:-1]  # Remove the line we just added
                new_lines.extend(context_handling)
                new_lines.append(line)  # Add the line back
                
                inserted = True
                in_execute = False
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print(f"  ✓ Fixed {file_path.name}")
    return True

def main():
    tools_dir = Path("/home/deano/projects/AIWhisperer/ai_whisperer/tools")
    
    # List of tools that need fixing based on the search
    tools_to_fix = [
        "analyze_dependencies_tool.py",
        "analyze_languages_tool.py",
        "create_plan_from_rfc_tool.py",
        "create_rfc_tool.py",
        "decompose_plan_tool.py",
        "delete_plan_tool.py",
        "delete_rfc_tool.py",
        "fetch_url_tool.py",
        "find_similar_code_tool.py",
        "format_for_external_agent_tool.py",
        "get_file_content_tool.py",
        "get_project_structure_tool.py",
        "list_directory_tool.py",
        "list_plans_tool.py",
        "list_rfcs_tool.py",
        "message_injector_tool.py",
        "move_plan_tool.py",
        "move_rfc_tool.py",
        "parse_external_result_tool.py",
        "prepare_plan_from_rfc_tool.py",
        "python_executor_tool.py",
        "read_file_tool.py",
        "read_plan_tool.py",
        "read_rfc_tool.py",
        "recommend_external_agent_tool.py",
        "save_generated_plan_tool.py",
        "search_files_tool.py",
        "session_health_tool.py",
        "session_inspector_tool.py",
        "update_plan_from_rfc_tool.py",
        "update_rfc_tool.py",
        "update_task_status_tool.py",
        "validate_external_agent_tool.py",
        "web_search_tool.py",
        "workspace_validator_tool.py",
    ]
    
    print(f"Fixing {len(tools_to_fix)} tool files...")
    print()
    
    fixed_count = 0
    for tool_file in tools_to_fix:
        file_path = tools_dir / tool_file
        if file_path.exists():
            if fix_tool_execute_method(file_path):
                fixed_count += 1
        else:
            print(f"  ✗ {tool_file} - File not found")
    
    print()
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()