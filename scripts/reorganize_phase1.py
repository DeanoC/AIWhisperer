#!/usr/bin/env python3
"""
Phase 1: Core and Utils module reorganization
This is a conservative first step in reorganizing the codebase.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List

# Phase 1 file movements - just core and utils
PHASE1_MOVEMENTS = {
    # Core modules
    "ai_whisperer/config.py": "ai_whisperer/core/config.py",
    "ai_whisperer/exceptions.py": "ai_whisperer/core/exceptions.py",
    "ai_whisperer/logging_custom.py": "ai_whisperer/core/logging.py",
    
    # Utils modules  
    "ai_whisperer/path_management.py": "ai_whisperer/utils/path.py",
    "ai_whisperer/workspace_detection.py": "ai_whisperer/utils/workspace.py",
    "ai_whisperer/json_validator.py": "ai_whisperer/utils/validation.py",
    "ai_whisperer/utils.py": "ai_whisperer/utils/helpers.py",
}

# Import mappings for Phase 1
PHASE1_IMPORTS = {
    "ai_whisperer.config": "ai_whisperer.core.config",
    "ai_whisperer.exceptions": "ai_whisperer.core.exceptions", 
    "ai_whisperer.logging_custom": "ai_whisperer.core.logging",
    "ai_whisperer.path_management": "ai_whisperer.utils.path",
    "ai_whisperer.workspace_detection": "ai_whisperer.utils.workspace",
    "ai_whisperer.json_validator": "ai_whisperer.utils.validation",
    "ai_whisperer.utils": "ai_whisperer.utils.helpers",
}


def create_directories():
    """Create the new directory structure for Phase 1."""
    dirs = [
        "ai_whisperer/core",
        "ai_whisperer/utils",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files with proper module docstrings
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            module_name = dir_path.replace('/', '.')
            if 'core' in dir_path:
                content = f'''"""
{module_name} - Core functionality for AIWhisperer

This package contains fundamental components:
- config: Configuration management
- exceptions: Exception hierarchy
- logging: Logging setup and utilities
"""
'''
            elif 'utils' in dir_path:
                content = f'''"""
{module_name} - Utility functions and helpers

This package contains utility modules:
- path: Path management utilities
- workspace: Workspace detection
- validation: JSON/YAML validation
- helpers: General helper functions
"""
'''
            else:
                content = f'"""{module_name}"""\n'
            
            init_file.write_text(content)
            print(f"Created {init_file}")


def move_file_with_git(old_path: str, new_path: str) -> bool:
    """Move a file using git mv to preserve history."""
    try:
        # Create parent directory if needed
        Path(new_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Use git mv to preserve history
        result = subprocess.run(
            ["git", "mv", old_path, new_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ Moved {old_path} → {new_path}")
            return True
        else:
            print(f"✗ Failed to move {old_path}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error moving {old_path}: {e}")
        return False


def update_imports_in_file(file_path: Path, import_mappings: Dict[str, str]) -> bool:
    """Update imports in a Python file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Update import statements
        for old_import, new_import in import_mappings.items():
            # Handle "from X import Y" statements
            content = re.sub(
                rf"from {re.escape(old_import)} import",
                f"from {new_import} import",
                content
            )
            # Handle "import X" statements
            content = re.sub(
                rf"^import {re.escape(old_import)}$",
                f"import {new_import}",
                content,
                flags=re.MULTILINE
            )
            # Handle "import X as Y" statements
            content = re.sub(
                rf"import {re.escape(old_import)} as",
                f"import {new_import} as",
                content
            )
        
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"  Error updating imports in {file_path}: {e}")
        return False


def update_all_imports():
    """Update imports in all Python files."""
    print("\nUpdating imports throughout codebase...")
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        if any(skip in root for skip in [".venv", "__pycache__", "node_modules", ".git", "refactor_backup"]):
            continue
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    # Update imports in each file
    updated_files = []
    for file_path in python_files:
        if update_imports_in_file(file_path, PHASE1_IMPORTS):
            updated_files.append(file_path)
    
    print(f"Updated imports in {len(updated_files)} files")
    
    # Show a sample of updated files
    if updated_files:
        print("\nSample of updated files:")
        for file_path in updated_files[:5]:
            print(f"  - {file_path}")
        if len(updated_files) > 5:
            print(f"  ... and {len(updated_files) - 5} more")


def verify_tests():
    """Run a subset of tests to verify the changes."""
    print("\nRunning tests to verify changes...")
    
    # Run unit tests for affected modules
    test_commands = [
        ["python", "-m", "pytest", "tests/unit/test_config.py", "-v"],
        ["python", "-m", "pytest", "tests/unit/test_utils.py", "-v"],
        ["python", "-m", "pytest", "tests/unit/test_workspace_detection.py", "-v"],
        ["python", "-m", "pytest", "-k", "test_exception", "-v"],
    ]
    
    all_passed = True
    for cmd in test_commands:
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"✓ {' '.join(cmd[4:])} passed")
        else:
            print(f"✗ {' '.join(cmd[4:])} failed")
            all_passed = False
    
    return all_passed


def main():
    """Main execution function."""
    print("AIWhisperer Module Reorganization - Phase 1")
    print("=" * 50)
    print("This phase reorganizes core and utils modules only")
    print("")
    
    # Check if we're in the right directory
    if not Path("ai_whisperer").exists():
        print("Error: Must run from project root directory")
        return 1
    
    # Show what will be done
    print("This script will:")
    print("1. Move 7 core/utils files to better locations")
    print("2. Update imports throughout the codebase")
    print("3. Run tests to verify changes")
    print("")
    
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Aborted")
        return 0
    
    # Create new directory structure
    print("\n1. Creating new directory structure...")
    create_directories()
    
    # Move files
    print("\n2. Moving files to new locations...")
    success_count = 0
    for old_path, new_path in PHASE1_MOVEMENTS.items():
        if Path(old_path).exists():
            if move_file_with_git(old_path, new_path):
                success_count += 1
        else:
            print(f"  Skipping {old_path} (not found)")
    
    print(f"\nMoved {success_count}/{len(PHASE1_MOVEMENTS)} files")
    
    if success_count == 0:
        print("No files were moved. Exiting.")
        return 1
    
    # Update imports
    print("\n3. Updating imports...")
    update_all_imports()
    
    # Run tests
    print("\n4. Verifying changes...")
    tests_passed = verify_tests()
    
    print("\n" + "=" * 50)
    print("PHASE 1 COMPLETE")
    print("=" * 50)
    
    if tests_passed:
        print("\n✓ All verification tests passed!")
        print("\nNext steps:")
        print("1. Run full test suite: python -m pytest")
        print("2. Review changes: git status")
        print("3. Commit changes: git add -A && git commit -m 'refactor: Phase 1 module reorganization'")
        print("4. Update any documentation that references old paths")
    else:
        print("\n⚠ Some tests failed. Please review and fix issues before committing.")
    
    return 0


if __name__ == "__main__":
    exit(main())