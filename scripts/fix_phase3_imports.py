#!/usr/bin/env python3
"""
Fix additional imports after Phase 3 reorganization.
"""

import os
import re
from pathlib import Path
from typing import Dict, List

# Additional import fixes for Phase 3
ADDITIONAL_FIXES = {
    # Fix internal imports within CLI module
    r"from \.\.cli_commands import": "from ai_whisperer.interfaces.cli.commands import",
    r"from ai_whisperer\.cli_commands import": "from ai_whisperer.interfaces.cli.commands import",
    
    # Fix any remaining command imports
    r"from ai_whisperer\.commands\.": "from ai_whisperer.interfaces.cli.commands.",
    
    # Fix __main__.py if needed
    r"from \.interfaces\.cli\.main import cli": "from ai_whisperer.interfaces.cli.main import cli",
}

# Files to specifically check and fix
SPECIFIC_FILES = [
    "ai_whisperer/__main__.py",
    "ai_whisperer/interfaces/cli/main.py",
    "ai_whisperer/interfaces/cli/commands.py",
    "ai_whisperer/interfaces/cli/batch.py",
    "ai_whisperer/interfaces/cli/commands/agent.py",
    "ai_whisperer/interfaces/cli/commands/help.py",
    "ai_whisperer/interfaces/cli/commands/session.py",
    "ai_whisperer/interfaces/cli/commands/status.py",
    "ai_whisperer/interfaces/cli/commands/debbie.py",
]


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a specific file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply fixes
        for pattern, replacement in ADDITIONAL_FIXES.items():
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
    print("Fixing additional imports after Phase 3 reorganization")
    print("=" * 50)
    
    # Fix specific files first
    print("\nFixing known files with import issues...")
    fixed_count = 0
    for file_path_str in SPECIFIC_FILES:
        file_path = Path(file_path_str)
        if file_path.exists():
            if fix_imports_in_file(file_path):
                fixed_count += 1
                print(f"Fixed imports in {file_path}")
    
    # Also scan all Python files for remaining issues
    print("\nScanning all Python files for remaining import issues...")
    python_files = []
    for root, dirs, files in os.walk("."):
        if any(skip in root for skip in [".venv", "__pycache__", "node_modules", ".git", "refactor_backup"]):
            continue
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
            print(f"Fixed imports in {file_path}")
    
    print(f"\nFixed imports in {fixed_count} files total")
    
    # Check __main__.py specifically
    print("\nChecking __main__.py...")
    main_file = Path("ai_whisperer/__main__.py")
    if main_file.exists():
        content = main_file.read_text()
        print(f"Current __main__.py imports:")
        for line in content.split('\n'):
            if 'import' in line and 'cli' in line:
                print(f"  {line.strip()}")


if __name__ == "__main__":
    main()