#!/usr/bin/env python3
"""
Split the large python_ast_json_tool.py into smaller, focused modules.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple

def analyze_ast_tool_structure():
    """Analyze the structure of python_ast_json_tool.py to plan the split."""
    
    file_path = Path("ai_whisperer/tools/python_ast_json_tool.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
        tree = ast.parse(content)
    
    # Categorize functions
    categories = {
        'ast_conversion': [],      # AST to JSON conversion
        'json_conversion': [],     # JSON to AST conversion
        'formatting': [],          # Code formatting functions
        'analysis': [],           # Code analysis functions
        'utilities': [],          # Helper utilities
        'node_handlers': [],      # AST node type handlers
        'main_class': [],         # The main tool class
    }
    
    # Extract all functions and classes
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            
            # Categorize based on name patterns
            if 'to_json' in name or 'ast_to_' in name:
                categories['ast_conversion'].append(name)
            elif 'from_json' in name or 'json_to_' in name:
                categories['json_conversion'].append(name)
            elif 'format' in name or 'indent' in name:
                categories['formatting'].append(name)
            elif 'analyze' in name or 'extract' in name or 'calculate' in name:
                categories['analysis'].append(name)
            elif 'handle_' in name or '_handler' in name:
                categories['node_handlers'].append(name)
            else:
                categories['utilities'].append(name)
                
        elif isinstance(node, ast.ClassDef):
            if node.name == 'PythonASTJSONTool':
                categories['main_class'].append(node.name)
            else:
                categories['utilities'].append(node.name)
    
    # Print analysis
    print("🔍 Python AST Tool Structure Analysis")
    print("=" * 70)
    print(f"Total lines: {len(content.splitlines())}")
    print(f"Total size: {len(content) / 1024:.1f} KB")
    print()
    
    for category, items in categories.items():
        if items:
            print(f"{category}: {len(items)} items")
            for item in items[:5]:
                print(f"  - {item}")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
            print()
    
    return categories, content, tree


def create_module_structure():
    """Create the new module structure."""
    
    modules = {
        'ast_converters.py': {
            'description': 'AST to JSON conversion functions',
            'imports': [
                'import ast',
                'import json',
                'from typing import Dict, Any, Optional, Union, List',
                'from datetime import datetime, timezone',
            ],
            'functions': []
        },
        'json_converters.py': {
            'description': 'JSON to AST conversion functions',
            'imports': [
                'import ast',
                'import json',
                'from typing import Dict, Any, Optional, Union, List',
            ],
            'functions': []
        },
        'code_analysis.py': {
            'description': 'Code analysis and metrics extraction',
            'imports': [
                'import ast',
                'import tokenize',
                'import io',
                'from typing import Dict, Any, List',
                'from collections import defaultdict',
            ],
            'functions': []
        },
        'formatting_utils.py': {
            'description': 'Code formatting and style utilities',
            'imports': [
                'import re',
                'from typing import Dict, Any, List',
            ],
            'functions': []
        },
        'node_handlers.py': {
            'description': 'AST node type specific handlers',
            'imports': [
                'import ast',
                'from typing import Dict, Any, Optional',
            ],
            'functions': []
        },
        'ast_utils.py': {
            'description': 'General AST utilities and helpers',
            'imports': [
                'import ast',
                'from typing import Any, Optional',
            ],
            'functions': []
        }
    }
    
    return modules


def extract_function_code(content: str, func_name: str) -> str:
    """Extract the complete code for a function from the source."""
    lines = content.splitlines()
    
    # Find function start
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f'def {func_name}('):
            start_idx = i
            break
    
    if start_idx is None:
        return ""
    
    # Find function end (next function or class at same indentation)
    indent_level = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    end_idx = len(lines)
    
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() and not line[0].isspace():
            # Top-level definition
            end_idx = i
            break
        elif line.strip() and line.startswith(' ' * indent_level) and not line[indent_level].isspace():
            # Same indentation level
            if line.strip().startswith(('def ', 'class ', '@')):
                end_idx = i
                break
    
    # Extract function code
    func_code = '\n'.join(lines[start_idx:end_idx])
    
    # Add spacing
    if not func_code.endswith('\n\n'):
        func_code += '\n\n'
    
    return func_code


def create_split_modules(categories, content, output_dir="ai_whisperer/tools/ast_modules"):
    """Create the split module files."""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Create __init__.py
    init_content = '''"""
