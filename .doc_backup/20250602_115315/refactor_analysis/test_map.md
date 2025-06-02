# AIWhisperer Test Map

## Summary
- Total Test Files: 157
- Total Test Classes: 158
- Total Test Methods: 812
- Total Test Functions: 392
- Total Tests: 1204

### Tests by Type
- integration: 27 files
- other: 5 files
- performance: 1 files
- server: 21 files
- unit: 103 files

### Tests by Marker
- @pytest.mark.asyncio: 29 files
- @pytest.mark.flaky: 3 files
- @pytest.mark.integration: 4 files
- @pytest.mark.parametrize: 8 files
- @pytest.mark.performance: 6 files
- @pytest.mark.skip: 5 files
- @pytest.mark.skipif: 13 files
- @pytest.mark.timeout: 1 files
- @pytest.mark.xfail: 13 files

## Test Details

### ai_whisperer/commands

#### `ai_whisperer/commands/test_commands.py`
- Type: other
- Size: 19 lines
- Test Classes:
  - `TestCommands`: 2 tests
- Tests modules:
  - `ai_whisperer.commands.echo`
  - `ai_whisperer.commands.status`

### tests

#### `tests/test_config.py`
- Type: other
- Size: 320 lines
- Test Functions: 12
- Tests modules:
  - `ai_whisperer.config`
  - `ai_whisperer.exceptions`
  - `ai_whisperer.path_management`
- Markers: @xfail

#### `tests/test_debbie_scenarios.py`
- Type: performance
- Size: 409 lines
- Test Classes:
  - `TestScenarios`: 0 tests
- Tests modules:
  - `ai_whisperer.batch.debbie_integration`
  - `ai_whisperer.batch.monitoring`
  - `ai_whisperer.batch.websocket_interceptor`
  - `ai_whisperer.logging_custom`
- Markers: @asyncio

#### `tests/test_openrouter_api.py`
- Type: other
- Size: 383 lines
- Test Functions: 21
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.ai_service.openrouter_ai_service`
  - `ai_whisperer.exceptions`

#### `tests/test_processing.py`
- Type: other
- Size: 153 lines
- Test Functions: 15
- Tests modules:
  - `ai_whisperer.exceptions`
  - `ai_whisperer.processing`

#### `tests/test_utils.py`
- Type: other
- Size: 16 lines
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.utils`

### tests/integration

#### `tests/integration/test_agent_continuation_fix.py`
- Type: integration
- Size: 148 lines
- Test Classes:
  - `TestAgentContinuationFix`: 1 tests
- Tests modules:
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.continuation_strategy`
  - `ai_whisperer.agents.stateless_agent`
  - `ai_whisperer.ai_loop.stateless_ai_loop`
  - `ai_whisperer.context.agent_context`
- Markers: @asyncio

#### `tests/integration/test_agent_continuation_integration.py`
- Type: integration
- Size: 320 lines
- Test Classes:
  - `TestAgentContinuationIntegration`: 3 tests
- Tests modules:
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.continuation_strategy`
  - `ai_whisperer.agents.stateless_agent`
  - `ai_whisperer.ai_loop.stateless_ai_loop`
  - `ai_whisperer.context.agent_context`
  - `ai_whisperer.path_management`
  - `ai_whisperer.prompt_system`
- Markers: @asyncio

#### `tests/integration/test_agent_jsonrpc_ws.py`
- Type: integration
- Size: 79 lines
- Tests modules:
  - `ai_whisperer.logging_custom`
- Markers: @xfail, @asyncio

#### `tests/integration/test_ai_tool_usage.py`
- Type: integration
- Size: 470 lines
- Test Functions: 5
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.ai_service.openrouter_ai_service`
  - `ai_whisperer.exceptions`
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.execute_command_tool`
  - `ai_whisperer.tools.read_file_tool`
  - `ai_whisperer.tools.tool_registry`
  - `ai_whisperer.tools.write_file_tool`
- Markers: @integration

#### `tests/integration/test_batch_mode_e2e.py`
- Type: integration
- Size: 48 lines
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.config`
- Markers: @integration

#### `tests/integration/test_context_integration.py`
- Type: integration
- Size: 113 lines
- Test Functions: 7
- Tests modules:
  - `ai_whisperer.agents.context_manager`
  - `ai_whisperer.context.agent_context`
  - `ai_whisperer.context_management`

#### `tests/integration/test_continuation_progress_tracking.py`
- Type: integration
- Size: 263 lines
- Test Classes:
  - `TestContinuationProgressTracking`: 0 tests
- Tests modules:
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.continuation_strategy`
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.agents.stateless_agent`
  - `ai_whisperer.context.agent_context`
- Markers: @asyncio

#### `tests/integration/test_continuation_simple.py`
- Type: integration
- Size: 177 lines
- Test Classes:
  - `TestContinuationSimple`: 5 tests
- Tests modules:
  - `ai_whisperer.agents.continuation_strategy`
  - `ai_whisperer.model_capabilities`
- Markers: @asyncio

#### `tests/integration/test_continuation_verification.py`
- Type: integration
- Size: 231 lines
- Test Classes:
  - `TestContinuationVerification`: 0 tests
- Tests modules:
  - `ai_whisperer.agents.continuation_strategy`
  - `ai_whisperer.model_capabilities`
- Markers: @asyncio

#### `tests/integration/test_conversation_persistence.py`
- Type: integration
- Size: 357 lines
- Test Classes:
  - `TestConversationPersistence`: 0 tests
- Tests modules:
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.stateless_agent`
  - `ai_whisperer.context.agent_context`
  - `ai_whisperer.context.context_manager`
  - `ai_whisperer.path_management`
