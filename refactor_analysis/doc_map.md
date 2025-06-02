# AIWhisperer Documentation Map

## Summary
- Total Documentation Files: 239
- Total Lines: 37,487
- Empty Files: 1
- Possibly Outdated: 54

### Documentation by Category
- architecture: 2 files
- archive: 17 files
- development: 2 files
- execution_log: 10 files
- implementation: 19 files
- other: 72 files
- plan: 27 files
- prompt: 18 files
- readme: 5 files
- rfc: 20 files
- status: 38 files
- user_guide: 9 files

## Documentation Details

### Architecture

#### `docs/architecture/architecture.md`
**Title**: AIWhisperer Stateless Architecture
- Lines: 120
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: interactive_server/message_models.py, message_models.py
  - Docs: prompt_system.md, stateless_architecture.md, configuration.md

#### `docs/architecture/stateless_architecture.md`
**Title**: Stateless Architecture Overview
- Lines: 108
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: tests/integration/test_no_delegates.py, ai_whisperer/ai_loop/stateless_ai_loop.py, test_stateless_session_manager.py

### Archive

#### `docs/archive/DEVELOPMENT_PLAN.md`
**Title**: AI Whisperer Development Plan
- Lines: 151
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/ai_whisperer/ai_loop.py, ai_loop.py, src/ai_whisperer/main.py
  - Docs: prompt.md

#### `docs/archive/analysis/cost_token_analysis_summary.md`
**Title**: Cost and Token Information Analysis for OpenRouter API Integration
- Lines: 102
- Last Modified: 2025-05-29
- References:
  - Python: src/ai_whisperer/ai_service_interaction.py, ai_service_interaction.py
  - Docs: store_cost_tokens_to_ai_calls.md

#### `docs/archive/analysis/docs_update_plan_cost_tracking.md`
**Title**: Documentation Update Plan: Cost and Token Tracking Feature
- Lines: 98
- Last Modified: 2025-05-29
- References:
  - Docs: usage.md, ai_service_interaction.md, index.md

#### `docs/archive/analysis/model_selection_plan.md`
**Title**: Model Selection Plan for Task-Specific Configuration
- Lines: 190
- Last Modified: 2025-05-29
- References:
  - Python: src/ai_whisperer/orchestrator.py, src/ai_whisperer/config.py, src/ai_whisperer/subtask_generator.py

#### `docs/archive/analysis/path_manager_analysis.md`
**Title**: Path Manager Usage Analysis for Directory Restriction
- Lines: 168
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: path_management.py, read_file_tool.py, cli.py

#### `docs/archive/analysis/prompt_analysis.md`
**Title**: Default Prompts Analysis: Fixed Items Requirements
- Lines: 64
- Last Modified: 2025-05-29
- References:
  - Docs: subtask_generator_default.md, initial_plan_default.md

#### `docs/archive/analysis/prompt_loading_analysis.md`
**Title**: Enhanced Analysis of Current Prompt Loading System
- Lines: 67
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/ai_whisperer/config.py, config.py
  - Docs: prompts/subtask_generator_default.md, prompts/refine_requirements_default.md, refine_requirements_default.md

#### `docs/archive/delegate_system/ai_loop_documentation.md`
**Title**: AI Loop Documentation
- Lines: 82
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: interactive_ai.py, ai_whisperer/ai_loop/ai_loopy.py, ai_loopy.py

#### `docs/archive/delegate_system/refactored_ai_loop_design.md`
**Title**: Refactored AI Loop Design
- Lines: 328
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Docs: ai_loop_refactor_analysis.md, docs/ai_loop_refactor_analysis.md

#### `docs/archive/delegate_system/user_message_analysis.md`
**Title**: Analysis and Design: User Message Delegate System
- Lines: 130
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/ai_whisperer/delegate_manager.py, delegate_manager.py, logging_custom.py
  - Docs: add_user_message_delegate.md

#### `docs/archive/delegate_system/user_message_system.md`
**Title**: User Message System
- Lines: 107
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/ai_whisperer/logging_custom.py, basic_output_test.py, logging_custom.py

#### `docs/archive/old_architecture/execution_engine.md`
**Title**: Execution Engine Documentation
- Lines: 150
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/ai_whisperer/ai_service_interaction.py, ai_service_interaction.py
  - Docs: landmark_selection.md, ./logging_monitoring.md, capital_validation_result.md

#### `docs/archive/old_architecture/internal_process.md`
**Title**: Internal Process Documentation
- Lines: 176
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/ai_whisperer/ai_loop.py, ai_loop.py, src/ai_whisperer/json_validator.py
  - Docs: ./logging_monitoring.md, logging_monitoring.md

#### `docs/archive/old_architecture/plan_document_execute_command_tool.md`
**Title**: Plan to Document `execute_command` Tool
- Lines: 129
- Last Modified: 2025-05-29
- References:
  - Python: script.py, execute_command_tool.py, data_processor.py
  - Docs: tool_interface_design.md

#### `docs/archive/terminal_ui/detail_option_implementation_plan.md`
**Title**: Plan: Add Detail Level Option to ANSIConsoleUserMessageHandler and CLI
- Lines: 216
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/basic_output_display_message.py, src/ai_whisperer/cli.py, src/ai_whisperer/main.py
  - Docs: docs/detail_option_implementation_plan.md, detail_option_implementation_plan.md, add_detail_cli_option.md

#### `docs/archive/terminal_ui/list_models_interaction_analysis.md`
**Title**: Analysis: Interactive `list-models` with "Ask AI about Model" Feature
- Lines: 123
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: ai_whisperer/commands.py, cli.py, monitor/interactive_delegate.py

#### `docs/archive/terminal_ui/terminal_command_mode_design.md`
**Title**: Terminal Monitor Command Mode Design
- Lines: 195
- Last Modified: 2025-05-29
- References:
  - Docs: monitor_terminal_analysis.md

### Development

#### `CONTRIBUTING.md`
**Title**: Contributing to AI Whisperer
- Lines: 3
- Last Modified: 2025-05-28

#### `docs/development-tool-wishlist.md`
**Title**: Development Tool Wishlist
- Lines: 67
- Last Modified: 2025-06-01

### Execution Log

#### `REFACTOR_EXECUTION_LOG.md`
**Title**: AIWhisperer Refactor Execution Log
- Lines: 172
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: cli.py, analyze_code_structure.py, main.py
  - Docs: REFACTOR_EXECUTION_LOG.md, REFACTOR_CHANGELOG.md, REFACTOR_PROTO_TO_PROD_OVERVIEW.md

#### `docs/agent-e-implementation-log.md`
**Title**: Agent E Implementation Log (GREEN Phase)
- Lines: 17
- Last Modified: 2025-06-01
- References:
  - Python: test_agent_e_task_decomposition.py

#### `docs/agent-e-subtask1-execution-log.md`
**Title**: Agent E Subtask 1 Execution Log
- Lines: 224
- Last Modified: 2025-06-01
- References:
  - Python: base_handler.py, session_manager.py, planner_handler.py
  - Docs: prompt.md

#### `docs/agent-e-subtask2-execution-log.md`
**Title**: Agent E Subtask 2 Execution Log
- Lines: 136
- Last Modified: 2025-06-01
- References:

