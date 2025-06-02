#!/usr/bin/env python3
"""
Debug script to investigate why the frontend shows "no plans found" 
while Agent P can see plans.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ai_whisperer.tools.list_plans_tool import ListPlansTool
from ai_whisperer.tools.read_plan_tool import ReadPlanTool
from ai_whisperer.utils.path import PathManager

def debug_plan_access():
    """Debug plan access and see what should be available to the UI"""
    
    print("=== DEBUGGING PLAN UI ISSUE ===\n")
    
    # Initialize path manager properly
    try:
        path_manager = PathManager.get_instance()
        # Initialize with current directory as workspace
        workspace_path = Path.cwd()
        path_manager.initialize({
            'workspace_path': workspace_path,
            'project_path': workspace_path
        })
        print(f"Workspace path: {workspace_path}")
        
    except Exception as e:
        print(f"Error initializing PathManager: {e}")
        # Fall back to manual directory checking
        workspace_path = Path.cwd()
        print(f"Using fallback workspace path: {workspace_path}")
    
    # Check plans directory structure
    print("\n1. CHECKING PLANS DIRECTORY STRUCTURE:")
    plans_base = Path(workspace_path) / ".WHISPER" / "plans"
    print(f"Plans base path: {plans_base}")
    print(f"Plans base exists: {plans_base.exists()}")
    
    if plans_base.exists():
        print("Contents of plans directory:")
        for item in plans_base.iterdir():
            print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
            if item.is_dir():
                for subitem in item.iterdir():
                    print(f"    - {subitem.name}")
    
    # Use the list_plans_tool to see what Agent P sees
    print("\n2. USING LIST_PLANS_TOOL (what Agent P sees):")
    list_tool = ListPlansTool()
    try:
        plans_result = list_tool.execute({"status": "all"})
        print(plans_result)
    except Exception as e:
        print(f"Error using list_plans_tool: {e}")
    
    # Check what specific plan data looks like
    print("\n3. CHECKING INDIVIDUAL PLAN DATA:")
    
    # Find first plan to read
    if plans_base.exists():
        for status_dir in ["in_progress", "archived"]:
            status_path = plans_base / status_dir
            if status_path.exists():
                for plan_dir in status_path.iterdir():
                    if plan_dir.is_dir():
                        print(f"\nReading plan: {plan_dir.name}")
                        read_tool = ReadPlanTool()
                        try:
                            plan_content = read_tool.execute({
                                "plan_name": plan_dir.name,
                                "include_tasks": False
                            })
                            print(plan_content)
                            
                            # Also check the raw JSON structure
                            plan_json_file = plan_dir / "plan.json"
                            if plan_json_file.exists():
                                print(f"\nRaw plan.json structure for {plan_dir.name}:")
                                with open(plan_json_file) as f:
                                    plan_data = json.load(f)
                                    print(f"Keys: {list(plan_data.keys())}")
                                    print(f"Title: {plan_data.get('title', 'No title')}")
                                    print(f"Tasks count: {len(plan_data.get('tasks', []))}")
                        except Exception as e:
                            print(f"Error reading plan {plan_dir.name}: {e}")
                        
                        # Only check first plan for now
                        break
                if status_path.exists() and any(status_path.iterdir()):
                    break
    
    # Check what the backend should be serving
    print("\n4. CHECKING BACKEND INTEGRATION:")
    print("The frontend expects JSON-RPC calls to 'plan.list' and 'plan.read' methods.")
    print("The backend should return:")
    print("- plan.list: { 'plans': [{'plan_name': 'name', ...}, ...] }")
    print("- plan.read: { 'plan': {plan_data} }")
    
    # Check if interactive server exists and how it handles plans
    interactive_server_path = Path(workspace_path) / "interactive_server"
    print(f"\nInteractive server path: {interactive_server_path}")
    print(f"Interactive server exists: {interactive_server_path.exists()}")
    
    if interactive_server_path.exists():
        print("Interactive server contents:")
        for item in interactive_server_path.iterdir():
            print(f"  - {item.name}")

if __name__ == "__main__":
    debug_plan_access()
