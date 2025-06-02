#!/usr/bin/env python3
"""
Phase 2: Service Layer module reorganization (non-interactive version)
This phase focuses on AI service and execution modules.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List

# Phase 2 file movements - service layer
PHASE2_MOVEMENTS = {
    # AI Service modules
    "ai_whisperer/ai_service/ai_service.py": "ai_whisperer/services/ai/base.py",
    "ai_whisperer/ai_service/openrouter_ai_service.py": "ai_whisperer/services/ai/openrouter.py",
    "ai_whisperer/ai_service/tool_calling.py": "ai_whisperer/services/ai/tool_calling.py",
    
    # Execution Service modules
    "ai_whisperer/ai_loop/stateless_ai_loop.py": "ai_whisperer/services/execution/ai_loop.py",
    "ai_whisperer/ai_loop/ai_config.py": "ai_whisperer/services/execution/ai_config.py",
    "ai_whisperer/ai_loop/tool_call_accumulator.py": "ai_whisperer/services/execution/tool_call_accumulator.py",
    "ai_whisperer/context_management.py": "ai_whisperer/services/execution/context.py",
    "ai_whisperer/state_management.py": "ai_whisperer/services/execution/state.py",
    
    # Agent Service modules (core agent infrastructure)
    "ai_whisperer/agents/base_handler.py": "ai_whisperer/services/agents/base.py",
    "ai_whisperer/agents/factory.py": "ai_whisperer/services/agents/factory.py",
    "ai_whisperer/agents/registry.py": "ai_whisperer/services/agents/registry.py",
    "ai_whisperer/agents/config.py": "ai_whisperer/services/agents/config.py",
    "ai_whisperer/agents/stateless_agent.py": "ai_whisperer/services/agents/stateless.py",
    "ai_whisperer/agents/session_manager.py": "ai_whisperer/services/agents/session_manager.py",
    "ai_whisperer/agents/context_manager.py": "ai_whisperer/services/agents/context_manager.py",
}

# Import mappings for Phase 2
PHASE2_IMPORTS = {
    # AI Service imports
    "ai_whisperer.services.ai.ai_service": "ai_whisperer.services.ai.base",
    "ai_whisperer.services.ai.openrouter_ai_service": "ai_whisperer.services.ai.openrouter",
    "ai_whisperer.services.ai.tool_calling": "ai_whisperer.services.ai.tool_calling",
    
    # Execution Service imports
    "ai_whisperer.services.execution.stateless_ai_loop": "ai_whisperer.services.execution.ai_loop",
    "ai_whisperer.services.execution.ai_config": "ai_whisperer.services.execution.ai_config",
    "ai_whisperer.services.execution.tool_call_accumulator": "ai_whisperer.services.execution.tool_call_accumulator",
    "ai_whisperer.context_management": "ai_whisperer.services.execution.context",
    "ai_whisperer.state_management": "ai_whisperer.services.execution.state",
    
    # Agent Service imports
    "ai_whisperer.agents.base_handler": "ai_whisperer.services.agents.base",
    "ai_whisperer.agents.factory": "ai_whisperer.services.agents.factory",
    "ai_whisperer.agents.registry": "ai_whisperer.services.agents.registry",
    "ai_whisperer.agents.config": "ai_whisperer.services.agents.config",
    "ai_whisperer.agents.stateless_agent": "ai_whisperer.services.agents.stateless",
    "ai_whisperer.agents.session_manager": "ai_whisperer.services.agents.session_manager",
    "ai_whisperer.agents.context_manager": "ai_whisperer.services.agents.context_manager",
}

# Relative import fixes specific to Phase 2
RELATIVE_IMPORT_FIXES = {
    # AI Service relative imports
    r"from \.ai_service": "from ai_whisperer.services.ai.base",
    r"from \.\.ai_service\.ai_service": "from ai_whisperer.services.ai.base",
    r"from \.openrouter_ai_service": "from ai_whisperer.services.ai.openrouter",
    r"from \.\.ai_service\.openrouter_ai_service": "from ai_whisperer.services.ai.openrouter",
    
    # AI Loop relative imports
    r"from \.stateless_ai_loop": "from ai_whisperer.services.execution.ai_loop",
    r"from \.\.ai_loop\.stateless_ai_loop": "from ai_whisperer.services.execution.ai_loop",
    r"from \.ai_config": "from ai_whisperer.services.execution.ai_config",
    r"from \.\.ai_loop\.ai_config": "from ai_whisperer.services.execution.ai_config",
    
    # Context/State relative imports
    r"from \.context_management": "from ai_whisperer.services.execution.context",
    r"from \.\.context_management": "from ai_whisperer.services.execution.context",
    r"from \.state_management": "from ai_whisperer.services.execution.state",
    r"from \.\.state_management": "from ai_whisperer.services.execution.state",
    
    # Agent relative imports
    r"from \.base_handler": "from ai_whisperer.services.agents.base",
    r"from \.\.agents\.base_handler": "from ai_whisperer.services.agents.base",
    r"from \.factory": "from ai_whisperer.services.agents.factory",
    r"from \.registry": "from ai_whisperer.services.agents.registry",
    r"from \.stateless_agent": "from ai_whisperer.services.agents.stateless",
}


def create_directories():
    """Create the new directory structure for Phase 2."""
    dirs = [
        "ai_whisperer/services",
        "ai_whisperer/services/ai",
        "ai_whisperer/services/execution", 
        "ai_whisperer/services/agents",
        "ai_whisperer/services/agents/handlers",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files with proper module docstrings
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            module_name = dir_path.replace('/', '.')
            if 'services/ai' in dir_path and dir_path.endswith('ai'):
                content = f'''"""
{module_name} - AI service integration