#### `docs/agent-e-subtask3-execution-log.md`
**Title**: Agent E Subtask 3 Execution Log
- Lines: 146
- Last Modified: 2025-06-01
- References:
  - Python: message_models.py
  - Docs: design.md

#### `docs/agent-e-subtask4-execution-log.md`
**Title**: Agent E Subtask 4 Execution Log
- Lines: 109
- Last Modified: 2025-06-01
- References:
  - Python: test_agent_stateless.py, test_agent_e_task_decomposition.py, test_agent_e_communication.py

#### `docs/agent-e-subtask5-execution-log.md`
**Title**: Agent E Subtask 5 Execution Log
- Lines: 89
- Last Modified: 2025-06-01
- References:
  - Python: test_agent_e_external_adapters.py

#### `docs/agent-e-tools-execution-log.md`
**Title**: Agent E Tools Implementation - Execution Log
- Lines: 150
- Last Modified: 2025-06-01
- References:
  - Python: parse_external_result_tool.py, /ai_whisperer/tools/recommend_external_agent_tool.py, decompose_plan_tool.py
  - Docs: prompt.md

#### `docs/debugging-session-2025-05-30/DEBBIE_ENHANCED_LOGGING_DESIGN.md`
**Title**: Debbie's Enhanced Logging & Python Execution Design
- Lines: 455
- Last Modified: 2025-05-30
- References:

#### `docs/research/ai-response-parsing-execution-log.md`
**Title**: AI Response Parsing and Display Execution Log
- Lines: 127
- Last Modified: 2025-06-02
- References:
  - Python: /home/deano/projects/AIWhisperer/interactive_server/message_models.py, /home/deano/projects/AIWhisperer/interactive_server/stateless_session_manager.py, stateless_ai_loop.py

### Implementation

#### `TECHNICAL_SPECIFICATIONS.md`
**Title**: Technical Specifications for UI Improvements
- Lines: 567
- Last Modified: 2025-06-02
- References:
  - Python: workspace_handler.py, terminal_handler.py

#### `docs/Initial/AI Coding Assistant Tool_ Research and Design Report.md`
**Title**: AI Coding Assistant Tool: Research and Design Report
- Lines: 318
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: parser_core.py

#### `docs/agent-e-data-structures-design.md`
**Title**: Agent E Data Structures Design
- Lines: 424
- Last Modified: 2025-06-01
- References:
  - Python: test_task_decomposer.py, task_decomposer.py, stateless_agent.py

#### `docs/agent_context_tracking_design.md`
**Title**: Agent Context Tracking Design
- Lines: 303
- Last Modified: 2025-05-29
- References:
  - Python: file.py, main.py

#### `docs/at_command_technical_spec.md`
**Title**: @ Command File Reference Technical Specification
- Lines: 236
- Last Modified: 2025-05-29
- References:
  - Python: path.py, main.py
  - Docs: README.md

#### `docs/code_generation_handler_design.md`
**Title**: Code Generation Handler Technical Design
- Lines: 387
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: ai_service_interaction.py, execution_engine.py, src/ai_whisperer/execution_engine.py
  - Docs: docs/code_generation_handler_research.md, code_generation_handler_research.md

#### `docs/context_manager_design.md`
**Title**: ContextManager Design
- Lines: 51
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: code_generation.py, src/ai_whisperer/agent_handlers/code_generation.py

