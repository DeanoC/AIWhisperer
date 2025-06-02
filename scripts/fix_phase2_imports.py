#!/usr/bin/env python3
"""
Fix additional imports and relative imports after Phase 2 reorganization.
"""

import os
import re
from pathlib import Path
from typing import Dict, List

# Additional import fixes for Phase 2
ADDITIONAL_FIXES = {
    # Fix incorrect config import in agents/__init__.py
    r"from ai_whisperer\.core\.config import AgentConfig": "from ai_whisperer.services.agents.config import AgentConfig",
    
    # Fix ai_service references that might have been missed
    r"from ai_whisperer\.ai_service import": "from ai_whisperer.services.ai import",
    r"ai_whisperer\.ai_service\.": "ai_whisperer.services.ai.",
    
    # Fix ai_loop references
    r"from ai_whisperer\.ai_loop import": "from ai_whisperer.services.execution import",
    r"ai_whisperer\.ai_loop\.": "ai_whisperer.services.execution.",
    
    # Fix remaining relative imports in moved files
    r"from \.tool_calling": "from ai_whisperer.services.ai.tool_calling",
    r"from \.base": "from ai_whisperer.services.agents.base",
    r"from \.registry": "from ai_whisperer.services.agents.registry",
    r"from \.config": "from ai_whisperer.services.agents.config",
    r"from \.factory": "from ai_whisperer.services.agents.factory",
    r"from \.context_manager": "from ai_whisperer.services.agents.context_manager",
    
    # Fix OpenRouterAIService imports that may need updating
    r"from \.openrouter import OpenRouterAIService": "from ai_whisperer.services.ai.openrouter import OpenRouterAIService",
}

# Files to specifically check and fix
SPECIFIC_FILES = [
    "ai_whisperer/agents/__init__.py",
    "ai_whisperer/services/ai/base.py",
    "ai_whisperer/services/ai/openrouter.py", 
    "ai_whisperer/services/ai/tool_calling.py",
    "ai_whisperer/services/execution/ai_loop.py",
    "ai_whisperer/services/agents/base.py",
    "ai_whisperer/services/agents/factory.py",
    "ai_whisperer/services/agents/stateless.py",
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


def main():
    """Main execution function."""
    print("Fixing additional imports after Phase 2 reorganization")
    print("=" * 50)
    
    # Fix specific files first
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