- Markers: @asyncio

#### `tests/integration/test_graceful_exit.py`
- Type: integration
- Size: 88 lines
- Markers: @asyncio

#### `tests/integration/test_interactive_session.py`
- Type: integration
- Size: 68 lines
- Test Functions: 2

#### `tests/integration/test_model_compatibility_simple.py`
- Type: integration
- Size: 424 lines
- Tests modules:
  - `ai_whisperer.agents.factory`
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.ai_service.openrouter_ai_service`
  - `ai_whisperer.config`
  - `ai_whisperer.model_capabilities`
- Markers: @parametrize, @asyncio

#### `tests/integration/test_model_continuation_compatibility.py`
- Type: integration
- Size: 436 lines
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.agents.stateless_agent`
  - `ai_whisperer.config`
  - `ai_whisperer.prompt_system`
- Markers: @parametrize, @asyncio

#### `tests/integration/test_patricia_rfc_plan_integration.py`
- Type: integration
- Size: 283 lines
- Test Classes:
  - `TestPatriciaRFCToPlanIntegration`: 1 tests
- Tests modules:
  - `ai_whisperer.batch.batch_client`
  - `ai_whisperer.batch.script_processor`
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.update_plan_from_rfc_tool`
- Markers: @integration, @asyncio

#### `tests/integration/test_plan_error_recovery.py`
- Type: integration
- Size: 364 lines
- Test Classes:
  - `TestPlanErrorRecovery`: 9 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.create_rfc_tool`
  - `ai_whisperer.tools.delete_plan_tool`
  - `ai_whisperer.tools.prepare_plan_from_rfc_tool`
  - `ai_whisperer.tools.read_plan_tool`
  - `ai_whisperer.tools.save_generated_plan_tool`
  - `ai_whisperer.tools.update_plan_from_rfc_tool`
- Markers: @xfail

#### `tests/integration/test_project_pathmanager_integration.py`
- Type: integration
- Size: 200 lines
- Test Classes:
  - `TestProjectPathManagerIntegration`: 6 tests
- Tests modules:
  - `ai_whisperer.path_management`
- Markers: @xfail

#### `tests/integration/test_project_settings_persistence.py`
- Type: integration
- Size: 49 lines
- Test Functions: 1

#### `tests/integration/test_rfc_plan_bidirectional.py`
- Type: integration
- Size: 439 lines
- Test Classes:
  - `TestRFCPlanBidirectional`: 7 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.create_rfc_tool`
  - `ai_whisperer.tools.delete_plan_tool`
  - `ai_whisperer.tools.move_plan_tool`
  - `ai_whisperer.tools.prepare_plan_from_rfc_tool`
  - `ai_whisperer.tools.read_plan_tool`
  - `ai_whisperer.tools.save_generated_plan_tool`
  - `ai_whisperer.tools.update_plan_from_rfc_tool`
  - `ai_whisperer.tools.update_rfc_tool`

#### `tests/integration/test_run_plan_script.py`
- Type: integration
- Size: 62 lines
- Test Functions: 1

#### `tests/integration/test_runner_plan_ingestion.py`
- Type: integration
- Size: 315 lines
- Test Functions: 8
- Tests modules:
  - `ai_whisperer.json_validator`
  - `ai_whisperer.path_management`
  - `ai_whisperer.plan_parser`

#### `tests/integration/test_session_integration.py`
- Type: integration
- Size: 8 lines
- Test Functions: 1

#### `tests/integration/test_workspace_pathmanager_integration.py`
- Type: integration
- Size: 50 lines
- Test Functions: 3
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.workspace_detection`
- Markers: @xfail

### tests/integration/batch_mode

#### `tests/integration/batch_mode/test_batch_performance.py`
- Type: integration
- Size: 320 lines
- Test Classes:
  - `TestBatchModePerformance`: 6 tests
- Tests modules:
  - `ai_whisperer.tools.batch_command_tool`
  - `ai_whisperer.tools.script_parser_tool`
  - `ai_whisperer.tools.tool_registry`
- Markers: @skip, @performance, @skipif

#### `tests/integration/batch_mode/test_batch_script_execution.py`
- Type: integration
- Size: 393 lines
- Test Classes:
  - `TestBatchScriptIntegration`: 11 tests
- Tests modules:
  - `ai_whisperer.tools.batch_command_tool`
  - `ai_whisperer.tools.script_parser_tool`
  - `ai_whisperer.tools.tool_registry`

#### `tests/integration/batch_mode/test_debbie_agent_integration.py`
- Type: integration
- Size: 106 lines
- Test Classes:
  - `TestDebbieAgentIntegration`: 4 tests
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.path_management`
- Markers: @flaky, @skipif

### tests/interactive_server

#### `tests/interactive_server/test_ai_service_timeout.py`
- Type: server
- Size: 131 lines
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.logging_custom`
- Markers: @xfail, @performance, @asyncio

#### `tests/interactive_server/test_integration_end_to_end.py`
- Type: integration
- Size: 110 lines
- Test Functions: 2

