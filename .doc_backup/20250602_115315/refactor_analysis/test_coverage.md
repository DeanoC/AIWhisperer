# Test Coverage Analysis

## Tested Modules

### `ai_whisperer`
Covered by 1 test file(s):
- tests/unit/test_cli_workspace_validation.py

### `ai_whisperer.agents.agent`
Covered by 3 test file(s):
- tests/unit/test_jsonrpc_handlers_refactor.py
- tests/unit/test_agent_factory.py
- tests/unit/test_agent_stateless.py

### `ai_whisperer.agents.agent_communication`
Covered by 1 test file(s):
- tests/unit/test_agent_e_communication.py

### `ai_whisperer.agents.agent_e_exceptions`
Covered by 1 test file(s):
- tests/unit/test_agent_e_task_decomposition.py

### `ai_whisperer.agents.agent_e_handler`
Covered by 1 test file(s):
- tests/unit/test_agent_e_communication.py

### `ai_whisperer.agents.config`
Covered by 9 test file(s):
- tests/unit/test_jsonrpc_handlers_refactor.py
- tests/unit/test_agent_e_integration.py
- tests/unit/test_agent_factory.py
- tests/unit/test_agent_config.py
- tests/unit/test_agent_stateless.py
- ... and 4 more

### `ai_whisperer.agents.context_manager`
Covered by 2 test file(s):
- tests/unit/test_agent_context_manager.py
- tests/integration/test_context_integration.py

### `ai_whisperer.agents.continuation_strategy`
Covered by 6 test file(s):
- tests/unit/test_continuation_strategy.py
- tests/integration/test_continuation_simple.py
- tests/integration/test_continuation_verification.py
- tests/integration/test_agent_continuation_integration.py
- tests/integration/test_continuation_progress_tracking.py
- ... and 1 more

### `ai_whisperer.agents.decomposed_task`
Covered by 2 test file(s):
- tests/unit/test_agent_e_task_decomposition.py
- tests/unit/test_agent_e_external_adapters.py

### `ai_whisperer.agents.external_adapters`
Covered by 1 test file(s):
- tests/unit/test_agent_e_external_adapters.py

### `ai_whisperer.agents.external_agent_result`
Covered by 1 test file(s):
- tests/unit/test_agent_e_external_adapters.py

### `ai_whisperer.agents.factory`
Covered by 3 test file(s):
- tests/unit/test_jsonrpc_handlers_refactor.py
- tests/unit/test_agent_factory.py
- tests/integration/test_model_compatibility_simple.py

### `ai_whisperer.agents.mailbox`
Covered by 1 test file(s):
- tests/unit/test_mailbox_system.py

### `ai_whisperer.agents.planner_handler`
Covered by 1 test file(s):
- tests/unit/test_planner_handler.py

### `ai_whisperer.agents.planner_tools`
Covered by 1 test file(s):
- tests/unit/test_planner_tools.py

### `ai_whisperer.agents.prompt_optimizer`
Covered by 1 test file(s):
- tests/unit/test_prompt_optimizer.py

### `ai_whisperer.agents.registry`
Covered by 15 test file(s):
- tests/unit/test_agent_tool_permission.py
- tests/unit/test_agent_e_integration.py
- tests/unit/test_agent_context_manager.py
- tests/unit/test_agent_tool_filtering.py
- tests/unit/test_agent_registry.py
- ... and 10 more

### `ai_whisperer.agents.session_manager`
Covered by 2 test file(s):
- tests/unit/test_agent_communication.py
- tests/unit/test_session_manager.py

### `ai_whisperer.agents.stateless_agent`
Covered by 7 test file(s):
- tests/unit/test_agent_e_integration.py
- tests/unit/test_agent_stateless.py
- tests/integration/test_agent_continuation_integration.py
- tests/integration/test_continuation_progress_tracking.py
- tests/integration/test_model_continuation_compatibility.py
- ... and 2 more

### `ai_whisperer.agents.task_decomposer`
Covered by 1 test file(s):
- tests/unit/test_agent_e_task_decomposition.py

### `ai_whisperer.ai_loop.ai_config`
Covered by 9 test file(s):
- tests/test_openrouter_api.py
- tests/unit/test_ai_interaction_history.py
- tests/unit/test_stateless_ailoop.py
- tests/unit/test_openrouter_advanced_features.py
- tests/unit/test_openrouter_api_detailed.py
- ... and 4 more

### `ai_whisperer.ai_loop.stateless_ai_loop`
Covered by 5 test file(s):
- tests/unit/test_stateless_ailoop.py
- tests/unit/test_agent_e_integration.py
- tests/unit/test_agent_stateless.py
- tests/integration/test_agent_continuation_integration.py
- tests/integration/test_agent_continuation_fix.py

