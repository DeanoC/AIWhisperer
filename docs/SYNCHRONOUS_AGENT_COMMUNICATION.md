# Synchronous Agent Communication in AIWhisperer

## Overview
AIWhisperer already has a synchronous agent communication mechanism built into the `send_mail` tool and `AgentSwitchHandler`. This document describes how it works and how to use it.

## Current Implementation

### Components

1. **send_mail tool** - Standard mail sending tool that agents use
2. **AgentSwitchHandler** - Detects mail sent to agents and triggers synchronous switching
3. **Mailbox system** - Stores messages for asynchronous access

### How It Works

When an agent sends mail to another agent:

```
Agent A → send_mail(to_agent="Debbie", ...) → Mailbox
    ↓
AgentSwitchHandler detects successful send_mail to agent
    ↓
Switches to Agent B (Debbie)
    ↓
Prompts: "You have received mail from Agent A. Let me check your mailbox."
    ↓
Agent B processes mail and responds
    ↓
Switches back to Agent A
```

### Key Code Locations

- **AgentSwitchHandler**: `/interactive_server/agent_switch_handler.py`
  - `handle_tool_results()` - Detects send_mail calls
  - `_perform_agent_switch()` - Handles the synchronous switch

- **send_mail_with_switch**: `/ai_whisperer/tools/send_mail_with_switch_tool.py`
  - Enhanced version with explicit switch metadata (not currently used)

### Agent Name Mapping

The handler maps friendly names to agent IDs:
- alice → a
- patricia / patricia the planner → p  
- tessa / tessa the tester → t
- debbie / debbie the debugger → d
- eamonn / eamonn the executioner → e

## Testing Synchronous Communication

### Conversation Replay Test
```
# User talking to Alice
Hi Alice! Can you send a message to Debbie asking her to analyze the workspace?

# User talking to Debbie directly  
Hi Debbie, can you check if you have any messages in your mailbox?
```

### Expected Flow
1. Alice receives user request
2. Alice uses send_mail tool: `send_mail(to_agent="Debbie", subject="Workspace analysis", body="...")`
3. System switches to Debbie
4. Debbie is prompted to check mailbox
5. Debbie uses check_mail tool
6. Debbie processes request and responds
7. System switches back to Alice
8. Alice sees that mail was delivered

## Limitations of Current Implementation

1. **Single-threaded**: Only one agent active at a time
2. **Blocking**: Original agent waits while target processes
3. **No parallelism**: Can't have multiple agents working simultaneously
4. **No background processing**: Agents can't work while user interacts with another

## Path to Async Agents

The current synchronous system provides the foundation, but true async requires:

1. **Independent AI Loops**: Each agent runs its own AI session
2. **Background execution**: Agents continue working when not active
3. **Event system**: Wake agents on timers or mailbox events
4. **Resource isolation**: Prevent conflicts between parallel agents
5. **Progress tracking**: Monitor background agent work

## Next Steps for Implementation

1. **Test current synchronous flow** - Verify it works as designed
2. **Create AgentSessionManager** - Manage multiple AI loops
3. **Implement background execution** - Allow agents to run independently
4. **Add wake/sleep system** - Timer and event-based activation
5. **Build coordination protocol** - Structured agent collaboration