#### `tests/interactive_server/test_interactive_client_script.py`
- Type: server
- Size: 48 lines
- Test Functions: 1
- Markers: @parametrize

#### `tests/interactive_server/test_interactive_message_models.py`
- Type: server
- Size: 54 lines
- Test Functions: 10

#### `tests/interactive_server/test_interactive_message_models_roundtrip.py`
- Type: server
- Size: 84 lines
- Test Functions: 10

#### `tests/interactive_server/test_jsonrpc_notifications.py`
- Type: server
- Size: 47 lines
- Test Functions: 2

#### `tests/interactive_server/test_jsonrpc_protocol.py`
- Type: server
- Size: 65 lines
- Test Functions: 3

#### `tests/interactive_server/test_jsonrpc_protocol_more.py`
- Type: server
- Size: 47 lines
- Test Functions: 3

#### `tests/interactive_server/test_jsonrpc_routing.py`
- Type: server
- Size: 41 lines
- Test Functions: 1

#### `tests/interactive_server/test_long_running_session.py`
- Type: server
- Size: 116 lines
- Test Functions: 1
- Markers: @performance

#### `tests/interactive_server/test_memory_usage_under_load.py`
- Type: server
- Size: 119 lines
- Markers: @xfail, @performance, @asyncio

#### `tests/interactive_server/test_message_models.py`
- Type: server
- Size: 25 lines
- Test Functions: 4

#### `tests/interactive_server/test_mocked_ailoop.py`
- Type: server
- Size: 273 lines
- Test Functions: 4
- Tests modules:
  - `ai_whisperer.ai_service.ai_service`

#### `tests/interactive_server/test_notifications_streaming.py`
- Type: server
- Size: 182 lines
- Test Functions: 2

#### `tests/interactive_server/test_openrouter_shutdown_patch.py`
- Type: server
- Size: 22 lines
- Tests modules:
  - `ai_whisperer.ai_service.openrouter_ai_service`

#### `tests/interactive_server/test_project_setup.py`
- Type: server
- Size: 26 lines
- Test Functions: 3

#### `tests/interactive_server/test_real_session_handlers.py`
- Type: server
- Size: 352 lines
- Test Functions: 4
- Markers: @skipif

#### `tests/interactive_server/test_session_manager.py`
- Type: server
- Size: 6 lines

#### `tests/interactive_server/test_tool_result_handler.py`
- Type: server
- Size: 127 lines
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.ai_service.ai_service`
  - `ai_whisperer.logging_custom`
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.tool_registry`
- Markers: @skipif

#### `tests/interactive_server/test_websocket_endpoint.py`
- Type: server
- Size: 109 lines
- Test Functions: 4
- Markers: @skipif

#### `tests/interactive_server/test_websocket_stress.py`
- Type: server
- Size: 219 lines
- Test Functions: 1
- Markers: @timeout

#### `tests/interactive_server/test_websocket_stress_subprocess.py`
- Type: server
- Size: 18 lines
- Test Functions: 1

### tests/unit

#### `tests/unit/test_agent_communication.py`
- Type: unit
- Size: 78 lines
- Test Functions: 3
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.agents.session_manager`

#### `tests/unit/test_agent_config.py`
- Type: unit
- Size: 115 lines
- Test Functions: 10
- Tests modules:
  - `ai_whisperer.agents.config`

#### `tests/unit/test_agent_context.py`
- Type: unit
- Size: 102 lines
- Test Functions: 10
- Tests modules:
  - `ai_whisperer.context.agent_context`
  - `ai_whisperer.context.provider`

#### `tests/unit/test_agent_context_manager.py`
- Type: unit
- Size: 69 lines
- Test Functions: 2
- Tests modules:
  - `ai_whisperer.agents.context_manager`
  - `ai_whisperer.agents.registry`

#### `tests/unit/test_agent_e_communication.py`
- Type: unit
- Size: 322 lines
- Test Classes:
  - `TestAgentCommunication`: 0 tests
  - `TestAgentMessage`: 2 tests
  - `TestCollaborativeRefinement`: 0 tests
- Tests modules:
  - `ai_whisperer.agents.agent_communication`
  - `ai_whisperer.agents.agent_e_handler`
- Markers: @asyncio

#### `tests/unit/test_agent_e_external_adapters.py`
- Type: unit
- Size: 569 lines
- Test Classes:
  - `TestExternalAgentAdapter`: 2 tests
  - `TestClaudeCodeAdapter`: 6 tests
  - `TestRooCodeAdapter`: 4 tests
  - `TestGitHubCopilotAdapter`: 4 tests
  - `TestAdapterErrorHandling`: 4 tests
  - `TestAdapterSelection`: 3 tests
- Tests modules:
  - `ai_whisperer.agents.decomposed_task`
  - `ai_whisperer.agents.external_adapters`
  - `ai_whisperer.agents.external_agent_result`

#### `tests/unit/test_agent_e_integration.py`
- Type: unit
- Size: 190 lines
- Test Classes:
  - `TestAgentEIntegration`: 6 tests
- Tests modules:
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.agents.stateless_agent`
  - `ai_whisperer.ai_loop.stateless_ai_loop`
  - `ai_whisperer.context.agent_context`
  - `ai_whisperer.tools.tool_registration`
  - `ai_whisperer.tools.tool_registry`