#### `docs/cost_token_storage_design.md`
**Title**: Design for Storing AI Interaction Cost and Token Information
- Lines: 138
- Last Modified: 2025-05-28
- References:
  - Python: state_management.py, src/ai_whisperer/state_management.py
  - Docs: cost_token_analysis_summary.md

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE3_INTERACTIVE_MONITORING_DESIGN.md`
**Title**: Debbie Phase 3: Interactive Mode Monitoring Design
- Lines: 155
- Last Modified: 2025-05-30
- References:
  - Python: main.py

#### `docs/debugging-session-2025-05-30/REASONING_TOKEN_IMPLEMENTATION.md`
**Title**: Reasoning Token Implementation
- Lines: 76
- Last Modified: 2025-05-30
- References:
  - Python: test_reasoning_tokens.py

#### `docs/execute_command_tool_design.md`
**Title**: Design for `execute_command` Tool
- Lines: 173
- Last Modified: 2025-05-28
- References:
  - Python: script_name.py, base_tool.py, execute_command_tool.py

#### `docs/file_browser_implementation_priority.md`
**Title**: File Browser Implementation Priority Guide
- Lines: 83
- Last Modified: 2025-05-29

#### `docs/mailbox-system-design.md`
**Title**: Universal Mailbox System Design
- Lines: 117
- Last Modified: 2025-06-01

#### `docs/path_management_design.md`
**Title**: Path Management System Design
- Lines: 131
- Last Modified: 2025-05-28
- References:
  - Docs: requirements.md

#### `docs/postprocessing_design.md`
**Title**: YAML Postprocessing Design
- Lines: 251
- Last Modified: 2025-05-28

#### `docs/research/agentic_ai_continuation_research/product_implementation_comparison.md`
**Title**: Implementation of Multi-Message Flows in AI Products
- Lines: 147
- Last Modified: 2025-06-02

#### `docs/tool_interface_design.md`
**Title**: AI Tool Interface Design for AIWhisperer
- Lines: 401
- Last Modified: 2025-05-28
- References:
  - Python: my_script.py, script.py, main.py

#### `docs/tool_management_design.md`
**Title**: AI Tool Management Design for AIWhisperer
- Lines: 381
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: .py
  - Docs: tool_interface_design.md, docs/tool_interface_design.md

#### `docs/workspace_ai_tools_spec.md`
**Title**: Workspace AI Tools Specification
- Lines: 237
- Last Modified: 2025-05-29
- References:
  - Python: file.py, @file.py

### Other

#### `CLAUDE.local.md`
- Lines: 0
- Last Modified: 2025-05-29
- ⚠️ **Empty File**

#### `CLAUDE.md`
**Title**: CLAUDE.md
- Lines: 328
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_rfc_plan_bidirectional.py, interactive_server/message_models.py, ai_whisperer/config.py
  - Docs: prompt.md, log.md, BATCH_MODE_USAGE_FOR_AI.md

#### `CODE_OF_CONDUCT.md`
**Title**: Code of Conduct
- Lines: 3
- Last Modified: 2025-05-28

#### `MERGE_READINESS_REPORT.md`
**Title**: Merge Readiness Report - Feature Branch: feature-agent-e
- Lines: 81
- Last Modified: 2025-06-01
- References:
  - Python: tests/unit/conftest.py, conftest.py, ai_whisperer/tools/python_ast_json_tool.py
  - Docs: TEST_COMPLETION_SUMMARY.md

#### `NEXT_STEPS_BATCH_MODE_PHASE2.md`
**Title**: Next Steps: Batch Mode Phase 2 - Debbie the Batcher
- Lines: 203
- Last Modified: 2025-05-30
- References:
  - Python: test_script_parser_tool.py, test_batch_command_tool.py, test_debbie_batcher_agent.py
  - Docs: prompt.md

#### `PR_DESCRIPTION.md`
**Title**: Fix Critical Chat Bugs and Add Debugging Tools
- Lines: 73
- Last Modified: 2025-05-30
- References:
  - Python: ai_whisperer/ai_service/openrouter_ai_service.py, ai_whisperer/ai_loop/stateless_ai_loop.py, stateless_ai_loop.py

#### `REFACTOR_CHANGELOG.md`
**Title**: AIWhisperer Refactor Change Log
- Lines: 72
- Last Modified: 2025-06-02
- References:
  - Docs: REFACTOR_EXECUTION_LOG.md, REFACTOR_CHANGELOG.md, REFACTOR_PROTO_TO_PROD_OVERVIEW.md

#### `REFACTOR_CURRENT_STATE_SNAPSHOT.md`
**Title**: AIWhisperer Current State Snapshot
- Lines: 67
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:

#### `REFACTOR_PROTO_TO_PROD_OVERVIEW.md`
**Title**: AIWhisperer Refactor: Prototype to Production Overview
- Lines: 212
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Docs: CLAUDE.md

#### `STRUCTURED_OUTPUT_FINDINGS.md`
**Title**: Structured Output Testing Results
- Lines: 93
- Last Modified: 2025-05-31
- References:
  - Python: test_structured_output.py

#### `UNTESTED_MODULES_REPORT.md`
**Title**: Untested Python Modules Report
- Lines: 105
- Last Modified: 2025-06-02
- References:
  - Python: ai_whisperer/commands/help.py, system_health_check_tool.py, server_manager.py

#### `docs/DEBBIE_SCRIPT_FORMATS.md`
**Title**: Debbie's Script Format Support
- Lines: 173
- Last Modified: 2025-06-02
- References:
  - Python: test_project_settings_persistence.py

#### `docs/FUTURE_IDEAS.md`
**Title**: Future Ideas and Improvements
- Lines: 353
- Last Modified: 2025-06-02
- 📝 Contains TODOs
- References:
  - Docs: file_browser_implementation_priority.md, file_browser_implementation_plan.md

#### `docs/QUICK_START.md`
**Title**: AIWhisperer Quick Start Guide
- Lines: 104
- Last Modified: 2025-05-29
- References:
  - Docs: requirements.md, architecture.md, README.md

#### `docs/STRUCTURED_OUTPUT_INTEGRATION.md`
**Title**: Structured Output Integration for Patricia Agent
- Lines: 106
- Last Modified: 2025-05-31
- References:
  - Python: test_structured_output.py, test_patricia_structured_plan.py

#### `docs/TECH_DEBT.md`
**Title**: Technical Debt
- Lines: 135
- Last Modified: 2025-05-31
- ⚠️ **Possibly Outdated**
- References:
  - Python: tests/unit/test_ai_loop.py, test_prompt_loading_integration.py, test_generate_overview_plan_command.py

#### `docs/agent-e-decomposition-example.md`
**Title**: Agent E Task Decomposition Example
- Lines: 246
- Last Modified: 2025-06-01
- References:
  - Python: base_tool.py, file.py, base_handler.py
  - Docs: prompt.md

#### `docs/agent-e-external-agents-research.md`
**Title**: Agent E External Agents Research Summary
- Lines: 181
- Last Modified: 2025-06-01
- References:

#### `docs/agent-p-issues-and-improvements.md`
**Title**: Agent P Issues and Improvements
- Lines: 107
- Last Modified: 2025-06-01

#### `docs/ai_service_interaction.md`
**Title**: AI Service Interaction Module
- Lines: 351
- Last Modified: 2025-05-28
- References:
  - Python: src/ai_whisperer/ai_service_interaction.py, exceptions.py, ai_service_interaction.py
  - Docs: configuration.md

#### `docs/architecture/project_management.md`
**Title**: Project Management System Architecture
- Lines: 201
- Last Modified: 2025-05-29
- References:
  - Docs: README.md

#### `docs/architecture/prompt_system.md`
**Title**: Prompt System Architecture
- Lines: 207
- Last Modified: 2025-05-29
- References:
  - Docs: prompt.md, default.md

#### `docs/batch-mode/PHASE1_TASKS.md`
**Title**: Phase 1: Workspace Detection - TDD Task List
- Lines: 265
- Last Modified: 2025-05-30
- References:
  - Python: ai_whisperer/workspace_validation.py, path_management.py, pytest tests/unit/test_workspace*.py tests/integration/test_workspace*.py
  - Docs: WORKSPACE_DETECTION.md

#### `docs/batch-mode/PHASE2_TASKS.md`
**Title**: Phase 2: Debbie the Batcher Agent - Detailed Task List
- Lines: 413
- Last Modified: 2025-05-30
- References:
  - Python: test_debbie_agent_performance.py, ai_whisperer/tools/script_parser_tool.py, test_debbie_prompt_loading.py
  - Docs: prompt.md, DEBBIE_AGENT_API.md, DEBBIE_USAGE_EXAMPLES.md

#### `docs/batch_debugging_with_debbie.md`
**Title**: Debugging the ListPlansTool Format Issue Using Batch Runner and Debbie
- Lines: 98
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: plan_handler.py

#### `docs/code_generation_handler_research.md`
**Title**: Code Generation Handler Research & Design
- Lines: 127
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: execution_engine.py, src/ai_whisperer/execution_engine.py, ai_interaction.py
  - Docs: project_dev/rfc/code_generator_task_type.md, code_generator_task_type.md

#### `docs/completed/REPOSITORY_CLEANUP_2025-05-29.md`
**Title**: Repository Cleanup Plan
- Lines: 181
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: tests/test_list_models_command.py, tests/unit/test_execution_engine_delegates.py, delegate_manager.py
  - Docs: refactored_ai_loop_design.md, user_message_analysis.md, COMMAND_SYSTEM_PLAN.md

#### `docs/config_examples.md`
**Title**: Configuration Examples for AI Whisperer
- Lines: 119
- Last Modified: 2025-05-28
- References:
  - Docs: subtask_generator_default.md, initial_plan_default.md

#### `docs/configuration.md`
**Title**: ---
- Lines: 263
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Docs: example_prompt.md, example_prompt_no_section_default.md, interactive_mode_api.md

#### `docs/debugging-session-2025-05-30/CHAT_BUG_ROOT_CAUSE.md`
**Title**: Chat Bug Root Cause Analysis
- Lines: 66
- Last Modified: 2025-05-30

#### `docs/debugging-session-2025-05-30/DEBBIE_BATCH_MODE_EXAMPLE.md`
**Title**: Debbie Batch Mode Usage Example
- Lines: 204
- Last Modified: 2025-05-30
- References:
  - Python: test_main.py, main.py, __init__.py
  - Docs: analysis_report.md, work_log_2025_05_30.md, README.md

#### `docs/debugging-session-2025-05-30/DEBBIE_INTRODUCTION_FIX.md`
**Title**: Debbie Introduction Fix
- Lines: 38
- Last Modified: 2025-05-30
- References:
  - Python: interactive_server/stateless_session_manager.py, stateless_session_manager.py

#### `docs/debugging-session-2025-05-30/WORKTREE_PATH_FIX.md`
**Title**: Worktree Path Resolution Fix
- Lines: 47
- Last Modified: 2025-05-30
- References:
  - Python: main.py, interactive_server/main.py
  - Docs: prompt.md, default.md

#### `docs/debugging-session-2025-05-30/WORKTREE_SETUP.md`
**Title**: Git Worktree Setup Guide for AIWhisperer
- Lines: 112
- Last Modified: 2025-05-30
- References:
  - Python: main.py
  - Docs: prompt.md, default.md

#### `docs/dependency-analysis-report.md`
**Title**: Dependency Analysis Report
- Lines: 80
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: tool_usage_logging.py, send_mail_tool.py, ai_whisperer/agents/mailbox_tools.py

#### `docs/directory_restriction_strategy.md`
**Title**: Directory Restriction Strategy for AI Whisperer Runner
- Lines: 152
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: path_management.py, read_file_tool.py, cli.py
  - Docs: path_manager_analysis.md, docs/path_manager_analysis.md

#### `docs/feature/agent-continuation-json-issue.md`
**Title**: Agent Continuation System - JSON Display Issue
- Lines: 100
- Last Modified: 2025-06-02
- References:
  - Docs: FUTURE_IDEAS.md, continuation_protocol.md

#### `docs/feature/agent-continuation-test-failures.md`
**Title**: Agent Continuation System - Remaining Test Failures
- Lines: 67
- Last Modified: 2025-06-02
- References:
  - Python: check_settings_persistence.py, tests/integration/test_conversation_persistence.py, test_isolated_server.py

#### `docs/feature/agent-continuation-test-results.md`
**Title**: Agent Continuation System - Test Results
- Lines: 78
- Last Modified: 2025-06-02
- References:

#### `docs/index.md`
**Title**: Welcome to AI Whisperer Documentation
- Lines: 35
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Docs: ai_service_interaction.md, user_message_system.md, logging_monitoring.md

#### `docs/research/agentic_ai_continuation_research/agentic_ai_continuation_report.md`
**Title**: Agentic AI Continuation: Multi-Tool Orchestration Without User Interaction
- Lines: 311
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**

#### `docs/research/agentic_ai_continuation_research/agentic_frameworks_analysis.md`
**Title**: Analysis of Continuation and Multi-Tool Orchestration in Agentic AI Frameworks
- Lines: 128
- Last Modified: 2025-06-02

#### `docs/research/agentic_ai_continuation_research/ai_continuation_final_report.md`
**Title**: AI Continuation: API vs System-Level Implementation
- Lines: 109
- Last Modified: 2025-06-02

#### `docs/research/agentic_ai_continuation_research/api_vs_system_comparison.md`
**Title**: API-Level vs System-Level Continuation in AI Systems
- Lines: 142
- Last Modified: 2025-06-02

#### `docs/research/agentic_ai_continuation_research/api_vs_system_continuation.md`
**Title**: API vs System-Level Continuation in AI Frameworks
- Lines: 108
- Last Modified: 2025-06-02

#### `docs/research/agentic_ai_continuation_research/continuation_trigger_analysis.md`
**Title**: Continuation Trigger Mechanisms in AI Systems
- Lines: 152
- Last Modified: 2025-06-02

#### `docs/research/agentic_ai_continuation_research/references.md`
**Title**: References for Agentic AI Continuation Research
- Lines: 27
- Last Modified: 2025-06-02

#### `docs/subtask_generator_feature.md`
**Title**: Subtask Generator Feature
- Lines: 138
- Last Modified: 2025-05-28
- References:
  - Python: test_feature_x.py, test_subtask_generator.py, feature_x.py
  - Docs: subtask_generator_default.md

#### `docs/tool_sets_and_tags.md`
**Title**: Tool Sets and Tags Documentation
- Lines: 246
- Last Modified: 2025-05-29
- References:

#### `docs/tool_testing_strategy.md`
**Title**: AI Tool Usage Testing Strategy for AIWhisperer
- Lines: 160
- Last Modified: 2025-05-28
- References:
  - Docs: tool_management_design.md, docs/tool_management_design.md, tool_interface_design.md

#### `frontend/.github/copilot-instructions.md`
- Lines: 3
- Last Modified: 2025-05-28

#### `frontend/tech_debt.md`
**Title**: Technical Debt Log
- Lines: 18
- Last Modified: 2025-05-28

#### `project_dev/Copilot thoughts.md`
- Lines: 233
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_plan_ingestion.py, ai_service_interaction.py, json_validator.py

#### `project_dev/context_management_analysis.md`
**Title**: Analysis of Current AIWhisperer Context Management Architecture
- Lines: 81
- Last Modified: 2025-05-29
- References:
  - Python: ai_whisperer/agents/context_manager.py, test_agent_context_manager.py, tests/unit/test_context_manager.py
  - Docs: ../../REFACTOR_PLAN.md, REFACTOR_PLAN.md

#### `project_dev/notes/Final Recommendation_TextualFrameworkforAIConversation.md`
**Title**: Final Recommendation: Textual Framework for AI Conversation Tool
- Lines: 437
- Last Modified: 2025-05-28
- References:
  - Python: app.py

#### `project_dev/performance_metrics.md`
**Title**: Performance Metrics for AILoop Interactive Integration
- Lines: 75
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: summarize_performance_metrics.py
  - Docs: performance_metrics_report.md

#### `project_dev/performance_metrics_report.md`
**Title**: Performance Metrics Summary
- Lines: 27
- Last Modified: 2025-05-28

#### `refactor_analysis/code_map.md`
**Title**: AIWhisperer Code Map
- Lines: 1789
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: external_adapters.py, planner_tools.py, ai_whisperer/commands/registry.py

#### `refactor_analysis/test_coverage.md`
**Title**: Test Coverage Analysis
- Lines: 504
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_openrouter_api_detailed.py, test_batch_command_performance.py, test_mocked_ailoop.py

#### `refactor_analysis/test_map.md`
**Title**: AIWhisperer Test Map
- Lines: 1455
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: tests/unit/test_context_manager.py, test_project_pathmanager_integration.py, test_integration_end_to_end.py

#### `test_results/manual_continuation_test.md`
**Title**: Manual Model Continuation Test Report
- Lines: 65
- Last Modified: 2025-06-02

#### `test_results/model_compatibility_report.md`
**Title**: Model Continuation Compatibility Report
- Lines: 84
- Last Modified: 2025-06-02

#### `tests/simple_project/c_hello_world_requirements.md`
**Title**: C "Hello, World!" Application Requirements
- Lines: 43
- Last Modified: 2025-05-28

#### `tests/simple_project/c_zx81_emulator_requirements.md`
**Title**: Basic Sinclair ZX81 Emulator Requirements (C)
- Lines: 47
- Last Modified: 2025-05-28

#### `tests/simple_project/javascript_3d_globe_requirements.md`
**Title**: Interactive 3D Globe Feature Requirements
- Lines: 31
- Last Modified: 2025-05-28

#### `tests/simple_project/javascript_hello_world_requirements.md`
**Title**: JavaScript "Hello, World!" Application Requirements
- Lines: 22
- Last Modified: 2025-05-28

#### `tests/simple_project/javascript_retro_website_requirements.md`
**Title**: Retro Style Static Website Requirements
- Lines: 35
- Last Modified: 2025-05-28

#### `tests/simple_project/python_ai_chat_requirements.md`
**Title**: AI Chat Simulation Requirements
- Lines: 43
- Last Modified: 2025-05-28

#### `tests/simple_project/python_echo_feature_requirements.md`
**Title**: Python Echo Feature Requirements
- Lines: 28
- Last Modified: 2025-05-28
- References:
  - Python: <program_name>.py

#### `tests/simple_project/python_hello_world_requirements.md`
**Title**: Functional Requirements: Python "Hello, World!"
- Lines: 26
- Last Modified: 2025-05-28

#### `tests/simple_project/python_text_adventure_requirements.md`
**Title**: Python Text Adventure Game Requirements
- Lines: 52
- Last Modified: 2025-05-28

#### `workspace_health_20250531_111146.md`
**Title**: Workspace Health Report
- Lines: 54
- Last Modified: 2025-05-31
- References:

### Plan

#### `IMPLEMENTATION_CHECKLIST_FILE_BROWSER.md`
**Title**: File Browser Implementation Checklist
- Lines: 167
- Last Modified: 2025-05-29
- References:
  - Python: file_service.py, workspace_handler.py, main.py

#### `UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md`
**Title**: AI Whisperer UI Improvements Implementation Plan
- Lines: 188
- Last Modified: 2025-06-02
- References:
  - Python: workspace_handler.py, list_plans_tool.py, terminal_handler.py

#### `docs/AGENT_P_RFC_IMPLEMENTATION_CHECKLIST.md`
**Title**: Agent P RFC Refinement - Implementation Checklist
- Lines: 209
- Last Modified: 2025-05-29
- References:
  - Python: commands/rfc.py, create_rfc_tool.py, update_rfc_tool.py
  - Docs: prompt.md, rfc_template.md

#### `docs/PATRICIA_PLAN_CONVERSION_GUIDE.md`
**Title**: Patricia's RFC-to-Plan Conversion Guide
- Lines: 253
- Last Modified: 2025-05-31
- References:
  - Docs: 31.md

#### `docs/agent_p_rfc_refinement_plan.md`
**Title**: Agent P RFC Refinement Feature - Implementation Plan
- Lines: 322
- Last Modified: 2025-05-29
- References:

#### `docs/batch-mode/IMPLEMENTATION_PLAN.md`
**Title**: Batch Mode Implementation Plan
- Lines: 283
- Last Modified: 2025-05-30
- References:
  - Python: workspace_detection.py, script_processor.py, server_manager.py
  - Docs: prompt.md

#### `docs/batch-mode/PHASE2_CHECKLIST.md`
**Title**: Phase 2: Debbie the Batcher Agent - Progress Checklist
- Lines: 266
- Last Modified: 2025-05-30
- References:
  - Python: tests/integration/test_agent_registry_debbie.py, test_agent_registry_debbie.py, tests/unit/test_script_parser_security.py
  - Docs: prompt.md, DEBBIE_AGENT_API.md, DEBBIE_USAGE_EXAMPLES.md

#### `docs/completed/AgentInspectorFeaturePlan.md`
- Lines: 122
- Last Modified: 2025-05-29
- References:

#### `docs/completed/AgentSystemImplementationPlan.md`
- Lines: 455
- Last Modified: 2025-05-29
- References:
  - Python: test_agent_communication.py, test_agent_context_manager.py, test_planner_handler.py
  - Docs: agent_planner.md, agent_tester.md

#### `docs/completed/FRONTEND_BACKEND_INTEGRATION_PLAN.md`
**Title**: Frontend-Backend Integration Plan
- Lines: 268
- Last Modified: 2025-05-29

#### `docs/completed/FRONTEND_TDD_CHECKLIST.md`
**Title**: Frontend TDD Implementation Checklist
- Lines: 283
- Last Modified: 2025-05-29

#### `docs/context_tracking_implementation_plan.md`
**Title**: Context Tracking Implementation Plan
- Lines: 277
- Last Modified: 2025-05-29
- References:
  - Python: ai_whisperer/context/context_manager.py, workspace_handler.py, storage.py

#### `docs/debugging-session-2025-05-30/DEBBIE_DEBUGGING_HELPER_CHECKLIST.md`
**Title**: Debbie the Debugging Helper - Implementation Checklist
- Lines: 354
- Last Modified: 2025-05-30
- References:
  - Python: ai_whisperer/tools/python_executor_tool.py, ai_whisperer/batch/websocket_interceptor.py, ai_whisperer/tools/debug_scripts.py
  - Docs: prompt.md

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE3_INTERACTIVE_MONITORING_PLAN.md`
**Title**: Debbie Phase 3: Interactive Mode Monitoring - Implementation Plan
- Lines: 247
- Last Modified: 2025-05-30
- References:
  - Python: test.py, debbie_observer.py, ai_whisperer/interactive/debbie_observer.py

