# Bug Investigation Workflow

A comprehensive async agent workflow for collaborative bug investigation and resolution. This workflow demonstrates how multiple specialized agents can work together to investigate reported bugs, identify root causes, and propose fixes.

## Features

- **Automatic severity classification** based on bug report keywords
- **Urgency-based agent wake patterns** for critical bugs
- **Multi-agent collaboration** with specialized roles
- **Root cause analysis** and systemic issue detection
- **Fix generation** with security-aware recommendations
- **Test case recommendations** for validation
- **Batch investigation** support for multiple bugs
- **Error recovery** with graceful degradation

## Agent Roles

- **Debbie (d)**: Lead Investigator - Analyzes error logs and identifies patterns
- **Alice (a)**: Code Analyst - Reviews code for issues and suggests improvements
- **Patricia (p)**: Solution Architect - Designs comprehensive fix strategies
- **Eamonn (e)**: Fix Implementation - Generates and implements code fixes
- **Tessa (t)**: Test Specialist - Designs test cases and identifies regression risks

## Usage

### Basic Investigation

```python
from examples.async_agents.bug_investigation_workflow import BugInvestigationWorkflow
from ai_whisperer.services.agents.async_session_manager_v2 import AsyncAgentSessionManager

# Initialize workflow
workflow = BugInvestigationWorkflow(
    workspace_path=Path("/path/to/workspace"),
    output_path=Path("/path/to/output")
)

# Create session manager
session_manager = AsyncAgentSessionManager(config)

# Single bug investigation
config = {
    "bug_report": {
        "id": "BUG-001",
        "title": "User service crashes when user not found",
        "description": "Getting KeyError when trying to retrieve non-existent user",
        "severity": "high",
        "error_log": "KeyError in user_service.get_user: 'user123'",
        "affected_file": "user_service.py"
    },
    "agents": ["d", "a"],  # Debbie and Alice
    "investigation_depth": "comprehensive"
}

result = await workflow.run(config, session_manager)
```

### Advanced Configuration

```python
config = {
    "bug_report": bug_data,
    "agents": ["d", "a", "p", "e", "t"],  # All agents
    "investigation_depth": "comprehensive",
    "collaborative_mode": True,  # Enable agent collaboration
    "max_investigation_rounds": 3,  # Multiple investigation rounds
    "generate_fix": True,  # Generate fix recommendations
    "check_related_issues": True,  # Look for systemic issues
    "handle_incomplete_reports": True,  # Handle insufficient bug reports
    "use_sleep_wake": True,  # Enable sleep/wake patterns
    "wake_on_severity": ["critical", "high"]  # Wake agents for these severities
}
```

### Batch Investigation

```python
config = {
    "bug_reports": [
        {"id": "BUG-001", "title": "Error 1", "severity": "high"},
        {"id": "BUG-002", "title": "Error 2", "severity": "medium"},
        {"id": "BUG-003", "title": "Error 3", "severity": "critical"}
    ],
    "agents": ["d", "a"],
    "parallel_investigation": True  # Investigate bugs in parallel
}
```

## Bug Report Structure

Bug reports can include:
- `id`: Unique identifier
- `title`: Brief description (required)
- `description`: Detailed description
- `severity`: critical/high/medium/low (auto-classified if not provided)
- `urgency`: immediate/normal
- `error_log`: Error messages or stack traces
- `affected_file`: File(s) affected by the bug
- `symptoms`: List of observed symptoms
- `reported_by`: Reporter identification

## Severity Classification

The workflow automatically classifies bug severity based on keywords:

- **Critical**: crash, security, vulnerability, production down
- **High**: data loss, data corruption, performance, memory leak
- **Medium**: Default for unclassified bugs
- **Low**: typo, ui, alignment, cosmetic, minor

## Result Structure

The workflow returns a comprehensive result including:

```python
{
    "status": "completed",  # or "failed", "completed_with_limitations"
    "bug_id": "BUG-001",
    "root_cause": "KeyError in critical path",
    "suggested_fix": "Add error handling and input validation",
    "proposed_fix": "Implement validation layer with error boundaries",
    "severity_confirmed": "high",
    "agent_findings": {
        "d": {"role": "initial_investigation", "findings": "..."},
        "a": {"role": "code_analysis", "findings": "..."}
    },
    "systemic_issues": ["Lack of input validation", "..."],
    "architectural_recommendations": ["Implement centralized validation", "..."],
    "test_recommendations": ["Test with missing user", "..."],
    "confidence_level": "high",  # or "medium", "low"
    "fix_ready": true,
    "execution_time": "5.23s"
}
```

## Example Scenarios

### Security Bug Investigation

```python
config = {
    "bug_report": {
        "title": "Credit card numbers exposed in logs",
        "description": "Sensitive payment data visible in debug logs",
        "severity": "critical"
    },
    "agents": ["d", "a", "p"],
    "generate_fix": True
}
# Result will include security-specific fix: "Mask sensitive data before logging"
```

### Incomplete Bug Report Handling

```python
config = {
    "bug_report": {
        "title": "Something is broken",
        "description": "It doesn't work"
    },
    "handle_incomplete_reports": True
}
# Result will include report_improvements and confidence_level: "low"
```

### Collaborative Investigation

```python
config = {
    "bug_report": bug_data,
    "agents": ["d", "a", "p"],
    "collaborative_mode": True,
    "max_investigation_rounds": 2
}
# Agents will exchange findings between rounds for deeper analysis
```

## Integration with Async Agents

This workflow integrates seamlessly with the async agents architecture:

1. **Independent AI loops**: Each agent runs in its own async loop
2. **Mailbox communication**: Agents communicate via the mailbox system
3. **Event-driven coordination**: Agents can wake on critical bug events
4. **Parallel execution**: Multiple agents can investigate simultaneously

## Error Handling

The workflow includes robust error handling:
- Agent failures are logged but don't stop the investigation
- Incomplete bug reports can be handled gracefully
- Results include confidence levels based on available information
- Failed agents are excluded from findings

## Best Practices

1. **Start simple**: Begin with basic investigation (Debbie + Alice)
2. **Add agents as needed**: Include Patricia for architectural issues
3. **Enable collaboration**: For complex bugs requiring deep analysis
4. **Monitor confidence**: Low confidence indicates insufficient information
5. **Review systemic issues**: Look for patterns across multiple bugs
6. **Validate fixes**: Always include Tessa for test recommendations