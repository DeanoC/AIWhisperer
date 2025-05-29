# Phase 2: Billy the Batcher Agent - Detailed Task List

**Date**: May 29, 2025  
**Status**: Ready for Implementation  
**Duration**: 4 days  
**Objective**: Create new agent specialized in batch script interpretation using strict TDD methodology

## Overview


Phase 2 creates "Billy the Batcher," a specialized agent that interprets batch scripts and acts as an automated user in the interactive mode. Billy's core function is to run an ai-loop similar to the existing chat mode, but instead of a human user, Billy reads the script and sends messages/commands to the normal project flow as if they were typed by a user. This means:

- Billy replaces the human user in the interactive session, driving the ai-loop by following the provided script.
- The batch mode is not a separate execution path, but a scripted automation of the existing interactive flow.
- Billy will read, interpret, and "chat" to the system, imitating an interactive user, ensuring all project logic and agent interactions remain unchanged except for the source of input.

This phase follows strict Test-Driven Development (TDD) principles where **tests are written first** before any implementation.

## TDD Methodology Emphasis

### Core TDD Principles for Phase 2
1. **Red-Green-Refactor Cycle**: Write failing test → Make it pass → Improve code
2. **Test First**: No production code without a failing test
3. **Single Responsibility**: Each test focuses on one specific behavior
4. **Incremental Development**: Build functionality step by step
5. **Continuous Integration**: Run all tests after each change

### Phase 2 TDD Structure
```
For each task:
1. Write comprehensive test cases (RED)
2. Implement minimal code to pass tests (GREEN)
3. Refactor for quality and maintainability (REFACTOR)
4. Verify all existing tests still pass
5. Move to next task
```

## Detailed Task Breakdown

### Task 2.1: Billy Agent Configuration Setup (Day 1, Morning)
**Objective**: Create agent configuration and registration infrastructure

#### TDD Approach:
1. **Write Tests First**:
   - Test agent exists in agents.yaml
   - Test agent has correct properties (name, role, description, etc.)
   - Test agent configuration validation
   - Test agent loading from configuration

2. **Implementation**:
   - Add Billy to `config/agents.yaml`
   - Create agent validation functions
   - Implement configuration loader tests

3. **Test Files to Create**:
   ```
   tests/unit/test_billy_agent_config.py
   tests/integration/test_agent_registry_billy.py
   ```

#### Expected Test Cases:
```python
def test_billy_agent_exists_in_config()
def test_billy_agent_has_required_properties()
def test_billy_agent_role_is_batch_processor()
def test_billy_agent_tools_are_configured()
def test_billy_agent_prompt_file_specified()
def test_billy_agent_integration_with_registry()
```

#### Deliverables:
- ✅ Billy agent configuration in agents.yaml
- ✅ Agent configuration validation tests
- ✅ All tests passing

---

### Task 2.2: Billy Agent Prompt System (Day 1, Afternoon)
**Objective**: Create specialized prompt for batch script interpretation

#### TDD Approach:
1. **Write Tests First**:
   - Test prompt file exists and loads correctly
   - Test prompt contains batch-specific instructions
   - Test prompt formatting and variable substitution
   - Test prompt integration with agent system

2. **Implementation**:
   - Create `prompts/agents/billy_batcher.prompt.md`
   - Implement prompt validation
   - Create prompt loading tests

3. **Test Files to Create**:
   ```
   tests/unit/test_billy_prompt_system.py
   tests/integration/test_billy_prompt_loading.py
   ```

#### Expected Test Cases:
```python
def test_billy_prompt_file_exists()
def test_billy_prompt_contains_batch_instructions()
def test_billy_prompt_variable_substitution()
def test_billy_prompt_integration_with_agent()
def test_billy_prompt_error_handling()
```

#### Deliverables:
- ✅ Billy batcher prompt file
- ✅ Prompt system integration tests
- ✅ All tests passing

---

### Task 2.3: Script Parser Tool Development (Day 2, Full Day)
**Objective**: Create tool for parsing and validating batch scripts

#### TDD Approach:
1. **Write Tests First**:
   - Test script file reading and validation
   - Test various script formats (JSON, YAML, plain text)
   - Test script syntax validation
   - Test error handling for malformed scripts
   - Test script security validation

2. **Implementation**:
   - Create `ai_whisperer/tools/script_parser_tool.py`
   - Implement ScriptParserTool class
   - Add tool registration and integration

