# Documentation to Code Mapping Analysis Report

Generated: 2025-06-02 13:05:42

## Summary

- **Documentation files analyzed**: 161
- **Code files found**: 415
- **Total code references**: 40118
- **Orphaned docs**: 1
- **Undocumented code files**: 193
- **Code coverage**: 222/415 files (53.5%)

## Orphaned Documentation
Files with no code references (candidates for archival):

- `CLAUDE.local.md`

## Undocumented Code
Code files with no documentation references:

- `ai_whisperer/agents/agent.py`
- `ai_whisperer/agents/context_manager.py`
- `ai_whisperer/agents/session_manager.py`
- `ai_whisperer/commands/debbie.py`
- `ai_whisperer/commands/errors.py`
- `ai_whisperer/commands/registry.py`
- `ai_whisperer/context/agent_context.py`
- `ai_whisperer/context/provider.py`
- `ai_whisperer/exceptions.py`
- `ai_whisperer/tools/delete_plan_tool.py`
- `ai_whisperer/tools/delete_rfc_tool.py`
- `ai_whisperer/tools/execute_command_tool.py`
- `ai_whisperer/tools/move_plan_tool.py`
- `ai_whisperer/tools/prepare_plan_from_rfc_tool.py`
- `ai_whisperer/tools/save_generated_plan_tool.py`
- `ai_whisperer/tools/session_analysis_tool.py`
- `ai_whisperer/tools/session_health_tool.py`
- `ai_whisperer/tools/tool_set.py`
- `ai_whisperer/tools/tool_usage_logging.py`
- `ai_whisperer/tools/workspace_stats_tool.py`
- `frontend/src/App.integration.test.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/ModelList.tsx`
- `frontend/src/components/AgentAvatar.test.tsx`
- `frontend/src/components/AgentAvatar.tsx`
- `frontend/src/components/AgentInspectorPanel.test.tsx`
- `frontend/src/components/AgentInspectorPanel.tsx`
- `frontend/src/components/AgentMessageBubble.test.tsx`
- `frontend/src/components/AgentMessageBubble.tsx`
- `frontend/src/components/AgentSelector.test.tsx`
- `frontend/src/components/AgentSelector.tsx`
- `frontend/src/components/AgentSidebar.test.tsx`
- `frontend/src/components/AgentSidebar.tsx`
- `frontend/src/components/AgentSwitcher.test.tsx`
- `frontend/src/components/AgentSwitcher.tsx`
- `frontend/src/components/AgentTransition.test.tsx`
- `frontend/src/components/AgentTransition.tsx`
- `frontend/src/components/ChatSession.test.tsx`
- `frontend/src/components/ChatView.tsx`
- `frontend/src/components/CodeChangesView.test.tsx`
- `frontend/src/components/CodeChangesView.tsx`
- `frontend/src/components/ContextPanel.test.tsx`
- `frontend/src/components/CurrentAgentDisplay.test.tsx`
- `frontend/src/components/CurrentAgentDisplay.tsx`
- `frontend/src/components/JSONPlanView.test.tsx`
- `frontend/src/components/MainLayout.test.tsx`
- `frontend/src/components/MainLayout.tsx`
- `frontend/src/components/PlanConfirmation.test.tsx`
- `frontend/src/components/PlanConfirmation.tsx`
- `frontend/src/components/PlanExport.test.tsx`
- `frontend/src/components/PlanExport.tsx`
- `frontend/src/components/PlanPreview.test.tsx`
- `frontend/src/components/PlanPreview.tsx`
- `frontend/src/components/ProjectIntegration.tsx`
- `frontend/src/components/ProjectSettingsPanel.tsx`
- `frontend/src/components/SettingsPage.tsx`
- `frontend/src/components/Sidebar.test.tsx`
- `frontend/src/components/TestResultsView.test.tsx`
- `frontend/src/components/TestResultsView.tsx`
- `frontend/src/components/ViewRouter.test.tsx`
- `frontend/src/components/ViewRouter.tsx`
- `frontend/src/components/index.ts`
- `frontend/src/contexts/ProjectContext.tsx`
- `frontend/src/contexts/ViewContext.tsx`
- `frontend/src/hooks/useAISession.test.tsx`
- `frontend/src/hooks/useAISession.ts`
- `frontend/src/hooks/useChat.test.tsx`
- `frontend/src/hooks/useChat.ts`
- `frontend/src/hooks/useViewContext.test.tsx`
- `frontend/src/hooks/useWebSocket.test.tsx`
- `frontend/src/hooks/useWebSocket.ts`
- `frontend/src/react-app-env.d.ts`
- `frontend/src/reportWebVitals.ts`
- `frontend/src/services/aiService.agent.test.ts`
- `frontend/src/services/aiService.test.ts`
- `frontend/src/services/aiService.ts`
- `frontend/src/services/jsonRpcService.test.ts`
- `frontend/src/services/jsonRpcService.ts`
- `frontend/src/services/jsonRpcWebSocket.integration.test.ts`
- `frontend/src/services/projectService.ts`
- `frontend/src/services/websocketService.test.ts`
- `frontend/src/services/websocketService.ts`
- `frontend/src/setupTests.ts`
- `frontend/src/types/agent.ts`
- `frontend/src/types/ai.test.ts`
- `frontend/src/types/ai.ts`
- `frontend/src/types/chat.test.ts`
- `frontend/src/types/chat.ts`
- `frontend/src/types/fileSystem.ts`
- `frontend/src/types/jsonRpc.test.ts`
- `frontend/src/types/jsonRpc.ts`
- `frontend/src/types/multiAgentSession.ts`
- `frontend/src/types/plan.ts`
- `frontend/src/types/project.ts`
- `interactive_server/__init__.py`
- `interactive_server/handlers/__init__.py`
- `interactive_server/handlers/plan_handler.py`
- `interactive_server/handlers/project_handlers.py`
- `interactive_server/models/__init__.py`
- `interactive_server/models/project.py`
- `interactive_server/services/__init__.py`
- `interactive_server/services/project_manager.py`
- `postprocessing/__init__.py`
- `postprocessing/pipeline.py`
- `postprocessing/scripted_steps/__init__.py`
- `postprocessing/scripted_steps/add_items_postprocessor.py`
- `postprocessing/scripted_steps/clean_backtick_wrapper.py`
- `postprocessing/scripted_steps/escape_text_fields.py`
- `postprocessing/scripted_steps/format_json.py`
- `postprocessing/scripted_steps/handle_required_fields.py`
- `postprocessing/scripted_steps/identity_transform.py`
- `postprocessing/scripted_steps/validate_syntax.py`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/debugging-tools/debbie/system_health_check/check_agent_announcements.json`
- `tests/debugging-tools/debbie/system_health_check/check_agents.json`
- `tests/debugging-tools/debbie/system_health_check/check_tool_functionality.yaml`
- `tests/debugging-tools/debbie/system_health_check/check_tools.yaml`
- `tests/debugging-tools/test_batch_test_runner.py`
- `tests/debugging-tools/test_run_batch_test.py`
- `tests/debugging-tools/test_run_batch_test_existing_server.py`
- `tests/integration/__init__.py`
- `tests/integration/rfc_plan/test_patricia_rfc_plan_integration.py`
- `tests/integration/rfc_plan/test_plan_error_recovery.py`
- `tests/integration/session/test_conversation_persistence.py`
- `tests/integration/session/test_interactive_session.py`
- `tests/integration/session/test_project_settings_persistence.py`
- `tests/integration/session/test_session_integration.py`
- `tests/interactive_server/handlers/test_project_setup.py`
- `tests/interactive_server/handlers/test_real_session_handlers.py`
- `tests/interactive_server/handlers/test_tool_result_handler.py`
- `tests/interactive_server/jsonrpc/test_jsonrpc_notifications.py`
- `tests/interactive_server/jsonrpc/test_jsonrpc_protocol.py`
- `tests/interactive_server/jsonrpc/test_jsonrpc_protocol_more.py`
- `tests/interactive_server/jsonrpc/test_jsonrpc_routing.py`
- `tests/interactive_server/test_performance_metrics_utils.py`
- `tests/interactive_server/websocket/test_notifications_streaming.py`
- `tests/interactive_server/websocket/test_websocket_endpoint.py`
- `tests/interactive_server/websocket/test_websocket_stress.py`
- `tests/interactive_server/websocket/test_websocket_stress_subprocess.py`
- `tests/performance/test_ai_service_timeout.py`
- `tests/performance/test_long_running_session.py`
- `tests/performance/test_memory_usage_under_load.py`
- `tests/performance/test_prompt_system_performance.py`
- `tests/test_runner_directory_access.py`
- `tests/unit/__init__.py`
- `tests/unit/agents/test_agent_config.py`
- `tests/unit/agents/test_agent_context.py`
- `tests/unit/agents/test_agent_factory.py`
- `tests/unit/agents/test_agent_inspect_command.py`
- `tests/unit/agents/test_agent_stateless.py`
- `tests/unit/agents/test_agent_tool_filtering.py`
- `tests/unit/agents/test_agent_tool_permission.py`
- `tests/unit/agents/test_debbie_command.py`
- `tests/unit/agents/test_debbie_observer.py`
- `tests/unit/agents/test_mailbox_system.py`
- `tests/unit/ai_loop/test_ai_interaction_history.py`
- `tests/unit/ai_loop/test_continuation_depth.py`
- `tests/unit/ai_loop/test_continuation_strategy.py`
- `tests/unit/ai_service/test_ai_service_interaction.py`
- `tests/unit/ai_service/test_openrouter_advanced_features.py`
- `tests/unit/ai_service/test_openrouter_api_detailed.py`
- `tests/unit/ai_service/test_tool_calling_standard.py`
- `tests/unit/batch/test_batch_command_performance.py`
- `tests/unit/batch/test_script_parser_security.py`
- `tests/unit/batch/test_script_parser_tool.py`
- `tests/unit/batch/test_script_parser_validation.py`
- `tests/unit/commands/test_clear_command.py`
- `tests/unit/commands/test_cli_workspace_validation.py`
- `tests/unit/context/test_context_provider.py`
- `tests/unit/context/test_context_serialization.py`
- `tests/unit/context/test_context_tracking.py`
- `tests/unit/postprocessing/test_format_json.py`
- `tests/unit/postprocessing/test_postprocessing_add_items.py`
- `tests/unit/postprocessing/test_postprocessing_backticks.py`
- `tests/unit/postprocessing/test_postprocessing_fields.py`
- `tests/unit/postprocessing/test_postprocessing_pipeline.py`
- `tests/unit/postprocessing/test_postprocessing_text_fields.py`
- `tests/unit/postprocessing/test_postprocessing_type_preservation.py`
- `tests/unit/postprocessing/test_scripted_postprocessing.py`
- `tests/unit/tools/test_execute_command_tool.py`
- `tests/unit/tools/test_file_tools.py`
- `tests/unit/tools/test_find_pattern_tool.py`
- `tests/unit/tools/test_get_file_content_tool.py`
- `tests/unit/tools/test_list_directory_tool.py`
- `tests/unit/tools/test_plan_tools.py`
- `tests/unit/tools/test_search_files_tool.py`
- `tests/unit/tools/test_tool_management.py`
- `tests/unit/tools/test_tool_sets.py`
- `tests/unit/tools/test_tool_usage_logging.py`
- `tests/unit/tools/test_web_tools.py`
- `tests/unit/tools/test_workspace_stats_tool.py`
- `tests/unit/tools/test_workspace_tools.py`

## Stale Documentation
Documentation that may be outdated:

- `CLAUDE.local.md`: No code references found
- `CLAUDE.md`: Code modified 0 days after doc
- `IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md`: Code modified 0 days after doc
- `IMPLEMENTATION_SUMMARY.md`: Code modified 0 days after doc
- `UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md`: Code modified 0 days after doc
- `docs/architecture/architecture.md`: Code modified 4 days after doc
- `docs/architecture/prompt_system.md`: Code modified 4 days after doc
- `docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md`: Code modified 0 days after doc
- `docs/archive/consolidated_phase2/PR_DESCRIPTION.md`: Code modified 0 days after doc
- `docs/archive/consolidated_phase2/docs/architecture/stateless_architecture.md`: Code modified 4 days after doc
- `docs/archive/consolidated_phase2/docs/archive/delegate_system/user_message_analysis.md`: Code modified 4 days after doc
- `docs/archive/consolidated_phase2/docs/completed/FRONTEND_TDD_CHECKLIST.md`: Code modified 4 days after doc
- `docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md`: Code modified 4 days after doc
- `docs/archive/consolidated_phase2/frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md`: Code modified 3 days after doc
- `docs/archive/legacy/analysis/path_manager_analysis.md`: Code modified 4 days after doc
- `docs/archive/legacy/terminal_ui/detail_option_implementation_plan.md`: Code modified 4 days after doc
- `docs/archive/legacy/terminal_ui/list_models_interaction_analysis.md`: Code modified 4 days after doc
- `docs/archive/phase2_consolidation/agent-e-implementation-summary.md`: Code modified 0 days after doc
- `docs/archive/phase2_consolidation/file_browser_implementation_checklist.md`: Code modified 3 days after doc
- `docs/archive/phase2_consolidation/file_browser_implementation_plan.md`: Code modified 3 days after doc
- `docs/archive/phase2_consolidation/file_browser_integration_summary.md`: Code modified 3 days after doc
- `docs/archive/refactor_tracking/REFACTOR_DELETION_PLAN.md`: Code modified 0 days after doc
- `docs/batch-mode/IMPLEMENTATION_PLAN.md`: Code modified 2 days after doc
- `docs/batch-mode/PHASE1_TASKS.md`: Code modified 0 days after doc
- `docs/batch-mode/USER_GUIDE.md`: Code modified 1 days after doc
- `docs/clear-command-implementation-summary.md`: Code modified 0 days after doc
- `docs/completed/AgentSystemImplementationPlan.md`: Code modified 1 days after doc
- `docs/context_tracking_implementation_plan.md`: Code modified 3 days after doc
- `docs/cost_token_storage_design.md`: Code modified 4 days after doc
- `docs/directory_restriction_strategy.md`: Code modified 4 days after doc
- `docs/execute_command_tool_design.md`: Code modified 3 days after doc
- `docs/feature/agent-continuation-test-failures.md`: Code modified 0 days after doc
- `docs/tool_sets_and_tags.md`: Code modified 3 days after doc

## Code Coverage Details

**`ai_whisperer/__init__.py`** (2 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md

**`ai_whisperer/__main__.py`** (3 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md

**`ai_whisperer/agents/__init__.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/agents/agent_communication.py`** (2 doc(s)):
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md

**`ai_whisperer/agents/base_handler.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/agents/config.py`** (4 doc(s)):
  - config_consolidation_analysis.md
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/legacy/analysis/path_manager_analysis.md
  - docs/directory_restriction_strategy.md

**`ai_whisperer/agents/config/agents.yaml`** (16 doc(s)):
  - CLAUDE.md
  - CONFIG_CONSOLIDATION_COMPLETE.md
  - PHASE_CONSOLIDATED_SUMMARY.md
  - cleanup_report_dryrun_20250602_124221.md
  - config_consolidation_analysis.md
  - docs/agent-e-execution-consolidated.md
  - docs/architecture/architecture.md
  - docs/architecture/prompt_system.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/phase2_consolidation/file_browser_implementation_checklist.md
  - docs/archive/refactor_tracking/REFACTOR_CURRENT_STATE_SNAPSHOT.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md
  - docs/feature/agent-continuation-configuration-guide.md
  - docs/feature/agent-continuation-test-results.md
  - docs/feature/agent-continuation-testing-guide.md
  - docs/file-browser-consolidated-implementation.md

**`ai_whisperer/agents/continuation_strategy.py`** (3 doc(s)):
  - docs/archive/phase2_consolidation/agent-continuation-implementation-checklist.md
  - docs/archive/phase2_consolidation/agent-continuation-implementation-plan.md
  - docs/feature/agent-continuation-consolidated-implementation.md

**`ai_whisperer/agents/debbie_tools.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/agents/decomposed_task.py`** (2 doc(s)):
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md

**`ai_whisperer/agents/factory.py`** (1 doc(s)):
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/agents/mail_notification.py`** (4 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md

**`ai_whisperer/agents/mailbox.py`** (3 doc(s)):
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/agents/mailbox_tools.py`** (6 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
  - docs/dependency-analysis-report.md

**`ai_whisperer/agents/prompt_optimizer.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/agents/registry.py`** (1 doc(s)):
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/agents/stateless_agent.py`** (2 doc(s)):
  - docs/archive/consolidated_phase2/docs/architecture/stateless_architecture.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/agents/task_decomposer.py`** (2 doc(s)):
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md

**`ai_whisperer/ai_loop/__init__.py`** (2 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md

**`ai_whisperer/ai_loop/ai_config.py`** (1 doc(s)):
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/ai_loop/stateless_ai_loop.py`** (4 doc(s)):
  - docs/archive/consolidated_phase2/PR_DESCRIPTION.md
  - docs/archive/consolidated_phase2/docs/architecture/stateless_architecture.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/ai_loop/tool_call_accumulator.py`** (3 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/ai_service/ai_service.py`** (1 doc(s)):
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/ai_service/openrouter_ai_service.py`** (3 doc(s)):
  - docs/archive/consolidated_phase2/PR_DESCRIPTION.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/ai_service/tool_calling.py`** (2 doc(s)):
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/batch/__init__.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/batch/batch_client.py`** (2 doc(s)):
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/batch/debbie_integration.py`** (3 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/batch/intervention.py`** (4 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/batch/monitoring.py`** (3 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/batch/script_processor.py`** (2 doc(s)):
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md

**`ai_whisperer/batch/server_manager.py`** (3 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md

**`ai_whisperer/batch/websocket_client.py`** (3 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md

**`ai_whisperer/batch/websocket_interceptor.py`** (3 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/cli.py`** (8 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md
  - docs/archive/legacy/analysis/path_manager_analysis.md
  - docs/archive/legacy/terminal_ui/list_models_interaction_analysis.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md
  - docs/directory_restriction_strategy.md

**`ai_whisperer/cli_commands.py`** (4 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/TECH_DEBT.md
  - docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md

**`ai_whisperer/cli_commands_batch_mode.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/agent.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/args.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/base.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/echo.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/help.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/session.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/status.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/commands/test_commands.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/config.py`** (1 doc(s)):
  - CLAUDE.md

**`ai_whisperer/context/__init__.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/context/context_item.py`** (1 doc(s)):
  - docs/context_tracking_implementation_plan.md

**`ai_whisperer/context/context_manager.py`** (2 doc(s)):
  - docs/clear-command-implementation-summary.md
  - docs/context_tracking_implementation_plan.md

**`ai_whisperer/context_management.py`** (2 doc(s)):
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/refactor_tracking/REFACTOR_DELETION_PLAN.md

**`ai_whisperer/json_validator.py`** (2 doc(s)):
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/refactor_tracking/REFACTOR_DELETION_PLAN.md

**`ai_whisperer/logging/__init__.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/logging/debbie_logger.py`** (2 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/logging/log_aggregator.py`** (3 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/logging_custom.py`** (5 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/consolidated_phase2/docs/archive/delegate_system/user_message_analysis.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/model_capabilities.py`** (2 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/model_info_provider.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/path_management.py`** (2 doc(s)):
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/batch-mode/PHASE1_TASKS.md

**`ai_whisperer/prompt_system.py`** (4 doc(s)):
  - docs/archive/legacy/analysis/path_manager_analysis.md
  - docs/archive/phase2_consolidation/agent-continuation-implementation-plan.md
  - docs/directory_restriction_strategy.md
  - docs/feature/agent-continuation-consolidated-implementation.md

**`ai_whisperer/state_management.py`** (3 doc(s)):
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/refactor_tracking/REFACTOR_DELETION_PLAN.md
  - docs/cost_token_storage_design.md

**`ai_whisperer/tools/__init__.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/analyze_dependencies_tool.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/analyze_languages_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/base_tool.py`** (1 doc(s)):
  - docs/execute_command_tool_design.md

**`ai_whisperer/tools/batch_command_tool.py`** (4 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md
  - docs/batch-mode/PHASE2_CHECKLIST.md
  - docs/batch-mode/PHASE2_TASKS.md

**`ai_whisperer/tools/check_mail_tool.py`** (4 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md
  - docs/dependency-analysis-report.md

**`ai_whisperer/tools/create_plan_from_rfc_tool.py`** (3 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
  - docs/dependency-analysis-report.md

**`ai_whisperer/tools/create_rfc_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/decompose_plan_tool.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/fetch_url_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/find_pattern_tool.py`** (2 doc(s)):
  - docs/archive/phase2_consolidation/file_browser_implementation_checklist.md
  - docs/file-browser-consolidated-implementation.md

**`ai_whisperer/tools/find_similar_code_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/format_for_external_agent_tool.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/get_file_content_tool.py`** (3 doc(s)):
  - docs/archive/phase2_consolidation/file_browser_implementation_checklist.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
  - docs/file-browser-consolidated-implementation.md

**`ai_whisperer/tools/get_project_structure_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/list_directory_tool.py`** (2 doc(s)):
  - docs/archive/phase2_consolidation/file_browser_implementation_checklist.md
  - docs/file-browser-consolidated-implementation.md

**`ai_whisperer/tools/list_plans_tool.py`** (1 doc(s)):
  - UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md

**`ai_whisperer/tools/list_rfcs_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/message_injector_tool.py`** (4 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/tools/monitoring_control_tool.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/move_rfc_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/parse_external_result_tool.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/python_ast_json_tool.py`** (3 doc(s)):
  - MERGE_READINESS_REPORT.md
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
  - docs/dependency-analysis-report.md

**`ai_whisperer/tools/python_executor_tool.py`** (3 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/tools/read_file_tool.py`** (1 doc(s)):
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`ai_whisperer/tools/read_plan_tool.py`** (1 doc(s)):
  - UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md

**`ai_whisperer/tools/read_rfc_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/recommend_external_agent_tool.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/reply_mail_tool.py`** (4 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md
  - docs/dependency-analysis-report.md

**`ai_whisperer/tools/script_parser_tool.py`** (4 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md
  - docs/batch-mode/PHASE2_CHECKLIST.md
  - docs/batch-mode/PHASE2_TASKS.md

**`ai_whisperer/tools/search_files_tool.py`** (2 doc(s)):
  - docs/archive/phase2_consolidation/file_browser_implementation_checklist.md
  - docs/file-browser-consolidated-implementation.md

**`ai_whisperer/tools/send_mail_tool.py`** (4 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/agent-e-consolidated-implementation.md
  - docs/archive/phase2_consolidation/agent-e-implementation-summary.md
  - docs/dependency-analysis-report.md

**`ai_whisperer/tools/session_inspector_tool.py`** (3 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/tools/system_health_check_tool.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/tool_registration.py`** (2 doc(s)):
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/dependency-analysis-report.md

**`ai_whisperer/tools/tool_registry.py`** (2 doc(s)):
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/execute_command_tool_design.md

**`ai_whisperer/tools/tool_sets.yaml`** (8 doc(s)):
  - CONFIG_CONSOLIDATION_COMPLETE.md
  - PHASE_CONSOLIDATED_SUMMARY.md
  - cleanup_report_dryrun_20250602_124221.md
  - config_consolidation_analysis.md
  - docs/archive/phase2_consolidation/file_browser_implementation_checklist.md
  - docs/archive/refactor_tracking/REFACTOR_CURRENT_STATE_SNAPSHOT.md
  - docs/file-browser-consolidated-implementation.md
  - docs/tool_sets_and_tags.md

**`ai_whisperer/tools/update_plan_from_rfc_tool.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/update_rfc_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/update_task_status_tool.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/validate_external_agent_tool.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/tools/web_search_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`ai_whisperer/tools/workspace_validator_tool.py`** (2 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`ai_whisperer/tools/write_file_tool.py`** (1 doc(s)):
  - docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md

**`ai_whisperer/user_message_level.py`** (2 doc(s)):
  - UNTESTED_MODULES_REPORT.md
  - docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md

**`ai_whisperer/utils.py`** (2 doc(s)):
  - docs/archive/phase2_consolidation/file_browser_integration_summary.md
  - docs/file-browser-consolidated-implementation.md

**`ai_whisperer/version.py`** (1 doc(s)):
  - UNTESTED_MODULES_REPORT.md

**`ai_whisperer/workspace_detection.py`** (2 doc(s)):
  - docs/batch-mode/IMPLEMENTATION_PLAN.md
  - docs/batch-mode/PHASE1_TASKS.md

**`frontend/src/App.tsx`** (3 doc(s)):
  - docs/archive/consolidated_phase2/docs/completed/FRONTEND_TDD_CHECKLIST.md
  - docs/archive/phase2_consolidation/file_browser_integration_summary.md
  - docs/file-browser-consolidated-implementation.md

**`frontend/src/ChatWindow.tsx`** (1 doc(s)):
  - docs/archive/consolidated_phase2/docs/completed/FRONTEND_TDD_CHECKLIST.md

**`frontend/src/MessageInput.tsx`** (4 doc(s)):
  - IMPLEMENTATION_SUMMARY.md
  - UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md
  - docs/archive/phase2_consolidation/file_browser_implementation_plan.md
  - docs/file-browser-consolidated-implementation.md

**`frontend/src/components/ContextPanel.tsx`** (1 doc(s)):
  - docs/context_tracking_implementation_plan.md

**`frontend/src/components/FileBrowser.tsx`** (4 doc(s)):
  - IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md
  - docs/archive/phase2_consolidation/file_browser_implementation_plan.md
  - docs/archive/phase2_consolidation/file_browser_integration_summary.md
  - docs/file-browser-consolidated-implementation.md

**`frontend/src/components/FilePicker.tsx`** (3 doc(s)):
  - IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md
  - docs/archive/phase2_consolidation/file_browser_implementation_plan.md
  - docs/file-browser-consolidated-implementation.md

**`frontend/src/components/JSONPlanView.tsx`** (2 doc(s)):
  - IMPLEMENTATION_SUMMARY.md
  - UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md

**`frontend/src/components/ProjectSelector.tsx`** (2 doc(s)):
  - IMPLEMENTATION_SUMMARY.md
  - UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md

**`frontend/src/components/Sidebar.tsx`** (1 doc(s)):
  - UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md

**`frontend/src/index.tsx`** (1 doc(s)):
  - docs/archive/consolidated_phase2/frontend/tech_debt.md

**`interactive_server/commands/agent.py`** (1 doc(s)):
  - docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md

**`interactive_server/debbie_observer.py`** (2 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md

**`interactive_server/handlers/workspace_handler.py`** (4 doc(s)):
  - IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md
  - docs/archive/phase2_consolidation/file_browser_integration_summary.md
  - docs/context_tracking_implementation_plan.md
  - docs/file-browser-consolidated-implementation.md

**`interactive_server/main.py`** (6 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/archive/legacy/terminal_ui/detail_option_implementation_plan.md
  - docs/archive/phase2_consolidation/file_browser_integration_summary.md
  - docs/file-browser-consolidated-implementation.md

**`interactive_server/message_models.py`** (3 doc(s)):
  - CLAUDE.md
  - docs/architecture/architecture.md
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md

**`interactive_server/services/file_service.py`** (4 doc(s)):
  - IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md
  - docs/archive/phase2_consolidation/file_browser_implementation_plan.md
  - docs/archive/phase2_consolidation/file_browser_integration_summary.md
  - docs/file-browser-consolidated-implementation.md

**`interactive_server/stateless_session_manager.py`** (7 doc(s)):
  - CLAUDE.md
  - PHASE_CONSOLIDATED_SUMMARY.md
  - docs/agent-e-execution-consolidated.md
  - docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md
  - docs/archive/consolidated_phase2/docs/architecture/stateless_architecture.md
  - docs/archive/debugging-session-2025-05-30-consolidated.md
  - docs/clear-command-implementation-summary.md

**`tests/examples/debbie_demo.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - TEST_REORGANIZATION_REPORT.md

**`tests/examples/debbie_practical_example.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - TEST_REORGANIZATION_REPORT.md

**`tests/fixtures/projects/code_generator/aiwhisperer_config.yaml`** (2 doc(s)):
  - cleanup_report_dryrun_20250602_124221.md
  - config_consolidation_analysis.md

**`tests/fixtures/projects/code_generator/n_times_4/overview_n_times_4.json`** (2 doc(s)):
  - cleanup_report_dryrun_20250602_124221.md
  - config_consolidation_analysis.md

**`tests/fixtures/projects/code_generator/n_times_4/subtask_generate_script.json`** (2 doc(s)):
  - cleanup_report_dryrun_20250602_124221.md
  - config_consolidation_analysis.md

**`tests/integration/batch_mode/test_batch_performance.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/batch_mode/test_batch_script_execution.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/batch_mode/test_debbie_agent_integration.py`** (2 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/rfc_plan/test_rfc_plan_bidirectional.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_agent_continuation_fix.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_agent_continuation_integration.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_agent_jsonrpc_ws.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_ai_tool_usage.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_batch_mode_e2e.py`** (3 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/batch-mode/IMPLEMENTATION_PLAN.md
  - docs/batch-mode/USER_GUIDE.md

**`tests/integration/test_context_integration.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_continuation_progress_tracking.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/feature/agent-continuation-test-failures.md

**`tests/integration/test_continuation_simple.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_continuation_verification.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/feature/agent-continuation-test-failures.md

**`tests/integration/test_graceful_exit.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_model_compatibility_simple.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_model_continuation_compatibility.py`** (2 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_project_pathmanager_integration.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_run_plan_script.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_runner_plan_ingestion.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/integration/test_workspace_pathmanager_integration.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/batch-mode/PHASE1_TASKS.md

**`tests/interactive_server/conftest.py`** (2 doc(s)):
  - TEST_REORGANIZATION_REPORT.md
  - docs/TECH_DEBT.md

**`tests/interactive_server/test_integration_end_to_end.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/interactive_server/test_interactive_client_script.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/interactive_server/test_interactive_message_models.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/interactive_server/test_interactive_message_models_roundtrip.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/interactive_server/test_message_models.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/interactive_server/test_mocked_ailoop.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/interactive_server/test_openrouter_shutdown_patch.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/interactive_server/test_session_manager.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/temp_output/test_generate_overview_plan_ac0/overview_initial_plan.json`** (2 doc(s)):
  - cleanup_report_dryrun_20250602_124221.md
  - config_consolidation_analysis.md

**`tests/temp_output/test_generate_overview_plan_ac0/subtask_step_1.json`** (2 doc(s)):
  - cleanup_report_dryrun_20250602_124221.md
  - config_consolidation_analysis.md

**`tests/uncategorized/test_config.py`** (1 doc(s)):
  - TEST_REORGANIZATION_REPORT.md

**`tests/uncategorized/test_debbie_scenarios.py`** (1 doc(s)):
  - TEST_REORGANIZATION_REPORT.md

**`tests/uncategorized/test_openrouter_api.py`** (1 doc(s)):
  - TEST_REORGANIZATION_REPORT.md

**`tests/uncategorized/test_processing.py`** (1 doc(s)):
  - TEST_REORGANIZATION_REPORT.md

**`tests/uncategorized/test_utils.py`** (1 doc(s)):
  - TEST_REORGANIZATION_REPORT.md

**`tests/unit/agents/test_agent_communication.py`** (1 doc(s)):
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/unit/agents/test_agent_context_manager.py`** (1 doc(s)):
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/unit/agents/test_agent_e_communication.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/agents/test_agent_e_external_adapters.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/agents/test_agent_e_integration.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/agents/test_agent_e_task_decomposition.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/agents/test_agent_jsonrpc.py`** (1 doc(s)):
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/unit/agents/test_agent_registry.py`** (1 doc(s)):
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/unit/agents/test_agent_tools.py`** (1 doc(s)):
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/unit/agents/test_planner_handler.py`** (1 doc(s)):
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/unit/agents/test_planner_tools.py`** (1 doc(s)):
  - docs/completed/AgentSystemImplementationPlan.md

**`tests/unit/ai_loop/test_refactored_ai_loop.py`** (1 doc(s)):
  - docs/archive/consolidated_phase2/frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md

**`tests/unit/ai_loop/test_stateless_ailoop.py`** (2 doc(s)):
  - REFACTOR_STAGE3_PHASE0_DOC_MODERNIZATION.md
  - docs/TECH_DEBT.md

**`tests/unit/batch/test_batch_command_tool.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`tests/unit/batch/test_debbie_agent_config.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`tests/unit/batch/test_debbie_prompt_system.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`tests/unit/commands/test_cli.py`** (1 doc(s)):
  - docs/archive/consolidated_phase2/frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md

**`tests/unit/conftest.py`** (1 doc(s)):
  - MERGE_READINESS_REPORT.md

**`tests/unit/context/test_context_manager.py`** (1 doc(s)):
  - docs/archive/consolidated_phase2/frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md

**`tests/unit/test_ast_to_json_conversion.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_direct_streaming.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_enhanced_prompt_system.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/feature/agent-continuation-test-failures.md

**`tests/unit/test_error_handling_ast_validation.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_error_handling_edge_cases.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_error_handling_file_io.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_error_handling_graceful_degradation.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_error_handling_system_stability.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_file_service.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_jsonrpc_handlers_refactor.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_logging.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/archive/consolidated_phase2/frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md

**`tests/unit/test_metadata_preservation.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_minimal_nested_schema.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_minimal_schema_validation.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_path_management.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_plan_ingestion.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_prompt_optimizer.py`** (2 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_prompt_rules_removal.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_refine_ai_interaction.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_rfc_extension_regression.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_rfc_move_extensions.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_rfc_naming.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_round_trip_working.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_session_manager.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_session_manager_refactor.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/test_state_management.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/archive/consolidated_phase2/frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md

**`tests/unit/test_workspace_detection.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/batch-mode/PHASE1_TASKS.md

**`tests/unit/test_workspace_detection_edge_cases.py`** (2 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md
  - docs/batch-mode/PHASE1_TASKS.md

**`tests/unit/test_workspace_handler.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_codebase_analysis_tools.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_python_ast_json_design.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_python_ast_json_tool.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_python_ast_parsing.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_python_ast_parsing_advanced.py`** (1 doc(s)):
  - TEST_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_rfc_tools.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_rfc_tools_complete.py`** (1 doc(s)):
  - PHASE_CONSOLIDATED_SUMMARY.md

**`tests/unit/tools/test_tool_tags.py`** (2 doc(s)):
  - docs/archive/phase2_consolidation/file_browser_implementation_checklist.md
  - docs/file-browser-consolidated-implementation.md

## API Documentation Migration Candidates

Files containing API documentation that should be moved to code:

- `CLAUDE.md`
- `CODE_OF_CONDUCT.md`
- `CONFIG_CONSOLIDATION_COMPLETE.md`
- `CONTRIBUTING.md`
- `DOCUMENTATION_CONSOLIDATION_SUMMARY.md`
- `IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md`
- `IMPLEMENTATION_SUMMARY.md`
- `MERGE_READINESS_REPORT.md`
- `NEXT_STEPS_BATCH_MODE_PHASE2.md`
- `PHASE_CONSOLIDATED_SUMMARY.md`
- `PROJECT_STATUS_UPDATE.md`
- `PROJECT_STATUS_UPDATE_PHASE2_COMPLETE.md`
- `README.md`
- `REFACTOR_DAY2_COMPLETE.md`
- `REFACTOR_DAY_COMPLETE_20250602.md`
- `REFACTOR_PHASE2_COMPLETE.md`
- `REFACTOR_STAGE3_PHASE0_DOC_MODERNIZATION.md`
- `REFACTOR_STAGE3_PLAN.md`
- `RFC_TO_PLAN_STATUS.md`
- `STRUCTURED_OUTPUT_FINDINGS.md`
- `TECHNICAL_SPECIFICATIONS.md`
- `TEST_CONSOLIDATED_SUMMARY.md`
- `TEST_REORGANIZATION_COMPLETE.md`
- `TEST_REORGANIZATION_REPORT.md`
- `UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md`
- `UNTESTED_MODULES_REPORT.md`
- `cleanup_report_dryrun_20250602_124221.md`
- `complete_doc_cleanup_plan.md`
- `config_consolidation_analysis.md`
- `docs/AGENT_P_RFC_IMPLEMENTATION_CHECKLIST.md`
- `docs/BATCH_MODE_USAGE_FOR_AI.md`
- `docs/DEBBIE_SCRIPT_FORMATS.md`
- `docs/FUTURE_IDEAS.md`
- `docs/Initial/AI Coding Assistant Tool_ Research and Design Report.md`
- `docs/PATRICIA_PLAN_CONVERSION_GUIDE.md`
- `docs/QUICK_START.md`
- `docs/README.md`
- `docs/STRUCTURED_OUTPUT_INTEGRATION.md`
- `docs/TECH_DEBT.md`
- `docs/agent-e-consolidated-implementation.md`
- `docs/agent-e-data-structures-design.md`
- `docs/agent-e-decomposition-example.md`
- `docs/agent-e-execution-consolidated.md`
- `docs/agent-e-external-agents-research.md`
- `docs/agent-p-issues-and-improvements.md`
- `docs/agent_context_tracking_design.md`
- `docs/agent_p_rfc_design_summary.md`
- `docs/agent_p_rfc_refinement_plan.md`
- `docs/ai_service_interaction.md`
- `docs/architecture/architecture.md`
- `docs/architecture/project_management.md`
- `docs/architecture/prompt_system.md`
- `docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md`
- `docs/archive/consolidated_phase2/PR_DESCRIPTION.md`
- `docs/archive/consolidated_phase2/REFACTOR_CHANGELOG.md`
- `docs/archive/consolidated_phase2/REFACTOR_EXECUTION_LOG.md`
- `docs/archive/consolidated_phase2/doc_consolidation_report_20250602_115034.md`
- `docs/archive/consolidated_phase2/docs/architecture/stateless_architecture.md`
- `docs/archive/consolidated_phase2/docs/archive/DEVELOPMENT_PLAN.md`
- `docs/archive/consolidated_phase2/docs/archive/delegate_system/user_message_analysis.md`
- `docs/archive/consolidated_phase2/docs/archive/delegate_system/user_message_system.md`
- `docs/archive/consolidated_phase2/docs/completed/FRONTEND_TDD_CHECKLIST.md`
- `docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md`
- `docs/archive/consolidated_phase2/frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md`
- `docs/archive/consolidated_phase2/frontend/tech_debt.md`
- `docs/archive/consolidated_phase2/refactor_backup/project_dev/done/agent_REFACTOR_CHECKLIST.md`
- `docs/archive/consolidated_phase2/refactor_backup/project_dev/done/agent_REFACTOR_PLAN.md`
- `docs/archive/debugging-session-2025-05-30-consolidated.md`
- `docs/archive/legacy/analysis/cost_token_analysis_summary.md`
- `docs/archive/legacy/analysis/docs_update_plan_cost_tracking.md`
- `docs/archive/legacy/analysis/model_selection_plan.md`
- `docs/archive/legacy/analysis/path_manager_analysis.md`
- `docs/archive/legacy/analysis/prompt_analysis.md`
- `docs/archive/legacy/analysis/prompt_loading_analysis.md`
- `docs/archive/legacy/delegate_system/ai_loop_documentation.md`
- `docs/archive/legacy/delegate_system/refactored_ai_loop_design.md`
- `docs/archive/legacy/old_architecture/execution_engine.md`
- `docs/archive/legacy/old_architecture/internal_process.md`
- `docs/archive/legacy/old_architecture/plan_document_execute_command_tool.md`
- `docs/archive/legacy/terminal_ui/detail_option_implementation_plan.md`
- `docs/archive/legacy/terminal_ui/list_models_interaction_analysis.md`
- `docs/archive/legacy/terminal_ui/terminal_command_mode_design.md`
- `docs/archive/phase2_consolidation/agent-continuation-implementation-checklist.md`
- `docs/archive/phase2_consolidation/agent-continuation-implementation-plan.md`
- `docs/archive/phase2_consolidation/agent-continuation-implementation-progress.md`
- `docs/archive/phase2_consolidation/agent-e-implementation-log.md`
- `docs/archive/phase2_consolidation/agent-e-implementation-progress.md`
- `docs/archive/phase2_consolidation/agent-e-implementation-summary.md`
- `docs/archive/phase2_consolidation/file_browser_implementation_checklist.md`
- `docs/archive/phase2_consolidation/file_browser_implementation_plan.md`
- `docs/archive/phase2_consolidation/file_browser_implementation_priority.md`
- `docs/archive/phase2_consolidation/file_browser_integration_summary.md`
- `docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md`
- `docs/archive/refactor_tracking/REFACTOR_CURRENT_STATE_SNAPSHOT.md`
- `docs/archive/refactor_tracking/REFACTOR_DELETION_PLAN.md`
- `docs/archive/refactor_tracking/REFACTOR_DOC_MAP_SUMMARY.md`
- `docs/archive/refactor_tracking/REFACTOR_MISC_MAP_SUMMARY.md`
- `docs/archive/refactor_tracking/REFACTOR_PROTO_TO_PROD_OVERVIEW.md`
- `docs/archive/refactor_tracking/doc_cleanup_final_action_plan.md`
- `docs/archive/refactor_tracking/doc_consolidation_report_20250602_114824.md`
- `docs/archive/refactor_tracking/doc_consolidation_report_20250602_115146.md`
- `docs/archive/refactor_tracking/doc_consolidation_report_20250602_115211.md`
- `docs/archive/refactor_tracking/doc_consolidation_report_20250602_115315.md`
- `docs/at_command_technical_spec.md`
- `docs/batch-mode/IMPLEMENTATION_PLAN.md`
- `docs/batch-mode/IMPLEMENTATION_STATUS.md`
- `docs/batch-mode/PHASE1_TASKS.md`
- `docs/batch-mode/PHASE2_CHECKLIST.md`
- `docs/batch-mode/PHASE2_TASKS.md`
- `docs/batch-mode/USER_GUIDE.md`
- `docs/batch_debugging_with_debbie.md`
- `docs/clear-command-implementation-summary.md`
- `docs/code_generation_handler_design.md`
- `docs/code_generation_handler_research.md`
- `docs/completed/AgentInspectorFeaturePlan.md`
- `docs/completed/AgentSystemImplementationPlan.md`
- `docs/completed/FRONTEND_BACKEND_INTEGRATION_PLAN.md`
- `docs/config_examples.md`
- `docs/configuration.md`
- `docs/context_manager_design.md`
- `docs/context_tracking_implementation_plan.md`
- `docs/cost_token_storage_design.md`
- `docs/debugging-session-2025-05-30/DEBBIE_BATCH_MODE_EXAMPLE.md`
- `docs/dependency-analysis-report.md`
- `docs/development-tool-wishlist.md`
- `docs/directory_restriction_strategy.md`
- `docs/execute_command_tool_design.md`
- `docs/feature/agent-continuation-configuration-guide.md`
- `docs/feature/agent-continuation-consolidated-implementation.md`
- `docs/feature/agent-continuation-fix-summary.md`
- `docs/feature/agent-continuation-json-issue.md`
- `docs/feature/agent-continuation-test-failures.md`
- `docs/feature/agent-continuation-test-results.md`
- `docs/feature/agent-continuation-test-summary.md`
- `docs/feature/agent-continuation-testing-guide.md`
- `docs/feature/continuation-performance-optimization-guide.md`
- `docs/file-browser-consolidated-implementation.md`
- `docs/index.md`
- `docs/mailbox-system-design.md`
- `docs/path_management_design.md`
- `docs/postprocessing_design.md`
- `docs/research/agentic_ai_continuation_research/agentic_ai_continuation_report.md`
- `docs/research/agentic_ai_continuation_research/agentic_frameworks_analysis.md`
- `docs/research/agentic_ai_continuation_research/ai_continuation_final_report.md`
- `docs/research/agentic_ai_continuation_research/aiwhisperer_implementation_guide.md`
- `docs/research/agentic_ai_continuation_research/api_vs_system_comparison.md`
- `docs/research/agentic_ai_continuation_research/api_vs_system_continuation.md`
- `docs/research/agentic_ai_continuation_research/continuation_trigger_analysis.md`
- `docs/research/agentic_ai_continuation_research/product_implementation_comparison.md`
- `docs/research/agentic_ai_continuation_research/references.md`
- `docs/research/agentic_ai_continuation_research/todo.md`
- `docs/research/ai-response-parsing-execution-log.md`
- `docs/rfc_to_plan_implementation_checklist.md`
- `docs/subtask_generator_feature.md`
- `docs/tool_interface_design.md`
- `docs/tool_management_design.md`
- `docs/tool_sets_and_tags.md`
- `docs/tool_testing_strategy.md`
- `docs/workspace_ai_tools_spec.md`
- `workspace_health_20250531_111146.md`

