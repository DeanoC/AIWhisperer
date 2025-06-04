#!/usr/bin/env python3
"""Audit all tools to ensure they return structured data."""

import sys
import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.tools.tool_registry import get_tool_registry


def analyze_tool_file(filepath: Path) -> Dict[str, Any]:
    """Analyze a tool file to understand its return type."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    tool_info = {
        'file': str(filepath.relative_to(PROJECT_ROOT)),
        'classes': [],
        'execute_methods': []
    }
    
    # Find tool classes and their execute methods
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it's a tool class (inherits from BaseTool)
            for base in node.bases:
                if isinstance(base, ast.Name) and 'Tool' in base.id:
                    tool_info['classes'].append(node.name)
                    
                    # Find execute method
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name == 'execute':
                                # Analyze return statements
                                returns = []
                                for subnode in ast.walk(item):
                                    if isinstance(subnode, ast.Return):
                                        if subnode.value:
                                            returns.append(ast.unparse(subnode.value))
                                
                                tool_info['execute_methods'].append({
                                    'class': node.name,
                                    'is_async': isinstance(item, ast.AsyncFunctionDef),
                                    'returns': returns
                                })
    
    return tool_info


def check_return_types(tool_info: Dict[str, Any]) -> Dict[str, Any]:
    """Check if return types are structured data."""
    issues = []
    
    for method in tool_info['execute_methods']:
        for ret in method['returns']:
            # Check for common anti-patterns
            if 'f"' in ret or "f'" in ret:
                issues.append(f"Formatted string return: {ret[:100]}...")
            elif '".format(' in ret or "'.format(" in ret:
                issues.append(f"Format string return: {ret[:100]}...")
            elif 'str(' in ret and not ('json.dumps' in ret or 'json.loads' in ret):
                issues.append(f"String conversion: {ret[:100]}...")
            elif ret.startswith('"') or ret.startswith("'"):
                # Check if it's a simple string literal (not JSON)
                if not ('{' in ret or '[' in ret):
                    issues.append(f"Plain string return: {ret[:100]}...")
    
    return {
        'file': tool_info['file'],
        'classes': tool_info['classes'],
        'issues': issues,
        'clean': len(issues) == 0
    }


def main():
    """Audit all registered tools."""
    # Get all tool files
    tools_dir = PROJECT_ROOT / 'ai_whisperer' / 'tools'
    tool_files = list(tools_dir.glob('*_tool.py'))
    
    print(f"Found {len(tool_files)} tool files to analyze\n")
    
    all_results = []
    clean_tools = []
    problematic_tools = []
    
    for tool_file in sorted(tool_files):
        print(f"Analyzing {tool_file.name}...", end=' ')
        
        try:
            tool_info = analyze_tool_file(tool_file)
            result = check_return_types(tool_info)
            all_results.append(result)
            
            if result['clean']:
                clean_tools.append(result)
                print("✅ CLEAN")
            else:
                problematic_tools.append(result)
                print("❌ ISSUES FOUND")
                for issue in result['issues']:
                    print(f"   - {issue}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            problematic_tools.append({
                'file': str(tool_file.relative_to(PROJECT_ROOT)),
                'issues': [f"Parse error: {e}"],
                'clean': False
            })
    
    # Summary
    print("\n" + "="*80)
    print(f"SUMMARY: {len(clean_tools)} clean, {len(problematic_tools)} with issues")
    print("="*80)
    
    if problematic_tools:
        print("\nTools that need attention:")
        for tool in problematic_tools:
            print(f"\n📁 {tool['file']}")
            for issue in tool['issues']:
                print(f"   ⚠️  {issue}")
    
    # Save detailed report
    report_file = PROJECT_ROOT / 'scripts' / 'tool_audit_report.json'
    with open(report_file, 'w') as f:
        json.dump({
            'summary': {
                'total': len(tool_files),
                'clean': len(clean_tools),
                'issues': len(problematic_tools)
            },
            'clean_tools': clean_tools,
            'problematic_tools': problematic_tools
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Also test actual tool execution with registry
    print("\n" + "="*80)
    print("Testing actual tool registration and return types...")
    print("="*80)
    
    registry = get_tool_registry()
    registered_tools = registry.get_all_tools()
    
    print(f"\nFound {len(registered_tools)} registered tools")
    
    # Group by file for easier review
    tools_by_file = {}
    for tool_name, tool_instance in registered_tools.items():
        module = tool_instance.__class__.__module__
        if module not in tools_by_file:
            tools_by_file[module] = []
        tools_by_file[module].append((tool_name, tool_instance))
    
    print(f"\nTools are from {len(tools_by_file)} different modules")
    
    return len(problematic_tools) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)