3. **Test Files to Create**:
   ```
   tests/unit/test_script_parser_tool.py
   tests/unit/test_script_parser_validation.py
   tests/unit/test_script_parser_security.py
   tests/integration/test_script_parser_tool_integration.py
   ```

#### Expected Test Cases:
```python
# Basic functionality
def test_script_parser_tool_creation()
def test_script_parser_reads_file()
def test_script_parser_validates_syntax()

# Format support
def test_script_parser_handles_json_format()
def test_script_parser_handles_yaml_format()
def test_script_parser_handles_plain_text()

# Error handling
def test_script_parser_handles_missing_file()
def test_script_parser_handles_malformed_json()
def test_script_parser_handles_invalid_yaml()
def test_script_parser_handles_permission_errors()

# Security
def test_script_parser_prevents_path_traversal()
def test_script_parser_validates_file_extensions()
def test_script_parser_checks_file_size_limits()

# Integration
def test_script_parser_tool_registry_integration()
def test_script_parser_billy_agent_integration()
```

#### Deliverables:
- ✅ ScriptParserTool with comprehensive validation
- ✅ Support for multiple script formats
- ✅ Security validation and error handling
- ✅ Full test coverage (aim for 95%+)
- ✅ All tests passing

---

### Task 2.4: Batch Command Tool Development (Day 3, Full Day)
**Objective**: Create tool for converting script commands to AIWhisperer actions

#### TDD Approach:
1. **Write Tests First**:
   - Test command interpretation and validation
   - Test command to action mapping
   - Test command parameter validation
   - Test command execution planning
   - Test error handling for invalid commands

2. **Implementation**:
   - Create `ai_whisperer/tools/batch_command_tool.py`
   - Implement BatchCommandTool class
   - Add command validation and mapping logic

3. **Test Files to Create**:
   ```
   tests/unit/test_batch_command_tool.py
   tests/unit/test_batch_command_mapping.py
   tests/unit/test_batch_command_validation.py
   tests/integration/test_batch_command_tool_integration.py
   ```

#### Expected Test Cases:
```python
# Basic functionality
def test_batch_command_tool_creation()
def test_batch_command_interpretation()
def test_batch_command_validation()

# Command mapping
def test_command_maps_to_correct_action()
def test_command_parameter_extraction()
def test_command_parameter_validation()
def test_unsupported_command_handling()

# Execution planning
def test_command_execution_order()
def test_command_dependency_resolution()
def test_command_parallelization_planning()

# Error handling
def test_invalid_command_syntax()
def test_missing_required_parameters()
def test_conflicting_commands()
def test_security_violation_detection()

# Integration
def test_batch_command_tool_registry_integration()
def test_batch_command_billy_agent_integration()
def test_batch_command_script_parser_integration()
```

#### Deliverables:
- ✅ BatchCommandTool with command interpretation
- ✅ Command to action mapping system
- ✅ Parameter validation and error handling
- ✅ Execution planning capabilities
- ✅ Full test coverage (aim for 95%+)
- ✅ All tests passing

---


### Task 2.5: Billy Agent Integration Testing (Day 4, Morning)
**Objective**: Comprehensive integration testing of Billy agent with all components, focusing on Billy's ai-loop imitating an interactive user

#### TDD Approach:
1. **Write Tests First**:
   - Test complete agent workflow
   - Test agent interaction with tools
   - Test agent response formatting
   - Test agent error handling
   - Test agent performance under load

2. **Implementation**:
   - Integration test suites
   - Performance benchmarks
   - Error scenario testing

3. **Test Files to Create**:
   ```
   tests/integration/test_billy_agent_complete_workflow.py
   tests/integration/test_billy_agent_tool_interactions.py
   tests/integration/test_billy_agent_error_scenarios.py
   tests/performance/test_billy_agent_performance.py
   ```


#### Expected Test Cases:
```python
# Complete workflow
def test_billy_ai_loop_processes_simple_script()
def test_billy_ai_loop_processes_complex_script()
def test_billy_ai_loop_handles_multi_step_commands()
def test_billy_ai_loop_imitates_interactive_user()

# Tool interactions
def test_billy_uses_script_parser_tool()
def test_billy_uses_batch_command_tool()
def test_billy_chains_tool_usage_correctly()

# Error scenarios
def test_billy_handles_tool_failures()
def test_billy_handles_invalid_scripts()
def test_billy_provides_helpful_error_messages()

# Performance
def test_billy_processes_large_scripts()
def test_billy_memory_usage_acceptable()
def test_billy_response_time_acceptable()
```

