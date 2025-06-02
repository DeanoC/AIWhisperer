#!/usr/bin/env python3
"""
Test Coverage Baseline Generator

This tool analyzes the current test coverage situation and generates a baseline
report to guide Phase 2 test coverage improvements. It identifies:
1. Modules without any tests
2. Critical modules needing immediate attention
3. Test coverage estimates for existing tests

Part of the AIWhisperer refactor Phase 2: Test Coverage Improvements
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import argparse


@dataclass
class TestCoverageInfo:
    """Information about test coverage for a module."""
    module_path: str
    has_tests: bool
    test_files: List[str]
    complexity_score: int
    priority_level: str  # 'critical', 'high', 'medium', 'low'
    reason: str


@dataclass
class CoverageReport:
    """Complete test coverage analysis report."""
    total_modules: int
    tested_modules: int
    critical_untested: List[TestCoverageInfo]
    high_priority_untested: List[TestCoverageInfo]
    coverage_by_system: Dict[str, float]


class TestCoverageAnalyzer:
    """Analyzes test coverage across the codebase."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.source_dirs = [
            "ai_whisperer",
            "interactive_server", 
            "postprocessing"
        ]
        
        # Critical modules that must have tests
        self.critical_modules = {
            'ai_whisperer/config.py': 'Configuration management - core system dependency',
            'ai_whisperer/json_validator.py': 'Schema validation - data integrity critical',
            'ai_whisperer/ai_loop/stateless_ai_loop.py': 'AI interaction core - business logic critical',
            'ai_whisperer/agents/base_handler.py': 'Agent system foundation - architecture critical',
            'ai_whisperer/tools/base_tool.py': 'Tool system foundation - architecture critical',
            'ai_whisperer/tools/tool_registry.py': 'Tool management - system coordination critical',
            'interactive_server/stateless_session_manager.py': 'Session management - user experience critical',
            'ai_whisperer/batch/server_manager.py': 'Batch processing - workflow critical',
            'ai_whisperer/path_management.py': 'Path resolution - file operations critical',
            'ai_whisperer/exceptions.py': 'Error handling - system stability critical',
            'ai_whisperer/utils.py': 'Core utilities - system foundation'
        }
        
        # High priority modules
        self.high_priority_modules = {
            'ai_whisperer/ai_loop/tool_call_accumulator.py': 'AI interaction coordination',
            'ai_whisperer/agents/factory.py': 'Agent creation and management',
            'ai_whisperer/agents/registry.py': 'Agent registration system',
            'ai_whisperer/context/context_manager.py': 'Context tracking system',
            'ai_whisperer/tools/execute_command_tool.py': 'Command execution - security critical',
            'ai_whisperer/tools/read_file_tool.py': 'File operations - frequently used',
            'ai_whisperer/tools/write_file_tool.py': 'File operations - data persistence',
            'interactive_server/handlers/workspace_handler.py': 'Workspace management',
            'postprocessing/pipeline.py': 'Content processing pipeline'
        }
    
    def find_all_python_modules(self) -> List[Path]:
        """Find all Python modules in source directories."""
        modules = []
        
        for source_dir in self.source_dirs:
            source_path = self.project_root / source_dir
            if source_path.exists():
                for py_file in source_path.rglob("*.py"):
                    if "__pycache__" not in str(py_file):
                        modules.append(py_file)
        
        return modules
    
    def find_test_files(self) -> Dict[str, List[str]]:
        """Find all test files and create mapping to tested modules."""
        test_to_modules = {}
        tests_dir = self.project_root / "tests"
        
        if not tests_dir.exists():
            return {}
        
        for test_file in tests_dir.rglob("test_*.py"):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse imports to find tested modules
                tree = ast.parse(content)
                tested_modules = []
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name.startswith(('ai_whisperer', 'interactive_server', 'postprocessing')):
                                    tested_modules.append(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            if node.module.startswith(('ai_whisperer', 'interactive_server', 'postprocessing')):
                                tested_modules.append(node.module)
                
                test_to_modules[str(test_file.relative_to(self.project_root))] = tested_modules
                
            except Exception as e:
                print(f"Warning: Could not analyze test file {test_file}: {e}")
        
        return test_to_modules
    
    def calculate_complexity_score(self, module_path: Path) -> int:
        """Calculate a complexity score for a module (0-10)."""
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Count complexity indicators
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
            conditionals = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.If, ast.While, ast.For)))
            try_except = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Try))
            
            # Simple complexity score
            score = min(10, (classes * 2) + functions + (conditionals * 0.5) + (try_except * 0.5))
            return int(score)
            
        except Exception:
            return 5  # Default medium complexity
    
    def determine_priority(self, module_rel_path: str, has_tests: bool, complexity: int) -> Tuple[str, str]:
        """Determine priority level and reason for a module."""
        if module_rel_path in self.critical_modules:
            if not has_tests:
                return 'critical', self.critical_modules[module_rel_path]
            else:
                return 'high', f"Critical module with existing tests - needs verification"
        
        if module_rel_path in self.high_priority_modules:
            if not has_tests:
                return 'high', self.high_priority_modules[module_rel_path]
            else:
                return 'medium', f"High priority module with existing tests"
        
        # Determine priority based on complexity and location
        if not has_tests:
            if complexity >= 7:
                return 'high', f"Complex module (score: {complexity}) without tests"
            elif complexity >= 4:
                return 'medium', f"Moderate complexity (score: {complexity}) without tests"
            else:
                return 'low', f"Simple module (score: {complexity}) without tests"
        else:
            return 'low', "Has existing test coverage"
    
    def analyze_coverage(self) -> CoverageReport:
        """Perform comprehensive test coverage analysis."""
        print("🔍 Analyzing test coverage across the codebase...")
        
        modules = self.find_all_python_modules()
        test_mapping = self.find_test_files()
        
        # Build reverse mapping: module -> test files
        module_to_tests = {}
        for test_file, tested_modules in test_mapping.items():
            for module in tested_modules:
                if module not in module_to_tests:
                    module_to_tests[module] = []
                module_to_tests[module].append(test_file)
        
        # Analyze each module
        coverage_info = []
        critical_untested = []
        high_priority_untested = []
        
        for module_path in modules:
            rel_path = str(module_path.relative_to(self.project_root))
            module_name = rel_path.replace('/', '.').replace('.py', '')
            
            # Check if module has tests
            has_tests = (
                module_name in module_to_tests or
                any(rel_path in tested for tested in test_mapping.values()) or
                any(module_path.stem in test_file for test_file in test_mapping.keys())
            )
            
            test_files = module_to_tests.get(module_name, [])
            complexity = self.calculate_complexity_score(module_path)
            priority, reason = self.determine_priority(rel_path, has_tests, complexity)
            
            info = TestCoverageInfo(
                module_path=rel_path,
                has_tests=has_tests,
                test_files=test_files,
                complexity_score=complexity,
                priority_level=priority,
                reason=reason
            )
            
            coverage_info.append(info)
            
            if not has_tests:
                if priority == 'critical':
                    critical_untested.append(info)
                elif priority == 'high':
                    high_priority_untested.append(info)
        
        # Calculate system-level coverage
        coverage_by_system = {}
        for system in self.source_dirs:
            system_modules = [info for info in coverage_info if info.module_path.startswith(system)]
            if system_modules:
                tested = sum(1 for info in system_modules if info.has_tests)
                coverage_by_system[system] = (tested / len(system_modules)) * 100
        
        total_modules = len(coverage_info)
        tested_modules = sum(1 for info in coverage_info if info.has_tests)
        
        return CoverageReport(
            total_modules=total_modules,
            tested_modules=tested_modules,
            critical_untested=critical_untested,
            high_priority_untested=high_priority_untested,
            coverage_by_system=coverage_by_system
        )
    
    def generate_report(self, report: CoverageReport, output_path: Path):
        """Generate a comprehensive test coverage baseline report."""
        with open(output_path, 'w') as f:
            f.write("# Test Coverage Baseline Report\n\n")
            f.write(f"Generated: {Path.cwd()}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Python modules**: {report.total_modules}\n")
            f.write(f"- **Modules with tests**: {report.tested_modules}\n")
            f.write(f"- **Overall coverage**: {(report.tested_modules/report.total_modules)*100:.1f}%\n")
            f.write(f"- **Critical untested modules**: {len(report.critical_untested)}\n")
            f.write(f"- **High priority untested**: {len(report.high_priority_untested)}\n\n")
            
            # System breakdown
            f.write("## Coverage by System\n\n")
            for system, coverage in sorted(report.coverage_by_system.items()):
                status = "🟢" if coverage > 70 else "🟡" if coverage > 40 else "🔴"
                f.write(f"- **{system}**: {status} {coverage:.1f}%\n")
            f.write("\n")
            
            # Critical untested modules
            if report.critical_untested:
                f.write("## 🔴 CRITICAL: Untested Modules (Immediate Action Required)\n\n")
                for info in sorted(report.critical_untested, key=lambda x: x.complexity_score, reverse=True):
                    f.write(f"### `{info.module_path}`\n")
                    f.write(f"- **Complexity**: {info.complexity_score}/10\n")
                    f.write(f"- **Reason**: {info.reason}\n")
                    f.write(f"- **Action**: Write comprehensive tests immediately\n\n")
            
            # High priority untested
            if report.high_priority_untested:
                f.write("## 🟡 HIGH PRIORITY: Untested Modules\n\n")
                for info in sorted(report.high_priority_untested, key=lambda x: x.complexity_score, reverse=True):
                    f.write(f"### `{info.module_path}`\n")
                    f.write(f"- **Complexity**: {info.complexity_score}/10\n")
                    f.write(f"- **Reason**: {info.reason}\n")
                    f.write(f"- **Action**: Add tests in Phase 2\n\n")
            
            # Recommendations
            f.write("## 📋 Phase 2 Testing Recommendations\n\n")
            f.write("### Week 1: Critical Infrastructure\n")
            f.write("Focus on the critical untested modules above. These are essential for system stability.\n\n")
            
            f.write("### Week 2: High Priority Modules\n")
            f.write("Address high priority untested modules and improve existing test coverage.\n\n")
            
            f.write("### Week 3: Integration and Edge Cases\n")
            f.write("Add integration tests and improve coverage of edge cases.\n\n")
            
            # Test creation priorities
            critical_count = len(report.critical_untested)
            high_count = len(report.high_priority_untested)
            
            f.write("## 🎯 Immediate Actions\n\n")
            f.write(f"1. **Create {critical_count} critical module tests** (estimated 2-3 days)\n")
            f.write(f"2. **Create {high_count} high priority tests** (estimated 3-4 days)\n")
            f.write("3. **Run coverage analysis** to measure improvement\n")
            f.write("4. **Focus on integration tests** for end-to-end workflows\n\n")
            
            f.write("## Success Metrics\n\n")
            current_coverage = (report.tested_modules/report.total_modules)*100
            target_coverage = min(90, current_coverage + 30)
            f.write(f"- **Target overall coverage**: {target_coverage:.0f}% (from {current_coverage:.1f}%)\n")
            f.write("- **All critical modules**: 100% test coverage\n")
            f.write("- **High priority modules**: 80% test coverage\n")
            f.write("- **Integration test suite**: Comprehensive workflow coverage\n")


def main():
    parser = argparse.ArgumentParser(description="Generate test coverage baseline report")
    parser.add_argument("--project-root", type=Path, default=Path("."),
                       help="Project root directory (default: current directory)")
    parser.add_argument("--output", type=Path, default=Path("test_coverage_baseline.md"),
                       help="Output report file")
    
    args = parser.parse_args()
    
    analyzer = TestCoverageAnalyzer(args.project_root)
    report = analyzer.analyze_coverage()
    
    print(f"\n📊 Coverage Analysis Complete!")
    print(f"📈 Overall coverage: {(report.tested_modules/report.total_modules)*100:.1f}%")
    print(f"🔴 Critical untested: {len(report.critical_untested)}")
    print(f"🟡 High priority untested: {len(report.high_priority_untested)}")
    
    analyzer.generate_report(report, args.output)
    print(f"📄 Report saved to: {args.output}")


if __name__ == "__main__":
    main()