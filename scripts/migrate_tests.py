#!/usr/bin/env python3
"""
Migration script for AIWhisperer test reorganization.
This script automates the file moves and renames.
"""

import os
import shutil
from pathlib import Path


def migrate_tests():
    """Execute the test migration."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / 'tests'
    
    # Create new directories
    new_dirs = [
        'unit/agents', 'unit/ai_loop', 'unit/ai_service',
        'unit/batch', 'unit/commands', 'unit/context',
        'unit/postprocessing', 'unit/tools',
        'integration/batch_mode', 'integration/rfc_plan',
        'integration/session', 'interactive_server/websocket',
        'interactive_server/jsonrpc', 'interactive_server/handlers',
        'performance', 'examples', 'fixtures/projects',
        'fixtures/scripts'
    ]
    
    for dir_path in new_dirs:
        (tests_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    # File operations
    operations = [
        ('move', 'debbie_practical_example.py', 'tests/examples/debbie_practical_example.py'),
        ('move', 'test_processing.py', 'tests/uncategorized/test_processing.py'),
        ('move', 'debbie_demo.py', 'tests/examples/debbie_demo.py'),
        ('move', 'test_config.py', 'tests/uncategorized/test_config.py'),
        ('move', 'test_utils.py', 'tests/uncategorized/test_utils.py'),
        ('move', 'test_openrouter_api.py', 'tests/uncategorized/test_openrouter_api.py'),
        ('move', 'test_debbie_scenarios.py', 'tests/uncategorized/test_debbie_scenarios.py'),
        ('move', 'debugging-tools/run_batch_test_existing_server.py', 'tests/tools/test_run_batch_test_existing_server.py'),
        ('move', 'unit/test_jsonrpc_handlers_refactor.py', 'tests/unit/test_jsonrpc_handlers_refactor.py'),
        ('move', 'unit/test_agent_e_integration.py', 'tests/unit/test_agent_e_integration.py'),
        ('move', 'unit/test_debbie_observer.py', 'tests/unit/test_debbie_observer.py'),
        ('move', 'unit/test_session_manager_refactor.py', 'tests/unit/test_session_manager_refactor.py'),
        ('move', 'unit/test_prompt_system_performance.py', 'tests/unit/test_prompt_system_performance.py'),
        ('move', 'unit/test_agent_jsonrpc.py', 'tests/unit/test_agent_jsonrpc.py'),
        ('move', 'unit/test_session_manager.py', 'tests/unit/test_session_manager.py'),
        ('move', 'unit/batch_mode/test_batch_command_performance.py', 'tests/unit/batch/test_batch_command_performance.py'),
        ('move', 'integration/test_agent_jsonrpc_ws.py', 'tests/integration/test_agent_jsonrpc_ws.py'),
        ('move', 'integration/batch_mode/test_batch_performance.py', 'tests/integration/test_batch_performance.py'),
        ('move', 'interactive_server/test_notifications_streaming.py', 'tests/interactive_server/test_notifications_streaming.py'),
        ('move', 'interactive_server/test_tool_result_handler.py', 'tests/interactive_server/test_tool_result_handler.py'),
        ('move', 'interactive_server/test_interactive_message_models.py', 'tests/interactive_server/test_interactive_message_models.py'),
        ('move', 'interactive_server/performance_metrics_utils.py', 'tests/interactive_server/test_performance_metrics_utils.py'),
        ('move', 'interactive_server/test_real_session_handlers.py', 'tests/interactive_server/test_real_session_handlers.py'),
        ('move', 'interactive_server/test_message_models.py', 'tests/interactive_server/test_message_models.py'),
        ('move', 'interactive_server/test_integration_end_to_end.py', 'tests/interactive_server/test_integration_end_to_end.py'),
        ('move', 'interactive_server/test_ai_service_timeout.py', 'tests/interactive_server/test_ai_service_timeout.py'),
        ('move', 'interactive_server/test_long_running_session.py', 'tests/interactive_server/test_long_running_session.py'),
        ('move', 'interactive_server/test_openrouter_shutdown_patch.py', 'tests/interactive_server/test_openrouter_shutdown_patch.py'),
        ('move', 'interactive_server/test_interactive_message_models_roundtrip.py', 'tests/interactive_server/test_interactive_message_models_roundtrip.py'),
        ('move', 'interactive_server/test_interactive_client_script.py', 'tests/interactive_server/test_interactive_client_script.py'),
        ('move', 'interactive_server/test_mocked_ailoop.py', 'tests/interactive_server/test_mocked_ailoop.py'),
        ('move', 'interactive_server/test_project_setup.py', 'tests/interactive_server/test_project_setup.py'),
        ('move', 'interactive_server/test_memory_usage_under_load.py', 'tests/interactive_server/test_memory_usage_under_load.py'),
        ('rename', 'conftest.py', 'test_conftest.py'),
        ('rename', 'runner_directory_access_tests.py', 'test_runner_directory_access_tests.py'),
        ('rename', 'debugging-tools/run_batch_test.py', 'debugging-tools/test_run_batch_test.py'),
        ('rename', 'debugging-tools/batch_test_runner.py', 'debugging-tools/test_batch_test_runner.py'),
        ('rename', 'unit/conftest.py', 'unit/test_conftest.py'),
        ('rename', 'interactive_server/conftest.py', 'interactive_server/test_conftest.py'),
    ]
    
    # Execute operations
    for op_type, old_path, new_path in operations:
        old_full = tests_dir / old_path
        new_full = tests_dir / new_path
        
        if old_full.exists():
            print(f'{op_type}: {old_path} → {new_path}')
            new_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_full), str(new_full))
        else:
            print(f'Warning: {old_path} not found')
    
    print('\nMigration complete!')


if __name__ == '__main__':
    migrate_tests()