### `ai_whisperer.ai_service.ai_service`
Covered by 4 test file(s):
- tests/unit/test_ai_service_interaction.py
- tests/unit/test_plan_tools.py
- tests/interactive_server/test_tool_result_handler.py
- tests/interactive_server/test_mocked_ailoop.py

### `ai_whisperer.ai_service.openrouter_ai_service`
Covered by 8 test file(s):
- tests/test_openrouter_api.py
- tests/unit/test_ai_interaction_history.py
- tests/unit/test_openrouter_advanced_features.py
- tests/unit/test_openrouter_api_detailed.py
- tests/unit/test_ai_service_interaction.py
- ... and 3 more

### `ai_whisperer.ai_service.tool_calling`
Covered by 1 test file(s):
- tests/unit/test_tool_calling_standard.py

### `ai_whisperer.batch.batch_client`
Covered by 1 test file(s):
- tests/integration/test_patricia_rfc_plan_integration.py

### `ai_whisperer.batch.debbie_integration`
Covered by 1 test file(s):
- tests/test_debbie_scenarios.py

### `ai_whisperer.batch.monitoring`
Covered by 1 test file(s):
- tests/test_debbie_scenarios.py

### `ai_whisperer.batch.script_processor`
Covered by 1 test file(s):
- tests/integration/test_patricia_rfc_plan_integration.py

### `ai_whisperer.batch.websocket_interceptor`
Covered by 1 test file(s):
- tests/test_debbie_scenarios.py

### `ai_whisperer.commands`
Covered by 1 test file(s):
- tests/unit/test_agent_inspect_command.py

### `ai_whisperer.commands.debbie`
Covered by 1 test file(s):
- tests/unit/test_debbie_command.py

### `ai_whisperer.commands.echo`
Covered by 1 test file(s):
- ai_whisperer/commands/test_commands.py

### `ai_whisperer.commands.errors`
Covered by 1 test file(s):
- tests/unit/test_debbie_command.py

### `ai_whisperer.commands.registry`
Covered by 1 test file(s):
- tests/unit/test_debbie_command.py

### `ai_whisperer.commands.status`
Covered by 1 test file(s):
- ai_whisperer/commands/test_commands.py

### `ai_whisperer.config`
Covered by 4 test file(s):
- tests/test_config.py
- tests/integration/test_model_compatibility_simple.py
- tests/integration/test_batch_mode_e2e.py
- tests/integration/test_model_continuation_compatibility.py

### `ai_whisperer.context.agent_context`
Covered by 11 test file(s):
- tests/unit/test_agent_e_integration.py
- tests/unit/test_agent_context.py
- tests/unit/test_agent_factory.py
- tests/unit/test_direct_streaming.py
- tests/unit/test_context_serialization.py
- ... and 6 more

### `ai_whisperer.context.context_item`
Covered by 2 test file(s):
- tests/unit/test_context_tracking.py
- tests/unit/test_clear_command.py

### `ai_whisperer.context.context_manager`
Covered by 3 test file(s):
- tests/unit/test_context_tracking.py
- tests/unit/test_clear_command.py
- tests/integration/test_conversation_persistence.py

### `ai_whisperer.context.provider`
Covered by 4 test file(s):
- tests/unit/test_stateless_ailoop.py
- tests/unit/test_agent_context.py
- tests/unit/test_context_serialization.py
- tests/unit/test_context_provider.py

### `ai_whisperer.context_management`
Covered by 3 test file(s):
- tests/unit/test_context_manager.py
- tests/unit/test_state_management.py
- tests/integration/test_context_integration.py

### `ai_whisperer.exceptions`
Covered by 10 test file(s):
- tests/test_processing.py
- tests/test_config.py
- tests/test_openrouter_api.py
- tests/unit/test_file_tools.py
- tests/unit/test_search_files_tool.py
- ... and 5 more

### `ai_whisperer.json_validator`
Covered by 1 test file(s):
- tests/integration/test_runner_plan_ingestion.py

### `ai_whisperer.logging_custom`
Covered by 5 test file(s):
- tests/test_debbie_scenarios.py
- tests/unit/test_logging.py
- tests/integration/test_agent_jsonrpc_ws.py
- tests/interactive_server/test_tool_result_handler.py
- tests/interactive_server/test_ai_service_timeout.py

### `ai_whisperer.model_capabilities`
Covered by 3 test file(s):
- tests/integration/test_continuation_simple.py
- tests/integration/test_continuation_verification.py
- tests/integration/test_model_compatibility_simple.py