- Markers: @asyncio

#### `tests/unit/test_agent_e_task_decomposition.py`
- Type: unit
- Size: 543 lines
- Test Classes:
  - `TestTaskDecomposer`: 11 tests
  - `TestDecomposedTask`: 4 tests
  - `TestDependencyResolution`: 3 tests
  - `TestExternalAgentPromptGeneration`: 3 tests
- Tests modules:
  - `ai_whisperer.agents.agent_e_exceptions`
  - `ai_whisperer.agents.decomposed_task`
  - `ai_whisperer.agents.task_decomposer`

#### `tests/unit/test_agent_factory.py`
- Type: unit
- Size: 177 lines
- Test Functions: 10
- Tests modules:
  - `ai_whisperer.agents.agent`
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.factory`
  - `ai_whisperer.context.agent_context`

#### `tests/unit/test_agent_inspect_command.py`
- Type: unit
- Size: 41 lines
- Test Classes:
  - `TestAgentInspectCommand`: 0 tests
- Tests modules:
  - `ai_whisperer.commands`
- Markers: @asyncio

#### `tests/unit/test_agent_jsonrpc.py`
- Type: unit
- Size: 41 lines
- Test Functions: 4

#### `tests/unit/test_agent_registry.py`
- Type: unit
- Size: 79 lines
- Test Functions: 4
- Tests modules:
  - `ai_whisperer.agents.registry`

#### `tests/unit/test_agent_stateless.py`
- Type: unit
- Size: 293 lines
- Test Classes:
  - `TestAgentWithStatelessAILoop`: 2 tests
- Tests modules:
  - `ai_whisperer.agents.agent`
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.stateless_agent`
  - `ai_whisperer.ai_loop.stateless_ai_loop`
  - `ai_whisperer.context.agent_context`
- Markers: @asyncio

#### `tests/unit/test_agent_tool_filtering.py`
- Type: unit
- Size: 64 lines
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.tool_registry`

#### `tests/unit/test_agent_tool_permission.py`
- Type: unit
- Size: 94 lines
- Test Functions: 2
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.tool_registry`

#### `tests/unit/test_agent_tools.py`
- Type: unit
- Size: 54 lines
- Test Functions: 3
- Tests modules:
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.tool_registry`

#### `tests/unit/test_ai_interaction_history.py`
- Type: unit
- Size: 206 lines
- Test Functions: 2
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.ai_service.openrouter_ai_service`

#### `tests/unit/test_ai_service_interaction.py`
- Type: unit
- Size: 542 lines
- Test Classes:
  - `TestOpenRouterAIServiceUnit`: 14 tests
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.ai_service.ai_service`
  - `ai_whisperer.ai_service.openrouter_ai_service`
  - `ai_whisperer.exceptions`
- Markers: @asyncio

#### `tests/unit/test_ast_to_json_conversion.py`
- Type: unit
- Size: 838 lines
- Test Classes:
  - `TestASTToJSONStatements`: 13 tests
  - `TestASTToJSONExpressions`: 16 tests
  - `TestASTToJSONComplexStructures`: 6 tests
  - `TestASTToJSONMetadataPreservation`: 6 tests
  - `TestASTToJSONSchemaCompliance`: 6 tests
  - `TestASTToJSONEdgeCases`: 6 tests
  - `TestASTToJSONWithOptions`: 5 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_clear_command.py`
- Type: unit
- Size: 186 lines
- Test Classes:
  - `TestClearCommand`: 0 tests
- Tests modules:
  - `ai_whisperer.context.context_item`
  - `ai_whisperer.context.context_manager`
  - `ai_whisperer.path_management`
- Markers: @asyncio

#### `tests/unit/test_cli.py`
- Type: unit
- Size: 26 lines
- Test Functions: 2
- Markers: @parametrize, @skip

#### `tests/unit/test_cli_workspace_validation.py`
- Type: unit
- Size: 25 lines
- Test Functions: 2
- Tests modules:
  - `ai_whisperer`

