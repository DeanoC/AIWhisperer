#!/usr/bin/env python3
"""Test specific tools to see their actual return values."""

import sys
import os
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

# Import some tools to test
from ai_whisperer.tools.workspace_stats_tool import WorkspaceStatsTool
from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
from ai_whisperer.tools.read_file_tool import ReadFileTool
from ai_whisperer.tools.get_project_structure_tool import GetProjectStructureTool
from ai_whisperer.tools.find_pattern_tool import FindPatternTool


def test_tool(tool_name, tool_instance, args):
    """Test a tool and check its return type."""
    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"Args: {args}")
    print(f"{'='*60}")
    
    try:
        result = tool_instance.execute(**args)
        result_type = type(result).__name__
        
        print(f"Return type: {result_type}")
        
        if isinstance(result, dict):
            print("✅ Returns a dictionary (structured data)")
            print(f"Keys: {list(result.keys())}")
            # Check if any values are formatted strings
            for key, value in result.items():
                if isinstance(value, str) and (value.startswith("Error:") or "successfully" in value):
                    print(f"⚠️  Key '{key}' contains a formatted message: {value[:100]}...")
        elif isinstance(result, list):
            print("✅ Returns a list (structured data)")
            print(f"Length: {len(result)}")
        elif isinstance(result, str):
            print("❌ Returns a string (not structured)")
            print(f"Content preview: {result[:200]}...")
            # Check if it's JSON
            try:
                parsed = json.loads(result)
                print("  → But it's valid JSON, could be parsed")
            except:
                print("  → Not valid JSON, plain text")
        else:
            print(f"⚡ Returns {result_type}")
            
    except Exception as e:
        print(f"❌ Error executing tool: {e}")
    
    return None


def main():
    """Test various tools."""
    path_manager = PathManager()
    
    # Test workspace stats tool
    ws_tool = WorkspaceStatsTool(path_manager)
    test_tool("WorkspaceStatsTool", ws_tool, {})
    
    # Test list directory tool
    list_tool = ListDirectoryTool()
    test_tool("ListDirectoryTool", list_tool, {"path": "."})
    
    # Test read file tool
    read_tool = ReadFileTool()
    test_tool("ReadFileTool", read_tool, {"file_path": "README.md", "max_lines": 10})
    
    # Test project structure tool
    struct_tool = GetProjectStructureTool()
    test_tool("GetProjectStructureTool", struct_tool, {"show_tree": True})
    
    # Test find pattern tool
    find_tool = FindPatternTool(path_manager)
    test_tool("FindPatternTool", find_tool, {"pattern": "TODO", "path": ".", "max_matches": 5})
    

if __name__ == "__main__":
    main()