### `ai_whisperer.path_management`
Covered by 33 test file(s):
- tests/test_config.py
- tests/unit/test_file_service.py
- tests/unit/test_context_tracking.py
- tests/unit/test_file_tools.py
- tests/unit/test_workspace_stats_tool.py
- ... and 28 more

### `ai_whisperer.plan_parser`
Covered by 2 test file(s):
- tests/unit/test_plan_ingestion.py
- tests/integration/test_runner_plan_ingestion.py

### `ai_whisperer.processing`
Covered by 1 test file(s):
- tests/test_processing.py

### `ai_whisperer.prompt_system`
Covered by 5 test file(s):
- tests/unit/test_prompt_system_performance.py
- tests/unit/test_enhanced_prompt_system.py
- tests/integration/test_agent_continuation_integration.py
- tests/integration/test_model_continuation_compatibility.py
- tests/unit/batch_mode/test_debbie_prompt_system.py

### `ai_whisperer.state_management`
Covered by 1 test file(s):
- tests/unit/test_state_management.py

### `ai_whisperer.tools.analyze_languages_tool`
Covered by 1 test file(s):
- tests/unit/test_codebase_analysis_tools.py

### `ai_whisperer.tools.base_tool`
Covered by 9 test file(s):
- tests/unit/test_agent_tool_permission.py
- tests/unit/test_tool_calling_standard.py
- tests/unit/test_python_ast_json_tool.py
- tests/unit/test_agent_tool_filtering.py
- tests/unit/test_agent_tools.py
- ... and 4 more

### `ai_whisperer.tools.batch_command_tool`
Covered by 4 test file(s):
- tests/unit/batch_mode/test_batch_command_tool.py
- tests/unit/batch_mode/test_batch_command_performance.py
- tests/integration/batch_mode/test_batch_performance.py
- tests/integration/batch_mode/test_batch_script_execution.py

### `ai_whisperer.tools.create_plan_from_rfc_tool`
Covered by 1 test file(s):
- tests/unit/test_plan_tools.py

### `ai_whisperer.tools.create_rfc_tool`
Covered by 6 test file(s):
- tests/unit/test_rfc_tools.py
- tests/unit/test_rfc_extension_regression.py
- tests/unit/test_rfc_move_extensions.py
- tests/unit/test_rfc_naming.py
- tests/integration/test_rfc_plan_bidirectional.py
- ... and 1 more

### `ai_whisperer.tools.delete_plan_tool`
Covered by 2 test file(s):
- tests/integration/test_rfc_plan_bidirectional.py
- tests/integration/test_plan_error_recovery.py

### `ai_whisperer.tools.delete_rfc_tool`
Covered by 2 test file(s):
- tests/unit/test_rfc_extension_regression.py
- tests/unit/test_rfc_naming.py

### `ai_whisperer.tools.execute_command_tool`
Covered by 3 test file(s):
- tests/unit/test_execute_command_tool.py
- tests/unit/test_tool_tags.py
- tests/integration/test_ai_tool_usage.py

### `ai_whisperer.tools.fetch_url_tool`
Covered by 1 test file(s):
- tests/unit/test_web_tools.py

### `ai_whisperer.tools.find_pattern_tool`
Covered by 1 test file(s):
- tests/unit/test_find_pattern_tool.py

### `ai_whisperer.tools.find_similar_code_tool`
Covered by 1 test file(s):
- tests/unit/test_codebase_analysis_tools.py

### `ai_whisperer.tools.get_file_content_tool`
Covered by 2 test file(s):
- tests/unit/test_workspace_tools.py
- tests/unit/test_get_file_content_tool.py

### `ai_whisperer.tools.get_project_structure_tool`
Covered by 1 test file(s):
- tests/unit/test_codebase_analysis_tools.py

### `ai_whisperer.tools.list_directory_tool`
Covered by 2 test file(s):
- tests/unit/test_workspace_tools.py
- tests/unit/test_list_directory_tool.py

### `ai_whisperer.tools.list_plans_tool`
Covered by 1 test file(s):
- tests/unit/test_plan_tools.py

### `ai_whisperer.tools.list_rfcs_tool`
Covered by 2 test file(s):
- tests/unit/test_rfc_tools.py
- tests/unit/test_rfc_naming.py

### `ai_whisperer.tools.monitoring_control_tool`
Covered by 1 test file(s):
- tests/unit/test_tool_calling_standard.py

### `ai_whisperer.tools.move_plan_tool`
Covered by 2 test file(s):
- tests/unit/test_plan_tools.py
- tests/integration/test_rfc_plan_bidirectional.py