#### `tests/unit/test_codebase_analysis_tools.py`
- Type: unit
- Size: 372 lines
- Test Classes:
  - `TestAnalyzeLanguagesTool`: 6 tests
  - `TestFindSimilarCodeTool`: 6 tests
  - `TestGetProjectStructureTool`: 7 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.analyze_languages_tool`
  - `ai_whisperer.tools.find_similar_code_tool`
  - `ai_whisperer.tools.get_project_structure_tool`

#### `tests/unit/test_context_manager.py`
- Type: unit
- Size: 71 lines
- Test Functions: 6
- Tests modules:
  - `ai_whisperer.context_management`

#### `tests/unit/test_context_provider.py`
- Type: unit
- Size: 50 lines
- Test Functions: 4
- Tests modules:
  - `ai_whisperer.context.provider`

#### `tests/unit/test_context_serialization.py`
- Type: unit
- Size: 95 lines
- Test Functions: 7
- Tests modules:
  - `ai_whisperer.context.agent_context`
  - `ai_whisperer.context.provider`

#### `tests/unit/test_context_tracking.py`
- Type: unit
- Size: 234 lines
- Test Classes:
  - `TestContextItem`: 4 tests
  - `TestAgentContextManager`: 7 tests
- Tests modules:
  - `ai_whisperer.context.context_item`
  - `ai_whisperer.context.context_manager`
  - `ai_whisperer.path_management`
- Markers: @xfail

#### `tests/unit/test_continuation_depth.py`
- Type: unit
- Size: 198 lines
- Markers: @asyncio

#### `tests/unit/test_continuation_strategy.py`
- Type: unit
- Size: 413 lines
- Test Classes:
  - `TestContinuationProgress`: 2 tests
  - `TestContinuationState`: 3 tests
  - `TestContinuationStrategy`: 19 tests
- Tests modules:
  - `ai_whisperer.agents.continuation_strategy`

#### `tests/unit/test_debbie_command.py`
- Type: unit
- Size: 317 lines
- Test Classes:
  - `TestDebbieCommand`: 16 tests
  - `TestDebbieCommandIntegration`: 1 tests
- Tests modules:
  - `ai_whisperer.commands.debbie`
  - `ai_whisperer.commands.errors`
  - `ai_whisperer.commands.registry`

#### `tests/unit/test_debbie_observer.py`
- Type: unit
- Size: 341 lines
- Test Classes:
  - `TestPatternDetector`: 4 tests
  - `TestInteractiveMonitor`: 6 tests
  - `TestDebbieObserver`: 6 tests
  - `TestDebbieObserverIntegration`: 1 tests
- Markers: @asyncio

#### `tests/unit/test_direct_streaming.py`
- Type: unit
- Size: 335 lines
- Test Classes:
  - `TestDirectStreaming`: 0 tests
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.context.agent_context`
- Markers: @asyncio

#### `tests/unit/test_enhanced_prompt_system.py`
- Type: unit
- Size: 374 lines
- Test Classes:
  - `TestEnhancedPromptSystem`: 13 tests
  - `TestPromptSystemIntegration`: 2 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.prompt_system`
- Markers: @integration

#### `tests/unit/test_error_handling_ast_validation.py`
- Type: unit
- Size: 490 lines
- Test Classes:
  - `TestSyntaxErrors`: 6 tests
  - `TestStructuralValidationErrors`: 4 tests
  - `TestJSONSerializationErrors`: 3 tests
  - `TestValidationRuleErrors`: 4 tests
  - `TestMetadataValidationErrors`: 3 tests
  - `TestConfigurationValidationErrors`: 3 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_error_handling_edge_cases.py`
- Type: unit
- Size: 534 lines
- Test Classes:
  - `TestMalformedInputFiles`: 7 tests
  - `TestBoundaryConditions`: 5 tests
  - `TestCorruptedStructures`: 5 tests
  - `TestSpecialCharacterEdgeCases`: 4 tests
  - `TestPathologicalInputs`: 3 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`
- Markers: @xfail

#### `tests/unit/test_error_handling_file_io.py`
- Type: unit
- Size: 559 lines
- Test Classes:
  - `TestFileAccessErrors`: 6 tests
  - `TestFileContentErrors`: 5 tests
  - `TestFileSystemErrors`: 4 tests
  - `TestConcurrentAccessErrors`: 3 tests
  - `TestResourceExhaustionErrors`: 3 tests
  - `TestBatchProcessingErrors`: 3 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_error_handling_graceful_degradation.py`
- Type: unit
- Size: 467 lines
- Test Classes:
  - `TestPartialProcessingDegradation`: 5 tests
  - `TestResourceConstraintDegradation`: 4 tests
  - `TestBatchProcessingDegradation`: 3 tests
  - `TestUserExperienceDegradation`: 4 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_error_handling_system_stability.py`
- Type: unit
- Size: 662 lines
- Test Classes:
  - `TestMemoryStability`: 4 tests
  - `TestThreadSafety`: 3 tests
  - `TestExceptionSafety`: 3 tests
  - `TestSystemResourceStability`: 3 tests
  - `TestDataIntegrityUnderErrors`: 3 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_execute_command_tool.py`
- Type: unit
- Size: 167 lines
- Test Functions: 11
- Tests modules:
  - `ai_whisperer.tools.execute_command_tool`

#### `tests/unit/test_file_service.py`
- Type: unit
- Size: 321 lines
- Test Classes:
  - `TestFileService`: 7 tests
- Tests modules:
  - `ai_whisperer.path_management`
- Markers: @asyncio

#### `tests/unit/test_file_tools.py`
- Type: unit
- Size: 344 lines
- Test Functions: 21
- Tests modules:
  - `ai_whisperer.exceptions`
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.read_file_tool`
  - `ai_whisperer.tools.write_file_tool`

#### `tests/unit/test_find_pattern_tool.py`
- Type: unit
- Size: 254 lines
- Test Classes:
  - `TestFindPatternTool`: 14 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.find_pattern_tool`

#### `tests/unit/test_format_json.py`
- Type: unit
- Size: 127 lines
- Test Classes:
  - `TestFormatJson`: 8 tests

#### `tests/unit/test_get_file_content_tool.py`
- Type: unit
- Size: 245 lines
- Test Functions: 15
- Tests modules:
  - `ai_whisperer.exceptions`
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.get_file_content_tool`

#### `tests/unit/test_jsonrpc_handlers_refactor.py`
- Type: unit
- Size: 170 lines
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.agents.agent`
  - `ai_whisperer.agents.config`
  - `ai_whisperer.agents.factory`
- Markers: @asyncio

