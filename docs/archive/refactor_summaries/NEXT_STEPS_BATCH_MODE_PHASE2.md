# Next Steps: Batch Mode Phase 2 - Debbie the Batcher

## Current Status
✅ **Debbie the Debugger is COMPLETE** - Successfully solving the agent stall issue
📋 **Batch Mode Phase 2 is READY** - Comprehensive TDD plan prepared

## Why Phase 2 Next?
1. **Builds on Success**: Leverages Debbie's debugging capabilities
2. **Fully Planned**: Detailed 4-day TDD implementation plan exists
3. **Clear Value**: Enables scripted automation of interactive sessions
4. **Natural Evolution**: Debbie becomes both debugger AND batcher

## Phase 2 Overview: Debbie the Batcher

### Core Concept
Debbie the Batcher acts as an automated user in interactive mode:
- Reads batch scripts (JSON/YAML/text)
- Interprets commands and sends them to the AI loop
- Imitates a human user typing commands
- Uses existing interactive flow (not a separate execution path)

### Key Components to Build

#### 1. **Agent Configuration** (Day 1 Morning)
```yaml
# Add to agents.yaml
d:
  name: "Debbie"
  role: "debugging_assistant, batch_processor"  # Dual role!
  prompt_file: "debbie_batcher.prompt.md"
  tool_sets: ["debugging_tools", "batch_tools", "filesystem"]
```

#### 2. **Script Parser Tool** (Day 2)
```python
class ScriptParserTool(BaseTool):
    """Parse and validate batch scripts in multiple formats"""
    - JSON script support
    - YAML script support  
    - Plain text commands
    - Security validation
    - Syntax checking
```

#### 3. **Batch Command Tool** (Day 3)
```python
class BatchCommandTool(BaseTool):
    """Convert script commands to AIWhisperer actions"""
    - Command interpretation
    - Parameter extraction
    - Action mapping
    - Execution planning
```

### TDD Implementation Plan

For each component, follow strict TDD:
1. **Write failing tests first** (RED)
2. **Implement minimal code to pass** (GREEN)
3. **Refactor for quality** (REFACTOR)
4. **Verify all tests still pass**

### Example Test Structure
```python
# tests/unit/test_debbie_batcher_agent.py
def test_debbie_has_batch_processor_role():
    """Debbie should have dual roles: debugger and batcher"""
    agent = AgentRegistry.get_agent('d')
    assert 'batch_processor' in agent.roles
    assert 'debugging_assistant' in agent.roles

def test_debbie_can_parse_json_script():
    """Debbie should parse JSON batch scripts"""
    script = {"commands": ["list files", "create RFC"]}
    result = debbie.parse_script(script)
    assert result.is_valid
    assert len(result.commands) == 2
```

## Implementation Schedule

### Day 1: Foundation
- **Morning**: Agent configuration and registration
- **Afternoon**: Specialized batch prompts
- **Tests**: 15+ unit tests for configuration

### Day 2: Script Parser
- **Full day**: ScriptParserTool development
- **Focus**: Multi-format support with security
- **Tests**: 25+ tests covering all formats

### Day 3: Command Tool
- **Full day**: BatchCommandTool development
- **Focus**: Command interpretation and mapping
- **Tests**: 30+ tests for command handling

### Day 4: Integration
- **Morning**: End-to-end integration testing
- **Afternoon**: Documentation and API design
- **Tests**: 20+ integration tests

## Success Metrics

### Coverage Targets
- Unit Tests: 95% code coverage
- Integration Tests: 90% workflow coverage
- Error Scenarios: 100% coverage
- Performance: Baseline established

### Deliverables
- ✅ Debbie with dual-role capabilities
- ✅ Script parsing for 3 formats
- ✅ Command interpretation system
- ✅ 90+ comprehensive tests
- ✅ Full API documentation

## Getting Started

### 1. Update Debbie's Configuration
```bash
# Edit agents.yaml to add batch_processor role
vim ai_whisperer/agents/config/agents.yaml
```

### 2. Create Test File Structure
```bash
# Create test directories
mkdir -p tests/unit/batch_mode
mkdir -p tests/integration/batch_mode
mkdir -p tests/performance/batch_mode

# Create initial test files
touch tests/unit/test_debbie_batcher_agent.py
touch tests/unit/test_script_parser_tool.py
touch tests/unit/test_batch_command_tool.py
```

### 3. Write First Failing Test
```python
# tests/unit/test_debbie_batcher_agent.py
import pytest
from ai_whisperer.agents.registry import AgentRegistry

def test_debbie_exists_with_batch_role():
    """Test that Debbie has batch processing capabilities"""
    agent = AgentRegistry.get_agent('d')
    assert agent is not None
    assert 'batch_processor' in agent.role
    # This will fail until we update the configuration
```

### 4. Run Test (Expect Failure)
```bash
pytest tests/unit/test_debbie_batcher_agent.py -v
# Should see RED (failing test)
```

### 5. Implement to Pass Test
Update agents.yaml, then run test again to see GREEN

## Benefits of Phase 2

1. **Automation**: Scripts can run unattended
2. **Consistency**: Repeatable processes
3. **Testing**: Easier to test AI workflows
4. **Integration**: Works with existing tools
5. **Debugging**: Debbie can debug her own batch runs!

## Example Batch Script (Future)
```json
{
  "name": "Create Feature RFC",
  "steps": [
    {"action": "list_rfcs", "params": {"status": "active"}},
    {"action": "create_rfc", "params": {
      "title": "New Authentication System",
      "description": "Implement OAuth2 with JWT tokens"
    }},
    {"action": "validate_rfc"},
    {"action": "notify", "params": {"message": "RFC created successfully"}}
  ]
}
```

## Risk Mitigation

1. **TDD Discipline**: Code reviews ensure tests come first
2. **Integration Issues**: Test with existing agents early
3. **Performance**: Monitor memory and response times
4. **Security**: Validate all script inputs

## Next Actions

1. **Review Phase 2 plan** in detail
2. **Set up test structure** as shown above
3. **Write first failing test** for agent configuration
4. **Begin Day 1 Morning** tasks

## Conclusion

Phase 2 builds naturally on Debbie's debugging success, transforming her into a dual-purpose agent that can both debug issues AND execute batch scripts. The comprehensive TDD plan ensures high quality and the 4-day timeline is achievable.

Ready to start? The first test is waiting to be written! 🚀