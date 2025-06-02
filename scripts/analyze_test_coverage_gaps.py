#!/usr/bin/env python3
"""
Analyze test coverage gaps in AIWhisperer.

This script identifies which source modules lack test coverage
and provides recommendations for test creation.
"""

import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class TestCoverageAnalyzer:
    """Analyze test coverage gaps."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        
        # Source directories to analyze
        self.source_dirs = {
            "ai_whisperer": project_root / "ai_whisperer",
            "interactive_server": project_root / "interactive_server",
            "postprocessing": project_root / "postprocessing",
        }
        
        self.test_files: Set[str] = set()
        self.source_modules: Dict[str, Path] = {}
        self.coverage_map: Dict[str, List[str]] = defaultdict(list)
        
    def analyze(self):
        """Run the coverage analysis."""
        print("Analyzing Test Coverage Gaps in AIWhisperer")
        print("=" * 80)
        
        self._scan_test_files()
        self._scan_source_modules()
        self._map_test_coverage()
        self._print_coverage_report()
        self._print_recommendations()
        
    def _scan_test_files(self):
        """Scan all test files."""
        for root, dirs, files in os.walk(self.tests_dir):
            # Skip __pycache__ and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    # Extract the module name from test file
                    module_name = file[5:-3]  # Remove 'test_' and '.py'
                    self.test_files.add(module_name)
                    
    def _scan_source_modules(self):
        """Scan all source modules."""
        for source_name, source_dir in self.source_dirs.items():
            if not source_dir.exists():
                continue
                
            for root, dirs, files in os.walk(source_dir):
                root_path = Path(root)
                
                # Skip test directories and __pycache__
                dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]
                
                for file in files:
                    if file.endswith('.py') and file != '__init__.py':
                        module_path = root_path / file
                        
                        # Create module identifier
                        rel_path = module_path.relative_to(source_dir)
                        module_parts = list(rel_path.parts[:-1]) + [file[:-3]]
                        module_id = '.'.join([source_name] + module_parts)
                        
                        self.source_modules[module_id] = module_path
                        
    def _map_test_coverage(self):
        """Map test files to source modules."""
        for test_name in self.test_files:
            # Try direct mapping
            for module_id in self.source_modules:
                module_base = module_id.split('.')[-1]
                
                # Direct match
                if test_name == module_base:
                    self.coverage_map[module_id].append(f"test_{test_name}")
                # Partial match (e.g., test_agent_* for agent.py)
                elif test_name.startswith(module_base + "_"):
                    self.coverage_map[module_id].append(f"test_{test_name}")
                # Handle special cases
                elif module_base in test_name:
                    self.coverage_map[module_id].append(f"test_{test_name}")
                    
    def _print_coverage_report(self):
        """Print the coverage report."""
        covered_modules = set(self.coverage_map.keys())
        uncovered_modules = set(self.source_modules.keys()) - covered_modules
        
        total_modules = len(self.source_modules)
        covered_count = len(covered_modules)
        uncovered_count = len(uncovered_modules)
        
        print(f"\n### Coverage Summary ###\n")
        print(f"Total source modules: {total_modules}")
        print(f"Modules with tests: {covered_count} ({covered_count/total_modules*100:.1f}%)")
        print(f"Modules without tests: {uncovered_count} ({uncovered_count/total_modules*100:.1f}%)")
        
        # Group uncovered modules by directory
        uncovered_by_dir = defaultdict(list)
        for module_id in sorted(uncovered_modules):
            parts = module_id.split('.')
            if len(parts) > 2:
                dir_name = '.'.join(parts[:2])
            else:
                dir_name = parts[0]
            uncovered_by_dir[dir_name].append(module_id)
            
        print(f"\n### Modules Without Test Coverage ###\n")
        
        # Priority modules (core functionality)
        priority_keywords = ['handler', 'manager', 'service', 'processor', 'validator', 'factory']
        priority_modules = []
        
        for dir_name, modules in sorted(uncovered_by_dir.items()):
            print(f"\n{dir_name}:")
            for module_id in sorted(modules):
                module_name = module_id.split('.')[-1]
                
                # Check if it's a priority module
                is_priority = any(keyword in module_name.lower() for keyword in priority_keywords)
                if is_priority:
                    priority_modules.append(module_id)
                    
                priority_marker = " [PRIORITY]" if is_priority else ""
                print(f"  - {module_id}{priority_marker}")
                
        print(f"\n### Priority Modules to Test ({len(priority_modules)}) ###\n")
        for module_id in sorted(priority_modules):
            print(f"  - {module_id}")
            
        # Show well-tested modules
        print(f"\n### Well-Tested Modules ###\n")
        well_tested = [(m, len(tests)) for m, tests in self.coverage_map.items() if len(tests) > 2]
        for module_id, test_count in sorted(well_tested, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {module_id}: {test_count} test files")
            
    def _print_recommendations(self):
        """Print recommendations for improving test coverage."""
        print(f"\n### Recommendations ###\n")
        
        recommendations = [
            "1. **Focus on Priority Modules**: Start with modules containing core functionality",
            "   (handlers, managers, services, processors, validators, factories)",
            "",
            "2. **Test Organization**: Follow the proposed structure:",
            "   - Unit tests: tests/unit/<module>/ for isolated component testing",
            "   - Integration tests: tests/integration/ for cross-component testing",
            "   - Performance tests: tests/performance/ for load and stress testing",
            "",
            "3. **Testing Strategy**:",
            "   - Aim for 80%+ code coverage on critical modules",
            "   - Write tests before fixing bugs (TDD approach)",
            "   - Include both positive and negative test cases",
            "   - Test edge cases and error conditions",
            "",
            "4. **Quick Wins**:",
            "   - Add tests for simple utility modules first",
            "   - Test configuration and validation modules",
            "   - Cover data models and DTOs",
            "",
            "5. **Integration Testing**:",
            "   - Test agent interactions end-to-end",
            "   - Verify batch mode workflows",
            "   - Test WebSocket communication flows",
            "   - Validate RFC to Plan conversions",
        ]
        
        for rec in recommendations:
            print(rec)
            
        print(f"\n### Test Creation Priority List ###\n")
        
        # Categorize uncovered modules
        categories = {
            "Critical Infrastructure": ["manager", "handler", "service", "processor"],
            "Tools & Utilities": ["tool", "validator", "converter", "parser"],
            "Data & Models": ["model", "schema", "dto"],
            "Integration Points": ["adapter", "client", "api"],
        }
        
        uncovered_modules = set(self.source_modules.keys()) - set(self.coverage_map.keys())
        
        for category, keywords in categories.items():
            matching_modules = []
            for module_id in uncovered_modules:
                module_name = module_id.split('.')[-1].lower()
                if any(keyword in module_name for keyword in keywords):
                    matching_modules.append(module_id)
                    
            if matching_modules:
                print(f"\n{category}:")
                for module_id in sorted(matching_modules)[:5]:
                    print(f"  - Create test_{module_id.split('.')[-1]}.py for {module_id}")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    analyzer = TestCoverageAnalyzer(project_root)
    analyzer.analyze()


if __name__ == "__main__":
    main()