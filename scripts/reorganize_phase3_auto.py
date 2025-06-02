#!/usr/bin/env python3
"""
Phase 3: Interface Layer module reorganization (non-interactive version)
This phase focuses on CLI and interface modules.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List

# Phase 3 file movements - interface layer
PHASE3_MOVEMENTS = {
    # CLI Interface modules
    "ai_whisperer/cli.py": "ai_whisperer/interfaces/cli/main.py",
    "ai_whisperer/cli_commands.py": "ai_whisperer/interfaces/cli/commands.py",
    "ai_whisperer/cli_commands_batch_mode.py": "ai_whisperer/interfaces/cli/batch.py",
    
    # Move command modules to CLI subdirectory
    "ai_whisperer/commands/agent.py": "ai_whisperer/interfaces/cli/commands/agent.py",
    "ai_whisperer/commands/args.py": "ai_whisperer/interfaces/cli/commands/args.py",
    "ai_whisperer/commands/base.py": "ai_whisperer/interfaces/cli/commands/base.py",
    "ai_whisperer/commands/debbie.py": "ai_whisperer/interfaces/cli/commands/debbie.py",
    "ai_whisperer/commands/echo.py": "ai_whisperer/interfaces/cli/commands/echo.py",
    "ai_whisperer/commands/errors.py": "ai_whisperer/interfaces/cli/commands/errors.py",
    "ai_whisperer/commands/help.py": "ai_whisperer/interfaces/cli/commands/help.py",
    "ai_whisperer/commands/registry.py": "ai_whisperer/interfaces/cli/commands/registry.py",
    "ai_whisperer/commands/session.py": "ai_whisperer/interfaces/cli/commands/session.py",
    "ai_whisperer/commands/status.py": "ai_whisperer/interfaces/cli/commands/status.py",
    "ai_whisperer/commands/test_commands.py": "ai_whisperer/interfaces/cli/commands/test_commands.py",
}

# Import mappings for Phase 3
PHASE3_IMPORTS = {
    # CLI imports
    "ai_whisperer.cli": "ai_whisperer.interfaces.cli.main",
    "ai_whisperer.cli_commands": "ai_whisperer.interfaces.cli.commands",
    "ai_whisperer.cli_commands_batch_mode": "ai_whisperer.interfaces.cli.batch",
    
    # Command imports
    "ai_whisperer.commands.agent": "ai_whisperer.interfaces.cli.commands.agent",
    "ai_whisperer.commands.args": "ai_whisperer.interfaces.cli.commands.args",
    "ai_whisperer.commands.base": "ai_whisperer.interfaces.cli.commands.base",
    "ai_whisperer.commands.debbie": "ai_whisperer.interfaces.cli.commands.debbie",
    "ai_whisperer.commands.echo": "ai_whisperer.interfaces.cli.commands.echo",
    "ai_whisperer.commands.errors": "ai_whisperer.interfaces.cli.commands.errors",
    "ai_whisperer.commands.help": "ai_whisperer.interfaces.cli.commands.help",
    "ai_whisperer.commands.registry": "ai_whisperer.interfaces.cli.commands.registry",
    "ai_whisperer.commands.session": "ai_whisperer.interfaces.cli.commands.session",
    "ai_whisperer.commands.status": "ai_whisperer.interfaces.cli.commands.status",
    "ai_whisperer.commands.test_commands": "ai_whisperer.interfaces.cli.commands.test_commands",
}

# Relative import fixes specific to Phase 3
RELATIVE_IMPORT_FIXES = {
    # CLI relative imports
    r"from \.cli_commands_batch_mode": "from ai_whisperer.interfaces.cli.batch",
    r"from \.cli_commands": "from ai_whisperer.interfaces.cli.commands",
    r"from \.cli": "from ai_whisperer.interfaces.cli.main",
    
    # Commands relative imports
    r"from \.base": "from ai_whisperer.interfaces.cli.commands.base",
    r"from \.args": "from ai_whisperer.interfaces.cli.commands.args",
    r"from \.errors": "from ai_whisperer.interfaces.cli.commands.errors",
    r"from \.registry": "from ai_whisperer.interfaces.cli.commands.registry",
    
    # Fix imports within commands directory
    r"from ai_whisperer\.commands": "from ai_whisperer.interfaces.cli.commands",
}


def create_directories():
    """Create the new directory structure for Phase 3."""
    dirs = [
        "ai_whisperer/interfaces",
        "ai_whisperer/interfaces/cli",
        "ai_whisperer/interfaces/cli/commands",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files with proper module docstrings
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            module_name = dir_path.replace('/', '.')
            if 'interfaces/cli/commands' in dir_path:
                content = f'''"""
{module_name} - CLI command implementations

This package contains specific command implementations:
- agent: Agent management commands
- session: Session management commands
- status: Status and info commands
- help: Help system
- debbie: Debbie debugger commands
"""
'''
            elif 'interfaces/cli' in dir_path and dir_path.endswith('cli'):
                content = f'''"""
{module_name} - Command Line Interface

