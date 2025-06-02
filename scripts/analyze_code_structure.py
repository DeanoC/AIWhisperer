#!/usr/bin/env python3
"""Analyze Python code structure for refactoring documentation."""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

class CodeAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.modules = {}
        self.imports = {}
        self.errors = []

    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract module info
            module_info = {
                'path': str(file_path.relative_to(self.root_path)),
                'classes': [],
                'functions': [],
                'imports': [],
                'from_imports': [],
                'size': len(content.splitlines()),
                'docstring': ast.get_docstring(tree)
            }
            
            # Analyze AST
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        'docstring': ast.get_docstring(node)
                    }
                    module_info['classes'].append(class_info)
                
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Top-level functions only
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node)
                    }
                    module_info['functions'].append(func_info)
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        import_info = {
                            'module': node.module,
                            'names': [alias.name for alias in node.names],
                            'level': node.level
                        }
                        module_info['from_imports'].append(import_info)
            
            return module_info
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            return None

    def analyze_directory(self, directory: Path) -> Dict[str, List]:
        """Analyze all Python files in a directory."""
        results = {
            'modules': [],
            'summary': {
                'total_files': 0,
                'total_classes': 0,
                'total_functions': 0,
                'total_lines': 0
            }
        }
        
        for py_file in directory.rglob('*.py'):
            # Skip __pycache__ and test files for now
            if '__pycache__' in str(py_file) or 'test_' in py_file.name:
                continue
            
            module_info = self.analyze_file(py_file)
            if module_info:
                results['modules'].append(module_info)
                results['summary']['total_files'] += 1
                results['summary']['total_classes'] += len(module_info['classes'])
                results['summary']['total_functions'] += len(module_info['functions'])
                results['summary']['total_lines'] += module_info['size']
        
        return results

    def find_circular_imports(self) -> List[List[str]]:
        """Detect circular import dependencies."""
        # This is a simplified version - would need more sophisticated analysis
        # for a complete solution
        return []

    def generate_report(self, output_dir: Path):
        """Generate comprehensive analysis reports."""
        output_dir.mkdir(exist_ok=True)
        
        # Analyze main package
        ai_whisperer_analysis = self.analyze_directory(self.root_path / 'ai_whisperer')
        
        # Save detailed module map
        with open(output_dir / 'code_map.json', 'w') as f:
            json.dump(ai_whisperer_analysis, f, indent=2)
        
        # Generate markdown report
        self.generate_markdown_report(ai_whisperer_analysis, output_dir / 'code_map.md')
        
        return ai_whisperer_analysis

    def generate_markdown_report(self, analysis: Dict, output_path: Path):
        """Generate a markdown report from analysis."""
        with open(output_path, 'w') as f:
            f.write("# AIWhisperer Code Map\n\n")
            f.write("## Summary\n")
            f.write(f"- Total Python Files: {analysis['summary']['total_files']}\n")
            f.write(f"- Total Classes: {analysis['summary']['total_classes']}\n")
            f.write(f"- Total Functions: {analysis['summary']['total_functions']}\n")
            f.write(f"- Total Lines: {analysis['summary']['total_lines']}\n\n")
            
            f.write("## Module Details\n\n")
            
            # Group by directory
            modules_by_dir = {}
            for module in analysis['modules']:
                dir_name = os.path.dirname(module['path'])
                if not dir_name:
                    dir_name = 'root'
                if dir_name not in modules_by_dir:
                    modules_by_dir[dir_name] = []
                modules_by_dir[dir_name].append(module)
            
            # Write by directory
            for dir_name in sorted(modules_by_dir.keys()):
                f.write(f"### {dir_name}\n\n")
                for module in sorted(modules_by_dir[dir_name], key=lambda x: x['path']):
                    f.write(f"#### `{module['path']}`\n")
                    if module['docstring']:
                        f.write(f"*{module['docstring'].splitlines()[0]}*\n\n")
                    
                    if module['classes']:
                        f.write("**Classes:**\n")
                        for cls in module['classes']:
                            f.write(f"- `{cls['name']}`: {len(cls['methods'])} methods\n")
                            if cls['docstring']:
                                f.write(f"  - {cls['docstring'].splitlines()[0]}\n")
                    
                    if module['functions']:
                        f.write("\n**Functions:**\n")
                        for func in module['functions']:
                            args = ', '.join(func['args'])
                            f.write(f"- `{func['name']}({args})`\n")
                            if func['docstring']:
                                f.write(f"  - {func['docstring'].splitlines()[0]}\n")
                    
                    f.write(f"\n**Stats:** {module['size']} lines")
                    f.write("\n\n---\n\n")

if __name__ == "__main__":
    analyzer = CodeAnalyzer(Path.cwd())
    analyzer.generate_report(Path("refactor_analysis"))
    print("Analysis complete! Check refactor_analysis/ directory for results.")