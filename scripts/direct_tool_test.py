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

# Import and test the tools
from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
from ai_whisperer.tools.read_file_tool import ReadFileTool

# Test read_file tool
print("="*60)
print("Test: read_file(path='README.md', start_line=1, end_line=10)")
print("="*60)

read_tool = ReadFileTool()
result = read_tool.execute(path='README.md', start_line=1, end_line=10)

print(f"\nReturn type: {type(result).__name__}")
print(f"Keys: {list(result.keys())}")

if 'error' in result:
    print(f"\nERROR: {result['error']}")
else:
    print(f"\nPath: {result['path']}")
    print(f"Total lines: {result['total_lines']}")
    print(f"Range: lines {result['range']['start']} to {result['range']['end']}")
    print(f"File size: {result['size']} bytes")
    print(f"\nFirst 5 lines:")
    for line_info in result['lines'][:5]:
        print(f"  {line_info['line_number']:3d}: {line_info['content']}")

# Show the JSON that would be sent to the AI
print("\n" + "="*60)
print("JSON representation (what AI receives):")
print("="*60)
# Truncate for readability
result_for_ai = result.copy()
if 'lines' in result_for_ai and len(result_for_ai['lines']) > 5:
    result_for_ai['lines'] = result_for_ai['lines'][:5] + [{"truncated": f"... and {len(result['lines']) - 5} more lines"}]

print(json.dumps(result_for_ai, indent=2))