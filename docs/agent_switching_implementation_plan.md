# Agent Switching Implementation Plan

## Overview
Implement synchronous agent switching when messages are sent via the mailbox system.

## Current State
- Mailbox system exists and works
- send_mail tool can send messages between agents
- Agent switching is not triggered when mail is sent
- Tools are executed in `ai_loop.py` `_execute_tool_calls` method

## Implementation Steps

### 1. Modify send_mail_tool.py ✅
- Add agent_switch metadata to ToolResult when sending to another agent
- Include source agent, target agent, and message ID

### 2. Enhance Tool Execution in Session Manager
- After tool execution, check if any tool returned agent_switch metadata
- If agent_switch is required:
  1. Store current agent context
  2. Switch to target agent
  3. Send notification about mail received
  4. Let target agent process mail (check_mail)
  5. Get response from target agent
  6. Store response in mailbox as reply
  7. Switch back to original agent
  8. Continue with original agent's flow

### 3. Add Agent Switch Handler
- Create method in StatelessInteractiveSession to handle agent switches
- Preserve context and state during switches
- Ensure proper cleanup on errors

### 4. Update check_mail_tool.py
- Modify to work seamlessly with the switching flow
- Mark messages as read when processed

### 5. Testing
- Test Alice sending mail to Patricia
- Test Patricia replying to Alice
- Test error handling during switches
- Test continuation after mail exchange

## Code Locations
- `/ai_whisperer/tools/send_mail_tool.py` - Tool that triggers switching ✅
- `/interactive_server/stateless_session_manager.py` - Session management and tool execution
- `/ai_whisperer/services/execution/ai_loop.py` - Tool execution logic
- `/ai_whisperer/tools/check_mail_tool.py` - Mail checking tool
- `/ai_whisperer/extensions/mailbox/mailbox.py` - Mailbox system

## Expected Behavior
1. Alice: "Send mail to Patricia asking about RFC review"
2. System: Executes send_mail tool
3. System: Detects agent_switch required
4. System: Switches to Patricia
5. Patricia: "You have mail from Alice"
6. Patricia: Checks mail and processes request
7. Patricia: Sends reply
8. System: Switches back to Alice
9. Alice: "Patricia replied with..."