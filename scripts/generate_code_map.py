#!/usr/bin/env python3
"""
Hierarchical Code Map Generator

This tool creates navigable code structure maps for LLMs to efficiently
explore the codebase. It generates a root CODE_MAP.md and directory-level
code_map.md files with test coverage and cross-references.

Part of the AIWhisperer refactor Phase 0: Documentation Modernization
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import argparse


@dataclass
class DirectoryInfo:
    """Information about a directory in the codebase."""
    path: str
    purpose: str
    key_files: List[str]
    test_files: List[str]
    test_coverage_percent: Optional[float]
    sub_directories: List[str]
    related_docs: List[str]


class CodeMapGenerator:
    """Generates hierarchical navigation maps for the codebase."""
    
    def __init__(self, project_root: Path, mapping_data_path: Path = None):
        self.project_root = project_root
        self.mapping_data = None
        
        if mapping_data_path and mapping_data_path.exists():
            with open(mapping_data_path, 'r') as f:
                self.mapping_data = json.load(f)
        
        # Directory purposes based on common patterns
        self.directory_purposes = {
            'ai_whisperer': 'Core application logic and AI interaction components',
            'ai_whisperer/agents': 'Modular agent handlers with specialized capabilities',
            'ai_whisperer/ai_loop': 'AI model interaction and response streaming management',
            'ai_whisperer/tools': 'Pluggable tools for file operations and command execution',
            'ai_whisperer/context': 'Context tracking and management system',
            'ai_whisperer/batch': 'Batch processing and server management',
            'ai_whisperer/logging': 'Logging and monitoring infrastructure',
            'ai_whisperer/commands': 'CLI command implementations',
            'interactive_server': 'FastAPI server with WebSocket support for real-time communication',
            'interactive_server/handlers': 'WebSocket request handlers and routing',
            'interactive_server/services': 'Backend services for project and file management',
            'interactive_server/models': 'Data models and schemas for API communication',
            'frontend': 'React TypeScript application providing chat interface',
            'frontend/src/components': 'React UI components for the chat interface',
            'frontend/src/services': 'Frontend services for API communication',
            'frontend/src/hooks': 'React hooks for state management and effects',
            'frontend/src/types': 'TypeScript type definitions',
            'postprocessing': 'Content processing pipeline for AI-generated output',
            'tests': 'Comprehensive test suite with unit, integration, and performance tests',
            'tests/unit': 'Unit tests organized by module',
            'tests/integration': 'Integration tests for end-to-end workflows',
            'tests/interactive_server': 'Tests for WebSocket and API functionality',
            'scripts': 'Automation and utility scripts for development',
            'config': 'Hierarchical configuration management',
            'docs': 'Project documentation and design specifications'
        }
    
    def analyze_directory(self, dir_path: Path) -> DirectoryInfo:
        """Analyze a directory and extract structural information."""
        rel_path = str(dir_path.relative_to(self.project_root))
        
        # Find Python files
        python_files = []
        if dir_path.exists():
            python_files = [f.name for f in dir_path.glob("*.py") if f.is_file()]
        
        # Find test files
        test_files = []
        test_dir = self.project_root / "tests"
        if test_dir.exists():
            # Look for tests that match this directory
            for test_file in test_dir.rglob("*.py"):
                test_name = test_file.stem
                if any(py_file.replace('.py', '') in test_name for py_file in python_files):
                    test_files.append(str(test_file.relative_to(self.project_root)))
        
        # Calculate test coverage estimate
        test_coverage = None
        if python_files:
            # Simple heuristic: percentage of files that have corresponding tests
            covered_files = 0
            for py_file in python_files:
                module_name = py_file.replace('.py', '')
                if any(module_name in test_file for test_file in test_files):
                    covered_files += 1
            test_coverage = (covered_files / len(python_files)) * 100
        
        # Find subdirectories
        sub_dirs = []
        if dir_path.exists():
            sub_dirs = [
                d.name for d in dir_path.iterdir() 
                if d.is_dir() and not d.name.startswith('.') and d.name != '__pycache__'
            ]
        
        # Get related documentation
        related_docs = []
        if self.mapping_data:
            code_coverage_map = self.mapping_data.get('code_coverage_map', {})
            for py_file in python_files:
                file_path = f"{rel_path}/{py_file}"
                if file_path in code_coverage_map:
                    related_docs.extend(code_coverage_map[file_path])
        
        # Remove duplicates and limit
        related_docs = list(set(related_docs))[:5]
        
        return DirectoryInfo(
            path=rel_path,
            purpose=self.directory_purposes.get(rel_path, self._infer_purpose(rel_path, python_files)),
            key_files=self._select_key_files(python_files),
            test_files=test_files,
            test_coverage_percent=test_coverage,
            sub_directories=sub_dirs,
            related_docs=related_docs
        )
    
    def _infer_purpose(self, rel_path: str, files: List[str]) -> str:
        """Infer the purpose of a directory from its path and files."""
        path_lower = rel_path.lower()
        
        if 'test' in path_lower:
            return "Test suite for functionality validation"
        elif 'config' in path_lower:
            return "Configuration files and settings"
        elif 'script' in path_lower:
            return "Utility scripts and automation tools"
        elif 'doc' in path_lower:
            return "Documentation and design specifications"
        elif 'frontend' in path_lower:
            return "Frontend application components"
        elif 'backend' in path_lower or 'server' in path_lower:
            return "Backend server implementation"
        elif any('handler' in f for f in files):
            return "Request and event handling functionality"
        elif any('tool' in f for f in files):
            return "Tool implementations and utilities"
        elif any('agent' in f for f in files):
            return "AI agent implementations"
        elif any('model' in f for f in files):
            return "Data models and schemas"
        else:
            return f"Implementation module for {Path(rel_path).name}"
    
    def _select_key_files(self, files: List[str]) -> List[str]:
        """Select the most important files to highlight."""
        if not files:
            return []
        
        # Prioritize certain file types
        key_files = []
        
        # Add main/init files first
        for f in files:
            if f in ['__init__.py', 'main.py', 'app.py', 'cli.py']:
                key_files.append(f)
        
        # Add base classes and important implementations
        for f in files:
            if any(keyword in f.lower() for keyword in ['base', 'main', 'core', 'manager', 'registry']):
                if f not in key_files:
                    key_files.append(f)
        
        # Fill remaining slots with other files
        remaining_slots = max(0, 5 - len(key_files))
        for f in files:
            if f not in key_files and remaining_slots > 0:
                key_files.append(f)
                remaining_slots -= 1
        
        return key_files
    
    def generate_root_code_map(self) -> str:
        """Generate the main CODE_MAP.md file."""
        lines = []
        
        lines.append("# AIWhisperer Code Map")
        lines.append("")
        lines.append("## Overview")
        lines.append("AIWhisperer is a Python CLI tool that uses AI models to automate software")
        lines.append("development planning and execution. This map provides efficient navigation")
        lines.append("for developers and AI assistants working with the codebase.")
        lines.append("")
        
        # Core Systems section
        lines.append("## Core Systems")
        lines.append("")
        
        core_systems = [
            ('ai_whisperer/ai_loop', 'AI Loop System'),
            ('ai_whisperer/agents', 'Agent System'), 
            ('ai_whisperer/tools', 'Tool System'),
            ('interactive_server', 'Interactive Backend'),
            ('frontend', 'Frontend Application')
        ]
        
        for dir_path, system_name in core_systems:
            dir_info = self.analyze_directory(self.project_root / dir_path)
            
            lines.append(f"### {system_name} (`{dir_path}/`)")
            lines.append(dir_info.purpose)
            
            if dir_info.key_files:
                lines.append(f"- **Key Files**: {', '.join(dir_info.key_files[:3])}")
            
            if dir_info.test_coverage_percent is not None:
                coverage_icon = "🟢" if dir_info.test_coverage_percent > 70 else "🟡" if dir_info.test_coverage_percent > 40 else "🔴"
                lines.append(f"- **Tests**: {coverage_icon} {dir_info.test_coverage_percent:.1f}% coverage")
            
            lines.append(f"- **Details**: [{dir_path}/code_map.md]({dir_path}/code_map.md)")
            lines.append("")
        
        # Supporting Systems section
        lines.append("## Supporting Systems")
        lines.append("")
        
        supporting_systems = [
            ('postprocessing', 'Content Processing'),
            ('config', 'Configuration'),
            ('tests', 'Test Suite'),
            ('scripts', 'Development Tools')
        ]
        
        for dir_path, system_name in supporting_systems:
            dir_info = self.analyze_directory(self.project_root / dir_path)
            
            lines.append(f"### {system_name} (`{dir_path}/`)")
            lines.append(dir_info.purpose)
            
            if dir_info.key_files:
                lines.append(f"- **Key Files**: {', '.join(dir_info.key_files[:2])}")
            lines.append("")
        
        # Quick Navigation section
        lines.append("## Quick Navigation")
        lines.append("")
        lines.append("### By Functionality")
        lines.append("- **AI Interaction**: `ai_whisperer/ai_loop/` → `ai_whisperer/agents/`")
        lines.append("- **Tool Development**: `ai_whisperer/tools/` → `docs/tool_interface_design.md`")
        lines.append("- **Web Interface**: `frontend/src/` → `interactive_server/`")
        lines.append("- **Configuration**: `config/` → `ai_whisperer/config.py`")
        lines.append("- **Testing**: `tests/unit/` → `tests/integration/`")
        lines.append("")
        
        lines.append("### By User Type")
        lines.append("- **New Developers**: Start with `README.md` → `docs/QUICK_START.md`")
        lines.append("- **AI Assistants**: This file → relevant subsystem code_map.md")
        lines.append("- **Tool Developers**: `docs/tool_interface_design.md` → `ai_whisperer/tools/`")
        lines.append("- **Agent Developers**: `docs/agent_context_tracking_design.md` → `ai_whisperer/agents/`")
        lines.append("")
        
        # Project Statistics
        if self.mapping_data:
            lines.append("## Project Statistics")
            lines.append(f"- **Total Code Files**: {self.mapping_data.get('code_files_found', 'Unknown')}")
            lines.append(f"- **Documentation Files**: {self.mapping_data.get('docs_analyzed', 'Unknown')}")
            lines.append(f"- **Code Documentation Coverage**: {len(self.mapping_data.get('code_coverage_map', {}))}/{self.mapping_data.get('code_files_found', 1) or 1} files")
            lines.append("")
        
        lines.append("## How to Use This Map")
        lines.append("1. **Start here** for system overview")
        lines.append("2. **Navigate to subsystem** via code_map.md links")
        lines.append("3. **Read file headers** for module understanding")
        lines.append("4. **Check related docs** for detailed design info")
        lines.append("5. **Follow cross-references** for related components")
        
        return '\n'.join(lines)
    
    def generate_directory_code_map(self, dir_path: Path) -> str:
        """Generate a code_map.md file for a specific directory."""
        dir_info = self.analyze_directory(dir_path)
        rel_path = str(dir_path.relative_to(self.project_root))
        
        lines = []
        
        # Header
        lines.append(f"# {Path(rel_path).name.title()} System Code Map")
        lines.append("")
        lines.append("## Overview")
        lines.append(dir_info.purpose)
        lines.append("")
        
        # Core Components
        if dir_info.key_files:
            lines.append("## Core Components")
            lines.append("")
            
            for file_name in dir_info.key_files:
                file_path = dir_path / file_name
                if file_path.exists():
                    purpose = self._get_file_purpose(file_path)
                    lines.append(f"### {file_name}")
                    lines.append(purpose)
                    
                    # Add test information
                    test_file = self._find_test_file(file_name, dir_info.test_files)
                    if test_file:
                        lines.append(f"- Tests: `{test_file}`")
                    else:
                        lines.append("- Tests: ⚠️ No tests found")
                    
                    lines.append("")
        
        # Subdirectories
        if dir_info.sub_directories:
            lines.append("## Subdirectories")
            lines.append("")
            
            for sub_dir in dir_info.sub_directories:
                sub_path = dir_path / sub_dir
                sub_info = self.analyze_directory(sub_path)
                
                lines.append(f"### {sub_dir}/")
                lines.append(sub_info.purpose)
                
                if sub_info.key_files:
                    lines.append(f"- **Key Files**: {', '.join(sub_info.key_files[:3])}")
                
                lines.append("")
        
        # Test Coverage
        if dir_info.test_coverage_percent is not None:
            lines.append("## Test Coverage")
            coverage = dir_info.test_coverage_percent
            status = "🟢 Good" if coverage > 70 else "🟡 Needs Improvement" if coverage > 40 else "🔴 Critical"
            lines.append(f"**Coverage**: {status} ({coverage:.1f}%)")
            
            if dir_info.test_files:
                lines.append("")
                lines.append("**Test Files**:")
                for test_file in dir_info.test_files[:5]:
                    lines.append(f"- `{test_file}`")
            lines.append("")
        
        # Related Documentation
        if dir_info.related_docs:
            lines.append("## Related Documentation")
            for doc in dir_info.related_docs:
                lines.append(f"- [{doc}](../../{doc})")
            lines.append("")
        
        # Navigation
        lines.append("## Navigation")
        lines.append(f"- **Parent**: [Project Root](../../CODE_MAP.md)")
        if dir_info.sub_directories:
            lines.append("- **Subdirectories**: " + ", ".join(f"`{d}/`" for d in dir_info.sub_directories))
        lines.append("")
        
        return '\n'.join(lines)
    
    def _get_file_purpose(self, file_path: Path) -> str:
        """Get a brief purpose description for a file."""
        file_name = file_path.name
        
        try:
            # Try to extract from file header or docstring
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for module docstring
            import ast
            tree = ast.parse(content)
            if (tree.body and 
                isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)):
                docstring = tree.body[0].value.value
                first_line = docstring.split('\n')[0].strip()
                if len(first_line) > 20:
                    return first_line
        except:
            pass
        
        # Fallback to filename-based inference
        if file_name == '__init__.py':
            return "Package initialization and exports"
        elif 'main' in file_name:
            return "Main application entry point"
        elif 'cli' in file_name:
            return "Command-line interface implementation"
        elif 'config' in file_name:
            return "Configuration management"
        elif 'tool' in file_name:
            return "AI tool implementation"
        elif 'handler' in file_name:
            return "Request/event handler implementation"
        elif 'manager' in file_name:
            return "Management and coordination logic"
        else:
            return f"Implementation for {file_name.replace('.py', '').replace('_', ' ')}"
    
    def _find_test_file(self, file_name: str, test_files: List[str]) -> Optional[str]:
        """Find the test file for a given source file."""
        module_name = file_name.replace('.py', '')
        for test_file in test_files:
            if module_name in test_file:
                return test_file
        return None
    
    def generate_all_maps(self, dry_run: bool = True) -> Dict[str, bool]:
        """Generate all code maps for the project."""
        results = {}
        
        # Generate root code map
        print("📊 Generating root CODE_MAP.md...")
        root_map = self.generate_root_code_map()
        root_path = self.project_root / "CODE_MAP.md"
        
        if not dry_run:
            with open(root_path, 'w', encoding='utf-8') as f:
                f.write(root_map)
            results["CODE_MAP.md"] = True
        else:
            print(f"  [DRY RUN] Would create CODE_MAP.md ({len(root_map.splitlines())} lines)")
            results["CODE_MAP.md"] = True
        
        # Generate directory-level maps
        directories_to_map = [
            'ai_whisperer',
            'ai_whisperer/agents',
            'ai_whisperer/ai_loop', 
            'ai_whisperer/tools',
            'interactive_server',
            'frontend/src',
            'postprocessing',
            'tests'
        ]
        
        for dir_path_str in directories_to_map:
            dir_path = self.project_root / dir_path_str
            if not dir_path.exists():
                continue
                
            print(f"📁 Generating {dir_path_str}/code_map.md...")
            dir_map = self.generate_directory_code_map(dir_path)
            map_path = dir_path / "code_map.md"
            
            if not dry_run:
                with open(map_path, 'w', encoding='utf-8') as f:
                    f.write(dir_map)
                results[f"{dir_path_str}/code_map.md"] = True
            else:
                print(f"  [DRY RUN] Would create {dir_path_str}/code_map.md ({len(dir_map.splitlines())} lines)")
                results[f"{dir_path_str}/code_map.md"] = True
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Generate hierarchical code navigation maps")
    parser.add_argument("--project-root", type=Path, default=Path("."),
                       help="Project root directory (default: current directory)")
    parser.add_argument("--mapping-data", type=Path, default=Path("doc_code_mapping_data.json"),
                       help="JSON mapping data from analysis tool")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Show what would be done without making changes")
    parser.add_argument("--execute", action="store_true",
                       help="Actually generate the maps (overrides --dry-run)")
    
    args = parser.parse_args()
    
    # Handle dry_run logic
    dry_run = args.dry_run and not args.execute
    
    generator = CodeMapGenerator(args.project_root, args.mapping_data)
    results = generator.generate_all_maps(dry_run)
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n📊 Code map generation {'simulation' if dry_run else 'execution'} complete!")
    print(f"🗺️  Generated: {total} maps, Successful: {successful}")


if __name__ == "__main__":
    main()