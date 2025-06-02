# Agent Continuation System - Testing Guide

## Overview

This guide explains how to test the agent continuation system using batch mode scripts. The continuation system allows agents to perform multi-step operations autonomously, even on single-tool models.

## Test Scripts

### 1. Comprehensive Regression Test
**File**: `/scripts/test_continuation_regression.json`

This is a comprehensive test suite that validates:
- Multi-tool execution on single-tool models
- Explicit continuation signals
- Safety limits and termination
- Cross-agent workflows
- Error recovery

**Run it with:**
```bash
python -m ai_whisperer.batch.batch_client scripts/test_continuation_regression.json
```

### 2. Quick Test Script
**File**: `/test_continuation_quick.txt`

A simpler text-based script for quick validation of basic functionality.

**Run it with:**
```bash
python -m ai_whisperer.cli test_continuation_quick.txt --config config.yaml
```

## What to Look For

### In the Console Output

1. **Multi-Tool Execution**:
   - Look for: `TOOL STRATEGY: SINGLE_TOOL_MODEL_ERROR` followed by successful execution
   - Multiple tools should execute even on Gemini (single-tool model)

2. **Continuation Decisions**:
   - Look for: `CONTINUATION STRATEGY DECISION: True/False`
   - Agents should continue when they signal CONTINUE status

3. **No JSON in Chat**:
   - User-facing responses should be natural language only
   - No continuation metadata should appear in chat

### In the Logs

Key log patterns to monitor:
```
INFO:ai_whisperer.ai_loop.stateless_ai_loop:🔧 EXECUTING TOOLS: Found N tool calls
INFO:interactive_server.stateless_session_manager:🔄 CONTINUATION STRATEGY DECISION: True
INFO:ai_whisperer.agents.continuation_strategy:Explicit continuation signal: True, reason: [reason]
INFO:ai_whisperer.agents.continuation_strategy:No explicit continuation signal found, defaulting to TERMINATE
```

## Test Scenarios

### Scenario 1: Multi-Tool Single Request
**Agent**: Alice or Patricia
**Test**: "List all files in directory X and read file Y"
**Expected**: Both tools execute successfully on Gemini

### Scenario 2: Explicit Continuation
**Agent**: Patricia
**Test**: "List RFCs then create a new one"
**Expected**: Lists RFCs, signals CONTINUE, creates new RFC

### Scenario 3: Safety Limits
**Agent**: Any
**Test**: Request that would require >10 iterations
**Expected**: Stops at configured limit (max_iterations)

### Scenario 4: Cross-Agent Context
**Agent**: Multiple
**Test**: Switch agents and reference previous work
**Expected**: Context maintained across agent switches

## Debugging Tips

1. **Enable Debug Logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   ```

2. **Check Continuation Config**:
   - Verify agents have `continuation_config` in `agents.yaml`
   - Ensure `require_explicit_signal: true` is set

3. **Monitor WebSocket Messages**:
   - Look for `continuation.progress` notifications
   - Check `AIMessageChunkNotification` for response streaming

## Success Criteria

A successful test run should show:
- ✅ Agents execute multiple tools when needed
- ✅ Continuation happens based on explicit signals
- ✅ No JSON appears in user responses  
- ✅ Safety limits prevent infinite loops
- ✅ Agents maintain context across continuations
- ✅ Error handling preserves continuation flow

## Batch Mode Script Format

### JSON Format
```json
{
  "name": "Test Name",
  "description": "Test description",
  "steps": [
    {
      "command": "switch_agent",
      "agent": "a"
    },
    {
      "command": "user_message",
      "message": "Your message here",
      "expect_tools": ["tool1", "tool2"],
      "timeout": 30
    }
  ]
}
```

### Text Format
```
# Comments start with #
@a  # Switch to agent 'a'
Your message here
@p  # Switch to agent 'p'
Another message
```

## Troubleshooting

### Issue: Agent doesn't continue
- Check agent has `continuation_config` in agents.yaml
- Verify continuation strategy is initialized (check logs)
- Ensure agent is sending proper continuation signals

### Issue: JSON appears in chat
- Update to latest continuation protocol
- Check that agents are using response structure correctly
- Verify prompt includes updated continuation instructions

### Issue: Too many continuations
- Check `max_iterations` in continuation config
- Verify TERMINATE signals are being sent
- Check timeout settings

## Next Steps

After running tests:
1. Review logs for any errors or warnings
2. Verify all test scenarios pass
3. Check performance metrics
4. Document any issues found
5. Run tests after any changes to continuation system