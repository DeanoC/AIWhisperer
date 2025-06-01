#!/usr/bin/env python3
"""Fix method body indentations in test files."""

import re

files_to_fix = [
    'tests/unit/test_ast_to_json_conversion.py',
    'tests/unit/test_ast_to_json_special_cases.py',
    'tests/unit/test_metadata_preservation.py'
]

def fix_method_bodies(filepath):
    """Fix indentation of method bodies that are not properly indented."""
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix pattern: method definition followed by unindented docstring/code
    # Look for def ... :\n followed by content at wrong indentation
    pattern = r'(\n    def \w+\(.*?\):\n)(    )(""".*?"""|\'\'\'.*?\'\'\'|[^\n]+)'
    
    def fix_indent(match):
        prefix = match.group(1)
        current_indent = match.group(2)
        content = match.group(3)
        # Add 4 more spaces to the content
        return prefix + '        ' + content
    
    # Fix docstrings and first lines after method definitions
    content = re.sub(pattern, fix_indent, content, flags=re.DOTALL)
    
    # Also fix lines that follow - if a line after def has content at column 4, move to column 8
    lines = content.split('\n')
    fixed_lines = []
    in_method = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def ') and line.strip().endswith(':'):
            in_method = True
            fixed_lines.append(line)
        elif in_method and line and not line[0].isspace() and not line.startswith('class'):
            # Hit a non-indented line, we're out of the method
            in_method = False
            fixed_lines.append(line)
        elif in_method and line.startswith('    ') and not line.startswith('        '):
            # This line needs more indentation
            if line.strip():  # Don't change empty lines
                fixed_lines.append('    ' + line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
            if line.strip() == '' and in_method:
                # Empty line might end the method context
                pass
    
    content = '\n'.join(fixed_lines)
    
    with open(filepath, 'w') as f:
        f.write(content)

for filepath in files_to_fix:
    fix_method_bodies(filepath)

print("All method indentations fixed!")