#!/usr/bin/env python3
"""
Documentation Consolidation Script for AIWhisperer Phase 2 Refactoring

This script analyzes and consolidates markdown documentation files to reduce
redundancy and improve organization. It identifies duplicate content, similar
files, and outdated documentation for consolidation or archival.
"""

import os
import re
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional
import argparse
from difflib import SequenceMatcher


class DocumentationAnalyzer:
    """Analyzes markdown documentation files for consolidation opportunities."""
    
    def __init__(self, project_root: Path, dry_run: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.backup_dir = project_root / ".doc_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.archive_dir = project_root / "docs" / "archive" / "consolidated_phase2"
        
        # Categories for grouping documentation
        self.categories = {
            "test_summaries": r"TEST_.*\.(md|MD)$",
            "phase_summaries": r".*PHASE\d+.*SUMMARY.*\.md$",
            "batch_mode": r".*BATCH.*MODE.*\.md$",
            "debugging_session": r"debugging-session-\d{4}-\d{2}-\d{2}",
            "agent_e_logs": r"agent-e-.*execution-log\.md$",
            "implementation_plans": r".*IMPLEMENTATION.*PLAN.*\.md$",
            "checklists": r".*CHECKLIST.*\.md$",
            "status_updates": r".*STATUS.*UPDATE.*\.md$",
            "rfc_docs": r".*RFC.*\.md$",
            "architecture": r".*architecture.*\.md$",
            "completed": r"completed/.*\.md$",
            "archive": r"archive/.*\.md$",
            "refactor_backup": r"refactor_backup/.*\.md$",
            "whisper_metadata": r"\.WHISPER/.*\.md$",
            "frontend_docs": r"frontend/.*\.md$",
            "api_docs": r"docs/api/.*\.md$",
        }
        
        self.consolidation_rules = {
            "test_summaries": "TEST_CONSOLIDATED_SUMMARY.md",
            "phase_summaries": "PHASE_CONSOLIDATED_SUMMARY.md",
            "batch_mode": "batch-mode/CONSOLIDATED_GUIDE.md",
            "agent_e_logs": "docs/agent-e-execution-consolidated.md",
            "debugging_session": "docs/archive/debugging-session-2025-05-30-consolidated.md",
        }
        
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the project, excluding vendor directories."""
        exclude_dirs = {'node_modules', '.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.pytest_cache'}
        md_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(('.md', '.MD')):
                    md_files.append(Path(root) / file)
                    
        return md_files
    
    def categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize files based on patterns."""
        categorized = defaultdict(list)
        uncategorized = []
        
        for file in files:
            file_str = str(file.relative_to(self.project_root))
            categorized_flag = False
            
            for category, pattern in self.categories.items():
                if re.search(pattern, file_str, re.IGNORECASE):
                    categorized[category].append(file)
                    categorized_flag = True
                    break
                    
            if not categorized_flag:
                uncategorized.append(file)
                
        categorized['uncategorized'] = uncategorized
        return dict(categorized)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content."""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def find_duplicates(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Find files with identical content."""
        hash_to_files = defaultdict(list)
        
        for file in files:
            try:
                file_hash = self.calculate_file_hash(file)
                hash_to_files[file_hash].append(file)
            except Exception as e:
                print(f"Error hashing {file}: {e}")
                
        # Return only duplicates
        return {h: files for h, files in hash_to_files.items() if len(files) > 1}
    
    def calculate_similarity(self, file1: Path, file2: Path) -> float:
        """Calculate similarity ratio between two files."""
        try:
            with open(file1, 'r', encoding='utf-8') as f1:
                content1 = f1.read()
            with open(file2, 'r', encoding='utf-8') as f2:
                content2 = f2.read()
                
            return SequenceMatcher(None, content1, content2).ratio()
        except Exception:
            return 0.0
    
    def find_similar_files(self, files: List[Path], threshold: float = 0.8) -> List[Tuple[Path, Path, float]]:
        """Find files with similar content above threshold."""
        similar_pairs = []
        
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                similarity = self.calculate_similarity(file1, file2)
                if similarity >= threshold:
                    similar_pairs.append((file1, file2, similarity))
                    
        return similar_pairs
    
    def analyze_file_metadata(self, file: Path) -> Dict:
        """Extract metadata from a file."""
        stat = file.stat()
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
                word_count = len(content.split())
        except Exception:
            lines = []
            word_count = 0
            
        return {
            'path': file,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'lines': len(lines),
            'words': word_count,
        }
    
    def identify_outdated_docs(self, files: List[Path]) -> List[Path]:
        """Identify potentially outdated documentation."""
        outdated = []
        current_date = datetime.now()
        
        for file in files:
            try:
                stat = file.stat()
                age_days = (current_date - datetime.fromtimestamp(stat.st_mtime)).days
                
                # Check for old files (>90 days)
                if age_days > 90:
                    outdated.append(file)
                    continue
                    
                # Check for deprecated patterns in content
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                deprecated_patterns = [
                    'deprecated',
                    'obsolete',
                    'old version',
                    'no longer used',
                    'legacy',
                    'outdated',
                ]
                
                for pattern in deprecated_patterns:
                    if pattern in content:
                        outdated.append(file)
                        break
                        
            except Exception:
                pass
                
        return outdated
    
    def create_consolidation_plan(self, categorized: Dict[str, List[Path]]) -> Dict:
        """Create a detailed consolidation plan."""
        plan = {
            'merge_groups': [],
            'archive': [],
            'delete': [],
            'keep': [],
            'outdated': [],
            'statistics': {}
        }
        
        # Handle test summaries
        if 'test_summaries' in categorized and len(categorized['test_summaries']) > 1:
            plan['merge_groups'].append({
                'target': self.project_root / self.consolidation_rules['test_summaries'],
                'sources': categorized['test_summaries'],
                'reason': 'Multiple test summary files for the same testing effort'
            })
        
        # Handle phase summaries
        if 'phase_summaries' in categorized and len(categorized['phase_summaries']) > 1:
            plan['merge_groups'].append({
                'target': self.project_root / self.consolidation_rules['phase_summaries'],
                'sources': categorized['phase_summaries'],
                'reason': 'Multiple phase summary files that should be consolidated'
            })
        
        # Handle debugging session files
        if 'debugging_session' in categorized:
            debugging_files = categorized['debugging_session']
            if len(debugging_files) > 10:  # Many files from single session
                plan['merge_groups'].append({
                    'target': self.project_root / self.consolidation_rules['debugging_session'],
                    'sources': debugging_files,
                    'reason': f'{len(debugging_files)} files from a single debugging session'
                })
        
        # Handle agent-e execution logs
        if 'agent_e_logs' in categorized and len(categorized['agent_e_logs']) > 3:
            plan['merge_groups'].append({
                'target': self.project_root / self.consolidation_rules['agent_e_logs'],
                'sources': categorized['agent_e_logs'],
                'reason': 'Multiple execution logs for Agent E implementation'
            })
        
        # Find exact duplicates across all files
        all_files = []
        for files in categorized.values():
            all_files.extend(files)
            
        duplicates = self.find_duplicates(all_files)
        for hash_val, dup_files in duplicates.items():
            if len(dup_files) > 1:
                # Keep the oldest file, delete others
                sorted_files = sorted(dup_files, key=lambda f: f.stat().st_mtime)
                plan['keep'].append(sorted_files[0])
                plan['delete'].extend(sorted_files[1:])
        
        # Archive old completed items
        if 'completed' in categorized:
            for file in categorized['completed']:
                stat = file.stat()
                # Archive if older than 30 days
                if (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days > 30:
                    plan['archive'].append(file)
        
        # Find outdated documentation
        plan['outdated'] = self.identify_outdated_docs(all_files)
        
        # Add outdated files to archive list (avoiding duplicates)
        for file in plan['outdated']:
            if file not in plan['archive'] and file not in plan['delete']:
                plan['archive'].append(file)
        
        # Handle refactor_backup files - these should be archived
        if 'refactor_backup' in categorized:
            for file in categorized['refactor_backup']:
                if file not in plan['archive']:
                    plan['archive'].append(file)
        
        # Calculate statistics
        total_files = len(all_files)
        files_to_merge = sum(len(group['sources']) for group in plan['merge_groups'])
        files_to_delete = len(plan['delete'])
        files_to_archive = len(plan['archive'])
        
        plan['statistics'] = {
            'total_files': total_files,
            'files_to_merge': files_to_merge,
            'files_to_delete': files_to_delete,
            'files_to_archive': files_to_archive,
            'outdated_files': len(plan['outdated']),
            'files_after_consolidation': total_files - files_to_delete - files_to_merge + len(plan['merge_groups']) - files_to_archive,
            'reduction_percentage': ((files_to_delete + files_to_merge - len(plan['merge_groups']) + files_to_archive) / total_files * 100) if total_files > 0 else 0
        }
        
        return plan
    
    def generate_report(self, categorized: Dict[str, List[Path]], plan: Dict) -> str:
        """Generate a detailed report of the analysis and consolidation plan."""
        report = []
        report.append("# AIWhisperer Documentation Consolidation Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}\n")
        
        # Current structure analysis
        report.append("## Current Structure Analysis\n")
        total_files = sum(len(files) for files in categorized.values())
        report.append(f"Total markdown files found: {total_files}\n")
        
        report.append("### Files by Category:\n")
        for category, files in sorted(categorized.items()):
            if files and category != 'uncategorized':
                report.append(f"- **{category.replace('_', ' ').title()}**: {len(files)} files")
                if len(files) <= 10:
                    for file in sorted(files):
                        rel_path = file.relative_to(self.project_root)
                        report.append(f"  - {rel_path}")
                else:
                    report.append(f"  - (showing first 5 of {len(files)} files)")
                    for file in sorted(files)[:5]:
                        rel_path = file.relative_to(self.project_root)
                        report.append(f"  - {rel_path}")
                    report.append("  - ...")
        
        # Uncategorized files summary
        if categorized.get('uncategorized'):
            report.append(f"\n- **Uncategorized**: {len(categorized['uncategorized'])} files")
        
        # Consolidation plan
        report.append("\n## Proposed Consolidation Plan\n")
        
        # Merge groups
        if plan['merge_groups']:
            report.append("### Files to be Merged:\n")
            for group in plan['merge_groups']:
                target = group['target'].relative_to(self.project_root)
                report.append(f"**Target**: `{target}`")
                report.append(f"**Reason**: {group['reason']}")
                report.append("**Source files**:")
                for source in group['sources']:
                    rel_path = source.relative_to(self.project_root)
                    report.append(f"  - {rel_path}")
                report.append("")
        
        # Files to delete
        if plan['delete']:
            report.append("### Files to be Deleted (Duplicates):\n")
            for file in plan['delete'][:20]:  # Show first 20
                rel_path = file.relative_to(self.project_root)
                report.append(f"- {rel_path}")
            if len(plan['delete']) > 20:
                report.append(f"- ... and {len(plan['delete']) - 20} more files")
            report.append("")
        
        # Files to archive
        if plan['archive']:
            report.append("### Files to be Archived:\n")
            for file in plan['archive'][:20]:  # Show first 20
                rel_path = file.relative_to(self.project_root)
                report.append(f"- {rel_path}")
            if len(plan['archive']) > 20:
                report.append(f"- ... and {len(plan['archive']) - 20} more files")
            report.append("")
        
        # Outdated files identified
        if plan.get('outdated'):
            report.append("### Outdated Files Identified:\n")
            report.append(f"Found {len(plan['outdated'])} potentially outdated files (>90 days old or containing deprecated markers)\n")
            for file in plan['outdated'][:10]:  # Show first 10
                rel_path = file.relative_to(self.project_root)
                stat = file.stat()
                age_days = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                report.append(f"- {rel_path} (age: {age_days} days)")
            if len(plan['outdated']) > 10:
                report.append(f"- ... and {len(plan['outdated']) - 10} more files")
            report.append("")
        
        # Statistics
        report.append("## Expected Results\n")
        stats = plan['statistics']
        report.append(f"- Current file count: {stats['total_files']}")
        report.append(f"- Files after consolidation: {stats['files_after_consolidation']}")
        report.append(f"- Reduction: {stats['total_files'] - stats['files_after_consolidation']} files ({stats['reduction_percentage']:.1f}%)")
        report.append(f"- Files to merge: {stats['files_to_merge']}")
        report.append(f"- Files to delete: {stats['files_to_delete']}")
        report.append(f"- Files to archive: {stats['files_to_archive']}")
        report.append(f"- Outdated files found: {stats.get('outdated_files', 0)}")
        
        return "\n".join(report)
    
    def backup_file(self, file: Path) -> Path:
        """Create a backup of a file before modification."""
        if not self.dry_run:
            relative_path = file.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, backup_path)
            return backup_path
        return file
    
    def merge_files(self, sources: List[Path], target: Path) -> None:
        """Merge multiple source files into a single target file."""
        if self.dry_run:
            print(f"[DRY RUN] Would merge {len(sources)} files into {target}")
            return
            
        print(f"Merging {len(sources)} files into {target}")
        
        # Backup sources
        for source in sources:
            self.backup_file(source)
        
        # Create merged content
        merged_content = []
        merged_content.append(f"# Consolidated Documentation")
        merged_content.append(f"\nThis file consolidates multiple related documents.")
        merged_content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        merged_content.append("## Table of Contents\n")
        
        # Add TOC
        for i, source in enumerate(sources, 1):
            title = source.stem.replace('_', ' ').replace('-', ' ').title()
            merged_content.append(f"{i}. [{title}](#{source.stem.lower()})")
        
        merged_content.append("\n---\n")
        
        # Add content from each file
        for source in sources:
            title = source.stem.replace('_', ' ').replace('-', ' ').title()
            merged_content.append(f"## {title}")
            merged_content.append(f"\n*Original file: {source.relative_to(self.project_root)}*\n")
            
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    merged_content.append(content)
                    merged_content.append("\n\n---\n")
            except Exception as e:
                merged_content.append(f"*Error reading file: {e}*\n")
                merged_content.append("\n---\n")
        
        # Write merged file
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write('\n'.join(merged_content))
        
        # Delete source files
        for source in sources:
            source.unlink()
            print(f"  Deleted: {source.relative_to(self.project_root)}")
    
    def archive_file(self, file: Path) -> None:
        """Archive a file to the archive directory."""
        if self.dry_run:
            print(f"[DRY RUN] Would archive {file}")
            return
        
        # Skip if file doesn't exist (may have been deleted in merge)
        if not file.exists():
            return
            
        print(f"Archiving {file}")
        
        # Backup first
        self.backup_file(file)
        
        # Move to archive
        relative_path = file.relative_to(self.project_root)
        archive_path = self.archive_dir / relative_path
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(archive_path))
        print(f"  Moved to: {archive_path.relative_to(self.project_root)}")
    
    def execute_plan(self, plan: Dict) -> None:
        """Execute the consolidation plan."""
        if self.dry_run:
            print("\n[DRY RUN MODE - No changes will be made]\n")
        else:
            print(f"\nCreating backup directory: {self.backup_dir}")
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Execute merges
        if plan['merge_groups']:
            print("\nExecuting file merges...")
            for group in plan['merge_groups']:
                self.merge_files(group['sources'], group['target'])
        
        # Execute deletions
        if plan['delete']:
            print("\nDeleting duplicate files...")
            for file in plan['delete']:
                if self.dry_run:
                    print(f"[DRY RUN] Would delete {file.relative_to(self.project_root)}")
                else:
                    self.backup_file(file)
                    file.unlink()
                    print(f"  Deleted: {file.relative_to(self.project_root)}")
        
        # Execute archival
        if plan['archive']:
            print("\nArchiving old files...")
            for file in plan['archive']:
                self.archive_file(file)
        
        if not self.dry_run:
            print(f"\nBackup created at: {self.backup_dir}")
            print("To restore, copy files from backup directory back to original locations")
    
    def run(self) -> None:
        """Run the complete analysis and consolidation process."""
        print("Starting AIWhisperer documentation analysis...")
        
        # Find all markdown files
        all_files = self.find_markdown_files()
        print(f"Found {len(all_files)} markdown files")
        
        # Categorize files
        categorized = self.categorize_files(all_files)
        
        # Create consolidation plan
        plan = self.create_consolidation_plan(categorized)
        
        # Generate and save report
        report = self.generate_report(categorized, plan)
        report_path = self.project_root / f"doc_consolidation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("CONSOLIDATION SUMMARY")
        print("="*60)
        stats = plan['statistics']
        print(f"Current files: {stats['total_files']}")
        print(f"Files after consolidation: {stats['files_after_consolidation']}")
        print(f"Total reduction: {stats['total_files'] - stats['files_after_consolidation']} files ({stats['reduction_percentage']:.1f}%)")
        print(f"\nBreakdown:")
        print(f"  - Files to merge: {stats['files_to_merge']} → {len(plan['merge_groups'])} consolidated files")
        print(f"  - Files to delete (duplicates): {stats['files_to_delete']}")
        print(f"  - Files to archive: {stats['files_to_archive']}")
        print(f"  - Outdated files identified: {stats.get('outdated_files', 0)}")
        print("="*60)
        
        # Ask for confirmation if not in dry run
        if not self.dry_run:
            if hasattr(self, 'force') and self.force:
                print("\n[FORCE MODE - Proceeding without confirmation]")
            else:
                response = input("\nProceed with consolidation? (yes/no): ")
                if response.lower() != 'yes':
                    print("Consolidation cancelled.")
                    return
        
        # Execute the plan
        self.execute_plan(plan)
        
        print("\nConsolidation complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze and consolidate AIWhisperer documentation files"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the consolidation (default is dry-run mode)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt when executing"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("/home/deano/projects/AIWhisperer"),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    analyzer = DocumentationAnalyzer(
        project_root=args.project_root,
        dry_run=not args.execute
    )
    
    analyzer.force = args.force
    analyzer.run()


if __name__ == "__main__":
    main()