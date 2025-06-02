#!/usr/bin/env python3
"""
Automated module reorganization script for AIWhisperer.
This script will move files to their new locations and update imports.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import ast

# Define the file movements
FILE_MOVEMENTS = {
    # Core modules
    "ai_whisperer/config.py": "ai_whisperer/core/config.py",
    "ai_whisperer/exceptions.py": "ai_whisperer/core/exceptions.py",
    "ai_whisperer/logging_custom.py": "ai_whisperer/core/logging.py",
    "ai_whisperer/model_capabilities.py": "ai_whisperer/core/model_capabilities.py",
    
    # Service modules - AI
    "ai_whisperer/ai_service/ai_service.py": "ai_whisperer/services/ai/base.py",
    "ai_whisperer/ai_service/openrouter_ai_service.py": "ai_whisperer/services/ai/openrouter.py",
    "ai_whisperer/ai_service/tool_calling.py": "ai_whisperer/services/ai/tool_calling.py",
    
    # Service modules - Execution
    "ai_whisperer/ai_loop/stateless_ai_loop.py": "ai_whisperer/services/execution/ai_loop.py",
    "ai_whisperer/ai_loop/ai_config.py": "ai_whisperer/services/execution/ai_config.py",
    "ai_whisperer/ai_loop/tool_call_accumulator.py": "ai_whisperer/services/execution/tool_call_accumulator.py",
    "ai_whisperer/context_management.py": "ai_whisperer/services/execution/context_management.py",
    "ai_whisperer/state_management.py": "ai_whisperer/services/execution/state_management.py",
    
    # Service modules - Agents
    "ai_whisperer/agents/base_handler.py": "ai_whisperer/services/agents/base.py",
    "ai_whisperer/agents/factory.py": "ai_whisperer/services/agents/factory.py",
    "ai_whisperer/agents/registry.py": "ai_whisperer/services/agents/registry.py",
    "ai_whisperer/agents/config.py": "ai_whisperer/services/agents/config.py",
    "ai_whisperer/agents/stateless_agent.py": "ai_whisperer/services/agents/stateless_agent.py",
    "ai_whisperer/agents/session_manager.py": "ai_whisperer/services/agents/session_manager.py",
    "ai_whisperer/agents/context_manager.py": "ai_whisperer/services/agents/context_manager.py",
    
    # Interface modules - CLI
    "ai_whisperer/cli.py": "ai_whisperer/interfaces/cli/main.py",
    "ai_whisperer/cli_commands.py": "ai_whisperer/interfaces/cli/commands_base.py",
    "ai_whisperer/cli_commands_batch_mode.py": "ai_whisperer/interfaces/cli/batch.py",
    
    # Utility modules
    "ai_whisperer/path_management.py": "ai_whisperer/utils/path.py",
    "ai_whisperer/prompt_system.py": "ai_whisperer/utils/prompt.py",
    "ai_whisperer/json_validator.py": "ai_whisperer/utils/validation.py",
    "ai_whisperer/workspace_detection.py": "ai_whisperer/utils/workspace.py",
    "ai_whisperer/utils.py": "ai_whisperer/utils/helpers.py",
    "ai_whisperer/model_info_provider.py": "ai_whisperer/utils/model_info.py",
    "ai_whisperer/user_message_level.py": "ai_whisperer/utils/message_level.py",
    
    # Extension modules - Batch
    "ai_whisperer/batch/batch_client.py": "ai_whisperer/extensions/batch/client.py",
    "ai_whisperer/batch/debbie_integration.py": "ai_whisperer/extensions/batch/debbie_integration.py",
    "ai_whisperer/batch/intervention.py": "ai_whisperer/extensions/batch/intervention.py",
    "ai_whisperer/batch/monitoring.py": "ai_whisperer/extensions/batch/monitoring.py",
    "ai_whisperer/batch/script_processor.py": "ai_whisperer/extensions/batch/script_processor.py",
    "ai_whisperer/batch/server_manager.py": "ai_whisperer/extensions/batch/server_manager.py",
    "ai_whisperer/batch/websocket_client.py": "ai_whisperer/extensions/batch/websocket_client.py",
    "ai_whisperer/batch/websocket_interceptor.py": "ai_whisperer/extensions/batch/websocket_interceptor.py",
    
    # Extension modules - Monitoring
    "ai_whisperer/logging/debbie_logger.py": "ai_whisperer/extensions/monitoring/debbie_logger.py",
    "ai_whisperer/logging/log_aggregator.py": "ai_whisperer/extensions/monitoring/log_aggregator.py",
    
    # Extension modules - Mailbox
    "ai_whisperer/agents/mailbox.py": "ai_whisperer/extensions/mailbox/mailbox.py",
    "ai_whisperer/agents/mailbox_tools.py": "ai_whisperer/extensions/mailbox/tools.py",
    "ai_whisperer/agents/mail_notification.py": "ai_whisperer/extensions/mailbox/notification.py",
}

# Import mappings (old import -> new import)
IMPORT_MAPPINGS = {
    "ai_whisperer.config": "ai_whisperer.core.config",
    "ai_whisperer.exceptions": "ai_whisperer.core.exceptions",
    "ai_whisperer.logging_custom": "ai_whisperer.core.logging",
    "ai_whisperer.model_capabilities": "ai_whisperer.core.model_capabilities",
    
    "ai_whisperer.ai_service.ai_service": "ai_whisperer.services.ai.base",
    "ai_whisperer.ai_service.openrouter_ai_service": "ai_whisperer.services.ai.openrouter",
    "ai_whisperer.ai_service.tool_calling": "ai_whisperer.services.ai.tool_calling",
    
    "ai_whisperer.ai_loop.stateless_ai_loop": "ai_whisperer.services.execution.ai_loop",
    "ai_whisperer.ai_loop.ai_config": "ai_whisperer.services.execution.ai_config",
    "ai_whisperer.ai_loop.tool_call_accumulator": "ai_whisperer.services.execution.tool_call_accumulator",
    "ai_whisperer.context_management": "ai_whisperer.services.execution.context_management",
    "ai_whisperer.state_management": "ai_whisperer.services.execution.state_management",
    
    "ai_whisperer.agents.base_handler": "ai_whisperer.services.agents.base",
    "ai_whisperer.agents.factory": "ai_whisperer.services.agents.factory",
    "ai_whisperer.agents.registry": "ai_whisperer.services.agents.registry",
    "ai_whisperer.agents.config": "ai_whisperer.services.agents.config",
    "ai_whisperer.agents.stateless_agent": "ai_whisperer.services.agents.stateless_agent",
    "ai_whisperer.agents.session_manager": "ai_whisperer.services.agents.session_manager",
    "ai_whisperer.agents.context_manager": "ai_whisperer.services.agents.context_manager",
    
    "ai_whisperer.cli": "ai_whisperer.interfaces.cli.main",
    "ai_whisperer.cli_commands": "ai_whisperer.interfaces.cli.commands_base",
    "ai_whisperer.cli_commands_batch_mode": "ai_whisperer.interfaces.cli.batch",
    
    "ai_whisperer.path_management": "ai_whisperer.utils.path",
    "ai_whisperer.prompt_system": "ai_whisperer.utils.prompt",
    "ai_whisperer.json_validator": "ai_whisperer.utils.validation",
    "ai_whisperer.workspace_detection": "ai_whisperer.utils.workspace",
    "ai_whisperer.utils": "ai_whisperer.utils.helpers",
    "ai_whisperer.model_info_provider": "ai_whisperer.utils.model_info",
    "ai_whisperer.user_message_level": "ai_whisperer.utils.message_level",
    
    "ai_whisperer.batch.batch_client": "ai_whisperer.extensions.batch.client",
    "ai_whisperer.batch.debbie_integration": "ai_whisperer.extensions.batch.debbie_integration",
    "ai_whisperer.batch.intervention": "ai_whisperer.extensions.batch.intervention",
    "ai_whisperer.batch.monitoring": "ai_whisperer.extensions.batch.monitoring",
    "ai_whisperer.batch.script_processor": "ai_whisperer.extensions.batch.script_processor",
    "ai_whisperer.batch.server_manager": "ai_whisperer.extensions.batch.server_manager",
    "ai_whisperer.batch.websocket_client": "ai_whisperer.extensions.batch.websocket_client",
    "ai_whisperer.batch.websocket_interceptor": "ai_whisperer.extensions.batch.websocket_interceptor",
    
    "ai_whisperer.logging.debbie_logger": "ai_whisperer.extensions.monitoring.debbie_logger",
    "ai_whisperer.logging.log_aggregator": "ai_whisperer.extensions.monitoring.log_aggregator",
    
    "ai_whisperer.agents.mailbox": "ai_whisperer.extensions.mailbox.mailbox",
    "ai_whisperer.agents.mailbox_tools": "ai_whisperer.extensions.mailbox.tools",
    "ai_whisperer.agents.mail_notification": "ai_whisperer.extensions.mailbox.notification",
}


def create_directories():
    """Create the new directory structure."""
    dirs = [
        "ai_whisperer/core",
        "ai_whisperer/models",
        "ai_whisperer/services/ai",
        "ai_whisperer/services/agents/handlers",
        "ai_whisperer/services/execution",
        "ai_whisperer/services/tools/implementations",
        "ai_whisperer/interfaces/cli/commands",
        "ai_whisperer/interfaces/api/handlers",
        "ai_whisperer/interfaces/interactive",
        "ai_whisperer/utils",
        "ai_whisperer/extensions/batch",
        "ai_whisperer/extensions/monitoring",
        "ai_whisperer/extensions/mailbox",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""{}"""\n'.format(dir_path.replace('/', '.')))


