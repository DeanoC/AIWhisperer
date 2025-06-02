#!/usr/bin/env python3
"""
Measure performance baseline for AIWhisperer.
This script measures key performance metrics before optimization.
"""

import time
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import importlib
import tracemalloc
import resource

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def measure_import_time(module_name: str) -> float:
    """Measure time to import a module."""
    start = time.time()
    try:
        importlib.import_module(module_name)
        return time.time() - start
    except Exception as e:
        print(f"  Error importing {module_name}: {e}")
        return -1


def measure_startup_time() -> dict:
    """Measure CLI startup time."""
    results = {}
    
    # Measure help command (minimal startup)
    start = time.time()
    result = subprocess.run(
        ["python", "-m", "ai_whisperer", "--help"],
        capture_output=True,
        text=True
    )
    results["cli_help"] = time.time() - start
    
    # Measure list-models (requires config)
    config_path = Path("config.yaml")
    if config_path.exists():
        start = time.time()
        result = subprocess.run(
            ["python", "-m", "ai_whisperer", "list-models", "--config", "config.yaml"],
            capture_output=True,
            text=True
        )
        results["cli_list_models"] = time.time() - start
    else:
        results["cli_list_models"] = -1
    
    return results


def measure_memory_usage() -> dict:
    """Measure memory usage of key operations."""
    tracemalloc.start()
    results = {}
    
    # Baseline memory
    current, peak = tracemalloc.get_traced_memory()
    results["baseline_mb"] = current / 1024 / 1024
    
    # Import core modules
    modules = [
        "ai_whisperer.core.config",
        "ai_whisperer.services.ai.openrouter",
        "ai_whisperer.services.execution.ai_loop",
        "ai_whisperer.tools.tool_registry",
        "ai_whisperer.services.agents.registry",
    ]
    
    for module in modules:
        try:
            importlib.import_module(module)
        except:
            pass
    
    current, peak = tracemalloc.get_traced_memory()
    results["after_imports_mb"] = current / 1024 / 1024
    results["peak_mb"] = peak / 1024 / 1024
    
    tracemalloc.stop()
    return results


def analyze_import_dependencies():
    """Analyze import times for key modules."""
    print("\n📦 Import Time Analysis")
    print("=" * 50)
    
    modules = {
        "Core": [
            "ai_whisperer.core.config",
            "ai_whisperer.core.logging",
            "ai_whisperer.core.exceptions",
        ],
        "Services": [
            "ai_whisperer.services.ai.openrouter",
            "ai_whisperer.services.execution.ai_loop",
            "ai_whisperer.services.agents.registry",
        ],
        "Tools": [
            "ai_whisperer.tools.tool_registry",
            "ai_whisperer.tools.base_tool",
        ],
        "Extensions": [
            "ai_whisperer.extensions.batch.client",
            "ai_whisperer.extensions.monitoring.debbie_logger",
        ],
        "CLI": [
            "ai_whisperer.interfaces.cli.main",
            "ai_whisperer.interfaces.cli.commands",
        ],
    }
    
    results = {}
    total_time = 0
    
    for category, module_list in modules.items():
        print(f"\n{category}:")
        category_time = 0
        category_results = {}
        
        for module in module_list:
            import_time = measure_import_time(module)
            if import_time >= 0:
                category_results[module] = import_time
                category_time += import_time
                total_time += import_time
                print(f"  {module}: {import_time:.3f}s")
        
        results[category] = {
            "modules": category_results,
            "total": category_time
        }
    
    results["total_import_time"] = total_time
    return results


def find_heavy_imports():
    """Find modules that take long to import."""
    print("\n🐌 Slow Import Detection (>0.1s)")
    print("=" * 50)
    
    # Get all Python files
    slow_imports = []
    
    for root, dirs, files in os.walk("ai_whisperer"):
        # Skip test directories
        if "__pycache__" in root or "test" in root:
            continue
            
        for file in files:
            if file.endswith(".py") and not file.startswith("test_"):
                module_path = Path(root) / file
                module_name = str(module_path).replace("/", ".").replace("\\", ".")[:-3]
                
                import_time = measure_import_time(module_name)
                if import_time > 0.1:  # Threshold for slow imports
                    slow_imports.append((module_name, import_time))
    
    # Sort by import time
    slow_imports.sort(key=lambda x: x[1], reverse=True)
    
    for module, time_taken in slow_imports[:10]:
        print(f"  {module}: {time_taken:.3f}s")
    
    return slow_imports


def main():
    """Run all performance measurements."""
    print("🔍 AIWhisperer Performance Baseline")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Measure startup times
    print("⏱️  Startup Time Measurements")
    print("=" * 50)
    startup_times = measure_startup_time()
    for operation, time_taken in startup_times.items():
        if time_taken >= 0:
            print(f"{operation}: {time_taken:.3f}s")
    
    # Measure memory usage
    print("\n💾 Memory Usage")
    print("=" * 50)
    memory_stats = measure_memory_usage()
    for stat, value in memory_stats.items():
        print(f"{stat}: {value:.2f} MB")
    
    # Analyze imports
    import_results = analyze_import_dependencies()
    
    # Find slow imports
    slow_imports = find_heavy_imports()
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "startup_times": startup_times,
        "memory_usage": memory_stats,
        "import_analysis": import_results,
        "slow_imports": [(m, t) for m, t in slow_imports[:10]],
    }
    
    # Save report
    report_path = Path("performance_baseline.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Performance baseline saved to: {report_path}")
    
    # Recommendations
    print("\n📊 Initial Observations:")
    print("=" * 50)
    
    if startup_times.get("cli_help", 0) > 1.0:
        print("⚠️  CLI startup is slow (>1s)")
    
    if slow_imports:
        print(f"⚠️  Found {len(slow_imports)} slow-loading modules")
    
    if memory_stats.get("after_imports_mb", 0) > 100:
        print("⚠️  High memory usage after imports")
    
    print("\n🎯 Optimization Targets:")
    print("1. Reduce import times for slow modules")
    print("2. Implement lazy loading for heavy dependencies")
    print("3. Optimize CLI startup path")
    print("4. Review memory usage patterns")


if __name__ == "__main__":
    main()