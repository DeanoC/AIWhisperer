#!/usr/bin/env python3
"""
Clean up unused imports to improve performance and code quality.
Focus on safe removals - primarily unused typing imports.
"""

import json
import re
from pathlib import Path
from typing import List, Tuple, Dict

def load_unused_imports():
    """Load the unused imports analysis."""
    with open('unused_imports.json', 'r') as f:
        return json.load(f)

def is_safe_to_remove(import_name: str, module: str) -> bool:
    """Determine if an import is safe to remove."""
    # Safe to remove typing imports that are truly unused
    safe_patterns = [
        'typing.',  # Typing imports
        'collections.',  # Collection types
        'datetime.',  # Date/time types
    ]
    
    # Never remove these
    unsafe_patterns = [
        'TYPE_CHECKING',  # Used for conditional imports
        'Any',  # Often used in complex type hints
        'Protocol',  # Used for structural typing
        '__future__',  # Future imports
        'annotations',  # Annotations import
    ]
    
    for pattern in unsafe_patterns:
        if pattern in import_name or pattern in module:
            return False
    
    for pattern in safe_patterns:
        if module.startswith(pattern):
            return True
    
    return False

def clean_imports_in_file(file_path: str, unused_imports: List[Tuple[str, str]]) -> Tuple[bool, int]:
    """Clean unused imports in a single file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        removed_count = 0
        
        for import_name, module in unused_imports:
            if not is_safe_to_remove(import_name, module):
                continue
            
            # Pattern for "from X import Y, Z" where we want to remove Y
            from_pattern = rf'from {re.escape(module.rsplit(".", 1)[0])} import ([^\\n]+)'
            match = re.search(from_pattern, content)
            
            if match:
                imports_str = match.group(1)
                imports = [i.strip() for i in imports_str.split(',')]
                
                if import_name in imports:
                    imports.remove(import_name)
                    
                    if imports:
                        # Replace with remaining imports
                        new_imports = ', '.join(imports)
                        new_line = f'from {module.rsplit(".", 1)[0]} import {new_imports}'
                        content = content.replace(match.group(0), new_line)
                    else:
                        # Remove entire import line
                        line_pattern = rf'^{re.escape(match.group(0))}\\n'
                        content = re.sub(line_pattern, '', content, flags=re.MULTILINE)
                    
                    removed_count += 1
        
        if content != original_content:
            # Clean up multiple blank lines
            content = re.sub(r'\\n\\n\\n+', '\\n\\n', content)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return True, removed_count
        
        return False, 0
        
    except Exception as e:
        print(f"  Error cleaning {file_path}: {e}")
        return False, 0

def clean_typing_imports():
    """Clean unused typing imports from the codebase."""
    print("🧹 Cleaning Unused Typing Imports")
    print("=" * 70)
    
    unused_imports = load_unused_imports()
    
    # Filter to files with many unused typing imports
    candidates = {}
    for file_path, imports in unused_imports.items():
        typing_imports = [(name, module) for name, module in imports 
                         if module.startswith('typing.')]
        if len(typing_imports) >= 3:  # Only clean files with 3+ unused typing imports
            candidates[file_path] = typing_imports
    
    print(f"Found {len(candidates)} files with multiple unused typing imports")
    print()
    
    total_cleaned = 0
    total_removed = 0
    
    # Clean files
    for file_path, typing_imports in sorted(candidates.items(), 
                                           key=lambda x: len(x[1]), 
                                           reverse=True)[:20]:  # Top 20 files
        
        cleaned, removed = clean_imports_in_file(file_path, typing_imports)
        
        if cleaned:
            print(f"✓ {file_path}: removed {removed} imports")
            total_cleaned += 1
            total_removed += removed
    
    print(f"\\nCleaned {total_cleaned} files, removed {total_removed} imports")
    
    return total_cleaned, total_removed

def optimize_type_checking_imports():
    """Add TYPE_CHECKING guards for heavy type-only imports."""
    print("\\n🔧 Optimizing Type-Only Imports")
    print("=" * 70)
    
    # Target files that import from heavy modules
    heavy_modules = [
        'ai_whisperer.services.ai.openrouter',
        'ai_whisperer.services.execution.ai_loop',
        'ai_whisperer.services.agents.registry',
        'ai_whisperer.tools.tool_registry',
    ]
    
    optimized = 0
    
    # This would require more complex AST analysis to implement properly
    # For now, just report what could be optimized
    
    print("Modules that could benefit from TYPE_CHECKING imports:")
    for module in heavy_modules:
        print(f"  - {module}")
    
    return optimized

def main():
    """Main cleanup function."""
    print("🎯 Import Cleanup and Optimization")
    print("=" * 70)
    
    # Clean unused typing imports
    cleaned_files, removed_imports = clean_typing_imports()
    
    # Optimize type checking imports
    optimized_files = optimize_type_checking_imports()
    
    print(f"\\n📊 Summary:")
    print(f"- Cleaned {cleaned_files} files")
    print(f"- Removed {removed_imports} unused imports")
    print(f"- Identified opportunities for TYPE_CHECKING optimization")
    
    print("\\n🎯 Next Steps:")
    print("1. Run tests to ensure nothing was broken")
    print("2. Implement TYPE_CHECKING guards for heavy imports")
    print("3. Consider using a tool like 'autoflake' for more aggressive cleanup")


if __name__ == "__main__":
    main()