#!/usr/bin/env python3
"""Direct test of list_directory tool."""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Initialize config
from ai_whisperer.core.config import load_config
config = load_config(PROJECT_ROOT / "config" / "main.yaml")

# Import and test the tool
from ai_whisperer.tools.list_directory_tool import ListDirectoryTool

# Create tool instance
tool = ListDirectoryTool()

# Test 1: List scripts directory
print("="*60)
print("Test: list_directory(path='scripts')")
print("="*60)

result = tool.execute(path='scripts')

print(f"\nReturn type: {type(result).__name__}")
print(f"Keys: {list(result.keys())}")

if 'error' in result:
    print(f"\nERROR: {result['error']}")
else:
    print(f"\nPath: {result['path']}")
    print(f"Total files: {result['total_files']}")
    print(f"Total directories: {result['total_directories']}")
    print(f"First 5 entries:")
    for entry in result['entries'][:5]:
        print(f"  - {entry['name']} ({entry['type']})")

# Show the JSON that would be sent to the AI
print("\n" + "="*60)
print("JSON representation (what AI receives):")
print("="*60)
# Truncate for readability
result_for_ai = result.copy()
if 'entries' in result_for_ai and len(result_for_ai['entries']) > 5:
    result_for_ai['entries'] = result_for_ai['entries'][:5] + [{"truncated": f"... and {len(result['entries']) - 5} more entries"}]

print(json.dumps(result_for_ai, indent=2))