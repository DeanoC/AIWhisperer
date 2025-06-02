# Repository Cleanup Plan

## Overview
This document outlines the cleanup tasks needed to remove obsolete files, documentation, and code from the AIWhisperer repository after the recent architectural changes.

## 1. Obsolete Documentation to Remove

### Delegate System Documentation (Now using Stateless Architecture)
- [x] `/docs/delegate_manager_analysis.md` - Removed
- [x] `/docs/delegate_manager_refactoring_plan.md` - Removed
- [x] `/docs/user_message_delegate_docs_plan.md` - Removed
- [x] `/project_dev/notes/Thread-Safe Delegates Design Document.md` - Removed
- [x] `/project_dev/notes/Thread-Safe Delegates in Python - Usage Guide.md` - Removed
- [x] `/project_dev/planning/delegate_integration_plan.md` - Removed
- [x] `/project_dev/rfc/add_delegate_manager.md` - Removed
- [x] `/project_dev/rfc/delegates_executionengine.md` - Removed
- [x] `/project_dev/rfc/add_user_message_delegate.md` - Removed

### Old Runner/Monitor Documentation (Replaced by Frontend)
- [x] `/project_dev/rfc/runner-monitor.md` - Removed
- [x] `/docs/runner_test_analysis.md` - Removed
- [x] `/COMMAND_SYSTEM_PLAN.md` - Removed
- [x] `/project_dev/rfc/test_1st_runner_test.md` - Removed
- [x] `/project_dev/done/add_1st_runner_test/` - Removed

### Completed Feature Plans
- [x] `/AgentInspectorFeaturePlan.md` - Moved to docs/completed/
- [x] `/AgentSystemImplementationPlan.md` - Moved to docs/completed/
- [x] `/FRONTEND_BACKEND_INTEGRATION_PLAN.md` - Moved to docs/completed/
- [x] `/FRONTEND_TDD_CHECKLIST.md` - Moved to docs/completed/
- [x] `/DEVELOPMENT_PLAN.md` - Archived (obsolete)

## 2. Code Cleanup

### CLI Commands (Obsolete with Interactive Mode)
- Per user direction: CLI mode will be changing significantly, existing code can be ignored/removed

### Remove Old Delegate Imports
- [x] Created TECH_DEBT.md to track CLI refactoring needs
- [x] Removed `ai_whisperer/delegate_manager.py`
- [x] Removed delegate-related test files:
  - `tests/interactive_server/test_delegate_bridge.py`
  - `tests/test_delegate_manager_integration.py`
  - `tests/test_user_message_delegate.py`  
  - `tests/unit/test_ai_loop_delegates.py`
  - `tests/unit/test_execution_engine_delegates.py`

## 3. Test Cleanup
- [x] `/tests/1st_runner_test/` - Removed
- [x] `__pycache__` directories - Cleaned up
- [x] Old test output files - Output directory empty

## 4. Project Organization

### Create New Structure
```
docs/
├── architecture/          # Current architecture docs ✓
├── completed/            # Completed feature plans ✓
├── development/          # Development guides ✓
├── api/                  # API documentation ✓
├── user/                 # User documentation ✓
├── archive/              # Archived obsolete docs ✓
└── metrics/              # Performance metrics ✓
```

### Files to Reorganize
- [x] Moved architecture docs to `docs/architecture/`
- [x] Moved completed plans to `docs/completed/`
- [x] Created archive for obsolete docs
- [x] Moved metrics CSVs to `docs/metrics/`
- [x] Removed old screenshots and output files
- [x] Removed old PowerShell planning scripts

## 5. Update Documentation

### Files to Update
- [x] `README.md` - Updated to reflect stateless architecture and interactive mode
- [x] `CLAUDE.md` - Updated development practices and removed delegate references
- [x] `docs/architecture/architecture.md` - Updated with stateless architecture
- [x] Created new `docs/QUICK_START.md` for new developers

## 6. Configuration Cleanup
- [x] Reviewed `config.yaml` - No delegate settings found
- [x] Configuration is clean

