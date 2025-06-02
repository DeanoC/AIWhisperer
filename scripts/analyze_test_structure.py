#!/usr/bin/env python3
"""Analyze test structure and coverage for refactoring documentation."""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set
import json

class TestAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.test_info = {}
        self.code_to_test_map = {}
        self.errors = []

    def analyze_test_file(self, file_path: Path) -> Dict:
        """Analyze a single test file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract test info
            test_info = {
                'path': str(file_path.relative_to(self.root_path)),
                'test_classes': [],
                'test_functions': [],
                'imports': [],
                'tested_modules': set(),
                'fixtures_used': set(),
                'size': len(content.splitlines()),
                'markers': set(),
                'test_type': self._determine_test_type(file_path, content)
            }
            
            # Parse AST
            tree = ast.parse(content)
            
            # Find imports to determine what's being tested
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        test_info['imports'].append(alias.name)
                        if 'ai_whisperer' in alias.name:
                            test_info['tested_modules'].add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and 'ai_whisperer' in node.module:
                        test_info['tested_modules'].add(node.module)
                        test_info['imports'].append(node.module)
                
                elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                    test_methods = [m.name for m in node.body 
                                  if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]
                    test_info['test_classes'].append({
                        'name': node.name,
                        'methods': test_methods,
                        'count': len(test_methods)
                    })
                
                elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    # Top-level test functions
                    if node.col_offset == 0:
                        test_info['test_functions'].append(node.name)
            
            # Find pytest markers
            marker_pattern = r'@pytest\.mark\.(\w+)'
            markers = re.findall(marker_pattern, content)
            test_info['markers'] = set(markers)
            
            # Find fixtures
            fixture_pattern = r'def\s+test_\w+\([^)]*\b(\w+)\b[^)]*\):'
            fixtures = re.findall(fixture_pattern, content)
            test_info['fixtures_used'] = set(fixtures) - {'self'}
            
            # Convert sets to lists for JSON serialization
            test_info['tested_modules'] = list(test_info['tested_modules'])
            test_info['markers'] = list(test_info['markers'])
            test_info['fixtures_used'] = list(test_info['fixtures_used'])
            
            return test_info
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            return None

    def _determine_test_type(self, file_path: Path, content: str) -> str:
        """Determine the type of test based on path and content."""
        path_str = str(file_path)
        
        if 'unit' in path_str:
            return 'unit'
        elif 'integration' in path_str:
            return 'integration'
        elif 'interactive_server' in path_str:
            return 'server'
        elif 'performance' in content or '@pytest.mark.performance' in content:
            return 'performance'
        elif 'e2e' in path_str or 'end_to_end' in content:
            return 'e2e'
        else:
            return 'other'

    def analyze_all_tests(self) -> Dict:
        """Analyze all test files in the project."""
        results = {
            'tests': [],
            'summary': {
                'total_files': 0,
                'total_test_classes': 0,
                'total_test_methods': 0,
                'total_test_functions': 0,
                'by_type': {},
                'by_marker': {},
                'tested_modules': set()
            }
        }
        
        # Find all test files
        test_pattern = '**/test_*.py'
        for test_file in self.root_path.glob(test_pattern):
            # Skip node_modules and venv
            if any(part in str(test_file) for part in ['node_modules', 'venv', '.venv', '__pycache__']):
                continue
            
            test_info = self.analyze_test_file(test_file)
            if test_info:
                results['tests'].append(test_info)
                
                # Update summary
                results['summary']['total_files'] += 1
                results['summary']['total_test_classes'] += len(test_info['test_classes'])
                results['summary']['total_test_functions'] += len(test_info['test_functions'])
                
                # Count test methods
                for test_class in test_info['test_classes']:
                    results['summary']['total_test_methods'] += test_class['count']
                
                # Track test types
                test_type = test_info['test_type']
                if test_type not in results['summary']['by_type']:
                    results['summary']['by_type'][test_type] = 0
                results['summary']['by_type'][test_type] += 1
                
                # Track markers
                for marker in test_info['markers']:
                    if marker not in results['summary']['by_marker']:
                        results['summary']['by_marker'][marker] = 0
                    results['summary']['by_marker'][marker] += 1
                
                # Track tested modules
                results['summary']['tested_modules'].update(test_info['tested_modules'])
        
        # Convert set to list for JSON
        results['summary']['tested_modules'] = sorted(list(results['summary']['tested_modules']))
        
        return results

    def find_untested_modules(self, code_map: Dict) -> List[str]:
        """Find modules that don't have corresponding tests."""
        tested_modules = set()
        for test in self.test_info.get('tests', []):
            tested_modules.update(test.get('tested_modules', []))
        
        all_modules = set()
        # Extract module paths from code map
        # This would need the code map from the previous analysis
        
        return sorted(list(all_modules - tested_modules))

    def generate_report(self, output_dir: Path):
        """Generate comprehensive test analysis reports."""
        output_dir.mkdir(exist_ok=True)
        
        # Analyze all tests
        test_analysis = self.analyze_all_tests()
        
        # Save detailed test map
        with open(output_dir / 'test_map.json', 'w') as f:
            json.dump(test_analysis, f, indent=2)
        
        # Generate markdown report
        self.generate_markdown_report(test_analysis, output_dir / 'test_map.md')
        
        # Generate test coverage report
        self.generate_coverage_report(test_analysis, output_dir / 'test_coverage.md')
        
        return test_analysis

    def generate_markdown_report(self, analysis: Dict, output_path: Path):
        """Generate a markdown report from test analysis."""
        with open(output_path, 'w') as f:
            f.write("# AIWhisperer Test Map\n\n")
            f.write("## Summary\n")
            summary = analysis['summary']
            f.write(f"- Total Test Files: {summary['total_files']}\n")
            f.write(f"- Total Test Classes: {summary['total_test_classes']}\n")
            f.write(f"- Total Test Methods: {summary['total_test_methods']}\n")
            f.write(f"- Total Test Functions: {summary['total_test_functions']}\n")
            f.write(f"- Total Tests: {summary['total_test_methods'] + summary['total_test_functions']}\n\n")
            
            f.write("### Tests by Type\n")
            for test_type, count in sorted(summary['by_type'].items()):
                f.write(f"- {test_type}: {count} files\n")
            
            if summary['by_marker']:
                f.write("\n### Tests by Marker\n")
                for marker, count in sorted(summary['by_marker'].items()):
                    f.write(f"- @pytest.mark.{marker}: {count} files\n")
            
            f.write("\n## Test Details\n\n")
            
            # Group by directory
            tests_by_dir = {}
            for test in analysis['tests']:
                dir_name = os.path.dirname(test['path'])
                if dir_name not in tests_by_dir:
                    tests_by_dir[dir_name] = []
                tests_by_dir[dir_name].append(test)
            
            # Write by directory
            for dir_name in sorted(tests_by_dir.keys()):
                f.write(f"### {dir_name or 'root'}\n\n")
                for test in sorted(tests_by_dir[dir_name], key=lambda x: x['path']):
                    f.write(f"#### `{test['path']}`\n")
                    f.write(f"- Type: {test['test_type']}\n")
                    f.write(f"- Size: {test['size']} lines\n")
                    
                    if test['test_classes']:
                        f.write("- Test Classes:\n")
                        for cls in test['test_classes']:
                            f.write(f"  - `{cls['name']}`: {cls['count']} tests\n")
                    
                    if test['test_functions']:
                        f.write(f"- Test Functions: {len(test['test_functions'])}\n")
                    
                    if test['tested_modules']:
                        f.write("- Tests modules:\n")
                        for module in sorted(test['tested_modules']):
                            f.write(f"  - `{module}`\n")
                    
                    if test['markers']:
                        f.write(f"- Markers: {', '.join(f'@{m}' for m in test['markers'])}\n")
                    
                    f.write("\n")

    def generate_coverage_report(self, analysis: Dict, output_path: Path):
        """Generate a test coverage report."""
        with open(output_path, 'w') as f:
            f.write("# Test Coverage Analysis\n\n")
            f.write("## Tested Modules\n\n")
            
            tested_modules = sorted(analysis['summary']['tested_modules'])
            for module in tested_modules:
                # Find which tests cover this module
                covering_tests = []
                for test in analysis['tests']:
                    if module in test['tested_modules']:
                        covering_tests.append(test['path'])
                
                f.write(f"### `{module}`\n")
                f.write(f"Covered by {len(covering_tests)} test file(s):\n")
                for test_path in covering_tests[:5]:  # Show first 5
                    f.write(f"- {test_path}\n")
                if len(covering_tests) > 5:
                    f.write(f"- ... and {len(covering_tests) - 5} more\n")
                f.write("\n")

if __name__ == "__main__":
    analyzer = TestAnalyzer(Path.cwd())
    analyzer.generate_report(Path("refactor_analysis"))
    
    # Also check for some common test issues
    print("\nChecking for test issues...")
    
    # Find test files not following naming convention
    non_standard = list(Path("tests").rglob("*.py"))
    non_standard = [f for f in non_standard if f.name != "__init__.py" and not f.name.startswith("test_") and "conftest" not in f.name]
    if non_standard:
        print(f"\nFound {len(non_standard)} test files not following test_* naming:")
        for f in non_standard[:5]:
            print(f"  - {f}")
    
    print("\nAnalysis complete! Check refactor_analysis/ directory for results.")