#!/usr/bin/env python3
"""
Complete the documentation archiving that failed during the consolidation process.
This script will safely archive the remaining files identified in the consolidation report.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Files that were supposed to be archived according to the consolidation report
FILES_TO_ARCHIVE = [
    "TEST_FIXES_SUMMARY.md",
    "TEST_FIX_COMPLETE_SUMMARY.md",
    "frontend/PHASE5_SUMMARY.md",
    "docs/completed/FRONTEND_TDD_CHECKLIST.md",
    "refactor_backup/project_dev/done/agent_REFACTOR_CHECKLIST.md",
    "docs/agent-e-subtask1-execution-log.md",
    "docs/agent-e-subtask2-execution-log.md",
    "docs/agent-e-subtask3-execution-log.md",
    "docs/agent-e-subtask4-execution-log.md",
    "docs/agent-e-subtask5-execution-log.md",
    "docs/agent-e-tools-execution-log.md",
    "docs/debugging-session-2025-05-30/LEGACY_CLEANUP_SUMMARY.md",
    "docs/completed/REPOSITORY_CLEANUP_2025-05-29.md",
    "docs/archive/DEVELOPMENT_PLAN.md",
    "docs/archive/delegate_system/user_message_system.md",
    "docs/archive/delegate_system/user_message_analysis.md",
    "docs/architecture/stateless_architecture.md",
    "refactor_backup/project_dev/done/agent_REFACTOR_PLAN.md",
    "frontend/tech_debt.md",
    "frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md",
    "REFACTOR_CHANGELOG.md",
    "CODEBASE_ANALYSIS_REPORT.md",
    "REFACTOR_EXECUTION_LOG.md",
    "doc_consolidation_report_20250602_115034.md",
    "PR_DESCRIPTION.md",
    # Phase summary files that were merged
    "BATCH_MODE_PHASE2_DAY1_SUMMARY.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE2_SUMMARY.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE2_DAY2_SUMMARY.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE2_DAY3_SUMMARY.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE3_DAY1_SUMMARY.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE2_DAY4_SUMMARY.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE1_SUMMARY.md",
    "docs/completed/AGENT_P_RFC_PHASE4_SUMMARY.md",
    # Test summary files that were merged
    "TEST_FINAL_STATUS.md",
    "REFACTOR_TEST_MAP_SUMMARY.md",
    "TEST_COMPLETION_SUMMARY.md",
    "TEST_STATUS_SUMMARY.md",
    # Additional debugging session files that were merged
    "docs/debugging-session-2025-05-30/DEBBIE_USAGE_GUIDE_FOR_AI_ASSISTANTS.md",
    "docs/debugging-session-2025-05-30/DEBBIE_IMPLEMENTATION_COMPLETE.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE3_INTERACTIVE_MONITORING_DESIGN.md",
    "docs/debugging-session-2025-05-30/DEBBIE_FIXES_SUMMARY.md",
    "docs/debugging-session-2025-05-30/WORKTREE_PATH_FIX.md",
    "docs/debugging-session-2025-05-30/TOOL_CALLING_IMPLEMENTATION_SUMMARY.md",
    "docs/debugging-session-2025-05-30/CHAT_BUG_ROOT_CAUSE.md",
    "docs/debugging-session-2025-05-30/REASONING_TOKEN_IMPLEMENTATION.md",
    "docs/debugging-session-2025-05-30/DEBBIE_PHASE3_INTERACTIVE_MONITORING_PLAN.md",
    "docs/debugging-session-2025-05-30/WORKTREE_SETUP.md",
    "docs/debugging-session-2025-05-30/DEBBIE_DEBUGGING_HELPER_CHECKLIST.md",
    "docs/debugging-session-2025-05-30/DEBBIE_INTRODUCTION_FIX.md",
    "docs/debugging-session-2025-05-30/WEBSOCKET_SESSION_FIX_SUMMARY.md",
    "docs/debugging-session-2025-05-30/DEBBIE_ENHANCED_LOGGING_DESIGN.md",
    "docs/debugging-session-2025-05-30/BUFFERING_BUG_FIX_SUMMARY.md",
    "docs/debugging-session-2025-05-30/OPENROUTER_SERVICE_SIMPLIFICATION_COMPLETE.md",
]


def archive_files(project_root: Path, dry_run: bool = True):
    """Archive the files that failed to be archived in the original script."""
    
    archive_dir = project_root / "docs" / "archive" / "consolidated_phase2"
    backup_dir = project_root / ".doc_backup" / f"archiving_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if not dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"Archive directory: {archive_dir}")
        print(f"Backup directory: {backup_dir}")
    else:
        print("[DRY RUN MODE - No changes will be made]")
    
    archived_count = 0
    missing_count = 0
    error_count = 0
    
    print(f"\nProcessing {len(FILES_TO_ARCHIVE)} files for archival...")
    
    for file_path in FILES_TO_ARCHIVE:
        source = project_root / file_path
        
        if not source.exists():
            print(f"  SKIP (not found): {file_path}")
            missing_count += 1
            continue
        
        try:
            # Determine archive path
            relative_path = Path(file_path)
            archive_path = archive_dir / relative_path
            
            if dry_run:
                print(f"  Would archive: {file_path}")
                print(f"    -> {archive_path.relative_to(project_root)}")
            else:
                # Create backup
                backup_path = backup_dir / relative_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, backup_path)
                
                # Move to archive
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(archive_path))
                print(f"  Archived: {file_path}")
                
                # Clean up empty directories
                try:
                    source.parent.rmdir()
                except OSError:
                    pass  # Directory not empty
            
            archived_count += 1
            
        except Exception as e:
            print(f"  ERROR archiving {file_path}: {e}")
            error_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("ARCHIVING SUMMARY")
    print(f"{'='*60}")
    print(f"Files processed: {len(FILES_TO_ARCHIVE)}")
    print(f"Files archived: {archived_count}")
    print(f"Files not found (already processed): {missing_count}")
    print(f"Errors: {error_count}")
    print(f"{'='*60}")
    
    return archived_count, missing_count, error_count


def check_file_locations(project_root: Path):
    """Check where the markdown files are actually located."""
    print("\nAnalyzing markdown file distribution...")
    
    # Count files by top-level directory
    dir_counts = {}
    total_files = 0
    
    for root, dirs, files in os.walk(project_root):
        # Skip vendor directories
        dirs[:] = [d for d in dirs if d not in {
            'node_modules', '.venv', 'venv', '__pycache__', 
            '.git', 'build', 'dist', '.pytest_cache'
        }]
        
        for file in files:
            if file.endswith(('.md', '.MD')):
                total_files += 1
                
                # Get top-level directory
                rel_path = Path(root).relative_to(project_root)
                if rel_path == Path('.'):
                    top_dir = 'root'
                else:
                    top_dir = rel_path.parts[0]
                
                dir_counts[top_dir] = dir_counts.get(top_dir, 0) + 1
    
    print(f"\nTotal markdown files: {total_files}")
    print("\nFiles by directory:")
    for dir_name, count in sorted(dir_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dir_name}: {count}")
    
    return total_files, dir_counts


def main():
    parser = argparse.ArgumentParser(
        description="Complete the failed documentation archiving process"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the archiving (default is dry-run mode)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze file distribution to understand count discrepancy"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("/home/deano/projects/AIWhisperer"),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    if args.analyze:
        total, distribution = check_file_locations(args.project_root)
        return
    
    # Run archiving
    archived, missing, errors = archive_files(
        project_root=args.project_root,
        dry_run=not args.execute
    )
    
    if not args.execute and archived > 0:
        print("\nTo execute the archiving, run with --execute flag")


if __name__ == "__main__":
    main()