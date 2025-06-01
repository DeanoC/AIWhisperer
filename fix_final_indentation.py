#!/usr/bin/env python3
"""Fix final indentation issues in test files."""

import re

def fix_ast_to_json_conversion():
    """Fix indentation in test_ast_to_json_conversion.py."""
    with open('tests/unit/test_ast_to_json_conversion.py', 'r') as f:
        content = f.read()
    
    # Fix the specific line 546 issue
    content = re.sub(
        r'"""(\n)        tree = ast\.parse\(code\)',
        r'"""\1    tree = ast.parse(code)',
        content
    )
    
    with open('tests/unit/test_ast_to_json_conversion.py', 'w') as f:
        f.write(content)

def fix_ast_to_json_special_cases():
    """Fix indentation in test_ast_to_json_special_cases.py."""
    with open('tests/unit/test_ast_to_json_special_cases.py', 'r') as f:
        content = f.read()
    
    # Fix the specific line 52 issue
    content = re.sub(
        r'"""(\n)        tree = ast\.parse\(code\)',
        r'"""\1    tree = ast.parse(code)',
        content
    )
    
    with open('tests/unit/test_ast_to_json_special_cases.py', 'w') as f:
        f.write(content)

def fix_json_to_ast_conversion():
    """Fix indentation in test_json_to_ast_conversion.py."""
    with open('tests/unit/test_json_to_ast_conversion.py', 'r') as f:
        content = f.read()
    
    # Fix line 480 - looks like incorrect indentation in a method
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if i == 479 and line.strip() == 'result = PythonASTJSONTool.json_to_ast("not a dict")':
            # Fix the indentation
            lines[i] = '        result = PythonASTJSONTool.json_to_ast("not a dict")'
    
    content = '\n'.join(lines)
    
    with open('tests/unit/test_json_to_ast_conversion.py', 'w') as f:
        f.write(content)

def fix_metadata_preservation():
    """Fix indentation in test_metadata_preservation.py."""
    with open('tests/unit/test_metadata_preservation.py', 'r') as f:
        lines = f.readlines()
    
    # Fix line 49 - unindent issue
    if len(lines) > 48:
        # Ensure proper indentation
        if lines[48].strip():
            lines[48] = '    ' + lines[48].lstrip()
    
    with open('tests/unit/test_metadata_preservation.py', 'w') as f:
        f.writelines(lines)

def fix_python_ast_json_design():
    """Fix indentation in test_python_ast_json_design.py."""
    with open('tests/unit/test_python_ast_json_design.py', 'r') as f:
        content = f.read()
    
    # Fix the tool.execute( indentation
    content = re.sub(
        r'(\n)                tool\.execute\(',
        r'\1        tool.execute(',
        content
    )
    
    with open('tests/unit/test_python_ast_json_design.py', 'w') as f:
        f.write(content)

def fix_python_ast_parsing():
    """Fix indentation in test_python_ast_parsing.py."""
    with open('tests/unit/test_python_ast_parsing.py', 'r') as f:
        content = f.read()
    
    # Fix the result = tool.execute( indentation
    content = re.sub(
        r'(\n)                result = tool\.execute\(',
        r'\1        result = tool.execute(',
        content
    )
    
    with open('tests/unit/test_python_ast_parsing.py', 'w') as f:
        f.write(content)

def fix_python_ast_parsing_advanced():
    """Fix indentation in test_python_ast_parsing_advanced.py."""
    with open('tests/unit/test_python_ast_parsing_advanced.py', 'r') as f:
        content = f.read()
    
    # Fix the result = tool.execute( indentation
    content = re.sub(
        r'(\n)                result = tool\.execute\(',
        r'\1        result = tool.execute(',
        content
    )
    
    with open('tests/unit/test_python_ast_parsing_advanced.py', 'w') as f:
        f.write(content)

def main():
    """Fix all indentation issues."""
    print("Fixing test_ast_to_json_conversion.py...")
    fix_ast_to_json_conversion()
    
    print("Fixing test_ast_to_json_special_cases.py...")
    fix_ast_to_json_special_cases()
    
    print("Fixing test_json_to_ast_conversion.py...")
    fix_json_to_ast_conversion()
    
    print("Fixing test_metadata_preservation.py...")
    fix_metadata_preservation()
    
    print("Fixing test_python_ast_json_design.py...")
    fix_python_ast_json_design()
    
    print("Fixing test_python_ast_parsing.py...")
    fix_python_ast_parsing()
    
    print("Fixing test_python_ast_parsing_advanced.py...")
    fix_python_ast_parsing_advanced()
    
    print("All indentation issues fixed!")

if __name__ == "__main__":
    main()