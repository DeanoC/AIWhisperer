#!/usr/bin/env python3
"""Fix final flake8 indentation issues."""

import os

# Define the specific fixes needed based on flake8 output
fixes = [
    {
        'file': 'tests/unit/test_ast_to_json_conversion.py',
        'line': 250,
        'context': 'test_convert_binary_operations'
    },
    {
        'file': 'tests/unit/test_ast_to_json_special_cases.py',
        'line': 54,
        'context': 'test_convert_pass_statement'
    },
    {
        'file': 'tests/unit/test_metadata_preservation.py',
        'line': 49,
        'context': 'assert statements in test_module_docstring_preservation'
    },
    {
        'file': 'tests/unit/test_python_ast_parsing.py',
        'line': 109,
        'context': 'test_parse_import_statements'
    },
    {
        'file': 'tests/unit/test_python_ast_parsing_advanced.py',
        'line': 105,
        'context': 'test_parse_decorator_syntax'
    }
]

def fix_file(filepath, line_num, context):
    """Fix a specific file's indentation issues."""
    print(f"Fixing {filepath} line {line_num} ({context})...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Fix based on context
    if 'test_convert_binary_operations' in context:
        # This is in a method, needs to be indented 8 spaces (class method body)
        for i in range(248, 252):  # Lines around 250
            if i < len(lines) and lines[i].strip():
                lines[i] = '        ' + lines[i].lstrip()
    
    elif 'test_convert_pass_statement' in context:
        # This is also in a method, needs 8 spaces
        for i in range(52, 56):  # Lines around 54
            if i < len(lines) and lines[i].strip():
                lines[i] = '        ' + lines[i].lstrip()
    
    elif 'assert statements' in context:
        # The assert statements need consistent indentation within the for loop
        # Looking at line 48, it seems to be inside a for loop with 8 space indentation
        # The assert statements should be at 12 spaces (inside the for loop body)
        for i in range(48, 52):  # Lines 49-51
            if i < len(lines) and lines[i].strip().startswith('assert'):
                lines[i] = '            ' + lines[i].lstrip()
    
    elif 'test_parse_import_statements' in context:
        # Method body needs 8 spaces
        for i in range(107, 115):  # Lines around 109
            if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('def'):
                lines[i] = '        ' + lines[i].lstrip()
    
    elif 'test_parse_decorator_syntax' in context:
        # Method body needs 8 spaces
        for i in range(103, 110):  # Lines around 105
            if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('def'):
                lines[i] = '        ' + lines[i].lstrip()
    
    with open(filepath, 'w') as f:
        f.writelines(lines)

# Process all fixes
for fix in fixes:
    if os.path.exists(fix['file']):
        fix_file(fix['file'], fix['line'], fix['context'])
    else:
        print(f"Warning: {fix['file']} not found")

print("\nAll flake8 issues should be fixed!")