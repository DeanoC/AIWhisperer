# Async Agent Examples

This directory contains real-world examples demonstrating how to use AIWhisperer's async agent architecture for complex multi-agent workflows.

## Overview

The async agent system allows multiple AI agents to work together asynchronously, communicating via a mailbox system, with support for:
- Independent agent execution
- Inter-agent communication via mailbox
- Sleep/wake patterns for resource efficiency
- State persistence across interruptions
- Parallel and sequential execution patterns

## Examples

### 1. Code Review Pipeline (`code_review_pipeline.py`)

A comprehensive code review workflow that coordinates multiple specialized agents:

- **Patricia (P)**: Analyzes code structure and architecture
- **Alice (A)**: Performs general code review
- **Tessa (T)**: Suggests tests and test improvements
- **Debbie (D)**: Debugs issues and analyzes errors

#### Usage

```python
from examples.async_agents.code_review_pipeline import CodeReviewWorkflow
from ai_whisperer.services.agents.async_session_manager_v2 import AsyncAgentSessionManager

# Initialize workflow
workflow = CodeReviewWorkflow(
    workspace_path="/path/to/code",
    output_path="/path/to/output"
)

# Configure workflow
config = {
    "agents": ["p", "a", "t", "d"],  # Which agents to use
    "files_to_review": ["main.py", "utils.py"],
    "review_type": "comprehensive",
    "parallel_execution": True,
    "use_sleep_wake": True  # Enable resource efficiency
}

# Create session manager
session_manager = AsyncAgentSessionManager(ai_config)
await session_manager.start()

# Run workflow
result = await workflow.run(config, session_manager)

# Check results
print(f"Status: {result['status']}")
print(f"Issues found: {result['total_issues_found']}")
print(f"Review summary: {result['review_summary']}")
```

## Workflow Patterns

### Sequential Pipeline
Agents process tasks one after another:
```
Agent A → Agent B → Agent C → Result
```

### Parallel Collaboration
Multiple agents work simultaneously:
```
        ┌→ Agent B →┐
Agent A →           → Agent D (aggregates)
        └→ Agent C →┘
```

### Event-Driven
Agents sleep until events occur:
```
Monitor Agent (sleeping) --event--> Wake & Process
                        └--------> Wake other agents
```

## Base Classes

### BaseWorkflow
All workflows should inherit from `BaseWorkflow` which provides:
- Agent session management
- Error handling
- Performance tracking
- State checkpoint support

### WorkflowResult
Base class for workflow results with:
- Status tracking
- Error collection
- Runtime calculation
- Serialization support

## Best Practices

1. **Use Type Hints**: All workflows should use proper type hints
2. **Handle Errors Gracefully**: Use try/except blocks and report errors in results
3. **Track Performance**: Monitor agent efficiency and resource usage
4. **Enable Checkpoints**: Support workflow resumption after interruptions
5. **Document Workflows**: Include clear documentation and examples

## Testing

All workflows should have comprehensive tests using TDD approach:

```python
# Test example
async def test_code_review_workflow():
    workflow = CodeReviewWorkflow(workspace, output)
    result = await workflow.run(config, session_manager)
    
    assert result["status"] == "completed"
    assert result["errors"] == []
    assert result["total_issues_found"] > 0
```

## Future Examples

Coming soon:
- Bug Investigation Workflow
- Documentation Generation Pipeline
- Continuous Monitoring System
- Multi-Stage Deployment Workflow

## Contributing

When adding new workflow examples:
1. Inherit from `BaseWorkflow`
2. Use `WorkflowResult` or create a subclass
3. Add comprehensive tests
4. Document usage patterns
5. Include error handling
6. Track performance metrics