#### `docs/feature/agent-continuation-implementation-checklist.md`
**Title**: Agent Continuation System Implementation Checklist
- Lines: 223
- Last Modified: 2025-06-02
- References:
  - Python: continuation_strategy.py, ai_whisperer/agents/continuation_strategy.py
  - Docs: mailbox_protocol.md, tool_guidelines.md, continuation_protocol.md

#### `docs/feature/agent-continuation-implementation-plan.md`
**Title**: Agent Continuation System Implementation Plan
- Lines: 557
- Last Modified: 2025-06-02
- References:
  - Python: ai_whisperer/prompt_system.py, continuation_strategy.py, prompt_system.py
  - Docs: mailbox_protocol.md, tool_guidelines.md, continuation_protocol.md

#### `docs/file_browser_implementation_checklist.md`
**Title**: File Browser & AI Tools Implementation Checklist
- Lines: 245
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_tool_tags.py, list_directory_tool.py, ai_whisperer/tools/search_files_tool.py
  - Docs: tool_sets_and_tags.md

#### `docs/file_browser_implementation_plan.md`
**Title**: File Browser Implementation Plan
- Lines: 162
- Last Modified: 2025-05-29
- References:
  - Python: file_service.py, workspace_explorer_tool.py, ai_whisperer/tools/file_reference_tool.py