#### `tests/unit/test_list_directory_tool.py`
- Type: unit
- Size: 184 lines
- Test Functions: 12
- Tests modules:
  - `ai_whisperer.exceptions`
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.list_directory_tool`

#### `tests/unit/test_logging.py`
- Type: unit
- Size: 264 lines
- Test Functions: 3
- Tests modules:
  - `ai_whisperer.logging_custom`

#### `tests/unit/test_mailbox_system.py`
- Type: unit
- Size: 170 lines
- Test Classes:
  - `TestMailboxSystem`: 6 tests
- Tests modules:
  - `ai_whisperer.agents.mailbox`

#### `tests/unit/test_metadata_preservation.py`
- Type: unit
- Size: 1075 lines
- Test Classes:
  - `TestDocstringPreservation`: 4 tests
  - `TestSourceLocationMetadata`: 5 tests
  - `TestCommentPreservation`: 5 tests
  - `TestFormattingPreservation`: 6 tests
  - `TestMetadataRoundTrip`: 5 tests
  - `TestEdgeCasesAndErrors`: 4 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_minimal_nested_schema.py`
- Type: unit
- Size: 0 lines

#### `tests/unit/test_minimal_schema_validation.py`
- Type: unit
- Size: 22 lines
- Test Functions: 1

#### `tests/unit/test_openrouter_advanced_features.py`
- Type: unit
- Size: 503 lines
- Test Classes:
  - `TestOpenRouterAdvancedFeatures`: 12 tests
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.ai_service.openrouter_ai_service`
  - `ai_whisperer.exceptions`
- Markers: @flaky, @xfail, @skip, @skipif

#### `tests/unit/test_openrouter_api_detailed.py`
- Type: unit
- Size: 132 lines
- Test Functions: 4
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.ai_service.openrouter_ai_service`

#### `tests/unit/test_path_management.py`
- Type: unit
- Size: 152 lines
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.path_management`

#### `tests/unit/test_plan_ingestion.py`
- Type: unit
- Size: 505 lines
- Test Functions: 22
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.plan_parser`

#### `tests/unit/test_plan_tools.py`
- Type: unit
- Size: 625 lines
- Test Classes:
  - `TestCreatePlanFromRFCTool`: 5 tests
  - `TestListPlansTool`: 3 tests
  - `TestReadPlanTool`: 2 tests
  - `TestUpdatePlanFromRFCTool`: 2 tests
  - `TestMovePlanTool`: 2 tests
- Tests modules:
  - `ai_whisperer.ai_service.ai_service`
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.create_plan_from_rfc_tool`
  - `ai_whisperer.tools.list_plans_tool`
  - `ai_whisperer.tools.move_plan_tool`
  - `ai_whisperer.tools.read_plan_tool`
  - `ai_whisperer.tools.update_plan_from_rfc_tool`

#### `tests/unit/test_planner_handler.py`
- Type: unit
- Size: 67 lines
- Test Functions: 5
- Tests modules:
  - `ai_whisperer.agents.planner_handler`
  - `ai_whisperer.agents.registry`

#### `tests/unit/test_planner_tools.py`
- Type: unit
- Size: 46 lines
- Test Functions: 3
- Tests modules:
  - `ai_whisperer.agents.planner_tools`

#### `tests/unit/test_postprocessing_add_items.py`
- Type: unit
- Size: 983 lines
- Test Classes:
  - `TestAddItemsPostprocessor`: 25 tests
- Markers: @xfail

#### `tests/unit/test_postprocessing_backticks.py`
- Type: unit
- Size: 138 lines
- Test Functions: 3
- Markers: @parametrize

#### `tests/unit/test_postprocessing_fields.py`
- Type: unit
- Size: 171 lines
- Test Functions: 1
- Markers: @parametrize

#### `tests/unit/test_postprocessing_pipeline.py`
- Type: unit
- Size: 105 lines
- Test Functions: 3

#### `tests/unit/test_postprocessing_text_fields.py`
- Type: unit
- Size: 129 lines
- Test Functions: 2
- Markers: @parametrize

#### `tests/unit/test_postprocessing_type_preservation.py`
- Type: unit
- Size: 124 lines
- Test Classes:
  - `TestTypePreservation`: 10 tests

#### `tests/unit/test_prompt_optimizer.py`
- Type: unit
- Size: 141 lines
- Test Classes:
  - `TestPromptOptimizer`: 9 tests
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.agents.prompt_optimizer`
- Markers: @parametrize

#### `tests/unit/test_prompt_rules_removal.py`
- Type: unit
- Size: 87 lines
- Test Classes:
  - `TestInitialPlanPromptRules`: 2 tests
  - `TestSubtaskGeneratorPromptRules`: 1 tests
- Test Functions: 2

#### `tests/unit/test_prompt_system_performance.py`
- Type: unit
- Size: 182 lines
- Test Classes:
  - `TestPromptSystemPerformance`: 5 tests
- Tests modules:
  - `ai_whisperer.prompt_system`
- Markers: @performance

