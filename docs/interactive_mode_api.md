# ---

## Real AILoop Integration: Behavioral Changes

With real AILoop integration, the following behaviors differ from the previous mocked implementation:

- **Streaming AI Output:**
  - `AIMessageChunkNotification` is sent in real time as the AI generates output.
  - The `isFinal` flag indicates the last chunk of a response.
- **Timeouts and Error Notifications:**
  - The server sends `SessionStatusNotification` with `reason: "timeout"` if the AI service or session times out.
  - Error scenarios (e.g., resource exhaustion, AI service errors) are reported via `SessionStatusNotification` or standard JSON-RPC errors.
- **Session Lifecycle:**
  - Session status codes and reasons are now accurate to real backend state (e.g., `status: 3, reason: "timeout"`).
- **Tool Calls:**
  - Tool call notifications and results are handled end-to-end with real tool execution.

---

## Real-World Response Times

Typical response times (from recent performance metrics):

- **First AI chunk latency:** ~65ms (median), <100ms (p95) under normal load
- **Session start latency:** ~2ms (median)
- **Timeout notification:** ~10s (configurable)

See `project_dev/performance_metrics_report.md` for up-to-date metrics.

---

## Expanded Error Codes and Notifications

In addition to standard JSON-RPC errors, the following notifications and error codes are used:

- **SessionStatusNotification**
  - `reason` values:
    - `"timeout"`: Session or AI service timed out
    - `"error"`: Internal error or resource exhaustion
    - `"completed"`: Session ended normally
    - `"disconnected"`: Client disconnected
    - ...others as needed
- **ErrorNotification** (if implemented):
  - Used for non-fatal errors or warnings
- **Resource/connection errors:**
  - May be reported as JSON-RPC errors or as `SessionStatusNotification` with `reason: "error"`

---

## Troubleshooting

**Common Issues:**

- **Connection drops:**
  - Check network stability and server logs for disconnect reasons.
- **Timeouts:**
  - If you receive a `SessionStatusNotification` with `reason: "timeout"`, the AI service or session exceeded its allowed time.
  - Consider increasing timeout settings in `config.yaml` if needed.
- **Invalid params:**
  - Ensure all required fields are present and correctly typed in your JSON-RPC requests.
- **Error codes:**
  - Refer to the error code table above for meanings.

**Debugging Tips:**
- Enable debug logging on the server for more details.
- Use the provided test scripts and manual client to reproduce and diagnose issues.

---

## Example Session (with Streaming and Timeout)

1. Client sends `startSession`.
2. Server responds with session info and sends a `SessionStatusNotification`.
3. Client sends `sendUserMessage`.
4. Server responds with message info and streams `AIMessageChunkNotification` (multiple, with `isFinal: true` on the last).
5. If a tool call is triggered, server sends `ToolCallNotification`.
6. Client responds with `provideToolResult`.
7. Server streams final `AIMessageChunkNotification`.
8. If a timeout or error occurs, server sends `SessionStatusNotification` with `reason: "timeout"` or `"error"`.

---
# Interactive Mode API Documentation

## Overview
This document describes the WebSocket-based JSON-RPC API for the interactive mode backend. It covers available methods, message formats, and usage instructions for frontend and client developers.

---

## Connection

- **WebSocket URL:** `ws://<host>:<port>/ws`
- **Protocol:** JSON-RPC 2.0 over WebSocket

---

## JSON-RPC Methods

### startSession

- **Description:** Start a new AI session.
- **Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "startSession",
  "params": {
    "userId": "string",
    "sessionParams": {
      "language": "string (optional)",
      "model": "string (optional)",
      "context": "string (optional)"
    }
  }
}
```

- **Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "sessionId": "string",
    "status": 1
  }
}
```

- **Notification:**
  - `SessionStatusNotification` (see below)

---

### sendUserMessage

- **Description:** Send a user message to the AI.
- **Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "sendUserMessage",
  "params": {
    "sessionId": "string",
    "message": "string"
  }
}
```

- **Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "messageId": "string",
    "status": 0
  }
}
```

- **Notifications:**
  - `AIMessageChunkNotification` (streaming AI output)
  - `SessionStatusNotification` (session status changes)
  - `ToolCallNotification` (if a tool call is triggered)

---

### provideToolResult

- **Description:** Provide a result for a tool call.
- **Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "provideToolResult",
  "params": {
    "sessionId": "string",
    "toolCallId": "string",
    "result": "string"
  }
}
```

- **Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "status": 0
  }
}
```

- **Notification:**
  - `AIMessageChunkNotification` (final AI output after tool result)

---

## Notifications

### AIMessageChunkNotification
```json
{
  "jsonrpc": "2.0",
  "method": "AIMessageChunkNotification",
  "params": {
    "sessionId": "string",
    "chunk": "string",
    "isFinal": true
  }
}
```

### SessionStatusNotification
```json
{
  "jsonrpc": "2.0",
  "method": "SessionStatusNotification",
  "params": {
    "sessionId": "string",
    "status": 1,
    "reason": "string (optional)"
  }
}
```

### ToolCallNotification
```json
{
  "jsonrpc": "2.0",
  "method": "ToolCallNotification",
  "params": {
    "sessionId": "string",
    "toolCallId": "string",
    "toolName": "string",
    "arguments": {"arg1": "value1"}
  }
}
```

---

## Usage Instructions

- Connect to the WebSocket endpoint.
- Start a session with `startSession`.
- Send user messages with `sendUserMessage`.
- Handle responses and notifications as they arrive (order may vary).
- If a tool call is triggered, respond with `provideToolResult`.
- Handle streaming and status notifications as needed.

---

## Error Handling

- All errors follow JSON-RPC 2.0 error format:

```json
{
  "jsonrpc": "2.0",
  "id": <id|null>,
  "error": {
    "code": <int>,
    "message": "string"
  }
}
```

- Common error codes:
  - `-32700`: Parse error
  - `-32600`: Invalid Request
  - `-32601`: Method not found
  - `-32602`: Invalid params

---

## Example Session

1. Client sends `startSession`.
2. Server responds with session info and sends a `SessionStatusNotification`.
3. Client sends `sendUserMessage`.
4. Server responds with message info and streams `AIMessageChunkNotification`.
5. If a tool call is triggered, server sends `ToolCallNotification`.
6. Client responds with `provideToolResult`.
7. Server streams final `AIMessageChunkNotification`.

---

For more details, see the test suite and message models in `interactive_server/message_models.py`.