#### `docs/research/agentic_ai_continuation_research/todo.md`
**Title**: Research on Agentic AI Continuation
- Lines: 14
- Last Modified: 2025-06-02

#### `frontend/IMPLEMENTATION_CHECKLIST.md`
**Title**: React Frontend Implementation Checklist
- Lines: 320
- Last Modified: 2025-05-28
- References:
  - Python: project_dev/interactive_client.py, interactive_client.py
  - Docs: interactive_mode_api.md

#### `frontend/TDD_IMPLEMENTATION_PLAN.md`
**Title**: TDD Implementation Plan: React Frontend for AI Whisperer
- Lines: 967
- Last Modified: 2025-05-29

#### `project_dev/Ideas and TODO.md`
**Title**: TODOs and Idea scratchpad
- Lines: 61
- Last Modified: 2025-05-28
- 📝 Contains TODOs
- References:
  - Python: config.py

#### `project_dev/done/agent_REFACTOR_CHECKLIST.md`
**Title**: AIWhisperer Refactor Checklist
- Lines: 280
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_direct_streaming.py, test_stateless_session_manager.py, test_no_delegates.py
  - Docs: stateless_architecture.md

#### `project_dev/done/agent_REFACTOR_PLAN.md`
**Title**: AIWhisperer Refactor Plan
- Lines: 166
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**

