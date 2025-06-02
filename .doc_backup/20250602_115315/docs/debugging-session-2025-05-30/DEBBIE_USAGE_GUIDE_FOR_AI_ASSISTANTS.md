# Debbie the Debugger - Usage Guide for AI Coding Assistants

## What Debbie Does (and Doesn't Do)

**Debbie DOES:**
- 🔍 **Detect** issues like agent stalls, errors, and performance problems
- 📊 **Monitor** sessions in real-time with detailed metrics
- 💉 **Provide workarounds** by injecting messages to unstick agents
- 📝 **Generate insights** about what's happening and why
- 🎯 **Track patterns** to identify recurring issues

**Debbie DOES NOT:**
- ❌ Fix the underlying code that causes issues
- ❌ Permanently solve architectural problems
- ❌ Replace the need for proper debugging and fixes
- ❌ Automatically patch bugs in the codebase

## Case Study: How Debbie Detects Agent Stalls

### The Problem
Agents in AIWhisperer sometimes stall after executing tools. They complete the tool execution but then wait indefinitely for user input instead of continuing with their task.

### How Debbie Detects It

```python
# From monitoring.py - Stall Detection Logic
if (current_time - session.last_activity) > self.stall_threshold:
    # Check if last message was a tool result
    recent_messages = session.get_recent_messages(5)
    if recent_messages and recent_messages[-1].type == "tool_result":
        # This is likely a continuation stall
        alert = AnomalyAlert(
            alert_type="session_stall",
            severity="high",
            session_id=session_id,
            message="Agent stalled after tool execution",
            details={
                "last_tool": recent_messages[-1].tool_name,
                "stall_duration": stall_duration,
                "pattern": "continuation_stall"
            }
        )
```

### Reading Debbie's Output

When Debbie detects a stall, you'll see output like this:

```
[05:35:38] ⚠️ [DEBBIE] Stall detected! Agent inactive for >30s after tool use
            └─ pattern: continuation_stall
            └─ confidence: 95%
            └─ last_tool: list_rfcs
            └─ session_id: demo_session_1
[05:35:38] 💭 [DEBBIE] This is a common issue where agents wait for user input after tools
[05:35:38] 💉 [DEBBIE] Injecting continuation prompt for session demo_session_1
```

### Understanding the Debug Information

1. **Timing Information**: `[05:35:38]` - When the issue was detected
2. **Pattern Identification**: `continuation_stall` - Specific type of stall
3. **Context**: `last_tool: list_rfcs` - What the agent was doing
4. **Confidence**: How sure Debbie is about the pattern
5. **Action Taken**: Injection of continuation prompt (workaround)

## How to Use Debbie as an AI Assistant

### 1. Starting Debbie for a Debugging Session

```python
from ai_whisperer.batch.debbie_integration import DebbieFactory

# Create Debbie with appropriate settings
debbie = DebbieFactory.create_default()  # or create_aggressive() for faster detection
await debbie.start()

# Integrate with your batch client
batch_client = await integrate_debbie_with_batch_client(batch_client, debbie)
```

### 2. Running with Monitoring

```python
# Run your problematic code - Debbie monitors automatically
await batch_client.run()

# Debbie will detect issues and provide workarounds in real-time
```

### 3. Analyzing the Results

```python
# Get a comprehensive analysis
analysis = await debbie.analyze_session(session_id)

# Key information for debugging:
print(f"Stall count: {analysis['metrics']['stall_count']}")
print(f"Error count: {analysis['metrics']['error_count']}")
print(f"Interventions: {analysis['interventions']['count']}")
print(f"Recommendations: {analysis['recommendations']}")
```

### 4. Understanding Debbie's Insights

Debbie provides different types of insights:

#### Pattern Detection
```
[DEBBIE] Recurring error pattern detected
         └─ error_type: ConnectionTimeout
         └─ occurrences: 3
         └─ pattern: Identical errors on same endpoint
```
**What this tells you**: The same error is happening repeatedly, suggesting a systematic issue rather than a random failure.

