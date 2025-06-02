#!/usr/bin/env python3
"""
Phase 4: Extensions module reorganization (non-interactive version)
This phase focuses on optional features like batch mode, monitoring, and mailbox.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List

# Phase 4 file movements - extensions
PHASE4_MOVEMENTS = {
    # Batch mode extension
    "ai_whisperer/batch/batch_client.py": "ai_whisperer/extensions/batch/client.py",
    "ai_whisperer/batch/debbie_integration.py": "ai_whisperer/extensions/batch/debbie_integration.py",
    "ai_whisperer/batch/intervention.py": "ai_whisperer/extensions/batch/intervention.py",
    "ai_whisperer/batch/monitoring.py": "ai_whisperer/extensions/batch/monitoring.py",
    "ai_whisperer/batch/script_processor.py": "ai_whisperer/extensions/batch/script_processor.py",
    "ai_whisperer/batch/server_manager.py": "ai_whisperer/extensions/batch/server_manager.py",
    "ai_whisperer/batch/websocket_client.py": "ai_whisperer/extensions/batch/websocket_client.py",
    "ai_whisperer/batch/websocket_interceptor.py": "ai_whisperer/extensions/batch/websocket_interceptor.py",
    "ai_whisperer/batch/__init__.py": "ai_whisperer/extensions/batch/__init__.py",
    "ai_whisperer/batch/__main__.py": "ai_whisperer/extensions/batch/__main__.py",
    
    # Monitoring extension
    "ai_whisperer/logging/debbie_logger.py": "ai_whisperer/extensions/monitoring/debbie_logger.py",
    "ai_whisperer/logging/log_aggregator.py": "ai_whisperer/extensions/monitoring/log_aggregator.py",
    "ai_whisperer/logging/__init__.py": "ai_whisperer/extensions/monitoring/__init__.py",
    
    # Mailbox extension
    "ai_whisperer/agents/mailbox.py": "ai_whisperer/extensions/mailbox/mailbox.py",
    "ai_whisperer/agents/mailbox_tools.py": "ai_whisperer/extensions/mailbox/tools.py",
    "ai_whisperer/agents/mail_notification.py": "ai_whisperer/extensions/mailbox/notification.py",
    
    # Agent-specific extensions (move specialized agents)
    "ai_whisperer/agents/agent.py": "ai_whisperer/extensions/agents/agent.py",
    "ai_whisperer/agents/agent_communication.py": "ai_whisperer/extensions/agents/communication.py",
    "ai_whisperer/agents/continuation_strategy.py": "ai_whisperer/extensions/agents/continuation_strategy.py",
    "ai_whisperer/agents/debbie_tools.py": "ai_whisperer/extensions/agents/debbie_tools.py",
    "ai_whisperer/agents/decomposed_task.py": "ai_whisperer/extensions/agents/decomposed_task.py",
    "ai_whisperer/agents/task_decomposer.py": "ai_whisperer/extensions/agents/task_decomposer.py",
    "ai_whisperer/agents/prompt_optimizer.py": "ai_whisperer/extensions/agents/prompt_optimizer.py",
}

# Import mappings for Phase 4
PHASE4_IMPORTS = {
    # Batch imports
    "ai_whisperer.batch.batch_client": "ai_whisperer.extensions.batch.client",
    "ai_whisperer.batch.debbie_integration": "ai_whisperer.extensions.batch.debbie_integration",
    "ai_whisperer.batch.intervention": "ai_whisperer.extensions.batch.intervention",
    "ai_whisperer.batch.monitoring": "ai_whisperer.extensions.batch.monitoring",
    "ai_whisperer.batch.script_processor": "ai_whisperer.extensions.batch.script_processor",
    "ai_whisperer.batch.server_manager": "ai_whisperer.extensions.batch.server_manager",
    "ai_whisperer.batch.websocket_client": "ai_whisperer.extensions.batch.websocket_client",
    "ai_whisperer.batch.websocket_interceptor": "ai_whisperer.extensions.batch.websocket_interceptor",
    "ai_whisperer.batch": "ai_whisperer.extensions.batch",
    
    # Monitoring imports
    "ai_whisperer.logging.debbie_logger": "ai_whisperer.extensions.monitoring.debbie_logger",
    "ai_whisperer.logging.log_aggregator": "ai_whisperer.extensions.monitoring.log_aggregator",
    
    # Mailbox imports
    "ai_whisperer.agents.mailbox": "ai_whisperer.extensions.mailbox.mailbox",
    "ai_whisperer.agents.mailbox_tools": "ai_whisperer.extensions.mailbox.tools",
    "ai_whisperer.agents.mail_notification": "ai_whisperer.extensions.mailbox.notification",
    
    # Agent extension imports
    "ai_whisperer.agents.agent": "ai_whisperer.extensions.agents.agent",
    "ai_whisperer.agents.agent_communication": "ai_whisperer.extensions.agents.communication",
    "ai_whisperer.agents.continuation_strategy": "ai_whisperer.extensions.agents.continuation_strategy",
    "ai_whisperer.agents.debbie_tools": "ai_whisperer.extensions.agents.debbie_tools",
    "ai_whisperer.agents.decomposed_task": "ai_whisperer.extensions.agents.decomposed_task",
    "ai_whisperer.agents.task_decomposer": "ai_whisperer.extensions.agents.task_decomposer",
    "ai_whisperer.agents.prompt_optimizer": "ai_whisperer.extensions.agents.prompt_optimizer",
}

# Relative import fixes specific to Phase 4
RELATIVE_IMPORT_FIXES = {
    # Batch relative imports
    r"from \.batch_client": "from ai_whisperer.extensions.batch.client",
    r"from \.debbie_integration": "from ai_whisperer.extensions.batch.debbie_integration",
    r"from \.intervention": "from ai_whisperer.extensions.batch.intervention",
    r"from \.monitoring": "from ai_whisperer.extensions.batch.monitoring",
    r"from \.script_processor": "from ai_whisperer.extensions.batch.script_processor",
    r"from \.server_manager": "from ai_whisperer.extensions.batch.server_manager",
    r"from \.websocket_client": "from ai_whisperer.extensions.batch.websocket_client",
    r"from \.websocket_interceptor": "from ai_whisperer.extensions.batch.websocket_interceptor",
    
    # Logging relative imports
    r"from \.debbie_logger": "from ai_whisperer.extensions.monitoring.debbie_logger",
    r"from \.log_aggregator": "from ai_whisperer.extensions.monitoring.log_aggregator",
    r"from \.\.logging\.debbie_logger": "from ai_whisperer.extensions.monitoring.debbie_logger",
    
    # Agent relative imports
    r"from \.mailbox": "from ai_whisperer.extensions.mailbox.mailbox",
    r"from \.mailbox_tools": "from ai_whisperer.extensions.mailbox.tools",
    r"from \.mail_notification": "from ai_whisperer.extensions.mailbox.notification",
    r"from \.agent_communication": "from ai_whisperer.extensions.agents.communication",
    r"from \.continuation_strategy": "from ai_whisperer.extensions.agents.continuation_strategy",
    r"from \.task_decomposer": "from ai_whisperer.extensions.agents.task_decomposer",
}


def create_directories():
    """Create the new directory structure for Phase 4."""
    dirs = [
        "ai_whisperer/extensions",
        "ai_whisperer/extensions/batch",
        "ai_whisperer/extensions/monitoring",
        "ai_whisperer/extensions/mailbox",
        "ai_whisperer/extensions/agents",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files with proper module docstrings
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            module_name = dir_path.replace('/', '.')
            if 'extensions/batch' in dir_path and dir_path.endswith('batch'):
                content = f'''"""
{module_name} - Batch mode processing extension

