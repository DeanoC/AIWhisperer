#!/usr/bin/env python3
"""
Fix additional imports after Phase 4 reorganization.
"""

import os
import re
from pathlib import Path
from typing import Dict, List

# Additional import fixes for Phase 4
ADDITIONAL_FIXES = {
    # Fix monitoring control tool import
    r"from ai_whisperer\.extensions\.batch\.monitoring_control_tool": "from ai_whisperer.extensions.batch.monitoring",
    r"from \.monitoring_control_tool": "from ai_whisperer.extensions.batch.monitoring",
    
    # Fix any batch relative imports
    r"from \.client import": "from ai_whisperer.extensions.batch.client import",
    r"from \.intervention import": "from ai_whisperer.extensions.batch.intervention import",
    r"from \.monitoring import": "from ai_whisperer.extensions.batch.monitoring import",
    r"from \.server_manager import": "from ai_whisperer.extensions.batch.server_manager import",
    r"from \.websocket_client import": "from ai_whisperer.extensions.batch.websocket_client import",
    r"from \.script_processor import": "from ai_whisperer.extensions.batch.script_processor import",
    
    # Fix extension agent imports
    r"from \.agent import Agent": "from ai_whisperer.extensions.agents.agent import Agent",
    r"from \.communication import": "from ai_whisperer.extensions.agents.communication import",
    r"from \.task_decomposer import": "from ai_whisperer.extensions.agents.task_decomposer import",
    r"from \.decomposed_task import": "from ai_whisperer.extensions.agents.decomposed_task import",
    
    # Fix mailbox imports
    r"from \.mailbox import": "from ai_whisperer.extensions.mailbox.mailbox import",
    r"from \.tools import": "from ai_whisperer.extensions.mailbox.tools import",
    r"from \.notification import": "from ai_whisperer.extensions.mailbox.notification import",
}

# Files to specifically check and fix
SPECIFIC_FILES = [
    "ai_whisperer/extensions/batch/client.py",
    "ai_whisperer/extensions/batch/intervention.py",
    "ai_whisperer/extensions/batch/monitoring.py",
    "ai_whisperer/extensions/batch/server_manager.py",
    "ai_whisperer/extensions/batch/websocket_client.py",
    "ai_whisperer/extensions/batch/websocket_interceptor.py",
    "ai_whisperer/extensions/batch/script_processor.py",
    "ai_whisperer/extensions/monitoring/debbie_logger.py",
    "ai_whisperer/extensions/mailbox/mailbox.py",
    "ai_whisperer/extensions/mailbox/tools.py",
    "ai_whisperer/extensions/agents/agent.py",
    "ai_whisperer/extensions/agents/task_decomposer.py",
    "ai_whisperer/tools/tool_registration.py",
]


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a specific file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply fixes
        for pattern, replacement in ADDITIONAL_FIXES.items():
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"  Error fixing imports in {file_path}: {e}")
        return False


def fix_monitoring_control_tool():
    """Fix the specific monitoring control tool import issue."""
    tool_reg = Path("ai_whisperer/tools/tool_registration.py")
    if tool_reg.exists():
        try:
            content = tool_reg.read_text()
            original = content
            
            # Fix the import
            content = re.sub(
                r"from ai_whisperer\.extensions\.batch\.monitoring_control_tool import MonitoringControlTool",
                "from ai_whisperer.extensions.batch.monitoring import MonitoringControlTool",
                content
            )
            
            if content != original:
                tool_reg.write_text(content)
                print("Fixed MonitoringControlTool import in tool_registration.py")
                return True
        except Exception as e:
            print(f"Error fixing monitoring control tool: {e}")
    return False


def main():
    """Main execution function."""
    print("Fixing additional imports after Phase 4 reorganization")
    print("=" * 50)
    
    # Fix the monitoring control tool import first
    print("\nFixing monitoring control tool import...")
    fix_monitoring_control_tool()
    
    # Fix specific files
    print("\nFixing known files with import issues...")
    fixed_count = 0
    for file_path_str in SPECIFIC_FILES:
        file_path = Path(file_path_str)
        if file_path.exists():
            if fix_imports_in_file(file_path):
                fixed_count += 1
                print(f"Fixed imports in {file_path}")
    
    # Also scan all Python files for remaining issues
    print("\nScanning all Python files for remaining import issues...")
    python_files = []
    for root, dirs, files in os.walk("."):
        if any(skip in root for skip in [".venv", "__pycache__", "node_modules", ".git", "refactor_backup"]):
            continue
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
            print(f"Fixed imports in {file_path}")
    
    print(f"\nFixed imports in {fixed_count} files total")


if __name__ == "__main__":
    main()