def move_file_with_git(old_path: str, new_path: str) -> bool:
    """Move a file using git mv to preserve history."""
    try:
        # Create parent directory if needed
        Path(new_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Use git mv to preserve history
        result = subprocess.run(
            ["git", "mv", old_path, new_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ Moved {old_path} → {new_path}")
            return True
        else:
            print(f"✗ Failed to move {old_path}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error moving {old_path}: {e}")
        return False


def update_imports_in_file(file_path: Path, import_mappings: Dict[str, str]):
    """Update imports in a Python file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Update import statements
        for old_import, new_import in import_mappings.items():
            # Handle "from X import Y" statements
            content = re.sub(
                rf"from {re.escape(old_import)} import",
                f"from {new_import} import",
                content
            )
            # Handle "import X" statements
            content = re.sub(
                rf"^import {re.escape(old_import)}$",
                f"import {new_import}",
                content,
                flags=re.MULTILINE
            )
            # Handle "import X as Y" statements
            content = re.sub(
                rf"import {re.escape(old_import)} as",
                f"import {new_import} as",
                content
            )
        
        if content != original_content:
            file_path.write_text(content)
            print(f"  Updated imports in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"  Error updating imports in {file_path}: {e}")
        return False


def update_all_imports():
    """Update imports in all Python files."""
    print("\nUpdating imports...")
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        if any(skip in root for skip in [".venv", "__pycache__", "node_modules", ".git"]):
            continue
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    # Update imports in each file
    updated_count = 0
    for file_path in python_files:
        if update_imports_in_file(file_path, IMPORT_MAPPINGS):
            updated_count += 1
    
    print(f"\nUpdated imports in {updated_count} files")


def main():
    """Main execution function."""
    print("AIWhisperer Module Reorganization Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("ai_whisperer").exists():
        print("Error: Must run from project root directory")
        return 1
    
    # Create new directory structure
    print("\n1. Creating new directory structure...")
    create_directories()
    
    # Move files
    print("\n2. Moving files to new locations...")
    success_count = 0
    for old_path, new_path in FILE_MOVEMENTS.items():
        if Path(old_path).exists():
            if move_file_with_git(old_path, new_path):
                success_count += 1
        else:
            print(f"  Skipping {old_path} (not found)")
    
    print(f"\nMoved {success_count}/{len(FILE_MOVEMENTS)} files")
    
    # Update imports
    print("\n3. Updating imports throughout codebase...")
    update_all_imports()
    
    # Run tests to verify
    print("\n4. Running tests to verify changes...")
    result = subprocess.run(["python", "-m", "pytest", "-x"], capture_output=True)
    if result.returncode == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed. Review and fix issues.")
    
    print("\n5. Next steps:")
    print("  - Review the changes with 'git status'")
    print("  - Run full test suite")
    print("  - Update documentation")
    print("  - Commit the reorganization")
    
    return 0


if __name__ == "__main__":
    exit(main())