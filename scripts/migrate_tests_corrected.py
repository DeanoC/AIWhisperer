#!/usr/bin/env python3
"""
Corrected migration script for AIWhisperer test reorganization.
This script properly handles the actual file locations in the project.
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict


class TestMigration:
    def __init__(self, project_root: Path, dry_run: bool = True, verbose: bool = True):
        self.project_root = project_root
        self.tests_dir = project_root / 'tests'
        self.dry_run = dry_run
        self.verbose = verbose
        self.operations = []
        self.warnings = []
        self.successes = []
        self.errors = []
        
    def log(self, message: str):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def create_backup_manifest(self):
        """Create a manifest of current test structure for backup purposes."""
        manifest_path = self.project_root / f'test_migration_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'files': {}
        }
        
        # Walk through tests directory and record all files
        for root, dirs, files in os.walk(self.tests_dir):
            for file in files:
                if file.endswith('.py') or file.endswith('.yaml') or file.endswith('.json'):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.tests_dir)
                    manifest['files'][str(rel_path)] = {
                        'size': full_path.stat().st_size,
                        'modified': full_path.stat().st_mtime
                    }
        
        if not self.dry_run:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            self.log(f"Created backup manifest: {manifest_path}")
        else:
            self.log(f"Would create backup manifest: {manifest_path}")
        
        return manifest_path
    
    def define_operations(self):
        """Define all the file operations needed for migration."""
        # Operations are tuples of (operation_type, source_path, target_path)
        # Source paths are relative to tests/ directory
        # Target paths are the desired locations
        
        self.operations = [
            # Root level test files that should be moved to examples or uncategorized
            ('move', 'debbie_practical_example.py', 'examples/debbie_practical_example.py'),
            ('move', 'debbie_demo.py', 'examples/debbie_demo.py'),
            ('move', 'test_processing.py', 'uncategorized/test_processing.py'),
            ('move', 'test_config.py', 'uncategorized/test_config.py'),
            ('move', 'test_utils.py', 'uncategorized/test_utils.py'),
            ('move', 'test_openrouter_api.py', 'uncategorized/test_openrouter_api.py'),
            ('move', 'test_debbie_scenarios.py', 'uncategorized/test_debbie_scenarios.py'),
            
            # Runner tests - rename but keep in place
            ('rename', 'runner_directory_access_tests.py', 'test_runner_directory_access.py'),
            
            # Debugging tools - rename to follow test_ convention
            ('rename', 'debugging-tools/run_batch_test.py', 'debugging-tools/test_run_batch_test.py'),
            ('rename', 'debugging-tools/batch_test_runner.py', 'debugging-tools/test_batch_test_runner.py'),
            ('rename', 'debugging-tools/run_batch_test_existing_server.py', 'debugging-tools/test_run_batch_test_existing_server.py'),
            
            # Interactive server tests are already in the right place, just need some renames
            ('rename', 'interactive_server/performance_metrics_utils.py', 'interactive_server/test_performance_metrics_utils.py'),
            
            # Unit tests that need reorganization
            ('move', 'unit/test_agent_communication.py', 'unit/agents/test_agent_communication.py'),
            ('move', 'unit/test_agent_config.py', 'unit/agents/test_agent_config.py'),
            ('move', 'unit/test_agent_context.py', 'unit/agents/test_agent_context.py'),
            ('move', 'unit/test_agent_context_manager.py', 'unit/agents/test_agent_context_manager.py'),
            ('move', 'unit/test_agent_e_communication.py', 'unit/agents/test_agent_e_communication.py'),
            ('move', 'unit/test_agent_e_external_adapters.py', 'unit/agents/test_agent_e_external_adapters.py'),
            ('move', 'unit/test_agent_e_integration.py', 'unit/agents/test_agent_e_integration.py'),
            ('move', 'unit/test_agent_e_task_decomposition.py', 'unit/agents/test_agent_e_task_decomposition.py'),
            ('move', 'unit/test_agent_factory.py', 'unit/agents/test_agent_factory.py'),
            ('move', 'unit/test_agent_inspect_command.py', 'unit/agents/test_agent_inspect_command.py'),
            ('move', 'unit/test_agent_jsonrpc.py', 'unit/agents/test_agent_jsonrpc.py'),
            ('move', 'unit/test_agent_registry.py', 'unit/agents/test_agent_registry.py'),
            ('move', 'unit/test_agent_stateless.py', 'unit/agents/test_agent_stateless.py'),
            ('move', 'unit/test_agent_tool_filtering.py', 'unit/agents/test_agent_tool_filtering.py'),
            ('move', 'unit/test_agent_tool_permission.py', 'unit/agents/test_agent_tool_permission.py'),
            ('move', 'unit/test_agent_tools.py', 'unit/agents/test_agent_tools.py'),
            ('move', 'unit/test_debbie_command.py', 'unit/agents/test_debbie_command.py'),
            ('move', 'unit/test_debbie_observer.py', 'unit/agents/test_debbie_observer.py'),
            ('move', 'unit/test_mailbox_system.py', 'unit/agents/test_mailbox_system.py'),
            ('move', 'unit/test_planner_handler.py', 'unit/agents/test_planner_handler.py'),
            ('move', 'unit/test_planner_tools.py', 'unit/agents/test_planner_tools.py'),
            
            # AI Loop tests
            ('move', 'unit/test_refactored_ai_loop.py', 'unit/ai_loop/test_refactored_ai_loop.py'),
            ('move', 'unit/test_stateless_ailoop.py', 'unit/ai_loop/test_stateless_ailoop.py'),
            ('move', 'unit/test_ai_interaction_history.py', 'unit/ai_loop/test_ai_interaction_history.py'),
            ('move', 'unit/test_continuation_depth.py', 'unit/ai_loop/test_continuation_depth.py'),
            ('move', 'unit/test_continuation_strategy.py', 'unit/ai_loop/test_continuation_strategy.py'),
            
            # AI Service tests
            ('move', 'unit/test_ai_service_interaction.py', 'unit/ai_service/test_ai_service_interaction.py'),
            ('move', 'unit/test_openrouter_advanced_features.py', 'unit/ai_service/test_openrouter_advanced_features.py'),
            ('move', 'unit/test_openrouter_api_detailed.py', 'unit/ai_service/test_openrouter_api_detailed.py'),
            ('move', 'unit/test_tool_calling_standard.py', 'unit/ai_service/test_tool_calling_standard.py'),
            
            # Context tests
            ('move', 'unit/test_context_manager.py', 'unit/context/test_context_manager.py'),
            ('move', 'unit/test_context_provider.py', 'unit/context/test_context_provider.py'),
            ('move', 'unit/test_context_serialization.py', 'unit/context/test_context_serialization.py'),
            ('move', 'unit/test_context_tracking.py', 'unit/context/test_context_tracking.py'),
            
            # Postprocessing tests
            ('move', 'unit/test_postprocessing_add_items.py', 'unit/postprocessing/test_postprocessing_add_items.py'),
            ('move', 'unit/test_postprocessing_backticks.py', 'unit/postprocessing/test_postprocessing_backticks.py'),
            ('move', 'unit/test_postprocessing_fields.py', 'unit/postprocessing/test_postprocessing_fields.py'),
            ('move', 'unit/test_postprocessing_pipeline.py', 'unit/postprocessing/test_postprocessing_pipeline.py'),
            ('move', 'unit/test_postprocessing_text_fields.py', 'unit/postprocessing/test_postprocessing_text_fields.py'),
            ('move', 'unit/test_postprocessing_type_preservation.py', 'unit/postprocessing/test_postprocessing_type_preservation.py'),
            ('move', 'unit/test_scripted_postprocessing.py', 'unit/postprocessing/test_scripted_postprocessing.py'),
            ('move', 'unit/test_format_json.py', 'unit/postprocessing/test_format_json.py'),
            
            # Tool tests
            ('move', 'unit/test_codebase_analysis_tools.py', 'unit/tools/test_codebase_analysis_tools.py'),
            ('move', 'unit/test_execute_command_tool.py', 'unit/tools/test_execute_command_tool.py'),
            ('move', 'unit/test_file_tools.py', 'unit/tools/test_file_tools.py'),
            ('move', 'unit/test_find_pattern_tool.py', 'unit/tools/test_find_pattern_tool.py'),
            ('move', 'unit/test_get_file_content_tool.py', 'unit/tools/test_get_file_content_tool.py'),
            ('move', 'unit/test_list_directory_tool.py', 'unit/tools/test_list_directory_tool.py'),
            ('move', 'unit/test_plan_tools.py', 'unit/tools/test_plan_tools.py'),
            ('move', 'unit/test_python_ast_json_design.py', 'unit/tools/test_python_ast_json_design.py'),
            ('move', 'unit/test_python_ast_json_tool.py', 'unit/tools/test_python_ast_json_tool.py'),
            ('move', 'unit/test_python_ast_parsing.py', 'unit/tools/test_python_ast_parsing.py'),
            ('move', 'unit/test_python_ast_parsing_advanced.py', 'unit/tools/test_python_ast_parsing_advanced.py'),
            ('move', 'unit/test_rfc_tools.py', 'unit/tools/test_rfc_tools.py'),
            ('move', 'unit/test_rfc_tools_complete.py', 'unit/tools/test_rfc_tools_complete.py'),
            ('move', 'unit/test_search_files_tool.py', 'unit/tools/test_search_files_tool.py'),
            ('move', 'unit/test_tool_management.py', 'unit/tools/test_tool_management.py'),
            ('move', 'unit/test_tool_sets.py', 'unit/tools/test_tool_sets.py'),
            ('move', 'unit/test_tool_tags.py', 'unit/tools/test_tool_tags.py'),
            ('move', 'unit/test_tool_usage_logging.py', 'unit/tools/test_tool_usage_logging.py'),
            ('move', 'unit/test_web_tools.py', 'unit/tools/test_web_tools.py'),
            ('move', 'unit/test_workspace_stats_tool.py', 'unit/tools/test_workspace_stats_tool.py'),
            ('move', 'unit/test_workspace_tools.py', 'unit/tools/test_workspace_tools.py'),
            
            # Command tests
            ('move', 'unit/test_cli.py', 'unit/commands/test_cli.py'),
            ('move', 'unit/test_cli_workspace_validation.py', 'unit/commands/test_cli_workspace_validation.py'),
            ('move', 'unit/test_clear_command.py', 'unit/commands/test_clear_command.py'),
            
            # Batch mode unit tests already have their own directory
            # Just need to move the performance test
            ('move', 'unit/batch_mode/test_batch_command_performance.py', 'unit/batch/test_batch_command_performance.py'),
            ('move', 'unit/batch_mode/test_batch_command_tool.py', 'unit/batch/test_batch_command_tool.py'),
            ('move', 'unit/batch_mode/test_debbie_agent_config.py', 'unit/batch/test_debbie_agent_config.py'),
            ('move', 'unit/batch_mode/test_debbie_prompt_system.py', 'unit/batch/test_debbie_prompt_system.py'),
            ('move', 'unit/batch_mode/test_script_parser_security.py', 'unit/batch/test_script_parser_security.py'),
            ('move', 'unit/batch_mode/test_script_parser_tool.py', 'unit/batch/test_script_parser_tool.py'),
            ('move', 'unit/batch_mode/test_script_parser_validation.py', 'unit/batch/test_script_parser_validation.py'),
            
            # Integration tests batch mode
            ('move', 'integration/batch_mode/test_batch_performance.py', 'integration/batch_mode/test_batch_performance.py'),
            ('move', 'integration/batch_mode/test_batch_script_execution.py', 'integration/batch_mode/test_batch_script_execution.py'),
            ('move', 'integration/batch_mode/test_debbie_agent_integration.py', 'integration/batch_mode/test_debbie_agent_integration.py'),
            
            # Integration tests for RFC/Plan
            ('move', 'integration/test_patricia_rfc_plan_integration.py', 'integration/rfc_plan/test_patricia_rfc_plan_integration.py'),
            ('move', 'integration/test_rfc_plan_bidirectional.py', 'integration/rfc_plan/test_rfc_plan_bidirectional.py'),
            ('move', 'integration/test_plan_error_recovery.py', 'integration/rfc_plan/test_plan_error_recovery.py'),
            
            # Integration tests for sessions
            ('move', 'integration/test_session_integration.py', 'integration/session/test_session_integration.py'),
            ('move', 'integration/test_interactive_session.py', 'integration/session/test_interactive_session.py'),
            ('move', 'integration/test_conversation_persistence.py', 'integration/session/test_conversation_persistence.py'),
            ('move', 'integration/test_project_settings_persistence.py', 'integration/session/test_project_settings_persistence.py'),
            
            # Performance tests from interactive_server
            ('move', 'interactive_server/test_ai_service_timeout.py', 'performance/test_ai_service_timeout.py'),
            ('move', 'interactive_server/test_long_running_session.py', 'performance/test_long_running_session.py'),
            ('move', 'interactive_server/test_memory_usage_under_load.py', 'performance/test_memory_usage_under_load.py'),
            ('move', 'unit/test_prompt_system_performance.py', 'performance/test_prompt_system_performance.py'),
            
            # Interactive server WebSocket tests
            ('move', 'interactive_server/test_websocket_endpoint.py', 'interactive_server/websocket/test_websocket_endpoint.py'),
            ('move', 'interactive_server/test_websocket_stress.py', 'interactive_server/websocket/test_websocket_stress.py'),
            ('move', 'interactive_server/test_websocket_stress_subprocess.py', 'interactive_server/websocket/test_websocket_stress_subprocess.py'),
            ('move', 'interactive_server/test_notifications_streaming.py', 'interactive_server/websocket/test_notifications_streaming.py'),
            
            # Interactive server JSON-RPC tests
            ('move', 'interactive_server/test_jsonrpc_notifications.py', 'interactive_server/jsonrpc/test_jsonrpc_notifications.py'),
            ('move', 'interactive_server/test_jsonrpc_protocol.py', 'interactive_server/jsonrpc/test_jsonrpc_protocol.py'),
            ('move', 'interactive_server/test_jsonrpc_protocol_more.py', 'interactive_server/jsonrpc/test_jsonrpc_protocol_more.py'),
            ('move', 'interactive_server/test_jsonrpc_routing.py', 'interactive_server/jsonrpc/test_jsonrpc_routing.py'),
            
            # Interactive server handler tests
            ('move', 'interactive_server/test_real_session_handlers.py', 'interactive_server/handlers/test_real_session_handlers.py'),
            ('move', 'interactive_server/test_tool_result_handler.py', 'interactive_server/handlers/test_tool_result_handler.py'),
            ('move', 'interactive_server/test_project_setup.py', 'interactive_server/handlers/test_project_setup.py'),
            
            # Fixtures - move projects
            ('move', 'simple_project', 'fixtures/projects/simple_project'),
            ('move', 'code_generator', 'fixtures/projects/code_generator'),
            
            # Note: We do NOT rename conftest.py files - they need to keep their names for pytest
        ]
        
        # Add operations to create necessary directories
        self.new_directories = [
            'unit/agents', 'unit/ai_loop', 'unit/ai_service',
            'unit/batch', 'unit/commands', 'unit/context',
            'unit/postprocessing', 'unit/tools',
            'integration/batch_mode', 'integration/rfc_plan',
            'integration/session', 'interactive_server/websocket',
            'interactive_server/jsonrpc', 'interactive_server/handlers',
            'performance', 'examples', 'fixtures/projects',
            'fixtures/scripts', 'uncategorized'
        ]
    
    def check_file_existence(self):
        """Check if all source files exist before attempting migration."""
        for op_type, source, target in self.operations:
            source_path = self.tests_dir / source
            if not source_path.exists():
                self.warnings.append(f"Source file not found: {source}")
            else:
                # Check if target already exists
                target_path = self.tests_dir / target
                if target_path.exists() and op_type == 'move':
                    self.warnings.append(f"Target already exists: {target}")
    
    def create_directories(self):
        """Create new directory structure."""
        for dir_path in self.new_directories:
            full_path = self.tests_dir / dir_path
            if not full_path.exists():
                if not self.dry_run:
                    full_path.mkdir(parents=True, exist_ok=True)
                self.log(f"{'Would create' if self.dry_run else 'Created'} directory: {dir_path}")
    
    def execute_operations(self):
        """Execute the file operations."""
        for op_type, source, target in self.operations:
            source_path = self.tests_dir / source
            target_path = self.tests_dir / target
            
            if not source_path.exists():
                self.errors.append(f"Cannot {op_type}: {source} (file not found)")
                continue
            
            try:
                if op_type == 'move':
                    if target_path.exists():
                        self.errors.append(f"Cannot move: {target} already exists")
                        continue
                    
                    if not self.dry_run:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source_path), str(target_path))
                    self.successes.append(f"Moved: {source} → {target}")
                    self.log(f"{'Would move' if self.dry_run else 'Moved'}: {source} → {target}")
                    
                elif op_type == 'rename':
                    if target_path.exists():
                        self.errors.append(f"Cannot rename: {target} already exists")
                        continue
                    
                    if not self.dry_run:
                        source_path.rename(target_path)
                    self.successes.append(f"Renamed: {source} → {target}")
                    self.log(f"{'Would rename' if self.dry_run else 'Renamed'}: {source} → {target}")
                    
            except Exception as e:
                self.errors.append(f"Error {op_type} {source}: {str(e)}")
    
    def print_summary(self):
        """Print a summary of the migration."""
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        
        if self.dry_run:
            print("\n** DRY RUN MODE - No changes were made **\n")
        
        print(f"Total operations defined: {len(self.operations)}")
        print(f"Successful operations: {len(self.successes)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.successes and self.verbose:
            print(f"\nSUCCESSFUL OPERATIONS ({len(self.successes)}):")
            for success in self.successes[:10]:  # Show first 10
                print(f"  ✓ {success}")
            if len(self.successes) > 10:
                print(f"  ... and {len(self.successes) - 10} more")
        
        print("\n" + "="*60)
    
    def run(self):
        """Run the migration process."""
        print("AIWhisperer Test Migration Tool")
        print("="*60)
        
        if self.dry_run:
            print("Running in DRY RUN mode - no changes will be made")
        else:
            print("Running in EXECUTE mode - files will be moved!")
            if '--force' not in sys.argv:
                response = input("Are you sure you want to proceed? (yes/no): ")
                if response.lower() != 'yes':
                    print("Migration cancelled.")
                    return
            else:
                print("FORCE mode enabled - proceeding without confirmation")
        
        print()
        
        # Step 1: Create backup manifest
        self.log("Step 1: Creating backup manifest...")
        self.create_backup_manifest()
        
        # Step 2: Define operations
        self.log("\nStep 2: Defining operations...")
        self.define_operations()
        
        # Step 3: Check file existence
        self.log("\nStep 3: Checking file existence...")
        self.check_file_existence()
        
        # Step 4: Create directories
        self.log("\nStep 4: Creating directory structure...")
        self.create_directories()
        
        # Step 5: Execute operations
        self.log("\nStep 5: Executing file operations...")
        self.execute_operations()
        
        # Step 6: Print summary
        self.print_summary()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate AIWhisperer test files to new structure')
    parser.add_argument('--execute', action='store_true', 
                        help='Execute the migration (default is dry-run)')
    parser.add_argument('--force', action='store_true',
                        help='Skip confirmation prompt when executing')
    parser.add_argument('--quiet', action='store_true',
                        help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    
    migrator = TestMigration(
        project_root=project_root,
        dry_run=not args.execute,
        verbose=not args.quiet
    )
    
    migrator.run()


if __name__ == '__main__':
    main()