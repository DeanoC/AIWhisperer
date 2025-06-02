#!/usr/bin/env python3
"""
Simple performance baseline measurement for AIWhisperer.
Focuses on key metrics without complex dependencies.
"""

import time
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def measure_cli_startup():
    """Measure basic CLI startup times."""
    print("⏱️  CLI Startup Times")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Help command (minimal startup)
    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "ai_whisperer", "--help"],
        capture_output=True,
        text=True
    )
    help_time = time.time() - start
    results["help_command"] = help_time
    print(f"Help command: {help_time:.3f}s")
    
    # Test 2: Version check
    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "ai_whisperer", "--version"],
        capture_output=True,
        text=True
    )
    version_time = time.time() - start
    results["version_command"] = version_time
    print(f"Version command: {version_time:.3f}s")
    
    return results


def analyze_module_sizes():
    """Analyze size of Python modules."""
    print("\n📏 Module Size Analysis")
    print("=" * 50)
    
    sizes = {}
    total_size = 0
    
    directories = [
        "ai_whisperer/core",
        "ai_whisperer/utils",
        "ai_whisperer/services",
        "ai_whisperer/interfaces",
        "ai_whisperer/extensions",
        "ai_whisperer/tools",
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue
            
        dir_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    size = file_path.stat().st_size
                    dir_size += size
                    file_count += 1
        
        sizes[directory] = {
            "total_bytes": dir_size,
            "total_kb": dir_size / 1024,
            "file_count": file_count,
            "avg_kb": (dir_size / 1024 / file_count) if file_count > 0 else 0
        }
        total_size += dir_size
        
        print(f"{directory}: {dir_size/1024:.1f} KB ({file_count} files, avg {sizes[directory]['avg_kb']:.1f} KB)")
    
    sizes["total_kb"] = total_size / 1024
    return sizes


def find_large_files():
    """Find unusually large Python files."""
    print("\n📦 Large Files (>50KB)")
    print("=" * 50)
    
    large_files = []
    
    for root, dirs, files in os.walk("ai_whisperer"):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                size = file_path.stat().st_size
                if size > 50 * 1024:  # 50KB threshold
                    large_files.append((str(file_path), size))
    
    large_files.sort(key=lambda x: x[1], reverse=True)
    
    for file_path, size in large_files[:10]:
        print(f"  {file_path}: {size/1024:.1f} KB")
    
    return large_files


def count_imports():
    """Count import statements to identify heavy dependencies."""
    print("\n📚 Import Analysis")
    print("=" * 50)
    
    import_counts = {}
    third_party_imports = set()
    
    for root, dirs, files in os.walk("ai_whisperer"):
        if "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                    
                    file_imports = 0
                    for line in lines:
                        line = line.strip()
                        if line.startswith(('import ', 'from ')) and not line.startswith('from .'):
                            file_imports += 1
                            # Track third-party imports
                            if 'import ' in line:
                                module = line.split()[1].split('.')[0]
                                if module not in ['ai_whisperer', 'os', 'sys', 'json', 'pathlib', 
                                               'datetime', 'typing', 'asyncio', 'logging']:
                                    third_party_imports.add(module)
                    
                    if file_imports > 20:  # Files with many imports
                        import_counts[str(file_path)] = file_imports
                except:
                    pass
    
    # Sort by import count
    sorted_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("Files with many imports (>20):")
    for file_path, count in sorted_imports[:10]:
        print(f"  {file_path}: {count} imports")
    
    print(f"\nThird-party dependencies found: {len(third_party_imports)}")
    print(f"  {', '.join(sorted(third_party_imports)[:10])}")
    
    return {"heavy_importers": sorted_imports[:10], "third_party": list(third_party_imports)}


def main():
    """Run performance baseline measurements."""
    print("🔍 AIWhisperer Performance Baseline")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version.split()[0],
    }
    
    # Measure CLI startup
    startup_times = measure_cli_startup()
    results["startup_times"] = startup_times
    
    # Analyze module sizes
    module_sizes = analyze_module_sizes()
    results["module_sizes"] = module_sizes
    
    # Find large files
    large_files = find_large_files()
    results["large_files"] = [(f, s) for f, s in large_files[:10]]
    
    # Count imports
    import_analysis = count_imports()
    results["import_analysis"] = import_analysis
    
    # Save results
    with open("performance_baseline.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Performance baseline saved to performance_baseline.json")
    
    # Optimization recommendations
    print("\n🎯 Optimization Opportunities:")
    print("=" * 50)
    
    if startup_times.get("help_command", 0) > 0.5:
        print("1. ⚠️  CLI startup is slow (>0.5s) - consider lazy imports")
    else:
        print("1. ✅ CLI startup is fast")
    
    if large_files:
        print(f"2. ⚠️  Found {len(large_files)} large files - consider splitting")
    
    if module_sizes.get("total_kb", 0) > 1000:
        print(f"3. ℹ️  Total codebase size: {module_sizes['total_kb']:.1f} KB")
    
    heavy_importers = import_analysis.get("heavy_importers", [])
    if heavy_importers:
        print(f"4. ⚠️  {len(heavy_importers)} files have >20 imports - consider refactoring")
    
    print("\n📋 Next Steps:")
    print("1. Implement lazy loading for heavy modules")
    print("2. Optimize import statements in CLI entry points")
    print("3. Consider code splitting for large files")
    print("4. Profile actual runtime performance")


if __name__ == "__main__":
    main()