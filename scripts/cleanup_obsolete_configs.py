#!/usr/bin/env python3
"""
Obsolete Configuration Cleanup Script

This script helps identify and optionally remove obsolete configuration files
identified during the configuration analysis.
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

class ConfigCleanup:
    """Cleans up obsolete configuration files"""
    
    # Patterns that indicate obsolete files
    OBSOLETE_PATTERNS = {
        'refactor_backup/project_dev/done/': 'Completed development artifacts',
        'refactor_backup/project_dev/in_dev/': 'In-progress development artifacts',
        'refactor_backup/.WHISPER/': 'Backup workspace files',
        'tests/temp_output/': 'Temporary test outputs',
        'output/web_search_cache/': 'Cache files',
        'subtask_': 'Task execution artifacts',
        'overview_': 'Task overview artifacts'
    }
    
    # Files to preserve even if they match patterns
    PRESERVE_FILES = {
        'aiwhisperer_config.yaml',  # May contain useful reference configs
        'agents.yaml',
        'tool_sets.yaml'
    }
    
    def __init__(self, root_path: str = '.', dry_run: bool = True):
        self.root_path = Path(root_path).absolute()
        self.dry_run = dry_run
        self.obsolete_files: List[Dict[str, str]] = []
        self.preserved_files: List[str] = []
        self.archive_dir = self.root_path / f"obsolete_configs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def find_obsolete_configs(self) -> List[Dict[str, str]]:
        """Find all obsolete configuration files based on patterns"""
        config_extensions = {'.yaml', '.yml', '.json', '.ini', '.toml', '.cfg'}
        
        for root, dirs, files in os.walk(self.root_path):
            # Skip certain directories
            if any(skip in root for skip in ['.git', 'node_modules', '.venv', '__pycache__']):
                continue
                
            root_path = Path(root)
            
            for file in files:
                if Path(file).suffix not in config_extensions:
                    continue
                    
                file_path = root_path / file
                relative_path = file_path.relative_to(self.root_path)
                relative_str = str(relative_path)
                
                # Check if file should be preserved
                if file in self.PRESERVE_FILES:
                    self.preserved_files.append(relative_str)
                    continue
                
                # Check obsolete patterns
                for pattern, reason in self.OBSOLETE_PATTERNS.items():
                    if pattern in relative_str:
                        self.obsolete_files.append({
                            'path': relative_str,
                            'absolute_path': str(file_path),
                            'reason': reason,
                            'size': file_path.stat().st_size
                        })
                        break
        
        return self.obsolete_files
    
    def categorize_obsolete_files(self) -> Dict[str, List[Dict[str, str]]]:
        """Categorize obsolete files by type"""
        categories = {}
        
        for file_info in self.obsolete_files:
            reason = file_info['reason']
            if reason not in categories:
                categories[reason] = []
            categories[reason].append(file_info)
            
        return categories
    
    def calculate_space_savings(self) -> int:
        """Calculate total space that would be freed"""
        return sum(f['size'] for f in self.obsolete_files)
    
    def archive_files(self, files: List[Dict[str, str]]):
        """Archive files instead of deleting them"""
        if not self.dry_run:
            self.archive_dir.mkdir(exist_ok=True)
            
        for file_info in files:
            source = Path(file_info['absolute_path'])
            if source.exists():
                dest = self.archive_dir / file_info['path']
                
                print(f"{'[DRY RUN] ' if self.dry_run else ''}Archive: {file_info['path']}")
                
                if not self.dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(dest))
    
    def delete_files(self, files: List[Dict[str, str]]):
        """Delete files permanently"""
        for file_info in files:
            file_path = Path(file_info['absolute_path'])
            if file_path.exists():
                print(f"{'[DRY RUN] ' if self.dry_run else ''}Delete: {file_info['path']}")
                
                if not self.dry_run:
                    file_path.unlink()
    
    def cleanup_empty_directories(self):
        """Remove empty directories after file cleanup"""
        if self.dry_run:
            return
            
        # Directories that might have obsolete files
        check_dirs = [
            'refactor_backup/project_dev/done',
            'refactor_backup/project_dev/in_dev',
            'tests/temp_output',
            'output/web_search_cache'
        ]
        
        for dir_path in check_dirs:
            full_path = self.root_path / dir_path
            if full_path.exists():
                # Remove empty subdirectories
                for root, dirs, files in os.walk(full_path, topdown=False):
                    if not files and not dirs:
                        Path(root).rmdir()
                        print(f"Removed empty directory: {Path(root).relative_to(self.root_path)}")
    
    def generate_cleanup_report(self) -> str:
        """Generate a detailed cleanup report"""
        categories = self.categorize_obsolete_files()
        space_savings = self.calculate_space_savings()
        
        report = []
        report.append("# Configuration Cleanup Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        
        # Summary
        report.append("\n## Summary")
        report.append(f"- Obsolete files found: {len(self.obsolete_files)}")
        report.append(f"- Preserved files: {len(self.preserved_files)}")
        report.append(f"- Space to be freed: {space_savings / 1024:.1f} KB")
        
        # Files by category
        report.append("\n## Obsolete Files by Category")
        for category, files in sorted(categories.items()):
            report.append(f"\n### {category} ({len(files)} files)")
            total_size = sum(f['size'] for f in files)
            report.append(f"Total size: {total_size / 1024:.1f} KB")
            
            # Show first 10 files
            for file_info in files[:10]:
                report.append(f"- `{file_info['path']}` ({file_info['size']} bytes)")
            
            if len(files) > 10:
                report.append(f"... and {len(files) - 10} more files")
        
        # Preserved files
        if self.preserved_files:
            report.append("\n## Preserved Files")
            report.append("These files matched obsolete patterns but were preserved:")
            for path in sorted(self.preserved_files)[:10]:
                report.append(f"- `{path}`")
            
            if len(self.preserved_files) > 10:
                report.append(f"... and {len(self.preserved_files) - 10} more files")
        
        return '\n'.join(report)
    
    def interactive_cleanup(self):
        """Interactive cleanup with user confirmation"""
        print("🔍 Scanning for obsolete configuration files...")
        self.find_obsolete_configs()
        
        if not self.obsolete_files:
            print("✅ No obsolete configuration files found!")
            return
        
        # Show summary
        categories = self.categorize_obsolete_files()
        space_savings = self.calculate_space_savings()
        
        print(f"\n📊 Found {len(self.obsolete_files)} obsolete files")
        print(f"💾 Space to be freed: {space_savings / 1024:.1f} KB")
        
        print("\n📁 Files by category:")
        for category, files in sorted(categories.items()):
            print(f"  - {category}: {len(files)} files")
        
        if self.dry_run:
            print("\n⚠️  This is a DRY RUN. No files will be modified.")
            print("Run with --execute to perform actual cleanup.")
            
            # Generate and save report
            report = self.generate_cleanup_report()
            report_path = self.root_path / f"cleanup_report_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_path.write_text(report)
            print(f"\n📄 Detailed report saved to: {report_path}")
            return
        
        # Ask for confirmation
        print("\n⚠️  WARNING: This will modify your filesystem!")
        print("Choose an action:")
        print("1. Archive files (move to archive directory)")
        print("2. Delete files permanently")
        print("3. Cancel")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print(f"\n📦 Archiving files to: {self.archive_dir.name}")
            self.archive_files(self.obsolete_files)
            self.cleanup_empty_directories()
            print(f"✅ Files archived to: {self.archive_dir}")
        elif choice == '2':
            confirm = input("\n⚠️  Are you SURE you want to permanently delete these files? (yes/no): ")
            if confirm.lower() == 'yes':
                print("\n🗑️  Deleting files...")
                self.delete_files(self.obsolete_files)
                self.cleanup_empty_directories()
                print("✅ Files deleted successfully")
            else:
                print("❌ Deletion cancelled")
                return
        else:
            print("❌ Cleanup cancelled")
            return
        
        # Generate final report
        report = self.generate_cleanup_report()
        report_path = self.root_path / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.write_text(report)
        print(f"\n📄 Cleanup report saved to: {report_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up obsolete configuration files')
    parser.add_argument('--execute', action='store_true',
                       help='Actually perform the cleanup (default is dry run)')
    parser.add_argument('--root', default='.',
                       help='Project root directory (default: current directory)')
    
    args = parser.parse_args()
    
    cleanup = ConfigCleanup(root_path=args.root, dry_run=not args.execute)
    cleanup.interactive_cleanup()