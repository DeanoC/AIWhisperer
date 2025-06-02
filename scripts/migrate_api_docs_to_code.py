#!/usr/bin/env python3
"""
API Documentation Migration Tool

This tool extracts API documentation from markdown files and migrates it to
Python code as docstrings. It focuses on function and class documentation
that should live with the code rather than in separate files.

Part of the AIWhisperer refactor Phase 0: Documentation Modernization
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass
import argparse


@dataclass
class APIDocumentation:
    """Represents extracted API documentation."""
    doc_file: str
    code_file: str
    entity_name: str  # class or function name
    entity_type: str  # 'class', 'function', 'method'
    documentation: str
    line_in_doc: int
    existing_docstring: Optional[str] = None


@dataclass
class MigrationResult:
    """Results of a migration operation."""
    migrations_attempted: int
    migrations_successful: int
    files_modified: int
    errors: List[str]
    skipped: List[str]


class APIDocMigrator:
    """Migrates API documentation from markdown to code docstrings."""
    
    def __init__(self, project_root: Path, mapping_data_path: Path = None):
        self.project_root = project_root
        self.mapping_data = None
        
        if mapping_data_path and mapping_data_path.exists():
            with open(mapping_data_path, 'r') as f:
                self.mapping_data = json.load(f)
        
        # Patterns to identify API documentation in markdown
        self.api_doc_patterns = [
            # Class with code block (like AITool)
            (r'##.*?`([A-Z][a-zA-Z0-9_]*)`.*?Abstract Base Class.*?\n```python.*?class \1.*?\n(.*?)```', 'class'),
            (r'###.*?`([A-Z][a-zA-Z0-9_]*)`.*?[Cc]lass.*?\n```python.*?class \1.*?\n(.*?)```', 'class'),
            
            # Properties and methods within code blocks
            (r'@property.*?\n\s*@abstractmethod.*?\n\s*def ([a-zA-Z_][a-zA-Z0-9_]*)\(.*?\).*?\n\s*"""(.*?)"""', 'property'),
            (r'@abstractmethod.*?\n\s*def ([a-zA-Z_][a-zA-Z0-9_]*)\(.*?\).*?\n\s*"""(.*?)"""', 'method'),
            (r'def ([a-zA-Z_][a-zA-Z0-9_]*)\(.*?\).*?\n\s*"""(.*?)"""', 'function'),
            
            # Function documentation sections
            (r'##\s+`([a-zA-Z_][a-zA-Z0-9_]*)\(\)`[^\n]*\n(.*?)(?=\n##|\n```|\Z)', 'function'),
            (r'###\s+`([a-zA-Z_][a-zA-Z0-9_]*)\(\)`[^\n]*\n(.*?)(?=\n###|\n##|\n```|\Z)', 'function'),
            
            # Class documentation sections
            (r'##\s+([A-Z][a-zA-Z0-9_]*)\s+[Cc]lass[^\n]*\n(.*?)(?=\n##|\n```|\Z)', 'class'),
            (r'###\s+([A-Z][a-zA-Z0-9_]*)\s+[Cc]lass[^\n]*\n(.*?)(?=\n###|\n##|\n```|\Z)', 'class'),
            
            # Methods with detailed descriptions
            (r'####\s+`([a-zA-Z_][a-zA-Z0-9_]*)\(\)`[^\n]*\n(.*?)(?=\n####|\n###|\n##|\n```|\Z)', 'method'),
        ]
    
    def find_api_docs_in_file(self, doc_path: Path) -> List[APIDocumentation]:
        """Extract API documentation from a markdown file."""
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {doc_path}: {e}")
            return []
        
        api_docs = []
        
        for pattern, entity_type in self.api_doc_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
            for match in matches:
                entity_name = match.group(1)
                documentation = match.group(2).strip()
                
                # Clean up the documentation
                documentation = self._clean_documentation(documentation)
                
                # Skip if documentation is too short or just boilerplate
                if len(documentation) < 50 or self._is_boilerplate(documentation):
                    continue
                
                # Try to find the corresponding code file
                code_file = self._find_code_file_for_entity(entity_name, entity_type)
                
                if code_file:
                    api_docs.append(APIDocumentation(
                        doc_file=str(doc_path.relative_to(self.project_root)),
                        code_file=code_file,
                        entity_name=entity_name,
                        entity_type=entity_type,
                        documentation=documentation,
                        line_in_doc=content[:match.start()].count('\n') + 1
                    ))
        
        return api_docs
    
    def _clean_documentation(self, doc: str) -> str:
        """Clean up extracted documentation."""
        # Remove markdown code blocks that are just examples
        doc = re.sub(r'```python\n.*?\n```', '', doc, flags=re.DOTALL)
        doc = re.sub(r'```\n.*?\n```', '', doc, flags=re.DOTALL)
        
        # Remove excessive whitespace
        doc = re.sub(r'\n\s*\n\s*\n', '\n\n', doc)
        doc = doc.strip()
        
        # Convert markdown formatting to docstring style
        doc = re.sub(r'\*\*(.*?)\*\*', r'\1', doc)  # Remove bold
        doc = re.sub(r'\*(.*?)\*', r'\1', doc)      # Remove italic
        doc = re.sub(r'`([^`]+)`', r'\1', doc)      # Remove inline code
        
        return doc
    
    def _is_boilerplate(self, doc: str) -> bool:
        """Check if documentation is just boilerplate."""
        boilerplate_indicators = [
            'TODO', 'TBD', 'Not implemented', 'Coming soon',
            'See code for details', 'Standard implementation'
        ]
        
        doc_lower = doc.lower()
        return any(indicator.lower() in doc_lower for indicator in boilerplate_indicators)
    
    def _find_code_file_for_entity(self, entity_name: str, entity_type: str) -> Optional[str]:
        """Find the Python file that likely contains the entity."""
        if not self.mapping_data:
            return self._find_code_file_heuristic(entity_name, entity_type)
        
        # Use mapping data to find files more accurately
        for code_file in self.mapping_data.get('code_coverage_map', {}).keys():
            if code_file.endswith('.py'):
                # Check if this file might contain the entity
                if self._file_likely_contains_entity(code_file, entity_name, entity_type):
                    return code_file
        
        return None
    
    def _find_code_file_heuristic(self, entity_name: str, entity_type: str) -> Optional[str]:
        """Find code file using heuristics when mapping data is not available."""
        # Convert entity name to likely file patterns
        potential_patterns = [
            f"{entity_name.lower()}.py",
            f"{entity_name.lower()}_tool.py",
            f"{entity_name.lower()}_handler.py",
            f"*{entity_name.lower()}*.py"
        ]
        
        # Search in common directories
        search_dirs = [
            self.project_root / "ai_whisperer",
            self.project_root / "interactive_server",
            self.project_root / "postprocessing"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for pattern in potential_patterns:
                    matches = list(search_dir.rglob(pattern))
                    if matches:
                        return str(matches[0].relative_to(self.project_root))
        
        return None
    
    def _file_likely_contains_entity(self, code_file: str, entity_name: str, entity_type: str) -> bool:
        """Check if a file likely contains the specified entity."""
        file_path = self.project_root / code_file
        
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if entity_type == 'class':
                return f"class {entity_name}" in content
            elif entity_type in ['function', 'method']:
                return f"def {entity_name}(" in content
            
        except Exception:
            pass
        
        return False
    
    def parse_python_file(self, file_path: Path) -> ast.AST:
        """Parse a Python file and return its AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content)
        except Exception as e:
            raise Exception(f"Failed to parse {file_path}: {e}")
    
    def find_entity_in_ast(self, tree: ast.AST, entity_name: str, entity_type: str) -> Optional[Union[ast.FunctionDef, ast.ClassDef]]:
        """Find a specific entity in the AST."""
        for node in ast.walk(tree):
            if entity_type == 'class' and isinstance(node, ast.ClassDef) and node.name == entity_name:
                return node
            elif entity_type in ['function', 'method'] and isinstance(node, ast.FunctionDef) and node.name == entity_name:
                return node
        return None
    
    def get_existing_docstring(self, node: Union[ast.FunctionDef, ast.ClassDef]) -> Optional[str]:
        """Extract existing docstring from an AST node."""
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            return node.body[0].value.value
        return None
    
    def format_docstring(self, documentation: str, entity_type: str) -> str:
        """Format documentation as a proper Google-style docstring."""
        lines = documentation.split('\n')
        
        # Find the first substantial line for the brief description
        brief = ""
        detailed = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not brief and len(line) > 10:
                brief = line
            else:
                detailed.append(line)
        
        # Build the docstring
        docstring_lines = []
        
        if brief:
            docstring_lines.append(brief)
        
        if detailed:
            docstring_lines.append("")
            docstring_lines.extend(detailed)
        
        # Add standard sections if this looks like API documentation
        if any(keyword in documentation.lower() for keyword in ['parameter', 'argument', 'return', 'raise']):
            if not any('Args:' in line for line in docstring_lines):
                # Try to extract parameter info
                param_info = self._extract_parameter_info(documentation)
                if param_info:
                    docstring_lines.append("")
                    docstring_lines.append("Args:")
                    docstring_lines.extend(f"    {line}" for line in param_info)
            
            if not any('Returns:' in line for line in docstring_lines):
                return_info = self._extract_return_info(documentation)
                if return_info:
                    docstring_lines.append("")
                    docstring_lines.append("Returns:")
                    docstring_lines.append(f"    {return_info}")
        
        return '\n'.join(docstring_lines)
    
    def _extract_parameter_info(self, documentation: str) -> List[str]:
        """Extract parameter information from documentation."""
        param_lines = []
        
        # Look for parameter patterns
        param_patterns = [
            r'[Pp]arameter[s]?\s*:?\s*\n(.*?)(?=\n[A-Z]|\Z)',
            r'[Aa]rgument[s]?\s*:?\s*\n(.*?)(?=\n[A-Z]|\Z)',
            r'[Ii]nput[s]?\s*:?\s*\n(.*?)(?=\n[A-Z]|\Z)'
        ]
        
        for pattern in param_patterns:
            match = re.search(pattern, documentation, re.DOTALL)
            if match:
                param_text = match.group(1).strip()
                for line in param_text.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('-'):
                        param_lines.append(line)
        
        return param_lines
    
    def _extract_return_info(self, documentation: str) -> Optional[str]:
        """Extract return information from documentation."""
        return_patterns = [
            r'[Rr]eturn[s]?\s*:?\s*(.*?)(?=\n[A-Z]|\Z)',
            r'[Oo]utput[s]?\s*:?\s*(.*?)(?=\n[A-Z]|\Z)'
        ]
        
        for pattern in return_patterns:
            match = re.search(pattern, documentation, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def update_file_with_docstring(self, file_path: Path, entity_name: str, 
                                 entity_type: str, new_docstring: str, dry_run: bool = False) -> bool:
        """Update a Python file to add/replace a docstring."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            tree = self.parse_python_file(file_path)
            entity_node = self.find_entity_in_ast(tree, entity_name, entity_type)
            
            if not entity_node:
                return False
            
            # Find the line where the entity is defined
            entity_line = entity_node.lineno - 1  # Convert to 0-based
            
            # Check if there's already a docstring
            existing_docstring = self.get_existing_docstring(entity_node)
            
            if existing_docstring:
                # Replace existing docstring
                docstring_start = entity_line + 1
                # Find the end of the existing docstring
                quote_style = '"""' if '"""' in lines[docstring_start] else "'''"
                docstring_end = docstring_start
                for i in range(docstring_start + 1, len(lines)):
                    if quote_style in lines[i]:
                        docstring_end = i
                        break
                
                # Replace the lines
                new_docstring_lines = self._format_docstring_lines(new_docstring)
                if not dry_run:
                    lines[docstring_start:docstring_end + 1] = new_docstring_lines
            else:
                # Add new docstring after the function/class definition
                insert_line = entity_line + 1
                new_docstring_lines = self._format_docstring_lines(new_docstring)
                if not dry_run:
                    lines[insert_line:insert_line] = new_docstring_lines
            
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False
    
    def _format_docstring_lines(self, docstring: str) -> List[str]:
        """Format a docstring into properly indented lines."""
        lines = ['    """\n']
        for line in docstring.split('\n'):
            if line.strip():
                lines.append(f"    {line}\n")
            else:
                lines.append("    \n")
        lines.append('    """\n')
        return lines
    
    def migrate_api_docs(self, target_docs: List[str] = None, dry_run: bool = True) -> MigrationResult:
        """Migrate API documentation from markdown files to code."""
        result = MigrationResult(0, 0, 0, [], [])
        
        # Find documentation files to process
        docs_to_process = []
        
        if target_docs:
            docs_to_process = [self.project_root / doc for doc in target_docs]
        else:
            # Process all docs with potential API documentation
            api_doc_candidates = [
                "CLAUDE.md",
                "docs/tool_interface_design.md",
                "docs/tool_management_design.md",
                "docs/agent_context_tracking_design.md",
                "docs/context_manager_design.md",
                "docs/postprocessing_design.md",
                "docs/execute_command_tool_design.md"
            ]
            
            docs_to_process = [
                self.project_root / doc for doc in api_doc_candidates
                if (self.project_root / doc).exists()
            ]
        
        print(f"🔍 Processing {len(docs_to_process)} documentation files...")
        
        all_api_docs = []
        for doc_path in docs_to_process:
            print(f"  Extracting from {doc_path.relative_to(self.project_root)}...")
            api_docs = self.find_api_docs_in_file(doc_path)
            all_api_docs.extend(api_docs)
        
        print(f"📝 Found {len(all_api_docs)} API documentation entries")
        
        # Group by code file for efficient processing
        by_file = {}
        for api_doc in all_api_docs:
            if api_doc.code_file not in by_file:
                by_file[api_doc.code_file] = []
            by_file[api_doc.code_file].append(api_doc)
        
        # Process each file
        for code_file, docs in by_file.items():
            file_path = self.project_root / code_file
            
            if not file_path.exists():
                result.errors.append(f"Code file not found: {code_file}")
                continue
            
            print(f"  Updating {code_file} with {len(docs)} docstrings...")
            
            file_modified = False
            for api_doc in docs:
                result.migrations_attempted += 1
                
                # Format the docstring
                formatted_docstring = self.format_docstring(api_doc.documentation, api_doc.entity_type)
                
                # Update the file
                success = self.update_file_with_docstring(
                    file_path, api_doc.entity_name, api_doc.entity_type, 
                    formatted_docstring, dry_run
                )
                
                if success:
                    result.migrations_successful += 1
                    file_modified = True
                    if dry_run:
                        print(f"    [DRY RUN] Would add docstring to {api_doc.entity_name}")
                    else:
                        print(f"    ✅ Added docstring to {api_doc.entity_name}")
                else:
                    result.errors.append(f"Failed to update {api_doc.entity_name} in {code_file}")
            
            if file_modified:
                result.files_modified += 1
        
        return result
    
    def generate_migration_report(self, result: MigrationResult, output_path: Path):
        """Generate a report of the migration results."""
        with open(output_path, 'w') as f:
            f.write("# API Documentation Migration Report\n\n")
            f.write(f"Generated: {Path.cwd()}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Migrations attempted**: {result.migrations_attempted}\n")
            f.write(f"- **Migrations successful**: {result.migrations_successful}\n")
            f.write(f"- **Files modified**: {result.files_modified}\n")
            success_rate = (result.migrations_successful/result.migrations_attempted*100) if result.migrations_attempted > 0 else 0
            f.write(f"- **Success rate**: {success_rate:.1f}%\n\n")
            
            if result.errors:
                f.write("## Errors\n\n")
                for error in result.errors:
                    f.write(f"- {error}\n")
                f.write("\n")
            
            if result.skipped:
                f.write("## Skipped\n\n")
                for skip in result.skipped:
                    f.write(f"- {skip}\n")
                f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Migrate API documentation to code docstrings")
    parser.add_argument("--project-root", type=Path, default=Path("."),
                       help="Project root directory (default: current directory)")
    parser.add_argument("--mapping-data", type=Path, default=Path("doc_code_mapping_data.json"),
                       help="JSON mapping data from analysis tool")
    parser.add_argument("--target-docs", nargs="+",
                       help="Specific documentation files to process")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Show what would be done without making changes")
    parser.add_argument("--execute", action="store_true",
                       help="Actually perform the migration (overrides --dry-run)")
    parser.add_argument("--output", type=Path, default=Path("api_migration_report.md"),
                       help="Output report file")
    
    args = parser.parse_args()
    
    # Handle dry_run logic
    dry_run = args.dry_run and not args.execute
    
    migrator = APIDocMigrator(args.project_root, args.mapping_data)
    result = migrator.migrate_api_docs(args.target_docs, dry_run)
    
    print(f"\n📊 Migration {'simulation' if dry_run else 'execution'} complete!")
    print(f"📝 Attempted: {result.migrations_attempted}, Successful: {result.migrations_successful}")
    print(f"📁 Files modified: {result.files_modified}")
    
    if result.errors:
        print(f"❌ Errors: {len(result.errors)}")
    
    migrator.generate_migration_report(result, args.output)
    print(f"📄 Report saved to: {args.output}")


if __name__ == "__main__":
    main()