#### Performance Analysis
```
[DEBBIE] Performance degradation detected!
         └─ current_avg: 520ms
         └─ baseline: 100ms
         └─ degradation: 5.2x slower
```
**What this tells you**: Something is causing the system to slow down over time - could be memory leak, resource exhaustion, or algorithmic issues.

#### Tool Loop Detection
```
[DEBBIE] Tool loop detected!
         └─ tool: search_files
         └─ executions: 7
         └─ pattern: Same parameters each time
```
**What this tells you**: An agent is stuck in a loop, repeatedly calling the same tool without making progress.

## Debugging Workflow with Debbie

### Step 1: Reproduce the Issue with Monitoring
```python
# Enable Debbie before running problematic code
debbie = DebbieFactory.create_aggressive()  # Fast detection
await debbie.start()
```

### Step 2: Let Debbie Detect and Work Around
- Debbie will automatically detect issues
- She'll apply workarounds to keep things running
- All actions are logged for analysis

### Step 3: Analyze the Root Cause
```python
# Get debugging report
report = debbie.get_debugging_report()

# Look for:
# - When issues occur (timing patterns)
# - What triggers them (specific tools/commands)
# - How often they happen (frequency)
# - What workarounds succeeded
```

### Step 4: Use Insights to Fix the Code
Based on Debbie's findings, you can:
1. Identify the specific code paths that cause stalls
2. Understand the conditions that trigger issues
3. See which workarounds are effective
4. Make informed decisions about permanent fixes

## Example: Using Debbie's Findings to Fix Code

### Debbie's Detection:
```
Multiple stalls detected after tool execution
Pattern: continuation_stall
Affected tools: list_rfcs, search_files, analyze_code
Workaround success rate: 100% with prompt injection
```

### What This Tells You:
1. The issue is systematic (affects multiple tools)
2. It's related to the continuation mechanism after tool execution
3. A simple prompt injection reliably works around it

### Potential Fixes to Investigate:
1. Check the agent's continuation logic after tool completion
2. Look for missing state updates after tool execution
3. Verify the message flow between tool completion and next action
4. Consider if the agent's prompt needs explicit continuation instructions

## Best Practices for AI Assistants Using Debbie

1. **Always Run Debbie During Development**
   - Helps catch issues early
   - Provides real-time feedback
   - Documents behavior patterns

2. **Use Aggressive Mode for Debugging**
   ```python
   debbie = DebbieFactory.create_aggressive()
   # Faster detection (2s vs 5s checks)
   # Lower thresholds (15s vs 30s for stalls)
   ```

3. **Review Intervention History**
   ```python
   # See what workarounds were needed
   history = debbie.orchestrator.executor.history.get_session_history(session_id)
   for intervention in history:
       print(f"{intervention.strategy}: {intervention.result}")
   ```

4. **Look for Patterns Across Sessions**
   - If the same issue appears repeatedly, it's systematic
   - If workarounds always succeed, the fix might be simple
   - If issues are random, might be race conditions or timing

## Interpreting Common Debbie Messages

### "Stall detected after tool execution"
**Means**: Agent completed a tool but didn't continue
**Investigate**: Continuation logic, state management, message flow

### "High error rate: 50%"
**Means**: Half of all operations are failing
**Investigate**: Error handling, retry logic, validation

### "Performance degraded to Xms"
**Means**: Operations taking longer than baseline
**Investigate**: Memory leaks, inefficient algorithms, resource contention

### "Tool loop detected"
**Means**: Same tool called repeatedly
**Investigate**: Loop conditions, exit criteria, state updates

## Future Capabilities (Coming Soon)

- **Root Cause Analysis**: Deeper investigation into why issues occur
- **Fix Suggestions**: Specific code changes to address issues
- **Historical Trends**: Pattern analysis across multiple sessions
- **Performance Profiling**: Detailed breakdowns of slow operations

---

Remember: Debbie is your debugging assistant. She helps you understand what's happening, provides temporary workarounds, and gives you the information needed to implement proper fixes. She's not a replacement for good debugging practices, but a powerful tool to make debugging more efficient and systematic.