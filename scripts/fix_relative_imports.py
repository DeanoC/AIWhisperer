#!/usr/bin/env python3
"""
Fix relative imports after module reorganization.
"""

import os
import re
from pathlib import Path
from typing import Dict, List

# Mapping of relative imports to absolute imports based on new structure
RELATIVE_IMPORT_FIXES = {
    # Core modules
    r"from \.exceptions": "from ai_whisperer.core.exceptions",
    r"from \.\.exceptions": "from ai_whisperer.core.exceptions",
    r"from \.config": "from ai_whisperer.core.config",
    r"from \.\.config": "from ai_whisperer.core.config",
    r"from \.logging_custom": "from ai_whisperer.core.logging",
    r"from \.\.logging_custom": "from ai_whisperer.core.logging",
    
    # Utils modules
    r"from \.path_management": "from ai_whisperer.utils.path",
    r"from \.\.path_management": "from ai_whisperer.utils.path",
    r"from \.workspace_detection": "from ai_whisperer.utils.workspace",
    r"from \.\.workspace_detection": "from ai_whisperer.utils.workspace",
    r"from \.json_validator": "from ai_whisperer.utils.validation",
    r"from \.\.json_validator": "from ai_whisperer.utils.validation",
    r"from \.utils": "from ai_whisperer.utils.helpers",
    r"from \.\.utils": "from ai_whisperer.utils.helpers",
}

# Also fix imports in __init__.py files
INIT_IMPORT_FIXES = {
    r"from \.workspace_detection": "from ai_whisperer.utils.workspace",
}


def fix_relative_imports_in_file(file_path: Path) -> bool:
    """Fix relative imports in a Python file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply fixes
        for pattern, replacement in RELATIVE_IMPORT_FIXES.items():
            content = re.sub(pattern, replacement, content)
        
        # Special handling for __init__.py files
        if file_path.name == "__init__.py":
            for pattern, replacement in INIT_IMPORT_FIXES.items():
                content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"  Error fixing imports in {file_path}: {e}")
        return False


def main():
    """Main execution function."""
    print("Fixing relative imports after module reorganization")
    print("=" * 50)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("ai_whisperer"):
        # Skip __pycache__
        if "__pycache__" in root:
            continue
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    # Fix imports in each file
    fixed_count = 0
    for file_path in python_files:
        if fix_relative_imports_in_file(file_path):
            fixed_count += 1
            print(f"Fixed imports in {file_path}")
    
    print(f"\nFixed relative imports in {fixed_count} files")
    
    # Also check test files
    print("\nChecking test files...")
    test_files = []
    for root, dirs, files in os.walk("tests"):
        if "__pycache__" in root:
            continue
        
        for file in files:
            if file.endswith(".py"):
                test_files.append(Path(root) / file)
    
    test_fixed = 0
    for file_path in test_files:
        if fix_relative_imports_in_file(file_path):
            test_fixed += 1
            print(f"Fixed imports in {file_path}")
    
    print(f"\nFixed relative imports in {test_fixed} test files")
    print(f"\nTotal files fixed: {fixed_count + test_fixed}")


if __name__ == "__main__":
    main()