#### `project_dev/done/store_cost_tokens_to_ai_calls/orchestration_plan.md`
**Title**: Orchestration Plan: Implement "Store Cost and Tokens to AI Calls" Feature
- Lines: 51
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:

#### `project_dev/manual_testing_checklist.md`
**Title**: Manual Testing Checklist: AILoop Interactive Server
- Lines: 55
- Last Modified: 2025-05-28

#### `project_dev/plan_update_todo_test_cases.md`
**Title**: Plan to Update Ideas and TODO.md with Missing Test Cases
- Lines: 29
- Last Modified: 2025-05-28
- 📝 Contains TODOs
- References:
  - Python: src/ai_whisperer/config.py, config.py
  - Docs: TODO.md

### Prompt

#### `prompts/agents/agent_eamonn.prompt.md`
**Title**: Agent E - Eamonn The Executioner
- Lines: 146
- Last Modified: 2025-06-02

#### `prompts/agents/agent_patricia.prompt.md`
**Title**: Agent Patricia (P) - The Planner
- Lines: 222
- Last Modified: 2025-05-31
- References:
  - Docs: 30.md

#### `prompts/agents/agent_planner.prompt.md`
- Lines: 16
- Last Modified: 2025-05-29

#### `prompts/agents/agent_tester.prompt.md`
- Lines: 15
- Last Modified: 2025-05-29

#### `prompts/agents/alice_assistant.prompt.md`
- Lines: 29
- Last Modified: 2025-05-29

#### `prompts/agents/code_generation.prompt.md`
**Title**: Code Generation Agent
- Lines: 49
- Last Modified: 2025-05-28
- References:
  - Python: file.py

#### `prompts/agents/debbie_debugger.prompt.md`
**Title**: Debbie the Debugger & Batch Processor
- Lines: 262
- Last Modified: 2025-05-30

#### `prompts/agents/default.md`
**Title**: FALLBACK DEFAULT PROMPT - THIS SHOULD NOT BE USED IN NORMAL OPERATION
- Lines: 53
- Last Modified: 2025-05-30
- References:
  - Docs: prompt.md

#### `prompts/agents/plan_refinement.prompt.md`
**Title**: Plan Refinement Prompt
- Lines: 109
- Last Modified: 2025-05-31

#### `prompts/core/initial_plan.prompt.md`
**Title**: Initial Plan Default Prompt
- Lines: 170
- Last Modified: 2025-05-28
- References:
  - Python: test_dogfood.py
  - Docs: analysis_summary.md, README.md

#### `prompts/core/refine_requirements.prompt.md`
**Title**: Prompt: Refine Rough Requirements Document
- Lines: 60
- Last Modified: 2025-05-28

#### `prompts/core/subtask_generator.prompt.md`
**Title**: Subtask Generator Default Prompt
- Lines: 32
- Last Modified: 2025-05-28

#### `prompts/shared/README.md`
**Title**: Shared Prompt Components
- Lines: 87
- Last Modified: 2025-06-02
- References:
  - Docs: mailbox_protocol.md, tool_guidelines.md, feature_name.md

#### `prompts/shared/continuation_protocol.md`
**Title**: Continuation Protocol
- Lines: 66
- Last Modified: 2025-06-02
- References:
  - Docs: 06.md

#### `prompts/shared/core.md`
**Title**: Core System Instructions
- Lines: 34
- Last Modified: 2025-06-02

#### `prompts/shared/mailbox_protocol.md`
**Title**: Mailbox Communication Protocol
- Lines: 117
- Last Modified: 2025-06-02
- References:
  - Python: auth.py, test_auth.py, file1.py
  - Docs: file2.md

#### `prompts/shared/output_format.md`
**Title**: Output Format Requirements
- Lines: 199
- Last Modified: 2025-06-02

#### `prompts/shared/tool_guidelines.md`
**Title**: Tool Usage Guidelines
- Lines: 133
- Last Modified: 2025-06-02
- References:
  - Python: file.py, generated_file.py

### Readme

#### `.pytest_cache/README.md`
**Title**: pytest cache directory #
- Lines: 8
- Last Modified: 2025-05-28

#### `README.md`
**Title**: AI Whisperer
- Lines: 291
- Last Modified: 2025-06-01
- ⚠️ **Possibly Outdated**
- References:
  - Python: src/ai_whisperer/path_management.py, src/ai_whisperer/prompt_system.py, prompt_system.py
  - Docs: requirements.md, prompt.md, docs/config_examples.md

#### `docs/README.md`
**Title**: AIWhisperer Documentation
- Lines: 49
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Docs: config_examples.md, architecture/prompt_system.md, tool_interface_design.md

#### `frontend/README.md`
**Title**: Code Quality
- Lines: 61
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**

#### `test_debbie_batch_README.md`
**Title**: Debbie Persona Test Script
- Lines: 61
- Last Modified: 2025-05-30
- References:
  - Python: test_debbie_batch.py

### Rfc

#### `.WHISPER/rfc/in_progress/agent-e-executioner-2025-05-31.md`
**Title**: RFC: Agent E - Eamonn The Executioner: Task Execution Agent
- Lines: 315
- Last Modified: 2025-06-01

#### `.WHISPER/rfc/in_progress/python-ast-json-2025-06-01.md`
**Title**: RFC: Python AST to JSON Converter for Agent Processing
- Lines: 75
- Last Modified: 2025-06-01

#### `.WHISPER/rfc/in_progress/structured-output-support-2025-06-01.md`
**Title**: RFC: Add Structured Output Support
- Lines: 48
- Last Modified: 2025-06-01

#### `RFC_TO_PLAN_STATUS.md`
**Title**: RFC-to-Plan Implementation Status
- Lines: 95
- Last Modified: 2025-05-31
- References:
  - Docs: CLAUDE.md

#### `docs/rfc_to_plan_implementation_checklist.md`
**Title**: RFC to Structured Plan Implementation Checklist ✅ COMPLETE!
- Lines: 320
- Last Modified: 2025-05-31
- References:
  - Python: test_rfc_plan_bidirectional.py, stateless_session_manager.py
  - Docs: prompt.md, CLAUDE.md

#### `project_dev/rfc/add_1st_runner_test.md`
**Title**: Add a 1st simple full real runner test
- Lines: 28
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**

#### `project_dev/rfc/add_detail_cli_option.md`
**Title**: Add a detail CLI option
- Lines: 11
- Last Modified: 2025-05-28

#### `project_dev/rfc/add_interactive_scaffolding.md`
**Title**: Add Interactive Scaffolding
- Lines: 39
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Docs: Recommendation_TextualFrameworkforAIConversation.md

#### `project_dev/rfc/add_tools_use.md`
**Title**: Add AI usable tools and a few basic tools for testing
- Lines: 23
- Last Modified: 2025-05-28

#### `project_dev/rfc/aiwhisperer_dogfood.md`
**Title**: Context
- Lines: 12
- Last Modified: 2025-05-28

#### `project_dev/rfc/code_generator_task_type.md`
**Title**: Code Generator Task Type
- Lines: 18
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Docs: initial_plan_default.md

#### `project_dev/rfc/ensure_runner_use_correct_dir.md`
**Title**: Ensure Runner Uses Correct Directory
- Lines: 21
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**

