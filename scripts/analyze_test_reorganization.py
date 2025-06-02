#!/usr/bin/env python3
"""
Analyze AIWhisperer test structure and create a reorganization plan.

This script analyzes the current test organization, identifies issues,
and creates a comprehensive reorganization plan to improve test structure.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class TestFile:
    """Information about a test file."""
    path: Path
    category: str  # unit, integration, server, etc.
    target_module: Optional[str] = None
    issues: List[str] = field(default_factory=list)
    proposed_path: Optional[Path] = None
    action: str = "keep"  # keep, move, rename, delete, review


@dataclass
class ModuleCoverage:
    """Coverage information for a source module."""
    module_path: Path
    test_files: List[Path] = field(default_factory=list)
    has_coverage: bool = False


class TestReorganizer:
    """Analyze and reorganize test structure."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.src_dir = project_root / "ai_whisperer"
        self.server_dir = project_root / "interactive_server"
        self.postprocessing_dir = project_root / "postprocessing"
        
        self.test_files: Dict[Path, TestFile] = {}
        self.source_modules: Dict[Path, ModuleCoverage] = {}
        self.issues: List[str] = []
        self.improvements: List[str] = []
        
    def analyze(self):
        """Run complete analysis."""
        print("Analyzing AIWhisperer test structure...")
        print("=" * 80)
        
        self._scan_test_files()
        self._scan_source_modules()
        self._analyze_test_coverage()
        self._identify_misplaced_tests()
        self._identify_naming_issues()
        self._identify_demo_files()
        self._create_reorganization_plan()
        
        self._print_current_structure()
        self._print_issues()
        self._print_proposed_structure()
        self._print_migration_plan()
        self._print_summary()
        
    def _scan_test_files(self):
        """Scan all test files and categorize them."""
        for root, dirs, files in os.walk(self.tests_dir):
            root_path = Path(root)
            
            # Skip __pycache__ and other hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    file_path = root_path / file
                    rel_path = file_path.relative_to(self.tests_dir)
                    
                    # Categorize based on location and name
                    category = self._categorize_test_file(rel_path)
                    
                    test_file = TestFile(
                        path=rel_path,
                        category=category
                    )
                    
                    # Try to determine target module
                    test_file.target_module = self._infer_target_module(file, rel_path)
                    
                    self.test_files[rel_path] = test_file
                    
    def _categorize_test_file(self, rel_path: Path) -> str:
        """Categorize a test file based on its location and name."""
        parts = rel_path.parts
        
        if parts[0] == "unit":
            return "unit"
        elif parts[0] == "integration":
            return "integration"
        elif parts[0] == "interactive_server":
            return "server"
        elif "performance" in str(rel_path) or "stress" in str(rel_path):
            return "performance"
        elif "demo" in str(rel_path) or "example" in str(rel_path):
            return "demo"
        elif parts[0] == "debugging-tools":
            return "tools"
        elif rel_path.name.startswith("test_"):
            # Test file in root tests directory
            return "uncategorized"
        else:
            return "other"
            
    def _infer_target_module(self, filename: str, rel_path: Path) -> Optional[str]:
        """Infer the target module from test filename."""
        if not filename.startswith("test_"):
            return None
            
        # Remove test_ prefix and .py suffix
        base_name = filename[5:-3]
        
        # Handle special cases
        if "integration" in str(rel_path) or "e2e" in str(rel_path):
            return "integration"
        elif "server" in str(rel_path) or "websocket" in str(rel_path) or "jsonrpc" in str(rel_path):
            return "interactive_server"
        elif "batch" in base_name:
            return "ai_whisperer.batch"
        elif "agent" in base_name:
            return "ai_whisperer.agents"
        elif "tool" in base_name and "calling" not in base_name:
            return "ai_whisperer.tools"
        elif "ai_service" in base_name or "openrouter" in base_name:
            return "ai_whisperer.ai_service"
        elif "ai_loop" in base_name or "ailoop" in base_name:
            return "ai_whisperer.ai_loop"
        elif "context" in base_name:
            return "ai_whisperer.context"
        elif "cli" in base_name or "command" in base_name:
            return "ai_whisperer.commands"
        elif "postprocessing" in base_name:
            return "postprocessing"
        elif "rfc" in base_name or "plan" in base_name:
            return "ai_whisperer.tools"  # RFC/Plan tools
        else:
            # Try to match with actual module names
            return f"ai_whisperer.{base_name}"
            
    def _scan_source_modules(self):
        """Scan source modules to check coverage."""
        for src_root in [self.src_dir, self.server_dir, self.postprocessing_dir]:
            if not src_root.exists():
                continue
                
            for root, dirs, files in os.walk(src_root):
                root_path = Path(root)
                
                # Skip test directories and __pycache__
                dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]
                
                for file in files:
                    if file.endswith('.py') and file != '__init__.py':
                        module_path = root_path / file
                        rel_path = module_path.relative_to(self.project_root)
                        
                        self.source_modules[rel_path] = ModuleCoverage(
                            module_path=rel_path
                        )
                        
    def _analyze_test_coverage(self):
        """Analyze which modules have test coverage."""
        for test_path, test_file in self.test_files.items():
            if test_file.target_module:
                # Find matching source modules
                for src_path, coverage in self.source_modules.items():
                    if test_file.target_module in str(src_path):
                        coverage.test_files.append(test_path)
                        coverage.has_coverage = True
                        
    def _identify_misplaced_tests(self):
        """Identify tests that are in the wrong directory."""
        for test_path, test_file in self.test_files.items():
            expected_category = None
            
            # Determine expected category based on content/name
            if "integration" in test_path.name or "e2e" in test_path.name:
                expected_category = "integration"
            elif any(x in test_path.name for x in ["jsonrpc", "websocket", "server", "session_manager"]):
                expected_category = "server"
            elif any(x in test_path.name for x in ["performance", "stress", "load"]):
                expected_category = "performance"
            elif test_path.name.startswith("test_") and test_file.target_module:
                # Most specific module tests should be unit tests
                if "integration" not in test_file.target_module:
                    expected_category = "unit"
                    
            if expected_category and expected_category != test_file.category:
                test_file.issues.append(
                    f"Misplaced: appears to be {expected_category} test but in {test_file.category}"
                )
                test_file.action = "move"
                
    def _identify_naming_issues(self):
        """Identify test files with naming issues."""
        for test_path, test_file in self.test_files.items():
            filename = test_path.name
            
            # Check if it's a Python file that should be a test
            if filename.endswith('.py') and filename != '__init__.py':
                if not filename.startswith('test_'):
                    if 'test' in filename.lower() or 'demo' not in filename.lower():
                        test_file.issues.append(f"Naming: should start with 'test_'")
                        test_file.action = "rename" if test_file.action == "keep" else test_file.action
                        
            # Check for backup files
            if filename.endswith('.bak'):
                test_file.issues.append("Backup file should be removed")
                test_file.action = "delete"
                
            # Check for skip files
            if filename.endswith('.skip'):
                test_file.issues.append("Skip file should be reviewed")
                test_file.action = "review"
                
    def _identify_demo_files(self):
        """Identify demo/example files mixed with tests."""
        demo_keywords = ['demo', 'example', 'practical', 'sample', 'debug']
        
        for test_path, test_file in self.test_files.items():
            filename = test_path.name.lower()
            
            if any(keyword in filename for keyword in demo_keywords):
                test_file.issues.append("Demo/example file mixed with tests")
                test_file.category = "demo"
                test_file.action = "move"
                
    def _create_reorganization_plan(self):
        """Create the reorganization plan for each test file."""
        for test_path, test_file in self.test_files.items():
            if test_file.action == "keep":
                continue
                
            # Determine new path based on issues
            if test_file.action == "move":
                new_dir = self._get_proper_directory(test_file)
                new_name = test_path.name
                
                # Fix naming if needed
                if not new_name.startswith('test_') and test_file.category != "demo":
                    new_name = f"test_{new_name}"
                    
                test_file.proposed_path = new_dir / new_name
                
            elif test_file.action == "rename":
                new_name = test_path.name
                if not new_name.startswith('test_'):
                    new_name = f"test_{new_name}"
                test_file.proposed_path = test_path.parent / new_name
                
    def _get_proper_directory(self, test_file: TestFile) -> Path:
        """Get the proper directory for a test file."""
        base = Path("tests")
        
        if test_file.category == "demo":
            return base / "examples"
        elif test_file.category == "performance":
            return base / "performance"
        elif test_file.category == "server":
            return base / "interactive_server"
        elif test_file.category == "integration":
            return base / "integration"
        elif test_file.category == "unit":
            # Organize unit tests by module
            if test_file.target_module:
                if "batch" in test_file.target_module:
                    return base / "unit" / "batch"
                elif "agents" in test_file.target_module:
                    return base / "unit" / "agents"
                elif "tools" in test_file.target_module:
                    return base / "unit" / "tools"
                elif "ai_service" in test_file.target_module:
                    return base / "unit" / "ai_service"
                elif "ai_loop" in test_file.target_module:
                    return base / "unit" / "ai_loop"
                elif "context" in test_file.target_module:
                    return base / "unit" / "context"
                elif "commands" in test_file.target_module:
                    return base / "unit" / "commands"
                elif "postprocessing" in test_file.target_module:
                    return base / "unit" / "postprocessing"
            return base / "unit"
        else:
            return base / test_file.category
            
    def _print_current_structure(self):
        """Print analysis of current structure."""
        print("\n### Current Test Structure Analysis ###\n")
        
        # Count by category
        category_counts = defaultdict(int)
        for test_file in self.test_files.values():
            category_counts[test_file.category] += 1
            
        print("Test Distribution:")
        total = len(self.test_files)
        for category, count in sorted(category_counts.items()):
            percentage = (count / total) * 100
            print(f"  - {category}: {count} files ({percentage:.1f}%)")
            
        print(f"\nTotal test files: {total}")
        
        # Coverage analysis
        uncovered = [m for m in self.source_modules.values() if not m.has_coverage]
        print(f"\nSource modules without tests: {len(uncovered)}")
        print(f"Coverage gap: {(len(uncovered) / len(self.source_modules)) * 100:.1f}%")
        
    def _print_issues(self):
        """Print identified issues."""
        print("\n### Identified Issues ###\n")
        
        issue_counts = defaultdict(int)
        files_with_issues = []
        
        for test_path, test_file in self.test_files.items():
            if test_file.issues:
                files_with_issues.append((test_path, test_file))
                for issue in test_file.issues:
                    issue_type = issue.split(':')[0]
                    issue_counts[issue_type] += 1
                    
        print("Issue Summary:")
        for issue_type, count in sorted(issue_counts.items()):
            print(f"  - {issue_type}: {count} files")
            
        print(f"\nFiles with issues ({len(files_with_issues)}):")
        for test_path, test_file in sorted(files_with_issues)[:10]:  # Show first 10
            print(f"  - {test_path}:")
            for issue in test_file.issues:
                print(f"    • {issue}")
                
        if len(files_with_issues) > 10:
            print(f"  ... and {len(files_with_issues) - 10} more")
            
    def _print_proposed_structure(self):
        """Print proposed new structure."""
        print("\n### Proposed New Structure ###\n")
        
        print("""
tests/
├── unit/                    # Module-specific unit tests
│   ├── agents/             # Agent system tests
│   ├── ai_loop/            # AI loop tests
│   ├── ai_service/         # AI service tests
│   ├── batch/              # Batch mode tests
│   ├── commands/           # CLI command tests
│   ├── context/            # Context management tests
│   ├── postprocessing/     # Postprocessing tests
│   └── tools/              # Tool tests
├── integration/            # Integration tests
│   ├── batch_mode/         # Batch mode integration
│   ├── rfc_plan/           # RFC to Plan integration
│   └── session/            # Session integration
├── interactive_server/     # Server-specific tests
│   ├── websocket/          # WebSocket tests
│   ├── jsonrpc/            # JSON-RPC tests
│   └── handlers/           # Handler tests
├── performance/            # Performance & stress tests
├── examples/               # Demo files & examples
├── fixtures/               # Test fixtures & data
│   ├── projects/           # Sample projects
│   └── scripts/            # Test scripts
└── conftest.py            # Shared test configuration
        """)
        
    def _print_migration_plan(self):
        """Print the migration plan."""
        print("\n### Migration Plan ###\n")
        
        # Group actions
        moves = []
        renames = []
        deletes = []
        reviews = []
        
        for test_path, test_file in self.test_files.items():
            if test_file.action == "move" and test_file.proposed_path:
                moves.append((test_path, test_file.proposed_path))
            elif test_file.action == "rename" and test_file.proposed_path:
                renames.append((test_path, test_file.proposed_path))
            elif test_file.action == "delete":
                deletes.append(test_path)
            elif test_file.action == "review":
                reviews.append(test_path)
                
        print(f"Files to move ({len(moves)}):")
        for old, new in sorted(moves)[:10]:
            print(f"  {old} → {new}")
        if len(moves) > 10:
            print(f"  ... and {len(moves) - 10} more")
            
        print(f"\nFiles to rename ({len(renames)}):")
        for old, new in sorted(renames)[:5]:
            print(f"  {old} → {new}")
        if len(renames) > 5:
            print(f"  ... and {len(renames) - 5} more")
            
        print(f"\nFiles to delete ({len(deletes)}):")
        for path in sorted(deletes):
            print(f"  - {path}")
            
        print(f"\nFiles to review ({len(reviews)}):")
        for path in sorted(reviews):
            print(f"  - {path}")
            
    def _print_summary(self):
        """Print summary of improvements."""
        print("\n### Summary of Improvements ###\n")
        
        improvements = [
            "✓ Clear separation of unit, integration, and server tests",
            "✓ Unit tests organized by module for easier navigation",
            "✓ Demo/example files moved to dedicated directory",
            "✓ Performance tests isolated in their own directory",
            "✓ Consistent test file naming (test_*.py)",
            "✓ Removal of backup and obsolete files",
            "✓ Better test-to-source module mapping",
            "✓ Fixtures and test data centralized",
        ]
        
        for improvement in improvements:
            print(improvement)
            
        # Calculate metrics
        total_actions = sum(1 for t in self.test_files.values() if t.action != "keep")
        print(f"\nTotal files requiring action: {total_actions}")
        print(f"Percentage of tests well-organized: {((len(self.test_files) - total_actions) / len(self.test_files)) * 100:.1f}%")
        
        print("\n### Next Steps ###\n")
        print("1. Review the migration plan")
        print("2. Create migration script to automate moves/renames")
        print("3. Update test imports after reorganization")
        print("4. Update CI/CD configurations")
        print("5. Update documentation with new structure")
        print("6. Add __init__.py files to new directories")
        
    def export_plan(self, output_file: Path):
        """Export the reorganization plan to a JSON file."""
        plan = {
            "summary": {
                "total_test_files": len(self.test_files),
                "files_to_move": sum(1 for t in self.test_files.values() if t.action == "move"),
                "files_to_rename": sum(1 for t in self.test_files.values() if t.action == "rename"),
                "files_to_delete": sum(1 for t in self.test_files.values() if t.action == "delete"),
                "files_to_review": sum(1 for t in self.test_files.values() if t.action == "review"),
            },
            "actions": []
        }
        
        for test_path, test_file in self.test_files.items():
            if test_file.action != "keep":
                plan["actions"].append({
                    "current_path": str(test_path),
                    "action": test_file.action,
                    "proposed_path": str(test_file.proposed_path) if test_file.proposed_path else None,
                    "issues": test_file.issues,
                    "category": test_file.category,
                    "target_module": test_file.target_module
                })
                
        with open(output_file, 'w') as f:
            json.dump(plan, f, indent=2)
            
        print(f"\nReorganization plan exported to: {output_file}")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    reorganizer = TestReorganizer(project_root)
    
    reorganizer.analyze()
    
    # Export plan for automation
    output_file = project_root / "test_reorganization_plan.json"
    reorganizer.export_plan(output_file)


if __name__ == "__main__":
    main()