## 7. Dependencies
- [x] Updated `requirements.txt` comments
- [x] Commented out prompt_toolkit (deprecated)

## 8. Additional Cleanup Completed
- [x] Removed `Screenshot 2025-05-29 085400.png` (bug demonstration)
- [x] Removed `output.txt` (empty file)
- [x] Moved performance metrics to `docs/metrics/`
- [x] Created `docs/TECH_DEBT.md` to track future refactoring needs

## 9. Terminal UI and Monitor Cleanup (2025-05-29)

### Removed Monitor Components:
- [x] `/monitor/` directory completely removed
  - `basic_output_display_message.py`
  - `interactive_list_models_ui.py`
  - `interactive_list_models_ui.tcss`
  - `interactive_ui_base.py`
  - `multiline_input.py`
  - `user_message_delegate.py`

### Removed Related Files:
- [x] `docs/textual_setup_analysis.md` - Textual framework analysis
- [x] `tests/unit/test_ansi_console_message_handler.py`
- [x] `tests/test_list_models_command.py`
- [x] `tests/integration/test_cli_detail_option.py`

### Code Updates:
- [x] Created `ai_whisperer/user_message_level.py` to replace monitor dependency
- [x] Updated imports in:
  - `ai_whisperer/cli.py`
  - `ai_whisperer/cli_commands.py`
  - `ai_whisperer/initial_plan_generator.py`
  - `ai_whisperer/tools/write_file_tool.py`
- [x] Simplified `ai_whisperer/main.py` without monitor/delegate dependencies
- [x] Updated `docs/TECH_DEBT.md` to reflect CLI deprecation

### Additional Fixes:
- [x] Fixed `ModuleNotFoundError` for delegate_manager in ai_loopy.py
- [x] Updated `ai_whisperer/ai_loop/__init__.py` to export only stateless components
- [x] Simplified `ai_whisperer/__init__.py` to avoid circular imports
- [x] Removed `ai_whisperer/interactive_ai.py` (old delegate-based interactive system)
- [x] Created `ai_whisperer/user_message_level.py` as standalone enum
- [x] Server now starts successfully without monitor/delegate dependencies

## 10. Documentation Cleanup (2025-05-29)

### Archived Obsolete Documentation:

#### Delegate System Docs → `archive/delegate_system/`
- [x] ai_loop_documentation.md
- [x] user_message_analysis.md 
- [x] user_message_system.md
- [x] refactored_ai_loop_design.md

#### Terminal UI Docs → `archive/terminal_ui/`
- [x] terminal_command_mode_design.md
- [x] list_models_interaction_analysis.md
- [x] detail_option_implementation_plan.md

#### Old Architecture Docs → `archive/old_architecture/`
- [x] execution_engine.md
- [x] internal_process.md
- [x] plan_document_execute_command_tool.md

#### Old Analysis Docs → `archive/analysis/`
- [x] docs_update_plan_cost_tracking.md
- [x] model_selection_plan.md
- [x] prompt_analysis.md
- [x] prompt_loading_analysis.md
- [x] path_manager_analysis.md
- [x] cost_token_analysis_summary.md

### Documentation Organization:
- [x] Created archive subdirectories for better organization
- [x] Created docs/README.md as documentation index
- [x] Kept current/relevant documentation in main docs directory
- [x] Total: 16 obsolete docs archived

### Documentation Updates:
- [x] Updated `new_prompt_system_design.md` to focus on agent integration
- [x] Renamed and moved to `docs/architecture/prompt_system.md`
- [x] Removed references to old non-agent systems
- [x] Added clear explanation of how prompts work with agents
- [x] Updated cross-references in other architecture docs

## Status: CLEANUP COMPLETE ✓

All cleanup tasks have been completed. The repository now reflects:
- Stateless architecture with direct streaming
- Interactive web interface as primary mode
- No terminal UI (Textual) dependencies
- No delegate system references
- Clean documentation structure
- Technical debt properly documented