#### `project_dev/rfc/refactor_ai_loop.md`
**Title**: Refactor several code_generation.py function to be reusable
- Lines: 18
- Last Modified: 2025-05-28
- References:
  - Python: test_run_plan_script.py, code_generation.py

#### `project_dev/rfc/refactor_prompt_loading.md`
**Title**: Refactor Prompt Loading
- Lines: 37
- Last Modified: 2025-05-28

#### `project_dev/rfc/seperate_ai_loop.md`
**Title**: Separate AI Loop
- Lines: 11
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: ai_loop.py

#### `project_dev/rfc/sort_out_paths.md`
**Title**: Sort out paths
- Lines: 41
- Last Modified: 2025-05-28

#### `project_dev/rfc/store_cost_tokens_to_ai_calls.md`
- Lines: 3
- Last Modified: 2025-05-28

#### `project_dev/rfc/test_refine.md`
**Title**: Requirements Refinement
- Lines: 28
- Last Modified: 2025-05-28

#### `prompts/agents/rfc_to_plan.prompt.md`
**Title**: RFC to Plan Conversion Prompt
- Lines: 103
- Last Modified: 2025-05-31

#### `templates/rfc_template.md`
**Title**: RFC: {title}
- Lines: 46
- Last Modified: 2025-05-29

### Status

#### `BATCH_MODE_PHASE2_DAY1_SUMMARY.md`
**Title**: Batch Mode Phase 2 - Day 1 Morning Summary
- Lines: 106
- Last Modified: 2025-05-30
- References:
  - Python: test_debbie_prompt_system.py, test_debbie_agent_config.py, test_debbie_agent_integration.py
  - Docs: prompt.md

#### `IMPLEMENTATION_SUMMARY.md`
**Title**: UI Improvements Implementation Summary
- Lines: 110
- Last Modified: 2025-06-02
- References:
  - Docs: UI_IMPROVEMENT_IMPLEMENTATION_PLAN.md, TECHNICAL_SPECIFICATIONS.md

#### `PROJECT_STATUS_UPDATE.md`
**Title**: AIWhisperer Project Status Update
- Lines: 111
- Last Modified: 2025-05-30
- References:
  - Python: /ai_whisperer/batch/intervention.py, /ai_whisperer/batch/monitoring.py, intervention.py

#### `PROJECT_STATUS_UPDATE_PHASE2_COMPLETE.md`
**Title**: Project Status Update: Debbie Phase 2 Complete
- Lines: 101
- Last Modified: 2025-05-30

#### `REFACTOR_CODE_MAP_SUMMARY.md`
**Title**: AIWhisperer Code Map Summary
- Lines: 132
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: ai_loop_legacy.py, registry.py, script_processor.py

#### `REFACTOR_TEST_MAP_SUMMARY.md`
**Title**: AIWhisperer Test Map Summary
- Lines: 141
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: monitoring_control_tool.py, base_handler.py, debbie_demo.py

#### `TEST_COMPLETION_SUMMARY.md`
**Title**: Test Completion Summary - Python AST JSON Tool
- Lines: 94
- Last Modified: 2025-06-01

#### `TEST_FINAL_STATUS.md`
**Title**: Test Suite Final Status
- Lines: 48
- Last Modified: 2025-06-01
- References:
  - Python: test_batch_performance.py, test_json_to_ast_conversion.py, test_python_ast_parsing_advanced.py

#### `TEST_FIXES_SUMMARY.md`
**Title**: Test Fixes Summary
- Lines: 81
- Last Modified: 2025-05-31
- References:
  - Python: ai_whisperer/tools/update_plan_from_rfc_tool.py, ai_whisperer/tools/python_executor_tool.py, test_rfc_plan_bidirectional.py

#### `TEST_FIX_COMPLETE_SUMMARY.md`
**Title**: Test Fix Complete Summary
- Lines: 61
- Last Modified: 2025-05-31
- References:
  - Python: test_stateless_ailoop.py, test_ai_service_interaction.py, create_plan_from_rfc_tool.py

#### `TEST_STATUS_SUMMARY.md`
**Title**: Test Status Summary for PR
- Lines: 78
- Last Modified: 2025-06-01
- References:
  - Python: test_agent_e_task_decomposition.py, test_agent_e_integration.py, test_python_ast_json_tool.py

#### `docs/agent-e-implementation-progress.md`
**Title**: Agent E Implementation Progress (GREEN Phase)
- Lines: 55
- Last Modified: 2025-06-01
- References:
  - Python: test_agent_e_task_decomposition.py, agent_e_exceptions.py, decomposed_task.py

#### `docs/agent-e-implementation-summary.md`
**Title**: Agent E (Eamonn The Executioner) Implementation Summary
- Lines: 110
- Last Modified: 2025-06-01
- References:
  - Python: external_adapters.py, agent_communication.py, decomposed_task.py
  - Docs: file.md

#### `docs/agent_p_rfc_design_summary.md`
**Title**: Agent P RFC Refinement - Design Summary
- Lines: 75
- Last Modified: 2025-05-29

#### `docs/batch-mode/IMPLEMENTATION_STATUS.md`
**Title**: Batch Mode Implementation Status Summary
- Lines: 146
- Last Modified: 2025-05-30
- References:
  - Docs: PHASE2_CHECKLIST.md, PHASE2_TASKS.md

#### `docs/clear-command-implementation-summary.md`
**Title**: /clear Command Implementation Summary
- Lines: 91
- Last Modified: 2025-06-02
- References:
  - Python: ai_whisperer/context/context_manager.py, context_manager.py, tests/unit/test_clear_command.py
  - Docs: summary.md

#### `docs/completed/AGENT_P_RFC_PHASE4_SUMMARY.md`
**Title**: Agent P RFC Refinement - Phase 4 Summary
- Lines: 176
- Last Modified: 2025-05-29
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_rfc_workflow.py, ai_whisperer/tools/move_rfc_tool.py, ai_whisperer/plan_runner.py
  - Docs: prompt.md

#### `docs/debugging-session-2025-05-30/BUFFERING_BUG_FIX_SUMMARY.md`
**Title**: Message Buffering Bug Fix Summary
- Lines: 44
- Last Modified: 2025-05-30
- References:
  - Python: main.py, interactive_server/main.py

#### `docs/debugging-session-2025-05-30/DEBBIE_FIXES_SUMMARY.md`
**Title**: Debbie "I am Gemini" Fix Summary
- Lines: 58
- Last Modified: 2025-05-30
- References:
  - Python: test_debbie_batch.py, main.py, stateless_session_manager.py

