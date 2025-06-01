#!/usr/bin/env python3
"""Fix remaining indentation errors in test files."""

import re

# Files and their specific issues
fixes = [
    {
        'file': 'tests/unit/test_ast_to_json_conversion.py',
        'line': 24,
        'fix': lambda lines: fix_method_indentation(lines, 24)
    },
    {
        'file': 'tests/unit/test_ast_to_json_special_cases.py', 
        'line': 26,
        'fix': lambda lines: fix_method_indentation(lines, 26)
    },
    {
        'file': 'tests/unit/test_metadata_preservation.py',
        'line': 50,
        'fix': lambda lines: fix_assert_indentation(lines, 48, 51)
    },
    {
        'file': 'tests/unit/test_python_ast_parsing.py',
        'line': 41,
        'fix': lambda lines: fix_method_indentation(lines, 41)
    },
    {
        'file': 'tests/unit/test_python_ast_parsing_advanced.py',
        'line': 105,
        'fix': lambda lines: fix_method_indentation(lines, 105)
    }
]

def fix_method_indentation(lines, line_num):
    """Fix indentation for method bodies."""
    # Line numbers are 1-based, array is 0-based
    idx = line_num - 1
    
    # Find the def line above
    for i in range(idx - 1, -1, -1):
        if lines[i].strip().startswith('def '):
            # Get the indentation of the def line
            def_indent = len(lines[i]) - len(lines[i].lstrip())
            # Method body should be indented 4 more spaces
            body_indent = def_indent + 4
            
            # Fix all lines that need fixing
            j = idx
            while j < len(lines) and lines[j].strip():
                if lines[j].strip():  # Don't modify empty lines
                    current_indent = len(lines[j]) - len(lines[j].lstrip())
                    # If this line has unexpected indent, fix it
                    if current_indent != body_indent and not lines[j].strip().startswith('#'):
                        lines[j] = ' ' * body_indent + lines[j].lstrip()
                j += 1
            break
    
    return lines

def fix_assert_indentation(lines, start_line, end_line):
    """Fix indentation for assert statements within a for loop."""
    # Find the for loop indentation
    for i in range(start_line - 1, -1, -1):
        if 'for ' in lines[i]:
            for_indent = len(lines[i]) - len(lines[i].lstrip())
            # Body of for loop should be indented 4 more
            body_indent = for_indent + 4
            
            # Fix the assert statements
            for j in range(start_line - 1, end_line):
                if lines[j].strip().startswith('assert'):
                    lines[j] = ' ' * body_indent + lines[j].lstrip()
            break
    
    return lines

# Process each file
for fix_info in fixes:
    print(f"Fixing {fix_info['file']} line {fix_info['line']}...")
    
    with open(fix_info['file'], 'r') as f:
        lines = f.readlines()
    
    lines = fix_info['fix'](lines)
    
    with open(fix_info['file'], 'w') as f:
        f.writelines(lines)

print("All remaining indentation issues fixed!")