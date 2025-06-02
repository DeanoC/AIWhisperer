#!/usr/bin/env python3
"""
Phase 2 Documentation Consolidation Script
Consolidates related implementation documentation files and performs final cleanup.
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

class Phase2DocCleanup:
    def __init__(self, project_root: str = ".", dry_run: bool = True):
        self.project_root = Path(project_root).resolve()
        self.docs_dir = self.project_root / "docs"
        self.archive_dir = self.docs_dir / "archive"
        self.dry_run = dry_run
        self.backup_dir = self.project_root / f"backup_phase2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.operations_log = []
        
    def log_operation(self, operation: str, details: str):
        """Log an operation for summary display."""
        self.operations_log.append({
            "operation": operation,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{'[DRY RUN] ' if self.dry_run else ''}{operation}: {details}")
    
    def create_backup(self, file_path: Path):
        """Create a backup of a file before modifying it."""
        if self.dry_run:
            return
            
        backup_path = self.backup_dir / file_path.relative_to(self.project_root)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        
    def consolidate_files(self, pattern: str, output_file: str, title: str) -> bool:
        """Consolidate multiple files matching a pattern into one file."""
        # Find all matching files
        matching_files = sorted(self.docs_dir.glob(pattern))
        
        if not matching_files:
            self.log_operation("SKIP", f"No files found matching {pattern}")
            return False
            
        output_path = self.docs_dir / output_file
        
        # Check if output already exists
        if output_path.exists():
            self.log_operation("SKIP", f"{output_file} already exists")
            return False
            
        self.log_operation("CONSOLIDATE", f"Merging {len(matching_files)} files into {output_file}")
        
        if not self.dry_run:
            # Create consolidated content
            content = f"# {title}\n\n"
            content += f"*Consolidated on {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            content += "This document consolidates multiple implementation files for better organization.\n\n"
            content += "---\n\n"
            
            for i, file_path in enumerate(matching_files):
                self.create_backup(file_path)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Add to consolidated content
                content += f"## Part {i+1}: {file_path.name}\n\n"
                content += file_content
                content += "\n\n---\n\n"
            
            # Write consolidated file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Archive original files
            for file_path in matching_files:
                archive_path = self.archive_dir / "phase2_consolidation" / file_path.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(archive_path))
                
        return True
    
    def consolidate_agent_e_docs(self):
        """Consolidate agent-e implementation documentation."""
        self.log_operation("PHASE", "Consolidating Agent-E documentation")
        
        # List of specific files to consolidate
        agent_e_files = [
            "agent-e-implementation-log.md",
            "agent-e-implementation-progress.md",
            "agent-e-implementation-summary.md",
            "agent-e-subtask1-execution-log.md",
            "agent-e-subtask2-execution-log.md",
            "agent-e-subtask3-execution-log.md",
            "agent-e-subtask4-execution-log.md",
            "agent-e-subtask5-execution-log.md",
            "agent-e-tools-execution-log.md"
        ]
        
        # Find existing files
        existing_files = []
        for filename in agent_e_files:
            file_path = self.docs_dir / filename
            if file_path.exists():
                existing_files.append(file_path)
        
        if not existing_files:
            self.log_operation("SKIP", "No agent-e implementation files found")
            return
            
        output_path = self.docs_dir / "agent-e-consolidated-implementation.md"
        
        if output_path.exists():
            self.log_operation("SKIP", "agent-e-consolidated-implementation.md already exists")
            return
            
        self.log_operation("CONSOLIDATE", f"Merging {len(existing_files)} agent-e files")
        
        if not self.dry_run:
            # Create consolidated content
            content = "# Agent-E Consolidated Implementation Documentation\n\n"
            content += f"*Consolidated on {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            content += "This document consolidates all Agent-E implementation documentation.\n\n"
            content += "---\n\n"
            
            for file_path in existing_files:
                self.create_backup(file_path)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                content += f"## {file_path.stem.replace('-', ' ').title()}\n\n"
                content += file_content
                content += "\n\n---\n\n"
            
            # Write consolidated file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Archive original files
            for file_path in existing_files:
                archive_path = self.archive_dir / "phase2_consolidation" / file_path.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(archive_path))
    
    def consolidate_file_browser_docs(self):
        """Consolidate file browser implementation documentation."""
        self.log_operation("PHASE", "Consolidating File Browser documentation")
        
        # List of specific files to consolidate
        file_browser_files = [
            "file_browser_implementation_checklist.md",
            "file_browser_implementation_plan.md",
            "file_browser_implementation_priority.md",
            "file_browser_integration_summary.md",
            "IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md"
        ]
        
        # Find existing files
        existing_files = []
        for filename in file_browser_files:
            file_path = self.docs_dir / filename
            if file_path.exists():
                existing_files.append(file_path)
        
        if not existing_files:
            self.log_operation("SKIP", "No file browser implementation files found")
            return
            
        output_path = self.docs_dir / "file-browser-consolidated-implementation.md"
        
        if output_path.exists():
            self.log_operation("SKIP", "file-browser-consolidated-implementation.md already exists")
            return
            
        self.log_operation("CONSOLIDATE", f"Merging {len(existing_files)} file browser files")
        
        if not self.dry_run:
            # Create consolidated content
            content = "# File Browser Consolidated Implementation Documentation\n\n"
            content += f"*Consolidated on {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            content += "This document consolidates all File Browser implementation documentation.\n\n"
            content += "---\n\n"
            
            for file_path in existing_files:
                self.create_backup(file_path)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                content += f"## {file_path.stem.replace('_', ' ').title()}\n\n"
                content += file_content
                content += "\n\n---\n\n"
            
            # Write consolidated file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Archive original files
            for file_path in existing_files:
                archive_path = self.archive_dir / "phase2_consolidation" / file_path.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(archive_path))
    
    def consolidate_agent_continuation_docs(self):
        """Consolidate agent continuation implementation documentation."""
        self.log_operation("PHASE", "Consolidating Agent Continuation documentation")
        
        feature_dir = self.docs_dir / "feature"
        if not feature_dir.exists():
            self.log_operation("SKIP", "No feature directory found")
            return
            
        # Find agent continuation files
        continuation_files = sorted(feature_dir.glob("agent-continuation-implementation-*.md"))
        
        if not continuation_files:
            self.log_operation("SKIP", "No agent continuation implementation files found")
            return
            
        output_path = feature_dir / "agent-continuation-consolidated-implementation.md"
        
        if output_path.exists():
            self.log_operation("SKIP", "agent-continuation-consolidated-implementation.md already exists")
            return
            
        self.log_operation("CONSOLIDATE", f"Merging {len(continuation_files)} agent continuation files")
        
        if not self.dry_run:
            # Create consolidated content
            content = "# Agent Continuation Consolidated Implementation Documentation\n\n"
            content += f"*Consolidated on {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            content += "This document consolidates all Agent Continuation implementation documentation.\n\n"
            content += "---\n\n"
            
            for file_path in continuation_files:
                self.create_backup(file_path)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                content += f"## {file_path.stem.replace('-', ' ').title()}\n\n"
                content += file_content
                content += "\n\n---\n\n"
            
            # Write consolidated file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Archive original files
            for file_path in continuation_files:
                archive_path = self.archive_dir / "phase2_consolidation" / file_path.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(archive_path))
    
    def archive_cleanup_files(self):
        """Archive the temporary cleanup plan files."""
        self.log_operation("PHASE", "Archiving cleanup plan files")
        
        cleanup_files = [
            "doc_cleanup_detailed_plan.md",
            "doc_cleanup_execution_summary.md",
            "complete_doc_cleanup_plan.md"
        ]
        
        archived_count = 0
        for filename in cleanup_files:
            file_path = self.docs_dir / filename
            if file_path.exists():
                if not self.dry_run:
                    self.create_backup(file_path)
                    archive_path = self.archive_dir / "cleanup_plans" / filename
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(archive_path))
                self.log_operation("ARCHIVE", f"Moved {filename} to archive/cleanup_plans/")
                archived_count += 1
            else:
                self.log_operation("SKIP", f"{filename} not found")
                
        if archived_count > 0:
            self.log_operation("COMPLETE", f"Archived {archived_count} cleanup plan files")
    
    def create_legacy_archive(self):
        """Move old archive files to a deeper archive structure."""
        self.log_operation("PHASE", "Creating legacy archive structure")
        
        legacy_dirs = ["analysis", "terminal_ui", "old_architecture", "delegate_system"]
        moved_count = 0
        
        for dirname in legacy_dirs:
            source_dir = self.archive_dir / dirname
            if source_dir.exists() and source_dir.is_dir():
                if not self.dry_run:
                    legacy_dir = self.archive_dir / "legacy" / dirname
                    legacy_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_dir), str(legacy_dir))
                self.log_operation("MOVE", f"Moved archive/{dirname}/ to archive/legacy/{dirname}/")
                moved_count += 1
            else:
                self.log_operation("SKIP", f"archive/{dirname}/ not found")
                
        if moved_count > 0:
            self.log_operation("COMPLETE", f"Moved {moved_count} directories to legacy archive")
    
    def generate_summary(self):
        """Generate a summary of all operations."""
        summary = "\n" + "="*50 + "\n"
        summary += "PHASE 2 CLEANUP SUMMARY\n"
        summary += "="*50 + "\n\n"
        
        if self.dry_run:
            summary += "**DRY RUN MODE - No actual changes made**\n\n"
        
        # Group operations by type
        operation_counts = {}
        for op in self.operations_log:
            op_type = op["operation"]
            if op_type not in operation_counts:
                operation_counts[op_type] = 0
            operation_counts[op_type] += 1
        
        summary += "Operations performed:\n"
        for op_type, count in operation_counts.items():
            summary += f"- {op_type}: {count}\n"
        
        summary += f"\nTotal operations: {len(self.operations_log)}\n"
        
        if not self.dry_run:
            summary += f"\nBackup created at: {self.backup_dir}\n"
        
        return summary
    
    def run(self):
        """Execute all phase 2 cleanup operations."""
        print("Starting Phase 2 Documentation Cleanup...")
        print(f"Project root: {self.project_root}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}\n")
        
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.log_operation("BACKUP", f"Created backup directory: {self.backup_dir}")
        
        # Execute consolidation phases
        self.consolidate_agent_e_docs()
        print()
        
        self.consolidate_file_browser_docs()
        print()
        
        self.consolidate_agent_continuation_docs()
        print()
        
        self.archive_cleanup_files()
        print()
        
        self.create_legacy_archive()
        print()
        
        # Generate and display summary
        print(self.generate_summary())
        
        # Save operations log
        if not self.dry_run:
            log_file = self.project_root / f"phase2_cleanup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "project_root": str(self.project_root),
                    "operations": self.operations_log
                }, f, indent=2)
            print(f"\nOperations log saved to: {log_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2 Documentation Consolidation Script")
    parser.add_argument("--project-root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--live", action="store_true", help="Execute changes (default is dry-run mode)")
    
    args = parser.parse_args()
    
    cleanup = Phase2DocCleanup(
        project_root=args.project_root,
        dry_run=not args.live
    )
    
    try:
        cleanup.run()
    except Exception as e:
        print(f"\nError during cleanup: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())