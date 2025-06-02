#!/usr/bin/env python3
"""
Find potentially unused imports in Python files.
This is a simple heuristic-based approach.
"""

import ast
import os
from pathlib import Path
from typing import Set, Dict, List, Tuple
import json

def get_imported_names(tree: ast.AST) -> Dict[str, Set[str]]:
    """Extract all imported names from an AST."""
    imports = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports[name] = {alias.name}
                
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if name == '*':
                    imports['*'] = {f"{module}.*"}
                else:
                    imports[name] = {f"{module}.{alias.name}"}
    
    return imports


def get_used_names(tree: ast.AST) -> Set[str]:
    """Extract all names used in the code."""
    used = set()
    imported_names = get_imported_names(tree)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in imported_names:
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Get the base name
            base = node
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                used.add(base.id)
    
    return used


def find_unused_imports_in_file(file_path: Path) -> List[Tuple[str, str]]:
    """Find potentially unused imports in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imported = get_imported_names(tree)
        used = get_used_names(tree)
        
        unused = []
        for name, modules in imported.items():
            if name == '*':
                continue
            if name not in used:
                # Check for common patterns that might be missed
                if not any(pattern in content for pattern in [
                    f"{name}(",  # Function call
                    f"{name}.",  # Attribute access
                    f":{name}",  # Type annotation
                    f"[{name}]", # Dict/List access
                    f"@{name}",  # Decorator
                    f"except {name}", # Exception
                    f"raise {name}",  # Raise exception
                    f"isinstance(", # Often used with imported types
                    f"issubclass(", # Often used with imported types
                    "TYPE_CHECKING", # Special case
                ]):
                    for module in modules:
                        unused.append((name, module))
        
        return unused
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return []


def analyze_directory(directory: str) -> Dict[str, List[Tuple[str, str]]]:
    """Analyze all Python files in a directory."""
    results = {}
    total_unused = 0
    
    for root, dirs, files in os.walk(directory):
        # Skip test and cache directories
        if any(skip in root for skip in ['__pycache__', 'test', '.git', 'venv']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                unused = find_unused_imports_in_file(file_path)
                if unused:
                    results[str(file_path)] = unused
                    total_unused += len(unused)
    
    return results, total_unused


def main():
    """Find unused imports in AIWhisperer codebase."""
    print("🔍 Searching for unused imports...")
    print("=" * 70)
    
    # Analyze main directories
    directories = ['ai_whisperer', 'interactive_server', 'postprocessing']
    
    all_results = {}
    total_unused = 0
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"\nAnalyzing {directory}/...")
            results, count = analyze_directory(directory)
            all_results.update(results)
            total_unused += count
    
    # Sort by number of unused imports
    sorted_results = sorted(all_results.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Show top files with unused imports
    print(f"\n📊 Found {total_unused} potentially unused imports in {len(all_results)} files")
    print("\nTop files with unused imports:")
    print("=" * 70)
    
    for file_path, unused_imports in sorted_results[:20]:
        print(f"\n{file_path} ({len(unused_imports)} unused):")
        for name, module in unused_imports[:5]:
            print(f"  - {name} from {module}")
        if len(unused_imports) > 5:
            print(f"  ... and {len(unused_imports) - 5} more")
    
    # Save full results
    with open('unused_imports.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Full results saved to unused_imports.json")
    
    # Generate cleanup script
    print("\n📝 Generating cleanup suggestions...")
    
    cleanup_count = 0
    with open('cleanup_imports.py', 'w') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write('"""Auto-generated script to clean up unused imports."""\n\n')
        f.write("import re\n")
        f.write("from pathlib import Path\n\n")
        f.write("def clean_file(file_path, unused_imports):\n")
        f.write("    # This is a template - review before running!\n")
        f.write("    pass\n\n")
        f.write("# Files to clean:\n")
        
        for file_path, unused_imports in sorted_results[:10]:
            if len(unused_imports) > 2:
                f.write(f"# {file_path}: {unused_imports[:3]}\n")
                cleanup_count += 1
    
    print(f"Generated cleanup suggestions for {cleanup_count} files")
    
    print("\n🎯 Recommendations:")
    print("1. Review unused_imports.json for false positives")
    print("2. Start with files having the most unused imports")
    print("3. Be careful with TYPE_CHECKING imports")
    print("4. Test after each cleanup")


if __name__ == "__main__":
    main()