#### Deliverables:
- ✅ Complete integration test suite
- ✅ Performance benchmarks established
- ✅ Error handling validation
- ✅ All tests passing

---

### Task 2.6: Documentation and API Design (Day 4, Afternoon)
**Objective**: Document Billy agent API for Phase 3 integration

#### TDD Approach:
1. **Write Tests First**:
   - Test API documentation completeness
   - Test example code in documentation
   - Test API contract validation

2. **Implementation**:
   - API documentation
   - Usage examples
   - Integration guides

3. **Documentation Files to Create**:
   ```
   docs/batch-mode/BILLY_AGENT_API.md
   docs/batch-mode/BILLY_USAGE_EXAMPLES.md
   docs/batch-mode/PHASE3_INTEGRATION_GUIDE.md
   ```

#### Expected Test Cases:
```python
def test_api_documentation_examples_work()
def test_documented_interfaces_exist()
def test_example_scripts_are_valid()
```

#### Deliverables:
- ✅ Billy agent API documentation
- ✅ Usage examples and tutorials
- ✅ Phase 3 integration specifications
- ✅ Documentation tests passing

## Phase 2 Test Coverage Requirements

### Minimum Coverage Targets:
- **Unit Tests**: 95% code coverage
- **Integration Tests**: 90% workflow coverage
- **Error Scenarios**: 100% error path coverage
- **Performance Tests**: Baseline metrics established

### Test Organization:
```
tests/
├── unit/
│   ├── test_billy_agent_config.py
│   ├── test_billy_prompt_system.py
│   ├── test_script_parser_tool.py
│   ├── test_script_parser_validation.py
│   ├── test_script_parser_security.py
│   ├── test_batch_command_tool.py
│   ├── test_batch_command_mapping.py
│   └── test_batch_command_validation.py
├── integration/
│   ├── test_agent_registry_billy.py
│   ├── test_billy_prompt_loading.py
│   ├── test_script_parser_tool_integration.py
│   ├── test_batch_command_tool_integration.py
│   ├── test_billy_agent_complete_workflow.py
│   ├── test_billy_agent_tool_interactions.py
│   └── test_billy_agent_error_scenarios.py
└── performance/
    └── test_billy_agent_performance.py
```

## Phase 2 Success Criteria

### Functional Requirements:
- ✅ Billy agent loads and registers correctly
- ✅ Script parser tool handles multiple formats
- ✅ Batch command tool converts scripts to actions
- ✅ Complete workflow processes scripts end-to-end
- ✅ Error handling provides clear feedback
- ✅ Performance meets baseline requirements

### Quality Requirements:
- ✅ 95% unit test coverage achieved
- ✅ 90% integration test coverage achieved
- ✅ 100% error path coverage achieved
- ✅ All tests pass consistently
- ✅ Code quality metrics met (linting, type hints)
- ✅ Documentation complete and tested

### Technical Requirements:
- ✅ Agent integrates with existing agent registry
- ✅ Tools integrate with existing tool system
- ✅ No breaking changes to existing functionality
- ✅ Memory usage within acceptable bounds
- ✅ Response times meet performance targets

## Phase 2 Risk Mitigation

### Technical Risks:
- **Agent Registry Conflicts**: Comprehensive integration testing
- **Tool Registration Issues**: Early tool system validation
- **Performance Bottlenecks**: Performance testing throughout development
- **Memory Leaks**: Memory profiling and stress testing

### Development Risks:
- **TDD Discipline**: Pair programming and code reviews
- **Test Quality**: Test review sessions and coverage monitoring
- **Integration Complexity**: Incremental integration approach
- **Documentation Lag**: Documentation tests and continuous updates

## Ready for Implementation

Phase 2 is now ready for implementation. The detailed task breakdown emphasizes:

1. **Strict TDD Methodology**: Tests written before implementation
2. **Comprehensive Coverage**: Unit, integration, and performance tests
3. **Incremental Development**: Small, testable increments
4. **Quality Focus**: High coverage targets and code quality metrics
5. **Integration Readiness**: Clear API design for Phase 3

**Next Steps**: Review this task list, confirm TDD approach, and begin with Task 2.1.
