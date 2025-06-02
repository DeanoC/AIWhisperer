#!/usr/bin/env python3
"""
Analyze the impact of module reorganization without making changes.
"""

import os
from pathlib import Path
from collections import defaultdict
import re

# Import the mappings from the reorganization script
from reorganize_modules import FILE_MOVEMENTS, IMPORT_MAPPINGS


def analyze_file_movements():
    """Analyze which files would be moved."""
    print("FILE MOVEMENT ANALYSIS")
    print("=" * 70)
    
    existing_files = []
    missing_files = []
    
    for old_path, new_path in FILE_MOVEMENTS.items():
        if Path(old_path).exists():
            existing_files.append((old_path, new_path))
        else:
            missing_files.append(old_path)
    
    print(f"\nFiles to be moved: {len(existing_files)}")
    print(f"Files not found: {len(missing_files)}")
    
    # Group by target directory
    by_target = defaultdict(list)
    for old, new in existing_files:
        target_dir = str(Path(new).parent)
        by_target[target_dir].append((old, new))
    
    print("\nFiles by target directory:")
    for target_dir in sorted(by_target.keys()):
        print(f"\n{target_dir}/ ({len(by_target[target_dir])} files)")
        for old, new in by_target[target_dir]:
            print(f"  {Path(old).name} ← {old}")


def analyze_import_impact():
    """Analyze which files would need import updates."""
    print("\n\nIMPORT UPDATE ANALYSIS")
    print("=" * 70)
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        if any(skip in root for skip in [".venv", "__pycache__", "node_modules", ".git", "refactor_backup"]):
            continue
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    # Check each file for imports that would change
    files_with_imports = defaultdict(list)
    import_count = 0
    
    for file_path in python_files:
        try:
            content = file_path.read_text()
            found_imports = []
            
            for old_import in IMPORT_MAPPINGS.keys():
                # Check for various import patterns
                if re.search(rf"from {re.escape(old_import)} import", content):
                    found_imports.append(old_import)
                elif re.search(rf"^import {re.escape(old_import)}$", content, re.MULTILINE):
                    found_imports.append(old_import)
                elif re.search(rf"import {re.escape(old_import)} as", content):
                    found_imports.append(old_import)
            
            if found_imports:
                files_with_imports[str(file_path)] = found_imports
                import_count += len(found_imports)
                
        except Exception as e:
            pass
    
    print(f"\nFiles needing import updates: {len(files_with_imports)}")
    print(f"Total imports to update: {import_count}")
    
    # Show most affected files
    sorted_files = sorted(files_with_imports.items(), key=lambda x: len(x[1]), reverse=True)
    
    print("\nMost affected files:")
    for file_path, imports in sorted_files[:10]:
        print(f"\n{file_path} ({len(imports)} imports)")
        for imp in imports[:3]:
            print(f"  - {imp} → {IMPORT_MAPPINGS[imp]}")
        if len(imports) > 3:
            print(f"  ... and {len(imports) - 3} more")


def check_test_coverage():
    """Check if tests exist for modules being moved."""
    print("\n\nTEST COVERAGE ANALYSIS")
    print("=" * 70)
    
    modules_with_tests = []
    modules_without_tests = []
    
    for old_path in FILE_MOVEMENTS.keys():
        if not Path(old_path).exists():
            continue
            
        # Derive test path
        module_path = Path(old_path)
        if module_path.name == "__init__.py":
            continue
            
        test_name = f"test_{module_path.stem}.py"
        test_paths = [
            Path("tests") / "unit" / module_path.parent.relative_to("ai_whisperer") / test_name,
            Path("tests") / "integration" / module_path.parent.relative_to("ai_whisperer") / test_name,
        ]
        
        has_test = any(tp.exists() for tp in test_paths)
        
        if has_test:
            modules_with_tests.append(old_path)
        else:
            modules_without_tests.append(old_path)
    
    print(f"\nModules with tests: {len(modules_with_tests)}")
    print(f"Modules without tests: {len(modules_without_tests)}")
    
    if modules_without_tests:
        print("\nModules being moved without tests:")
        for module in sorted(modules_without_tests)[:10]:
            print(f"  - {module}")
        if len(modules_without_tests) > 10:
            print(f"  ... and {len(modules_without_tests) - 10} more")


def main():
    """Run all analyses."""
    print("MODULE REORGANIZATION IMPACT ANALYSIS")
    print("=" * 70)
    
    analyze_file_movements()
    analyze_import_impact()
    check_test_coverage()
    
    print("\n\nSUMMARY")
    print("=" * 70)
    print("This reorganization will:")
    print(f"- Move {len([p for p in FILE_MOVEMENTS.keys() if Path(p).exists()])} files")
    print("- Create a cleaner, more logical structure")
    print("- Require updating imports across the codebase")
    print("- Need test path updates")
    print("\nRun 'python scripts/reorganize_modules.py' to execute the reorganization")


if __name__ == "__main__":
    main()