#### `tests/unit/test_python_ast_json_design.py`
- Type: unit
- Size: 200 lines
- Test Classes:
  - `TestPythonASTJSONDesignRequirements`: 10 tests
  - `TestPythonASTJSONSchemaCompleteness`: 4 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_python_ast_json_tool.py`
- Type: unit
- Size: 231 lines
- Test Classes:
  - `TestPythonASTJSONToolSchema`: 5 tests
  - `TestPythonASTJSONToolAPI`: 6 tests
  - `TestPythonASTJSONToolStaticMethods`: 6 tests
  - `TestPythonASTJSONToolBidirectional`: 5 tests
  - `TestPythonASTJSONToolIntegration`: 3 tests
- Tests modules:
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_python_ast_parsing.py`
- Type: unit
- Size: 607 lines
- Test Classes:
  - `TestASTParsingFilePaths`: 1 tests
  - `TestASTParsingModules`: 1 tests
  - `TestASTParsingCodeStrings`: 1 tests
  - `TestASTParsingInvalidSyntax`: 6 tests
  - `TestASTNodeStructureVerification`: 1 tests
  - `TestPython38PlusFeatures`: 8 tests
  - `TestASTParsingEdgeCases`: 1 tests
  - `TestASTParsingMetadata`: 4 tests
- Test Functions: 18
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_python_ast_parsing_advanced.py`
- Type: unit
- Size: 340 lines
- Test Classes:
  - `TestASTParsingAdvancedFeatures`: 8 tests
  - `TestASTParsingErrorHandling`: 1 tests
  - `TestASTParsingPerformance`: 1 tests
  - `TestASTParsingStaticMethods`: 5 tests
- Test Functions: 3
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_refactored_ai_loop.py`
- Type: unit
- Size: 493 lines
- Test Functions: 1
- Markers: @asyncio

#### `tests/unit/test_refine_ai_interaction.py`
- Type: unit
- Size: 214 lines
- Test Classes:
  - `TestRefineAIInteraction`: 4 tests
- Markers: @skipif

#### `tests/unit/test_rfc_extension_regression.py`
- Type: unit
- Size: 187 lines
- Test Classes:
  - `TestRFCExtensionRegression`: 4 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.create_rfc_tool`
  - `ai_whisperer.tools.delete_rfc_tool`
  - `ai_whisperer.tools.move_rfc_tool`

#### `tests/unit/test_rfc_move_extensions.py`
- Type: unit
- Size: 250 lines
- Test Classes:
  - `TestMoveRFCExtensions`: 5 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.create_rfc_tool`
  - `ai_whisperer.tools.move_rfc_tool`
- Markers: @skipif

#### `tests/unit/test_rfc_naming.py`
- Type: unit
- Size: 297 lines
- Test Classes:
  - `TestRFCNaming`: 9 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.create_rfc_tool`
  - `ai_whisperer.tools.delete_rfc_tool`
  - `ai_whisperer.tools.list_rfcs_tool`
  - `ai_whisperer.tools.move_rfc_tool`
  - `ai_whisperer.tools.read_rfc_tool`

#### `tests/unit/test_rfc_tools.py`
- Type: unit
- Size: 347 lines
- Test Classes:
  - `TestCreateRFCTool`: 5 tests
  - `TestReadRFCTool`: 3 tests
  - `TestListRFCsTool`: 4 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.create_rfc_tool`
  - `ai_whisperer.tools.list_rfcs_tool`
  - `ai_whisperer.tools.read_rfc_tool`

#### `tests/unit/test_rfc_tools_complete.py`
- Type: unit
- Size: 353 lines
- Test Classes:
  - `TestUpdateRFCTool`: 8 tests
  - `TestMoveRFCTool`: 7 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.move_rfc_tool`
  - `ai_whisperer.tools.update_rfc_tool`

#### `tests/unit/test_round_trip_working.py`
- Type: unit
- Size: 421 lines
- Test Classes:
  - `TestRoundTripBasicConstructs`: 4 tests
  - `TestRoundTripDataStructures`: 3 tests
  - `TestRoundTripControlFlow`: 3 tests
  - `TestRoundTripRealWorld`: 1 tests
- Tests modules:
  - `ai_whisperer.tools.python_ast_json_tool`

#### `tests/unit/test_scripted_postprocessing.py`
- Type: unit
- Size: 101 lines
- Test Functions: 3

#### `tests/unit/test_search_files_tool.py`
- Type: unit
- Size: 305 lines
- Test Functions: 16
- Tests modules:
  - `ai_whisperer.exceptions`
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.search_files_tool`

#### `tests/unit/test_session_manager.py`
- Type: unit
- Size: 85 lines
- Test Functions: 4
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.agents.session_manager`

#### `tests/unit/test_session_manager_refactor.py`
- Type: unit
- Size: 8 lines
- Test Functions: 1

#### `tests/unit/test_state_management.py`
- Type: unit
- Size: 204 lines
- Test Classes:
  - `TestStateManagement`: 12 tests
- Tests modules:
  - `ai_whisperer.context_management`
  - `ai_whisperer.state_management`
- Markers: @skipif

#### `tests/unit/test_stateless_ailoop.py`
- Type: unit
- Size: 954 lines
- Test Classes:
  - `TestStatelessAILoop`: 0 tests
- Tests modules:
  - `ai_whisperer.ai_loop.ai_config`
  - `ai_whisperer.ai_loop.stateless_ai_loop`
  - `ai_whisperer.context.provider`
- Markers: @xfail, @asyncio, @skipif

#### `tests/unit/test_tool_calling_standard.py`
- Type: unit
- Size: 455 lines
- Test Classes:
  - `TestToolCallingStandard`: 7 tests
  - `TestDebbieSessionTools`: 0 tests
  - `TestModelSpecificBehavior`: 1 tests
  - `TestStreamingToolCalls`: 1 tests
- Tests modules:
  - `ai_whisperer.ai_service.tool_calling`
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.monitoring_control_tool`
  - `ai_whisperer.tools.session_analysis_tool`
  - `ai_whisperer.tools.session_health_tool`