This package contains the CLI implementation:
- main: Main CLI entry point
- commands: Base command infrastructure
- batch: Batch mode processing
- commands/: Specific command implementations
"""
'''
            elif 'interfaces' in dir_path and dir_path.endswith('interfaces'):
                content = f'''"""
{module_name} - User interfaces

This package contains all user interface implementations:
- cli: Command line interface
- (future: api, web, etc.)
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


def update_imports_in_file(file_path: Path, import_mappings: Dict[str, str], relative_fixes: Dict[str, str] = None) -> bool:
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
        
        # Fix relative imports if provided
        if relative_fixes:
            for pattern, replacement in relative_fixes.items():
                content = re.sub(pattern, replacement, content)
        
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
        if update_imports_in_file(file_path, PHASE3_IMPORTS, RELATIVE_IMPORT_FIXES):
            updated_files.append(file_path)
    
    print(f"Updated imports in {len(updated_files)} files")
    
    # Show a sample of updated files
    if updated_files:
        print("\nSample of updated files:")
        for file_path in updated_files[:5]:
            print(f"  - {file_path}")
        if len(updated_files) > 5:
            print(f"  ... and {len(updated_files) - 5} more")


def update_main_entry_point():
    """Update __main__.py to use new CLI location."""
    main_file = Path("ai_whisperer/__main__.py")
    if main_file.exists():
        try:
            content = main_file.read_text()
            original_content = content
            
            # Update import
            content = re.sub(
                r"from \.cli import cli",
                "from ai_whisperer.interfaces.cli.main import cli",
                content
            )
            content = re.sub(
                r"from ai_whisperer\.cli import cli",
                "from ai_whisperer.interfaces.cli.main import cli",
                content
            )
            
            if content != original_content:
                main_file.write_text(content)
                print("✓ Updated __main__.py entry point")
                return True
        except Exception as e:
            print(f"✗ Error updating __main__.py: {e}")
    return False


def cleanup_empty_directories():
    """Remove empty directories left after moving files."""
    commands_dir = Path("ai_whisperer/commands")
    if commands_dir.exists() and not any(commands_dir.iterdir()):
        try:
            commands_dir.rmdir()
            print(f"✓ Removed empty directory: {commands_dir}")
        except Exception as e:
            print(f"✗ Could not remove {commands_dir}: {e}")


def verify_tests():
    """Run a subset of tests to verify the changes."""
    print("\nRunning tests to verify changes...")
    
    # Run unit tests for affected modules
    test_commands = [
        ["python", "-m", "pytest", "tests/unit/commands/", "-v", "-x"],
        ["python", "-m", "pytest", "tests/unit/test_cli.py", "-v"],
        ["python", "-m", "pytest", "-k", "test_batch", "-v", "--maxfail=3"],
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
    print("AIWhisperer Module Reorganization - Phase 3 (Auto)")
    print("=" * 50)
    print("This phase reorganizes interface layer modules")
    print("")
    
    # Check if we're in the right directory
    if not Path("ai_whisperer").exists():
        print("Error: Must run from project root directory")
        return 1
    
    # Show what will be done
    print("This script will:")
    print("1. Move 14 CLI/interface files to better locations")
    print("2. Update imports throughout the codebase")
    print("3. Update the main entry point")
    print("4. Clean up empty directories")
    print("5. Run tests to verify changes")
    print("")
    print("Auto-confirming execution (non-interactive mode)")
    
    # Create new directory structure
    print("\n1. Creating new directory structure...")
    create_directories()
    
    # Move files
    print("\n2. Moving files to new locations...")
    success_count = 0
    for old_path, new_path in PHASE3_MOVEMENTS.items():
        if Path(old_path).exists():
            if move_file_with_git(old_path, new_path):
                success_count += 1
        else:
            print(f"  Skipping {old_path} (not found)")
    
    print(f"\nMoved {success_count}/{len(PHASE3_MOVEMENTS)} files")
    
    if success_count == 0:
        print("No files were moved. Exiting.")
        return 1
    
    # Update imports
    print("\n3. Updating imports...")
    update_all_imports()
    
    # Update main entry point
    print("\n4. Updating main entry point...")
    update_main_entry_point()
    
    # Clean up empty directories
    print("\n5. Cleaning up empty directories...")
    cleanup_empty_directories()
    
    # Run tests
    print("\n6. Verifying changes...")
    tests_passed = verify_tests()
    
    print("\n" + "=" * 50)
    print("PHASE 3 COMPLETE")
    print("=" * 50)
    
    if tests_passed:
        print("\n✓ All verification tests passed!")
        print("\nNext steps:")
        print("1. Run full test suite: python -m pytest")
        print("2. Review changes: git status")
        print("3. Commit changes: git add -A && git commit -m 'refactor: Phase 3 interface layer reorganization'")
        print("4. Update any documentation that references old paths")
    else:
        print("\n⚠ Some tests failed. Please review and fix issues before committing.")
        print("This is expected - imports in test files may need updating.")
    
    return 0


if __name__ == "__main__":
    exit(main())