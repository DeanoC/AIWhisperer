# Async Agents User Guide

## Overview

AIWhisperer now supports true asynchronous multi-agent workflows where multiple agents can work independently in parallel, coordinating through the mailbox system. This guide explains how to use both synchronous and asynchronous agent communication patterns.

## Communication Patterns

### 1. Synchronous Agent Communication

For immediate responses, use the synchronous pattern where one agent sends a message and waits for a response.

**Via Tools (within AIWhisperer):**
```python
# Alice can use send_mail_with_switch to get immediate response
send_mail_with_switch(
    to_agent="Debbie",
    subject="Analyze workspace",
    body="Please analyze the current project structure"
)
# System automatically switches to Debbie, processes, and returns response
```

**How it works:**
1. Agent A sends mail using `send_mail_with_switch`
2. System switches to Agent B
3. Agent B processes the request
4. System switches back to Agent A with the response
5. Agent A continues with the result

### 2. Asynchronous Agent Communication

For parallel workflows, use the async pattern where agents work independently.

**Via WebSocket API:**
```javascript
// Create multiple agents
await sendRequest("async.createAgent", {
    sessionId: sessionId,
    agentId: "analyzer",
    autoStart: true
});

await sendRequest("async.createAgent", {
    sessionId: sessionId,
    agentId: "writer",
    autoStart: true
});

// Agents work in parallel, coordinating via mailbox
```

**How it works:**
1. Each agent runs its own AI loop independently
2. Agents communicate asynchronously via mailbox
3. Agents can sleep/wake on timers or events
4. Multiple agents can work simultaneously

## WebSocket API Reference

### Creating Agents

**async.createAgent**
```json
{
    "method": "async.createAgent",
    "params": {
        "sessionId": "session-123",
        "agentId": "analyzer",
        "autoStart": true
    }
}
```

### Managing Agent Lifecycle

**async.startAgent** - Start an agent's background processor
```json
{
    "method": "async.startAgent",
    "params": {
        "sessionId": "session-123",
        "agentId": "analyzer"
    }
}
```

**async.stopAgent** - Stop an agent
```json
{
    "method": "async.stopAgent",
    "params": {
        "sessionId": "session-123",
        "agentId": "analyzer"
    }
}
```

### Sleep/Wake Control

**async.sleepAgent** - Put agent to sleep
```json
{
    "method": "async.sleepAgent",
    "params": {
        "sessionId": "session-123",
        "agentId": "monitor",
        "durationSeconds": 60,
        "wakeEvents": ["alert", "data_ready"]
    }
}
```

**async.wakeAgent** - Wake a sleeping agent
```json
{
    "method": "async.wakeAgent",
    "params": {
        "sessionId": "session-123",
        "agentId": "monitor",
        "reason": "User requested immediate check"
    }
}
```

### Task Management

**async.sendTask** - Send task directly to agent
```json
{
    "method": "async.sendTask",
    "params": {
        "sessionId": "session-123",
        "agentId": "analyzer",
        "prompt": "Analyze the latest customer feedback data"
    }
}
```

### Monitoring

**async.getAgentStates** - Get all agent states
```json
{
    "method": "async.getAgentStates",
    "params": {
        "sessionId": "session-123"
    }
}
```

Response:
```json
{
    "agents": {
        "analyzer": {
            "state": "active",
            "current_task": "mailbox_message",
            "queue_size": 2,
            "sleeping_until": null
        },
        "writer": {
            "state": "idle",
            "current_task": null,
            "queue_size": 0,
            "sleeping_until": null
        }
    }
}
```

### Event Broadcasting

**async.broadcastEvent** - Broadcast event to agents
```json
{
    "method": "async.broadcastEvent",
    "params": {
        "sessionId": "session-123",
        "event": "data_ready",
        "data": {
            "source": "analyzer",
            "timestamp": "2025-06-05T16:30:00Z"
        }
    }
}
```

## Example Workflows

### 1. Parallel Analysis and Report Generation