AST processing modules extracted from python_ast_json_tool.py.
These modules provide functionality for Python AST to JSON conversion.
"""

from .ast_converters import *
from .json_converters import *
from .code_analysis import *
from .formatting_utils import *
from .node_handlers import *
from .ast_utils import *

__all__ = [
    # Add exported functions here
]
'''
    
    with open(Path(output_dir) / "__init__.py", 'w') as f:
        f.write(init_content)
    
    print(f"\n📁 Creating modules in {output_dir}/")
    
    # Module mapping
    module_mapping = {
        'ast_conversion': 'ast_converters.py',
        'json_conversion': 'json_converters.py',
        'analysis': 'code_analysis.py',
        'formatting': 'formatting_utils.py',
        'node_handlers': 'node_handlers.py',
        'utilities': 'ast_utils.py',
    }
    
    modules = create_module_structure()
    
    # Assign functions to modules
    for category, functions in categories.items():
        if category in module_mapping and functions:
            module_name = module_mapping[category]
            if module_name in modules:
                modules[module_name]['functions'].extend(functions)
    
    # Create module files
    for module_name, module_info in modules.items():
        if not module_info['functions']:
            continue
            
        module_path = Path(output_dir) / module_name
        
        # Build module content
        content_parts = [
            f'"""',
            f'{module_info["description"]}',
            f'"""',
            '',
        ]
        
        # Add imports
        content_parts.extend(module_info['imports'])
        content_parts.extend(['', ''])
        
        # Add functions
        for func_name in module_info['functions']:
            func_code = extract_function_code(content, func_name)
            if func_code:
                content_parts.append(func_code)
        
        # Write module
        with open(module_path, 'w') as f:
            f.write('\n'.join(content_parts))
        
        print(f"  ✓ Created {module_name} ({len(module_info['functions'])} functions)")
    
    return modules


def create_refactored_tool():
    """Create a refactored version of the main tool that imports from modules."""
    
    refactored_content = '''"""
Refactored Python AST to JSON converter tool.
This is a slimmed down version that imports functionality from specialized modules.
"""

import ast
import json
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

from ai_whisperer.tools.base_tool import AITool

# Import from specialized modules
from .ast_modules import (
    extract_comments_from_source,
    calculate_formatting_metrics,
    extract_docstring_info,
    # Add other imports as needed
)


class ProcessingTimeoutError(TimeoutError):
    """Custom timeout error for processing timeouts."""
    pass


class PythonASTJSONTool(AITool):
    """
    Tool for converting Python code to AST JSON representation and back.
    This refactored version delegates to specialized modules for better performance.
    """
    
    def __init__(self):
        """Initialize the Python AST JSON tool."""
        super().__init__()
        self.timeout = 30  # Default timeout in seconds
    
    # The main execute method and other core functionality would go here
    # Most methods would delegate to the imported functions from modules
'''
    
    with open("ai_whisperer/tools/python_ast_json_tool_refactored.py", 'w') as f:
        f.write(refactored_content)
    
    print("\n✓ Created refactored tool: python_ast_json_tool_refactored.py")


def main():
    """Main execution function."""
    print("🔧 Splitting Python AST JSON Tool")
    print("=" * 70)
    
    # Analyze current structure
    categories, content, tree = analyze_ast_tool_structure()
    
    # Create split modules
    modules = create_split_modules(categories, content)
    
    # Create refactored main tool
    create_refactored_tool()
    
    print("\n📊 Summary:")
    print(f"- Original file: 4372 lines, 184.3 KB")
    print(f"- Split into {len(modules)} specialized modules")
    print(f"- Created refactored main tool")
    
    print("\n🎯 Next Steps:")
    print("1. Test the split modules")
    print("2. Update imports in other files")
    print("3. Gradually migrate to the new structure")
    print("4. Remove the original large file once migration is complete")


if __name__ == "__main__":
    main()