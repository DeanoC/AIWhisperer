#!/usr/bin/env python3
"""Test updated tools to verify they return structured data."""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# We need to initialize config first
from ai_whisperer.core.config import load_config
config = load_config(PROJECT_ROOT / "config" / "main.yaml")

# Import PathManager
from ai_whisperer.utils.path import PathManager

# Import tools to test
from ai_whisperer.tools.list_directory_tool import ListDirectoryTool


def test_list_directory():
    """Test the updated list_directory tool."""
    print("\n" + "="*60)
    print("Testing Updated ListDirectoryTool")
    print("="*60)
    
    tool = ListDirectoryTool()
    
    # Test 1: List root directory
    print("\nTest 1: List root directory")
    result = tool.execute(path=".")
    print(f"Result type: {type(result).__name__}")
    print(f"Keys: {list(result.keys())}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Total files: {result['total_files']}")
        print(f"Total directories: {result['total_directories']}")
        print(f"Sample entries: {result['entries'][:3]}")
    
    # Test 2: List with error (non-existent path)
    print("\nTest 2: Non-existent path")
    result = tool.execute(path="non_existent_dir")
    print(f"Result type: {type(result).__name__}")
    print(f"Has error: {'error' in result}")
    if 'error' in result:
        print(f"Error message: {result['error']}")
    
    # Test 3: Recursive listing
    print("\nTest 3: Recursive listing of 'scripts' directory")
    result = tool.execute(path="scripts", recursive=True, max_depth=2)
    print(f"Result type: {type(result).__name__}")
    print(f"Recursive: {result.get('recursive', False)}")
    print(f"Max depth: {result.get('max_depth', 'N/A')}")
    if 'error' not in result:
        print(f"Total entries: {len(result['entries'])}")
        # Show some entries at different depths
        for depth in [0, 1]:
            depth_entries = [e for e in result['entries'] if e.get('depth', 0) == depth]
            if depth_entries:
                print(f"  Depth {depth}: {len(depth_entries)} entries")
                print(f"    Sample: {depth_entries[0]}")


def main():
    """Run all tests."""
    # Initialize PathManager
    path_manager = PathManager()
    
    # Test list_directory
    test_list_directory()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()