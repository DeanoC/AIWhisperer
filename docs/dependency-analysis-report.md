# Dependency Analysis Report

## Summary

This report analyzes import dependencies in the AIWhisperer codebase to identify orphaned modules, import patterns, and potential circular dependencies.

## Key Findings

### 1. Unregistered Tools (5 tools not in tool_registration.py)
- `check_mail_tool.py` - Used by mailbox_tools.py
- `create_plan_from_rfc_tool.py` - Only used in tests
- `python_ast_json_tool.py` - Extensively tested but not registered
- `reply_mail_tool.py` - Used by mailbox_tools.py
- `send_mail_tool.py` - Used by mailbox_tools.py

**Note**: The mailbox tools (check_mail, reply_mail, send_mail) are registered through `register_mailbox_tools()` in `ai_whisperer/agents/mailbox_tools.py`, not directly in tool_registration.py.

### 2. Orphaned/Unused Modules
- **execution_engine**: 0 imports found - appears to be completely orphaned
- **delegates**: Only 1 import reference found, mostly in comments/documentation
- **runners**: 20 import references found, but mostly in tests and scripts

### 3. Import Dependencies Between Major Components

#### Tools → Agents (Potential Circular Dependency)
```
ai_whisperer/tools/reply_mail_tool.py → ai_whisperer.agents.mailbox
ai_whisperer/tools/check_mail_tool.py → ai_whisperer.agents.mailbox
ai_whisperer/tools/send_mail_tool.py → ai_whisperer.agents.mailbox
ai_whisperer/tools/tool_usage_logging.py → ai_whisperer.agents.registry
```

#### Agents → Tools (Expected Direction)
```
ai_whisperer/agents/debbie_tools.py → various debugging tools
ai_whisperer/agents/mailbox_tools.py → mailbox-related tools
```

### 4. Tool Usage Analysis

#### Heavily Used/Tested Tools
- `python_ast_json_tool` - 14 files reference it (mostly tests)
- File operation tools (read, write, execute_command, etc.)
- RFC and Plan management tools

#### Potentially Underutilized Tools
- `create_plan_from_rfc_tool` - Only found in 3 files (including tests)
- External agent tools (format_for_external_agent, validate_external_agent, etc.)

### 5. Architecture Observations

1. **Stateless Architecture**: The codebase has moved from delegates to a stateless architecture, but references to "delegates" still exist in several files.

2. **Tool Registration**: Most tools are registered centrally in `tool_registration.py`, but some (mailbox tools) have their own registration mechanism.

3. **Circular Dependency Risk**: The mailbox tools importing from agents while agents import tools creates a potential circular dependency. This should be refactored to have a separate mailbox module that both can import from.

## Recommendations

### Immediate Actions
1. **Remove orphaned modules**: Delete or archive execution_engine if truly unused
2. **Register missing tools**: Add python_ast_json_tool and create_plan_from_rfc_tool to tool_registration.py
3. **Fix circular dependencies**: Extract mailbox functionality to a separate module

### Code Cleanup
1. Remove remaining references to "delegates" in the codebase
2. Consolidate tool registration - either all in tool_registration.py or document exceptions clearly
3. Review and potentially remove underutilized external agent tools if no longer needed

### Documentation Updates
1. Document why certain tools (mailbox tools) have special registration
2. Update architecture documentation to reflect the current stateless design
3. Create a tool inventory with usage statistics

## Tool Count Summary
- Total tool files: 48
- Registered in tool_registration.py: 43
- Registered elsewhere (mailbox): 3
- Unregistered but tested: 2 (python_ast_json_tool, create_plan_from_rfc_tool)
- Total accounted for: 48 ✓