#### `docs/debugging-session-2025-05-30/DEBBIE_IMPLEMENTATION_COMPLETE.md`
**Title**: Debbie the Debugger - Implementation Complete 🎉
- Lines: 182
- Last Modified: 2025-05-30
- References:
  - Python: debbie_demo.py, test_debbie_scenarios.py, /ai_whisperer/batch/intervention.py
  - Docs: prompt.md

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE1_SUMMARY.md`
**Title**: Debbie the Debugger - Phase 1 Implementation Summary
- Lines: 229
- Last Modified: 2025-05-30
- References:
  - Python: workspace_validator_tool.py, logging_custom.py, message_injector_tool.py
  - Docs: prompt.md

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE2_DAY2_SUMMARY.md`
**Title**: Debbie Phase 2 Day 2 Summary: ScriptParserTool Implementation
- Lines: 110
- Last Modified: 2025-05-30
- References:
  - Python: test_batch_command_tool.py

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE2_DAY3_SUMMARY.md`
**Title**: Debbie Phase 2 Day 3 Summary: BatchCommandTool Implementation
- Lines: 146
- Last Modified: 2025-05-30

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE2_DAY4_SUMMARY.md`
**Title**: Debbie Phase 2 Day 4 Summary: Integration Testing and Finalization
- Lines: 149
- Last Modified: 2025-05-30
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_batch_script_execution.py, /tests/integration/batch_mode/test_batch_script_execution.py

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE2_SUMMARY.md`
**Title**: Debbie the Debugger - Phase 2 Implementation Summary
- Lines: 196
- Last Modified: 2025-05-30
- References:
  - Python: debbie_integration.py, websocket_interceptor.py, monitoring.py

#### `docs/debugging-session-2025-05-30/DEBBIE_PHASE3_DAY1_SUMMARY.md`
**Title**: Debbie Phase 3 Day 1 Summary: Core Observer Infrastructure
- Lines: 129
- Last Modified: 2025-05-30
- References:
  - Python: debbie_observer.py, stateless_session_manager.py, interactive_server/debbie_observer.py

#### `docs/debugging-session-2025-05-30/LEGACY_CLEANUP_SUMMARY.md`
**Title**: Legacy Code Cleanup Summary
- Lines: 38
- Last Modified: 2025-05-30
- ⚠️ **Possibly Outdated**
- References:
  - Python: ai_whisperer/subtask_generator.py, ai_whisperer/execution_engine.py, ai_whisperer/plan_runner.py

#### `docs/debugging-session-2025-05-30/OPENROUTER_SERVICE_SIMPLIFICATION_COMPLETE.md`
**Title**: OpenRouter Service Simplification Complete
- Lines: 64
- Last Modified: 2025-05-30
- References:
  - Python: openrouter_ai_service_simplified.py, openrouter_ai_service_old.py, openrouter_ai_service.py

#### `docs/debugging-session-2025-05-30/TOOL_CALLING_IMPLEMENTATION_SUMMARY.md`
**Title**: Tool Calling Implementation Summary
- Lines: 75
- Last Modified: 2025-05-30
- References:
  - Python: stateless_ai_loop.py, monitoring_control_tool.py, ai_whisperer/ai_loop/tool_call_accumulator.py

#### `docs/debugging-session-2025-05-30/WEBSOCKET_SESSION_FIX_SUMMARY.md`
**Title**: WebSocket Session Management Fix Summary
- Lines: 76
- Last Modified: 2025-05-30
- References:
  - Python: ai_whisperer/ai_loop/stateless_ai_loop.py, stateless_ai_loop.py, stateless_session_manager.py

#### `docs/feature/agent-continuation-fix-summary.md`
**Title**: Agent Continuation System - Fix Summary
- Lines: 73
- Last Modified: 2025-06-02
- References:
  - Python: test_agent_continuation_fix.py, /home/deano/projects/AIWhisperer/interactive_server/stateless_session_manager.py, /home/deano/projects/AIWhisperer/tests/integration/test_agent_continuation_fix.py

#### `docs/feature/agent-continuation-implementation-progress.md`
**Title**: Agent Continuation System Implementation Progress
- Lines: 126
- Last Modified: 2025-06-02
- References:
  - Docs: mailbox_protocol.md, tool_guidelines.md, continuation_protocol.md

#### `docs/feature/agent-continuation-phase3-summary.md`
**Title**: Agent Continuation System - Phase 3 Complete
- Lines: 143
- Last Modified: 2025-06-02
- References:

#### `docs/feature/agent-continuation-test-summary.md`
**Title**: Agent Continuation System - Test Summary
- Lines: 46
- Last Modified: 2025-06-02
- References:
  - Python: test_continuation_simple.py

#### `docs/feature/continuation-phase4-summary.md`
**Title**: Phase 4 Completion Summary: Model-Specific Optimizations
- Lines: 85
- Last Modified: 2025-06-02
- ⚠️ **Possibly Outdated**
- References:
  - Python: tests/integration/test_model_continuation_compatibility.py, ai_whisperer/model_override.py, model_capabilities.py
  - Docs: guide.md

#### `docs/file_browser_integration_summary.md`
**Title**: File Browser Integration Summary
- Lines: 111
- Last Modified: 2025-05-29
- References:
  - Python: file_service.py, workspace_handler.py, main.py

#### `frontend/PHASE5_SUMMARY.md`
**Title**: Phase 5 Implementation Summary
- Lines: 87
- Last Modified: 2025-05-29
- References:

#### `test_results/model_continuation_compatibility_summary.md`
**Title**: Model Continuation Compatibility Test Summary
- Lines: 75
- Last Modified: 2025-06-02

### User Guide

#### `docs/BATCH_MODE_USAGE_FOR_AI.md`
**Title**: BATCH MODE USAGE FOR AI ASSISTANTS
- Lines: 169
- Last Modified: 2025-06-02
- References:

#### `docs/batch-mode/USER_GUIDE.md`
**Title**: AI Whisperer Batch Mode User Guide
- Lines: 114
- Last Modified: 2025-05-29
- References:
  - Python: test_batch_mode_e2e.py, tests/integration/test_batch_mode_e2e.py, project_dev/interactive_client.py
  - Docs: IMPLEMENTATION_PLAN.md

#### `docs/debugging-session-2025-05-30/DEBBIE_USAGE_GUIDE_FOR_AI_ASSISTANTS.md`
**Title**: Debbie the Debugger - Usage Guide for AI Coding Assistants
- Lines: 243
- Last Modified: 2025-05-30
- References:
  - Python: monitoring.py

#### `docs/feature/agent-continuation-configuration-guide.md`
**Title**: Agent Continuation Configuration Guide
- Lines: 267
- Last Modified: 2025-06-02
- References:

#### `docs/feature/agent-continuation-testing-guide.md`
**Title**: Agent Continuation System - Testing Guide
- Lines: 162
- Last Modified: 2025-06-02
- References:

#### `docs/feature/continuation-performance-optimization-guide.md`
**Title**: Continuation System Performance Optimization Guide
- Lines: 190
- Last Modified: 2025-06-02
- References:
  - Python: run_model_compatibility_tests.py

#### `docs/research/agentic_ai_continuation_research/aiwhisperer_implementation_guide.md`
**Title**: AIWhisperer Continuation Implementation Guide
- Lines: 215
- Last Modified: 2025-06-02

#### `frontend/PHASE1_IMPLEMENTATION_GUIDE.md`
**Title**: Phase 1: Quick Implementation Guide
- Lines: 127
- Last Modified: 2025-05-29

#### `frontend/PROJECT_REFACTOR_AND_INTERACTIVE_MODE_GUIDE.md`
**Title**: Project Refactor and Interactive Mode Guide
- Lines: 163
- Last Modified: 2025-05-28
- ⚠️ **Possibly Outdated**
- References:
  - Python: test_logging.py, test_ai_loop.py, test_cli.py

