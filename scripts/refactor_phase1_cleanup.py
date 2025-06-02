#!/usr/bin/env python3
"""Phase 1 cleanup script for AIWhisperer refactor."""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Script configuration
DRY_RUN = False  # Set to False to actually delete files
BACKUP_DIR = Path("refactor_backup")

# Files to delete
OBSOLETE_PYTHON_FILES = [
    # Old AI Loop
    "ai_whisperer/ai_loop/ai_loopy.py",
    
    # Agent E Experimental System
    "ai_whisperer/agents/agent_e_handler.py",
    "ai_whisperer/agents/agent_e_exceptions.py",
    "ai_whisperer/agents/external_agent_result.py",
    "ai_whisperer/agents/external_adapters.py",
    "ai_whisperer/agents/agent_e_tools.py",
    
    # Old Planning System
    "ai_whisperer/agents/planner_handler.py",
    "ai_whisperer/agents/planner_tools.py",
    "ai_whisperer/plan_parser.py",
    
    # Old State Management
    "ai_whisperer/state_management.py",
    "ai_whisperer/context_management.py",
    
    # Old Processing
    "ai_whisperer/processing.py",
    "ai_whisperer/json_validator.py",
    
    # Obsolete Entry Points
    "ai_whisperer/main.py",
    "ai_whisperer/batch/__main__.py",
    "ai_whisperer/interactive_entry.py",
    
    # Other obsolete
    "ai_whisperer/model_override.py",
    "ai_whisperer/task_selector.py",
]

# Directories to delete entirely
OBSOLETE_DIRECTORIES = [
    "project_dev",  # All prototype/obsolete
    ".WHISPER",     # Test artifacts only
]

# Patterns for temporary files
TEMP_FILE_PATTERNS = [
    "*.txt",  # But we'll exclude requirements.txt
    "debug_*.txt",
    "test_*.txt",
    "batch_test_*.txt",
]

def create_backup(path: Path) -> Path:
    """Create a backup of a file or directory."""
    backup_path = BACKUP_DIR / path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    if path.is_file():
        shutil.copy2(path, backup_path)
    else:
        shutil.copytree(path, backup_path)
    
    return backup_path

def delete_file(file_path: str, reason: str):
    """Delete a single file with logging."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"  ⚠️  NOT FOUND: {file_path}")
        return
    
    if DRY_RUN:
        print(f"  🔍 WOULD DELETE: {file_path} ({reason})")
    else:
        # Create backup
        backup_path = create_backup(path)
        # Delete file
        path.unlink()
        print(f"  ✅ DELETED: {file_path} (backed up to {backup_path})")

def delete_directory(dir_path: str, reason: str):
    """Delete an entire directory with logging."""
    path = Path(dir_path)
    
    if not path.exists():
        print(f"  ⚠️  NOT FOUND: {dir_path}")
        return
    
    # Count files
    file_count = sum(1 for _ in path.rglob("*") if _.is_file())
    
    if DRY_RUN:
        print(f"  🔍 WOULD DELETE: {dir_path}/ ({file_count} files, {reason})")
    else:
        # Create backup
        backup_path = create_backup(path)
        # Delete directory
        shutil.rmtree(path)
        print(f"  ✅ DELETED: {dir_path}/ ({file_count} files, backed up to {backup_path})")

def find_temp_files() -> list:
    """Find all temporary files to delete."""
    temp_files = []
    root = Path(".")
    
    # Find .txt files in root (excluding requirements.txt)
    for txt_file in root.glob("*.txt"):
        if txt_file.name != "requirements.txt":
            temp_files.append(txt_file)
    
    return temp_files

def main():
    """Run the cleanup process."""
    print("🧹 AIWhisperer Refactor - Phase 1 Cleanup")
    print("=" * 60)
    
    if DRY_RUN:
        print("🔍 DRY RUN MODE - No files will be deleted")
    else:
        print("⚠️  DELETION MODE - Files will be permanently removed!")
        print("   (Running in automated mode - no confirmation needed)")
    
    print()
    
    # Statistics
    total_files = 0
    total_dirs = 0
    
    # 1. Delete obsolete Python files
    print("📁 Deleting obsolete Python files...")
    for file_path in OBSOLETE_PYTHON_FILES:
        delete_file(file_path, "obsolete code")
        total_files += 1
    
    print()
    
    # 2. Delete obsolete directories
    print("📁 Deleting obsolete directories...")
    for dir_path in OBSOLETE_DIRECTORIES:
        delete_directory(dir_path, "obsolete/test artifacts")
        total_dirs += 1
    
    print()
    
    # 3. Delete temporary files
    print("📁 Deleting temporary files...")
    temp_files = find_temp_files()
    for temp_file in temp_files:
        delete_file(str(temp_file), "temporary file")
        total_files += 1
    
    print()
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   - Python files to delete: {len(OBSOLETE_PYTHON_FILES)}")
    print(f"   - Directories to delete: {len(OBSOLETE_DIRECTORIES)}")
    print(f"   - Temp files to delete: {len(temp_files)}")
    print(f"   - Total items: {total_files + total_dirs}")
    
    if DRY_RUN:
        print()
        print("💡 This was a dry run. To actually delete files, set DRY_RUN = False")
        print("   at the top of this script and run again.")
    else:
        print()
        print("✅ Cleanup complete! All files backed up to:", BACKUP_DIR)

if __name__ == "__main__":
    main()