### `ai_whisperer.tools.move_rfc_tool`
Covered by 4 test file(s):
- tests/unit/test_rfc_extension_regression.py
- tests/unit/test_rfc_move_extensions.py
- tests/unit/test_rfc_tools_complete.py
- tests/unit/test_rfc_naming.py

### `ai_whisperer.tools.prepare_plan_from_rfc_tool`
Covered by 2 test file(s):
- tests/integration/test_rfc_plan_bidirectional.py
- tests/integration/test_plan_error_recovery.py

### `ai_whisperer.tools.python_ast_json_tool`
Covered by 12 test file(s):
- tests/unit/test_error_handling_ast_validation.py
- tests/unit/test_python_ast_parsing.py
- tests/unit/test_error_handling_edge_cases.py
- tests/unit/test_python_ast_json_tool.py
- tests/unit/test_ast_to_json_conversion.py
- ... and 7 more

### `ai_whisperer.tools.read_file_tool`
Covered by 3 test file(s):
- tests/unit/test_file_tools.py
- tests/unit/test_tool_tags.py
- tests/integration/test_ai_tool_usage.py

### `ai_whisperer.tools.read_plan_tool`
Covered by 3 test file(s):
- tests/unit/test_plan_tools.py
- tests/integration/test_rfc_plan_bidirectional.py
- tests/integration/test_plan_error_recovery.py

### `ai_whisperer.tools.read_rfc_tool`
Covered by 2 test file(s):
- tests/unit/test_rfc_tools.py
- tests/unit/test_rfc_naming.py

### `ai_whisperer.tools.save_generated_plan_tool`
Covered by 2 test file(s):
- tests/integration/test_rfc_plan_bidirectional.py
- tests/integration/test_plan_error_recovery.py

### `ai_whisperer.tools.script_parser_tool`
Covered by 7 test file(s):
- tests/unit/batch_mode/test_script_parser_security.py
- tests/unit/batch_mode/test_script_parser_tool.py
- tests/unit/batch_mode/test_batch_command_tool.py
- tests/unit/batch_mode/test_script_parser_validation.py
- tests/unit/batch_mode/test_batch_command_performance.py
- ... and 2 more

### `ai_whisperer.tools.search_files_tool`
Covered by 2 test file(s):
- tests/unit/test_workspace_tools.py
- tests/unit/test_search_files_tool.py

### `ai_whisperer.tools.session_analysis_tool`
Covered by 1 test file(s):
- tests/unit/test_tool_calling_standard.py

### `ai_whisperer.tools.session_health_tool`
Covered by 1 test file(s):
- tests/unit/test_tool_calling_standard.py

### `ai_whisperer.tools.tool_registration`
Covered by 1 test file(s):
- tests/unit/test_agent_e_integration.py

### `ai_whisperer.tools.tool_registry`
Covered by 12 test file(s):
- tests/unit/test_agent_tool_permission.py
- tests/unit/test_workspace_tools.py
- tests/unit/test_agent_e_integration.py
- tests/unit/test_agent_tool_filtering.py
- tests/unit/test_agent_tools.py
- ... and 7 more

### `ai_whisperer.tools.tool_set`
Covered by 1 test file(s):
- tests/unit/test_tool_sets.py

### `ai_whisperer.tools.tool_usage_logging`
Covered by 1 test file(s):
- tests/unit/test_tool_usage_logging.py

### `ai_whisperer.tools.update_plan_from_rfc_tool`
Covered by 4 test file(s):
- tests/unit/test_plan_tools.py
- tests/integration/test_rfc_plan_bidirectional.py
- tests/integration/test_patricia_rfc_plan_integration.py
- tests/integration/test_plan_error_recovery.py

### `ai_whisperer.tools.update_rfc_tool`
Covered by 2 test file(s):
- tests/unit/test_rfc_tools_complete.py
- tests/integration/test_rfc_plan_bidirectional.py

### `ai_whisperer.tools.web_search_tool`
Covered by 1 test file(s):
- tests/unit/test_web_tools.py

### `ai_whisperer.tools.workspace_stats_tool`
Covered by 1 test file(s):
- tests/unit/test_workspace_stats_tool.py

### `ai_whisperer.tools.write_file_tool`
Covered by 3 test file(s):
- tests/unit/test_file_tools.py
- tests/unit/test_tool_tags.py
- tests/integration/test_ai_tool_usage.py

### `ai_whisperer.utils`
Covered by 1 test file(s):
- tests/test_utils.py

### `ai_whisperer.workspace_detection`
Covered by 3 test file(s):
- tests/unit/test_workspace_detection_edge_cases.py
- tests/unit/test_workspace_detection.py
- tests/integration/test_workspace_pathmanager_integration.py