This package contains AI service implementations:
- base: Base AI service interface
- openrouter: OpenRouter API integration
- tool_calling: Tool calling functionality
"""
'''
            elif 'services/execution' in dir_path:
                content = f'''"""
{module_name} - Execution engine services

This package contains the execution engine:
- ai_loop: Main AI execution loop
- ai_config: AI configuration management
- context: Context management
- state: State management
"""
'''
            elif 'services/agents' in dir_path and not dir_path.endswith('handlers'):
                content = f'''"""
{module_name} - Agent system services

This package contains the agent infrastructure:
- base: Base agent handler
- factory: Agent factory
- registry: Agent registry
- config: Agent configuration
- handlers: Specific agent implementations
"""
'''
            elif 'services' in dir_path and dir_path.endswith('services'):
                content = f'''"""
{module_name} - Business logic services

This package contains core services:
- ai: AI service integration
- execution: Execution engine
- agents: Agent system
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
        if update_imports_in_file(file_path, PHASE2_IMPORTS, RELATIVE_IMPORT_FIXES):
            updated_files.append(file_path)
    
    print(f"Updated imports in {len(updated_files)} files")
    
    # Show a sample of updated files
    if updated_files:
        print("\nSample of updated files:")
        for file_path in updated_files[:5]:
            print(f"  - {file_path}")
        if len(updated_files) > 5:
            print(f"  ... and {len(updated_files) - 5} more")


def cleanup_empty_directories():
    """Remove empty directories left after moving files."""
    empty_dirs = []
    
    # Check ai_service directory
    ai_service_dir = Path("ai_whisperer/ai_service")
    if ai_service_dir.exists() and not any(ai_service_dir.iterdir()):
        empty_dirs.append(ai_service_dir)
    
    # Check ai_loop directory
    ai_loop_dir = Path("ai_whisperer/ai_loop")
    if ai_loop_dir.exists() and not any(ai_loop_dir.iterdir()):
        empty_dirs.append(ai_loop_dir)
    
    # Remove empty directories
    for empty_dir in empty_dirs:
        try:
            empty_dir.rmdir()
            print(f"✓ Removed empty directory: {empty_dir}")
        except Exception as e:
            print(f"✗ Could not remove {empty_dir}: {e}")


def verify_tests():
    """Run a subset of tests to verify the changes."""
    print("\nRunning tests to verify changes...")
    
    # Run unit tests for affected modules
    test_commands = [
        ["python", "-m", "pytest", "tests/unit/ai_service/", "-v", "-x"],
        ["python", "-m", "pytest", "tests/unit/ai_loop/", "-v", "-x"],
        ["python", "-m", "pytest", "tests/unit/agents/test_base_handler.py", "-v"],
        ["python", "-m", "pytest", "tests/unit/test_state_management.py", "-v"],
        ["python", "-m", "pytest", "-k", "test_context", "-v", "--maxfail=3"],
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
    print("AIWhisperer Module Reorganization - Phase 2 (Auto)")
    print("=" * 50)
    print("This phase reorganizes service layer modules")
    print("")
    
    # Check if we're in the right directory
    if not Path("ai_whisperer").exists():
        print("Error: Must run from project root directory")
        return 1
    
    # Show what will be done
    print("This script will:")
    print("1. Move 15 service layer files to better locations")
    print("2. Update imports throughout the codebase")
    print("3. Clean up empty directories")
    print("4. Run tests to verify changes")
    print("")
    print("Auto-confirming execution (non-interactive mode)")
    
    # Create new directory structure
    print("\n1. Creating new directory structure...")
    create_directories()
    
    # Move files
    print("\n2. Moving files to new locations...")
    success_count = 0
    for old_path, new_path in PHASE2_MOVEMENTS.items():
        if Path(old_path).exists():
            if move_file_with_git(old_path, new_path):
                success_count += 1
        else:
            print(f"  Skipping {old_path} (not found)")
    
    print(f"\nMoved {success_count}/{len(PHASE2_MOVEMENTS)} files")
    
    if success_count == 0:
        print("No files were moved. Exiting.")
        return 1
    
    # Update imports
    print("\n3. Updating imports...")
    update_all_imports()
    
    # Clean up empty directories
    print("\n4. Cleaning up empty directories...")
    cleanup_empty_directories()
    
    # Run tests
    print("\n5. Verifying changes...")
    tests_passed = verify_tests()
    
    print("\n" + "=" * 50)
    print("PHASE 2 COMPLETE")
    print("=" * 50)
    
    if tests_passed:
        print("\n✓ All verification tests passed!")
        print("\nNext steps:")
        print("1. Run full test suite: python -m pytest")
        print("2. Review changes: git status")
        print("3. Commit changes: git add -A && git commit -m 'refactor: Phase 2 service layer reorganization'")
        print("4. Update any documentation that references old paths")
    else:
        print("\n⚠ Some tests failed. Please review and fix issues before committing.")
        print("This is expected - imports in test files may need updating.")
    
    return 0


if __name__ == "__main__":
    exit(main())