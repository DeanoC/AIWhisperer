# Manual Testing Checklist: AILoop Interactive Server

## 1. WebSocket Connection

- [ ] Connect to `/ws` endpoint using a WebSocket client (e.g., browser, Postman, `websocat`)
- [ ] Verify connection is accepted and remains open
- [ ] Disconnect and reconnect; ensure no resource leaks or errors

## 2. Session Lifecycle

- [ ] Start a session (`startSession` JSON-RPC)
- [ ] Receive `SessionStatusNotification` (status=Active)
- [ ] Stop session (`stopSession` JSON-RPC)
- [ ] Receive `SessionStatusNotification` (status=Stopped)
- [ ] Attempt to stop a non-existent session; receive appropriate response

## 3. Messaging

- [ ] Send a valid user message (`sendUserMessage`)
- [ ] Receive `AIMessageChunkNotification` (streamed response)
- [ ] Send invalid user message (e.g., non-string); receive error notification
- [ ] Send multiple messages in sequence; verify ordering and responses

## 4. Tool Calls

- [ ] Trigger a tool call (if supported by prompt)
- [ ] Receive `ToolCallNotification`
- [ ] Provide tool result (`provideToolResult`)
- [ ] Receive follow-up AI response

## 5. Error Handling

- [ ] Simulate AI service outage (e.g., disconnect backend, use invalid API key)
- [ ] Receive error notification and/or graceful degradation
- [ ] Send malformed JSON-RPC; receive error response
- [ ] Disconnect WebSocket during streaming; ensure server cleans up session

## 6. Concurrency & Stress

- [ ] Open 10+ concurrent WebSocket sessions; verify all can send/receive
- [ ] Observe server memory/CPU usage under load
- [ ] Run long-lived session (10+ minutes); verify stability

## 7. Observability

- [ ] Check server logs for errors, warnings, and resource cleanup
- [ ] Confirm error messages are clear and actionable

---

**Notes:**

- Use a variety of clients and network conditions
- Document any unexpected behavior or errors
- Update this checklist as new features or edge cases are discovered