```python
# Create agents
analyzer = create_agent("analyzer")
writer = create_agent("writer")
reviewer = create_agent("reviewer")

# Start parallel workflow
send_task(analyzer, "Analyze customer sentiment from feedback.csv")
send_task(writer, "Prepare report template for sentiment analysis")

# Analyzer finishes and sends results to writer
# Writer incorporates results and sends to reviewer
# Reviewer approves and notifies completion
```

### 2. Monitoring with Sleep/Wake

```python
# Create monitor agent
monitor = create_agent("monitor")

# Set to wake on events
sleep_agent(monitor, wake_events=["alert", "hourly_check"])

# Monitor sleeps until:
# - An "alert" event is broadcast
# - The "hourly_check" timer fires
# - Manual wake is triggered
```

### 3. Task Decomposition and Parallel Execution

```python
# Planner decomposes work
planner = create_agent("planner")
send_task(planner, "Create plan for new feature implementation")

# Planner creates tasks and delegates:
# - Task A → Coder1
# - Task B → Coder2  
# - Task C → Coder3

# Coders work in parallel
# Each sends results to integrator when done
# Integrator combines and tests
```

## Best Practices

### 1. Choose the Right Pattern

**Use Synchronous (`send_mail_with_switch`) when:**
- You need an immediate response
- The task is blocking
- Order of operations matters
- Simple request/response pattern

**Use Asynchronous (parallel agents) when:**
- Tasks can run independently
- You want to maximize throughput
- Complex workflows with multiple stages
- Long-running background tasks

### 2. Agent Design

- **Single Responsibility**: Each agent should have a clear, focused purpose
- **Stateless Operations**: Agents should not depend on internal state between tasks
- **Error Handling**: Agents should handle errors gracefully and report via mailbox
- **Resource Awareness**: Monitor queue sizes and agent states

### 3. Communication

- **Clear Messages**: Use descriptive subjects and structured body content
- **Priority Levels**: Use appropriate priority for messages
- **Event Names**: Use consistent, descriptive event names
- **Timeout Handling**: Consider timeouts for critical operations

### 4. Monitoring and Debugging

- Regularly check agent states
- Monitor queue sizes to prevent overload
- Use wake events judiciously
- Log important state transitions

## Limitations

1. **Resource Usage**: Each agent consumes resources (memory, API calls)
2. **Coordination Complexity**: Complex workflows require careful design
3. **Debugging**: Multi-agent interactions can be harder to debug
4. **State Management**: No built-in distributed state management

## Migration Guide

### From Sequential to Parallel

**Before (Sequential):**
```python
# Alice does task 1
result1 = alice.do_task1()
# Then Patricia does task 2
result2 = patricia.do_task2(result1)
# Then Eamonn does task 3
result3 = eamonn.do_task3(result2)
```

**After (Parallel where possible):**
```python
# Start independent tasks in parallel
alice_task = send_task("alice", "Do task 1")
patricia_prep = send_task("patricia", "Prepare for task 2")

# When alice completes, she sends result to patricia
# Patricia combines prep work with alice's result
# Eamonn monitors and processes when ready
```

## Troubleshooting

### Agent Not Responding
1. Check agent state with `async.getAgentStates`
2. Verify agent is started and not sleeping
3. Check mailbox for unprocessed messages
4. Review agent's task queue size

### Messages Not Delivered
1. Verify agent names are correct
2. Check mailbox system is functioning
3. Ensure agents are checking their mail
4. Look for errors in agent processing

### Performance Issues
1. Monitor number of active agents
2. Check task queue sizes
3. Review agent sleep/wake patterns
4. Consider consolidating agents

## Future Enhancements

- **Agent Persistence**: Save/restore agent state across restarts
- **Distributed Execution**: Run agents on multiple servers
- **Advanced Scheduling**: Cron-like scheduling for agents
- **Agent Templates**: Reusable agent configurations
- **Visual Monitoring**: Real-time agent workflow visualization