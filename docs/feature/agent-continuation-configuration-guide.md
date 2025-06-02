# Agent Continuation Configuration Guide

This guide explains how to configure the continuation behavior for agents in AIWhisperer.

## Overview

The continuation system allows agents to automatically execute multiple steps without requiring manual prompting between each step. This is especially useful for complex tasks that require several tool calls in sequence.

## Configuration Location

Agent continuation settings are defined in `ai_whisperer/agents/config/agents.yaml` under each agent's `continuation_config` section.

## Configuration Options

### Basic Structure

```yaml
agents:
  agent_id:
    name: "Agent Name"
    # ... other agent config ...
    continuation_config:
      require_explicit_signal: boolean
      max_iterations: integer
      timeout: integer
      continuation_patterns: list[string]
      termination_patterns: list[string]
```

### Configuration Fields

#### `require_explicit_signal` (boolean)
- **Default**: `true`
- **Description**: Whether the agent must include an explicit `continuation` field in responses
- **Values**:
  - `true`: Agent must include `continuation: {status: "CONTINUE"}` to continue
  - `false`: System uses pattern matching to detect continuation intent
- **Recommendation**: Use `false` for better reliability with current LLMs

#### `max_iterations` (integer)
- **Default**: `5`
- **Description**: Maximum number of continuation iterations allowed
- **Purpose**: Prevents infinite loops and runaway operations
- **Range**: 1-20 (recommended: 3-10)

#### `timeout` (integer)
- **Default**: `300` (5 minutes)
- **Description**: Maximum time in seconds for all continuation operations
- **Purpose**: Safety limit to prevent stuck operations
- **Range**: 60-3600 (1 minute to 1 hour)

#### `continuation_patterns` (list[string])
- **Default**: Empty list
- **Description**: Regular expression patterns that indicate continuation is needed
- **Used when**: `require_explicit_signal: false`
- **Examples**:
  ```yaml
  continuation_patterns:
    - "now I'll"
    - "next,? I'll"
    - "let me.*proceed"
    - "continuing with"
    - "moving on to"
  ```

#### `termination_patterns` (list[string])
- **Default**: Empty list
- **Description**: Regular expression patterns that indicate task completion
- **Used when**: `require_explicit_signal: false`
- **Examples**:
  ```yaml
  termination_patterns:
    - "task.*complete"
    - "all done"
    - "finished.*successfully"
    - "completed.*all.*steps"
  ```

## Agent-Specific Configurations

### Patricia the Planner (Agent P)
```yaml
continuation_config:
  require_explicit_signal: false
  max_iterations: 5
  timeout: 300
  continuation_patterns:
    - "now I'll"
    - "let me.*create"
    - "proceeding to"
  termination_patterns:
    - "RFC.*created"
    - "plan.*complete"
```
- Moderate iteration limit for RFC/plan operations
- Pattern-based for reliability

### Agent E (Eamonn the Executioner)
```yaml
continuation_config:
  require_explicit_signal: false
  max_iterations: 10
  timeout: 600
  continuation_patterns:
    - "now I'll"
    - "next, I"
    - "let me.*next"
    - "proceeding to"
    - "moving on to"
    - "I'll continue with"
  termination_patterns:
    - "completed successfully"
    - "task is complete"
    - "finished.*all.*steps"
    - "ready for execution"
    - "all done"
```
- Higher iteration limit for complex plan decomposition
- Longer timeout for processing large plans
- More continuation patterns for flexibility

### Debbie the Debugger
```yaml
continuation_config:
  require_explicit_signal: true
  max_iterations: 10
  timeout: 600
```
- Uses explicit signals for precise control
- High iteration limit for thorough debugging
- Extended timeout for complex investigations

### Alice & Tessa
```yaml
continuation_config:
  require_explicit_signal: true
  max_iterations: 5
  timeout: 300
```
- Standard configuration
- Explicit signals for predictable behavior

## Continuation Protocol

When `require_explicit_signal: true`, agents must include a continuation field:

```json
{
  "response": "I've completed step 1. Now I'll proceed to step 2.",
  "tool_calls": [...],
  "continuation": {
    "status": "CONTINUE",
    "reason": "Need to execute step 2",
    "progress": {
      "current_step": 1,
      "total_steps": 3,
      "steps_completed": ["Listed files"],
      "steps_remaining": ["Analyze content", "Generate report"]
    }
  }
}
```

## Progress Notifications

During continuation, the system sends WebSocket notifications:

```json
{
  "jsonrpc": "2.0",
  "method": "continuation.progress",
  "params": {
    "sessionId": "...",
    "agent_id": "e",
    "iteration": 2,
    "max_iterations": 10,
    "progress": {
      "current_step": 2,
      "total_steps": 4,
      "completion_percentage": 50,
      "steps_completed": ["Listed plans", "Read plan"],
      "steps_remaining": ["Decompose plan", "Analyze dependencies"]
    },
    "current_tools": ["decompose_plan"],
    "timestamp": "2024-01-15T10:30:45.123Z"
  }
}
```

## Best Practices

### 1. Choose the Right Signal Mode
- Use `require_explicit_signal: false` for most agents
- Current LLMs don't reliably output structured continuation fields
- Pattern matching is more reliable in practice

### 2. Set Appropriate Limits
- Balance between task completion and safety
- Consider the agent's typical workflow
- Plan decomposition might need 10+ steps
- Simple queries might need only 2-3 steps

### 3. Design Clear Patterns
- Make continuation patterns specific but flexible
- Avoid patterns that might match normal conversation
- Test patterns with real agent responses

### 4. Prompt Engineering
Include continuation guidance in agent prompts:
```markdown
When performing multi-step operations:
1. Always indicate your next step: "Now I'll...", "Next, I'll..."
2. Complete all requested steps in sequence
3. Say "Task complete" or "All done" when finished
```

### 5. Monitor Progress
- Watch for agents hitting max iterations frequently
- Adjust limits based on real usage patterns
- Use progress notifications for user feedback

## Troubleshooting

### Agent Stops Too Early
- Check if response matches termination patterns
- Verify continuation patterns are being triggered
- Increase `max_iterations` if hitting limit

### Agent Continues Indefinitely
- Add more specific termination patterns
- Reduce `max_iterations`
- Check for overly broad continuation patterns

### No Continuation Happening
- Verify `continuation_config` is present
- Check if patterns match agent's language
- Enable debug logging to see decisions

### Pattern Matching Issues
Test patterns with Python:
```python
import re
pattern = r"now I'll"
text = "I've found the files. Now I'll analyze them."
if re.search(pattern, text, re.IGNORECASE):
    print("Pattern matches!")
```

## Example: Multi-Step Task

User: "Execute the python-ast-json plan"

Agent E with proper configuration:
1. "I'll list the available plans first." → CONTINUE
2. "Found the plan. Now I'll read its details." → CONTINUE  
3. "Got the plan data. Next, I'll decompose it into tasks." → CONTINUE
4. "Plan decomposed. Let me analyze dependencies." → CONTINUE
5. "All tasks prepared and dependencies resolved. Task complete." → TERMINATE

All steps execute automatically without user intervention.

## Future Enhancements

- Dynamic pattern learning from successful continuations
- Per-session continuation preferences
- Model-specific optimizations
- Continuation templates for common workflows