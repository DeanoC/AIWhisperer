#!/usr/bin/env python3
"""
File Header Generation Tool

This tool generates concise module headers for Python files to make them
instantly understandable to LLMs. Headers include module purpose, key APIs,
usage examples, and dependencies - all within 100 lines.

Part of the AIWhisperer refactor Phase 0: Documentation Modernization
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass
import argparse


@dataclass
class ClassInfo:
    """Information about a class in a Python file."""
    name: str
    base_classes: List[str]
    methods: List[str]
    docstring: Optional[str]
    is_public: bool


@dataclass
class FunctionInfo:
    """Information about a function in a Python file."""
    name: str
    is_async: bool
    parameters: List[str]
    return_annotation: Optional[str]
    docstring: Optional[str]
    is_public: bool


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    file_path: str
    imports: List[str]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    constants: List[str]
    existing_docstring: Optional[str]
    line_count: int


class FileHeaderGenerator:
    """Generates descriptive headers for Python files."""
    
    def __init__(self, project_root: Path, mapping_data_path: Path = None):
        self.project_root = project_root
        self.mapping_data = None
        
        if mapping_data_path and mapping_data_path.exists():
            with open(mapping_data_path, 'r') as f:
                self.mapping_data = json.load(f)
    
    def analyze_python_file(self, file_path: Path) -> ModuleInfo:
        """Analyze a Python file and extract structural information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            tree = ast.parse(content)
        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")
            return ModuleInfo(
                file_path=str(file_path.relative_to(self.project_root)),
                imports=[], classes=[], functions=[], constants=[],
                existing_docstring=None, line_count=0
            )
        
        # Extract module docstring
        existing_docstring = None
        if (tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            existing_docstring = tree.body[0].value.value
        
        # Analyze imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Analyze classes
        classes = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                classes.append(class_info)
        
        # Analyze functions
        functions = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._analyze_function(node)
                functions.append(func_info)
        
        # Analyze constants (module-level assignments)
        constants = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append(target.id)
        
        return ModuleInfo(
            file_path=str(file_path.relative_to(self.project_root)),
            imports=list(set(imports)),  # Remove duplicates
            classes=classes,
            functions=functions,
            constants=constants,
            existing_docstring=existing_docstring,
            line_count=len(lines)
        )
    
    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition."""
        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(f"{base.value.id}.{base.attr}")
        
        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
        
        # Extract docstring
        docstring = None
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        return ClassInfo(
            name=node.name,
            base_classes=base_classes,
            methods=methods,
            docstring=docstring,
            is_public=not node.name.startswith('_')
        )
    
    def _analyze_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> FunctionInfo:
        """Analyze a function definition."""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param = arg.arg
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param += f": {arg.annotation.id}"
                elif isinstance(arg.annotation, ast.Constant):
                    param += f": {arg.annotation.value}"
            parameters.append(param)
        
        # Extract return annotation
        return_annotation = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_annotation = node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return_annotation = str(node.returns.value)
        
        # Extract docstring
        docstring = None
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        return FunctionInfo(
            name=node.name,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            parameters=parameters,
            return_annotation=return_annotation,
            docstring=docstring,
            is_public=not node.name.startswith('_')
        )
    
    def determine_module_purpose(self, module_info: ModuleInfo) -> str:
        """Determine the primary purpose of a module based on its structure."""
        file_path = module_info.file_path
        
        # Use existing docstring if it's good
        if module_info.existing_docstring and len(module_info.existing_docstring) > 50:
            first_line = module_info.existing_docstring.split('\n')[0].strip()
            if len(first_line) > 20 and not first_line.lower().startswith('todo'):
                return first_line
        
        # Infer from file path and content
        if 'test' in file_path:
            return f"Test suite for {self._get_module_name(file_path)}"
        elif file_path.endswith('__init__.py'):
            return f"Package initialization for {Path(file_path).parent.name}"
        elif file_path.endswith('_tool.py'):
            return f"AI tool implementation for {self._extract_tool_name(file_path)}"
        elif file_path.endswith('_handler.py'):
            return f"Handler implementation for {self._extract_handler_name(file_path)}"
        elif 'agent' in file_path.lower():
            return "AI agent implementation for specialized task handling"
        elif 'config' in file_path.lower():
            return "Configuration management and settings"
        elif 'cli' in file_path.lower():
            return "Command-line interface implementation"
        elif module_info.classes:
            main_class = module_info.classes[0]
            return f"Implementation of {main_class.name} class"
        elif module_info.functions:
            return f"Utility functions for {self._get_module_name(file_path)}"
        else:
            return f"Module for {self._get_module_name(file_path)}"
    
    def _get_module_name(self, file_path: str) -> str:
        """Extract a readable module name from file path."""
        name = Path(file_path).stem
        if name == '__init__':
            name = Path(file_path).parent.name
        return name.replace('_', ' ')
    
    def _extract_tool_name(self, file_path: str) -> str:
        """Extract tool name from tool file path."""
        name = Path(file_path).stem
        if name.endswith('_tool'):
            name = name[:-5]  # Remove '_tool' suffix
        return name.replace('_', ' ')
    
    def _extract_handler_name(self, file_path: str) -> str:
        """Extract handler name from handler file path."""
        name = Path(file_path).stem
        if name.endswith('_handler'):
            name = name[:-8]  # Remove '_handler' suffix
        return name.replace('_', ' ')
    
    def get_related_docs(self, module_info: ModuleInfo) -> List[str]:
        """Find documentation files related to this module."""
        if not self.mapping_data:
            return []
        
        related_docs = []
        code_coverage_map = self.mapping_data.get('code_coverage_map', {})
        
        if module_info.file_path in code_coverage_map:
            related_docs = code_coverage_map[module_info.file_path]
        
        return related_docs
    
    def generate_header(self, module_info: ModuleInfo, max_lines: int = 100) -> str:
        """Generate a comprehensive module header."""
        lines = []
        
        # Module declaration
        module_name = Path(module_info.file_path).stem
        if module_name == '__init__':
            module_name = Path(module_info.file_path).parent.name
        
        lines.append('"""')
        lines.append(f"Module: {module_info.file_path}")
        lines.append(f"Purpose: {self.determine_module_purpose(module_info)}")
        lines.append("")
        
        # Add detailed description based on content
        if module_info.existing_docstring and len(module_info.existing_docstring) > 100:
            # Use existing detailed description
            desc_lines = module_info.existing_docstring.split('\n')[1:6]  # Take next few lines
            for line in desc_lines:
                if line.strip() and not line.strip().startswith('"""'):
                    lines.append(line.strip())
        else:
            # Generate description based on analysis
            self._add_generated_description(lines, module_info)
        
        lines.append("")
        
        # Key Components section
        if module_info.classes or module_info.functions:
            lines.append("Key Components:")
            
            # List main classes
            for cls in module_info.classes[:3]:  # Limit to top 3
                if cls.is_public:
                    desc = cls.docstring.split('\n')[0] if cls.docstring else "Class implementation"
                    lines.append(f"- {cls.name}: {desc}")
            
            # List main functions
            public_funcs = [f for f in module_info.functions if f.is_public][:3]
            for func in public_funcs:
                desc = func.docstring.split('\n')[0] if func.docstring else "Function implementation"
                lines.append(f"- {func.name}(): {desc}")
            
            lines.append("")
        
        # Usage example if it's a clear API
        if self._should_include_usage_example(module_info):
            lines.append("Usage:")
            self._add_usage_example(lines, module_info)
            lines.append("")
        
        # Dependencies section
        if module_info.imports:
            key_imports = self._filter_key_imports(module_info.imports)
            if key_imports:
                lines.append("Dependencies:")
                for imp in key_imports[:5]:  # Limit to 5 most important
                    lines.append(f"- {imp}")
                lines.append("")
        
        # Related documentation
        related_docs = self.get_related_docs(module_info)
        if related_docs:
            lines.append("Related:")
            for doc in related_docs[:3]:  # Limit to 3 most relevant
                lines.append(f"- See {doc}")
            lines.append("")
        
        lines.append('"""')
        
        # Ensure we stay within the line limit
        if len(lines) > max_lines:
            # Truncate and add notice
            lines = lines[:max_lines-2]
            lines.append("... (truncated for brevity)")
            lines.append('"""')
        
        return '\n'.join(lines)
    
    def _add_generated_description(self, lines: List[str], module_info: ModuleInfo):
        """Add a generated description based on module analysis."""
        if 'tool' in module_info.file_path:
            lines.append("This module implements an AI-usable tool that extends the AITool")
            lines.append("base class. It provides structured input/output handling and")
            lines.append("integrates with the OpenRouter API for AI model interactions.")
        elif 'agent' in module_info.file_path:
            lines.append("This module implements an AI agent that processes user messages")
            lines.append("and executes specialized tasks. It integrates with the tool system")
            lines.append("and manages conversation context.")
        elif 'handler' in module_info.file_path:
            lines.append("This module provides request handling functionality with")
            lines.append("message routing and response processing capabilities.")
        elif module_info.classes:
            main_class = module_info.classes[0]
            lines.append(f"This module provides the {main_class.name} class which")
            if main_class.base_classes:
                lines.append(f"extends {', '.join(main_class.base_classes[:2])} to implement")
            lines.append("specialized functionality for the AIWhisperer system.")
        else:
            lines.append("This module provides utility functions and supporting")
            lines.append("infrastructure for the AIWhisperer application.")
    
    def _should_include_usage_example(self, module_info: ModuleInfo) -> bool:
        """Determine if we should include a usage example."""
        # Include examples for tools, main classes, and clear APIs
        return (
            'tool' in module_info.file_path or
            any(cls.is_public for cls in module_info.classes) or
            'cli' in module_info.file_path or
            'main' in module_info.file_path
        )
    
    def _add_usage_example(self, lines: List[str], module_info: ModuleInfo):
        """Add a usage example based on the module type."""
        if 'tool' in module_info.file_path:
            tool_name = self._extract_tool_name(module_info.file_path)
            lines.append(f"    tool = {module_info.classes[0].name if module_info.classes else 'Tool'}()")
            lines.append("    result = await tool.execute(**parameters)")
        elif module_info.classes:
            main_class = module_info.classes[0]
            lines.append(f"    {main_class.name.lower()} = {main_class.name}()")
            if main_class.methods:
                first_method = next((m for m in main_class.methods if not m.startswith('_')), None)
                if first_method:
                    lines.append(f"    result = {main_class.name.lower()}.{first_method}()")
        elif module_info.functions:
            first_func = next((f for f in module_info.functions if f.is_public), None)
            if first_func:
                lines.append(f"    result = {first_func.name}({', '.join(first_func.parameters[:2])})")
    
    def _filter_key_imports(self, imports: List[str]) -> List[str]:
        """Filter to show only the most important imports."""
        # Filter out standard library and common imports
        filtered = []
        skip_patterns = ['os', 'sys', 'json', 'typing', 're', 'pathlib', 'datetime']
        
        for imp in imports:
            if not any(pattern in imp for pattern in skip_patterns):
                if imp.startswith('ai_whisperer') or imp.startswith('interactive_server'):
                    filtered.append(imp)
                elif len(filtered) < 3:  # Include some external deps
                    filtered.append(imp)
        
        return filtered
    
    def add_header_to_file(self, file_path: Path, header: str, dry_run: bool = True) -> bool:
        """Add or replace the module header in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find where to insert the header
            insert_pos = 0
            
            # Skip shebang if present
            if lines and lines[0].startswith('#!'):
                insert_pos = 1
            
            # Skip encoding declarations
            while insert_pos < len(lines) and (
                lines[insert_pos].strip().startswith('#') and 
                ('coding' in lines[insert_pos] or 'encoding' in lines[insert_pos])
            ):
                insert_pos += 1
            
            # Check if there's already a module docstring
            tree = ast.parse(''.join(lines))
            has_existing_docstring = (
                tree.body and 
                isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)
            )
            
            if has_existing_docstring:
                # Find the end of the existing docstring and replace it
                in_docstring = False
                docstring_start = None
                docstring_end = None
                
                for i, line in enumerate(lines[insert_pos:], insert_pos):
                    if '"""' in line and not in_docstring:
                        docstring_start = i
                        in_docstring = True
                        if line.count('"""') == 2:  # Single-line docstring
                            docstring_end = i + 1
                            break
                    elif '"""' in line and in_docstring:
                        docstring_end = i + 1
                        break
                
                if docstring_start is not None and docstring_end is not None:
                    # Replace existing docstring
                    new_lines = (
                        lines[:docstring_start] + 
                        [header + '\n\n'] + 
                        lines[docstring_end:]
                    )
                else:
                    # Fallback: insert at the beginning
                    new_lines = lines[:insert_pos] + [header + '\n\n'] + lines[insert_pos:]
            else:
                # Insert new header
                new_lines = lines[:insert_pos] + [header + '\n\n'] + lines[insert_pos:]
            
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
            
            return True
            
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False
    
    def process_files(self, file_patterns: List[str] = None, dry_run: bool = True) -> Dict[str, bool]:
        """Process Python files and add headers."""
        results = {}
        
        # Find Python files to process
        if file_patterns:
            files_to_process = []
            for pattern in file_patterns:
                files_to_process.extend(self.project_root.glob(pattern))
        else:
            # Default: process all Python files in main directories
            search_dirs = [
                "ai_whisperer/**/*.py",
                "interactive_server/**/*.py", 
                "postprocessing/**/*.py"
            ]
            files_to_process = []
            for pattern in search_dirs:
                files_to_process.extend(self.project_root.glob(pattern))
        
        # Filter out __pycache__ and test files for now
        files_to_process = [
            f for f in files_to_process 
            if '__pycache__' not in str(f) and f.is_file()
        ]
        
        print(f"🔍 Processing {len(files_to_process)} Python files...")
        
        for file_path in files_to_process:
            print(f"  Analyzing {file_path.relative_to(self.project_root)}...")
            
            # Analyze the file
            module_info = self.analyze_python_file(file_path)
            
            # Generate header
            header = self.generate_header(module_info)
            
            # Add header to file
            success = self.add_header_to_file(file_path, header, dry_run)
            results[str(file_path.relative_to(self.project_root))] = success
            
            if dry_run:
                print(f"    [DRY RUN] Would add {len(header.splitlines())} line header")
            else:
                status = "✅" if success else "❌"
                print(f"    {status} {'Added' if success else 'Failed to add'} header")
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Generate descriptive headers for Python files")
    parser.add_argument("--project-root", type=Path, default=Path("."),
                       help="Project root directory (default: current directory)")
    parser.add_argument("--mapping-data", type=Path, default=Path("doc_code_mapping_data.json"),
                       help="JSON mapping data from analysis tool")
    parser.add_argument("--files", nargs="+",
                       help="Specific file patterns to process (e.g., 'ai_whisperer/tools/*.py')")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Show what would be done without making changes")
    parser.add_argument("--execute", action="store_true",
                       help="Actually perform the header generation (overrides --dry-run)")
    
    args = parser.parse_args()
    
    # Handle dry_run logic
    dry_run = args.dry_run and not args.execute
    
    generator = FileHeaderGenerator(args.project_root, args.mapping_data)
    results = generator.process_files(args.files, dry_run)
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n📊 Header generation {'simulation' if dry_run else 'execution'} complete!")
    print(f"📝 Processed: {total}, Successful: {successful}")
    
    if successful < total:
        failed = [path for path, success in results.items() if not success]
        print(f"❌ Failed files: {', '.join(failed[:5])}")


if __name__ == "__main__":
    main()