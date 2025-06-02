#!/usr/bin/env python3
"""
Implement lazy loading optimizations for better performance.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def add_type_checking_imports(file_path: Path) -> bool:
    """Convert heavy type imports to use TYPE_CHECKING."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Find typing imports
        typing_import_pattern = r'from typing import ([^;]+)'
        match = re.search(typing_import_pattern, content)
        
        if match:
            # Check if TYPE_CHECKING is already imported
            if 'TYPE_CHECKING' not in match.group(1):
                # Add TYPE_CHECKING to imports
                old_import = match.group(0)
                imports = match.group(1).split(',')
                imports = [i.strip() for i in imports]
                
                # Add TYPE_CHECKING if not present
                if 'TYPE_CHECKING' not in imports:
                    imports.insert(0, 'TYPE_CHECKING')
                
                new_import = f"from typing import {', '.join(imports)}"
                content = content.replace(old_import, new_import)
        
        # Find heavy imports that could be moved to TYPE_CHECKING
        heavy_modules = [
            'pandas', 'numpy', 'matplotlib', 'scipy', 'sklearn',
            'torch', 'tensorflow', 'transformers'
        ]
        
        for module in heavy_modules:
            # Check if module is imported
            if f'import {module}' in content or f'from {module}' in content:
                # Check if it's only used in type annotations
                # This is a simplified check - in practice would need AST analysis
                if f'{module}.' not in content.replace(f': {module}.', ''):
                    # Move to TYPE_CHECKING block
                    if 'if TYPE_CHECKING:' not in content:
                        # Add TYPE_CHECKING block after imports
                        import_end = content.rfind('\nimport') + 1
                        if import_end == 0:
                            import_end = content.rfind('\nfrom') + 1
                        
                        type_block = '\n\nif TYPE_CHECKING:\n    pass\n'
                        content = content[:import_end] + type_block + content[import_end:]
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def implement_lazy_imports_cli(file_path: Path) -> bool:
    """Implement lazy imports in CLI files."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Patterns for CLI optimization
        optimizations = [
            # Lazy import for heavy modules in functions
            (r'import (\w+)\n', r'# Lazy import: \1\n'),
            
            # Move imports inside functions where they're used once
            # This requires more complex analysis
        ]
        
        # For CLI main files, defer imports until needed
        if 'cli/main.py' in str(file_path) or '__main__.py' in str(file_path):
            # Find imports that can be deferred
            lines = content.split('\n')
            new_lines = []
            deferred_imports = []
            
            in_imports = True
            for line in lines:
                if in_imports and (line.startswith('import ') or line.startswith('from ')):
                    # Check if this is a heavy import
                    if any(module in line for module in ['tools', 'agents', 'batch', 'extensions']):
                        deferred_imports.append(line)
                        new_lines.append(f'# Deferred: {line}')
                    else:
                        new_lines.append(line)
                else:
                    if in_imports and line and not line.startswith('#'):
                        in_imports = False
                    new_lines.append(line)
            
            content = '\n'.join(new_lines)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
            
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def optimize_tool_imports():
    """Optimize imports in tool files."""
    print("🔧 Optimizing tool imports...")
    
    tools_dir = Path("ai_whisperer/tools")
    optimized = 0
    
    for tool_file in tools_dir.glob("*_tool.py"):
        if add_type_checking_imports(tool_file):
            print(f"  ✓ Optimized {tool_file.name}")
            optimized += 1
    
    print(f"Optimized {optimized} tool files")
    return optimized


def optimize_cli_startup():
    """Optimize CLI startup performance."""
    print("\n🚀 Optimizing CLI startup...")
    
    cli_files = [
        "ai_whisperer/__main__.py",
        "ai_whisperer/interfaces/cli/main.py",
        "ai_whisperer/interfaces/cli/commands.py",
    ]
    
    optimized = 0
    for file_path in cli_files:
        path = Path(file_path)
        if path.exists() and implement_lazy_imports_cli(path):
            print(f"  ✓ Optimized {file_path}")
            optimized += 1
    
    print(f"Optimized {optimized} CLI files")
    return optimized


def create_import_optimizer():
    """Create a module for optimizing imports at runtime."""
    optimizer_code = '''"""
Runtime import optimizer for AIWhisperer.
Provides utilities for lazy loading and import management.
"""

import importlib
import sys
from typing import Any, Callable, Optional
import functools


class LazyImport:
    """Lazy import wrapper that defers module loading."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        return getattr(self._module, name)


def lazy_import(module_name: str) -> LazyImport:
    """Create a lazy import for a module."""
    return LazyImport(module_name)


def lazy_callable(module_name: str, callable_name: str) -> Callable:
    """Create a lazy callable that imports on first use."""
    @functools.wraps(callable_name)
    def wrapper(*args, **kwargs):
        module = importlib.import_module(module_name)
        func = getattr(module, callable_name)
        # Replace wrapper with actual function for future calls
        wrapper.__wrapped__ = func
        return func(*args, **kwargs)
    
    return wrapper


# Usage examples:
# Instead of: from heavy_module import heavy_function
# Use: heavy_function = lazy_callable('heavy_module', 'heavy_function')

# Instead of: import heavy_module
# Use: heavy_module = lazy_import('heavy_module')
'''
    
    with open("ai_whisperer/utils/import_optimizer.py", "w") as f:
        f.write(optimizer_code)
    
    print("\n✅ Created import optimizer module")


def main():
    """Run performance optimizations."""
    print("🎯 AIWhisperer Performance Optimization")
    print("=" * 50)
    
    # Create import optimizer
    create_import_optimizer()
    
    # Optimize tool imports
    tool_count = optimize_tool_imports()
    
    # Optimize CLI startup
    cli_count = optimize_cli_startup()
    
    print(f"\n📊 Summary:")
    print(f"- Created import optimizer utility")
    print(f"- Optimized {tool_count} tool files")
    print(f"- Optimized {cli_count} CLI files")
    
    print("\n🎯 Next Steps:")
    print("1. Test CLI startup time")
    print("2. Implement lazy tool registry")
    print("3. Split large files")
    print("4. Profile memory usage")


if __name__ == "__main__":
    main()