- Markers: @asyncio

#### `tests/unit/test_tool_management.py`
- Type: unit
- Size: 228 lines
- Test Functions: 8
- Tests modules:
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.tool_registry`

#### `tests/unit/test_tool_sets.py`
- Type: unit
- Size: 412 lines
- Test Classes:
  - `TestToolSet`: 2 tests
  - `TestToolSetManager`: 4 tests
  - `TestToolRegistryWithSets`: 4 tests
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.tool_registry`
  - `ai_whisperer.tools.tool_set`

#### `tests/unit/test_tool_tags.py`
- Type: unit
- Size: 96 lines
- Test Functions: 5
- Tests modules:
  - `ai_whisperer.tools.execute_command_tool`
  - `ai_whisperer.tools.read_file_tool`
  - `ai_whisperer.tools.tool_registry`
  - `ai_whisperer.tools.write_file_tool`

#### `tests/unit/test_tool_usage_logging.py`
- Type: unit
- Size: 41 lines
- Test Functions: 1
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.tools.base_tool`
  - `ai_whisperer.tools.tool_usage_logging`

#### `tests/unit/test_web_tools.py`
- Type: unit
- Size: 360 lines
- Test Classes:
  - `TestWebSearchTool`: 7 tests
  - `TestFetchURLTool`: 8 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.fetch_url_tool`
  - `ai_whisperer.tools.web_search_tool`
- Markers: @skipif

#### `tests/unit/test_workspace_detection.py`
- Type: unit
- Size: 52 lines
- Test Functions: 5
- Tests modules:
  - `ai_whisperer.workspace_detection`

#### `tests/unit/test_workspace_detection_edge_cases.py`
- Type: unit
- Size: 63 lines
- Test Functions: 4
- Tests modules:
  - `ai_whisperer.workspace_detection`

#### `tests/unit/test_workspace_handler.py`
- Type: unit
- Size: 236 lines
- Test Classes:
  - `TestWorkspaceHandler`: 1 tests
- Tests modules:
  - `ai_whisperer.path_management`
- Markers: @asyncio

#### `tests/unit/test_workspace_stats_tool.py`
- Type: unit
- Size: 261 lines
- Test Classes:
  - `TestWorkspaceStatsTool`: 15 tests
- Tests modules:
  - `ai_whisperer.path_management`
  - `ai_whisperer.tools.workspace_stats_tool`

#### `tests/unit/test_workspace_tools.py`
- Type: unit
- Size: 104 lines
- Test Functions: 4
- Tests modules:
  - `ai_whisperer.tools.get_file_content_tool`
  - `ai_whisperer.tools.list_directory_tool`
  - `ai_whisperer.tools.search_files_tool`
  - `ai_whisperer.tools.tool_registry`

### tests/unit/batch_mode

#### `tests/unit/batch_mode/test_batch_command_performance.py`
- Type: unit
- Size: 281 lines
- Test Classes:
  - `TestBatchCommandPerformance`: 7 tests
- Tests modules:
  - `ai_whisperer.tools.batch_command_tool`
  - `ai_whisperer.tools.script_parser_tool`
- Markers: @skip, @xfail, @performance

#### `tests/unit/batch_mode/test_batch_command_tool.py`
- Type: unit
- Size: 501 lines
- Test Classes:
  - `TestBatchCommandTool`: 18 tests
  - `TestCommandInterpreter`: 6 tests
- Tests modules:
  - `ai_whisperer.tools.batch_command_tool`
  - `ai_whisperer.tools.script_parser_tool`

#### `tests/unit/batch_mode/test_debbie_agent_config.py`
- Type: unit
- Size: 74 lines
- Test Classes:
  - `TestDebbieAgentConfig`: 6 tests
- Tests modules:
  - `ai_whisperer.agents.registry`

#### `tests/unit/batch_mode/test_debbie_prompt_system.py`
- Type: unit
- Size: 147 lines
- Test Classes:
  - `TestDebbiePromptSystem`: 6 tests
- Tests modules:
  - `ai_whisperer.agents.registry`
  - `ai_whisperer.path_management`
  - `ai_whisperer.prompt_system`
- Markers: @flaky, @skipif

#### `tests/unit/batch_mode/test_script_parser_security.py`
- Type: unit
- Size: 257 lines
- Test Classes:
  - `TestScriptParserSecurity`: 10 tests
- Tests modules:
  - `ai_whisperer.tools.script_parser_tool`
- Markers: @skip, @skipif

#### `tests/unit/batch_mode/test_script_parser_tool.py`
- Type: unit
- Size: 258 lines
- Test Classes:
  - `TestScriptParserTool`: 18 tests
- Tests modules:
  - `ai_whisperer.tools.script_parser_tool`

#### `tests/unit/batch_mode/test_script_parser_validation.py`
- Type: unit
- Size: 255 lines
- Test Classes:
  - `TestScriptParserValidation`: 13 tests
- Tests modules:
  - `ai_whisperer.tools.script_parser_tool`