This extension provides batch processing capabilities:
- Script-based automation
- WebSocket-based server communication
- Automated intervention handling
- Monitoring and debugging integration
"""
'''
            elif 'extensions/monitoring' in dir_path:
                content = f'''"""
{module_name} - Monitoring and debugging extension

This extension provides enhanced monitoring:
- Debbie debugger logger
- Log aggregation
- Pattern detection
"""
'''
            elif 'extensions/mailbox' in dir_path:
                content = f'''"""
{module_name} - Agent mailbox system extension

This extension provides inter-agent communication:
- Mailbox system
- Message tools
- Notifications
"""
'''
            elif 'extensions/agents' in dir_path and dir_path.endswith('agents'):
                content = f'''"""
{module_name} - Agent-specific extensions

This extension provides specialized agent features:
- Task decomposition
- Communication protocols
- Continuation strategies
- Prompt optimization
"""
'''
            elif 'extensions' in dir_path and dir_path.endswith('extensions'):
                content = f'''"""
{module_name} - Optional feature extensions

This package contains optional extensions:
- batch: Batch mode processing
- monitoring: Enhanced monitoring and debugging
- mailbox: Inter-agent communication
- agents: Agent-specific features
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
        if update_imports_in_file(file_path, PHASE4_IMPORTS, RELATIVE_IMPORT_FIXES):
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
    
    # Check batch directory
    batch_dir = Path("ai_whisperer/batch")
    if batch_dir.exists() and not any(batch_dir.iterdir()):
        empty_dirs.append(batch_dir)
    
    # Check logging directory
    logging_dir = Path("ai_whisperer/logging")
    if logging_dir.exists() and not any(logging_dir.iterdir()):
        empty_dirs.append(logging_dir)
    
    # Check if agents directory is now empty (after moving extensions)
    agents_dir = Path("ai_whisperer/agents")
    if agents_dir.exists():
        # Check if only __pycache__ or config remains
        remaining = list(agents_dir.iterdir())
        non_cache = [f for f in remaining if f.name != "__pycache__" and f.name != "config"]
        if not non_cache:
            # Clean up pycache first
            pycache = agents_dir / "__pycache__"
            if pycache.exists():
                subprocess.run(["rm", "-rf", str(pycache)], capture_output=True)
            if not any(agents_dir.iterdir()):
                empty_dirs.append(agents_dir)
    
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
        ["python", "-m", "pytest", "tests/unit/batch/", "-v", "--maxfail=3"],
        ["python", "-m", "pytest", "tests/unit/logging/", "-v"],
        ["python", "-m", "pytest", "-k", "test_mailbox", "-v"],
        ["python", "-m", "pytest", "-k", "test_agent_communication", "-v"],
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
    print("AIWhisperer Module Reorganization - Phase 4 (Auto)")
    print("=" * 50)
    print("This phase reorganizes optional extension modules")
    print("")
    
    # Check if we're in the right directory
    if not Path("ai_whisperer").exists():
        print("Error: Must run from project root directory")
        return 1
    
    # Show what will be done
    print("This script will:")
    print("1. Move ~23 extension files to better locations")
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
    for old_path, new_path in PHASE4_MOVEMENTS.items():
        if Path(old_path).exists():
            if move_file_with_git(old_path, new_path):
                success_count += 1
        else:
            print(f"  Skipping {old_path} (not found)")
    
    print(f"\nMoved {success_count}/{len(PHASE4_MOVEMENTS)} files")
    
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
    print("PHASE 4 COMPLETE")
    print("=" * 50)
    
    if tests_passed:
        print("\n✓ All verification tests passed!")
        print("\nNext steps:")
        print("1. Run full test suite: python -m pytest")
        print("2. Review changes: git status")
        print("3. Commit changes: git add -A && git commit -m 'refactor: Phase 4 extensions reorganization'")
        print("4. Update any documentation that references old paths")
    else:
        print("\n⚠ Some tests failed. Please review and fix issues before committing.")
        print("This is expected - imports in test files may need updating.")
    
    return 0


if __name__ == "__main__":
    exit(main())