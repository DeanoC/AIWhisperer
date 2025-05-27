# AIWhisperer Interactive Server Architecture

## Overview

This document describes the architecture of the interactive server, focusing on session management, event flow, and integration with the AILoop and related components.

---

## 1. Session Management

### InteractiveSessionManager & InteractiveSession
- **InteractiveSessionManager**: Manages all active sessions, mapping each WebSocket connection to a unique session.
- **InteractiveSession**: Represents a single user session, encapsulating the AI loop, context, delegates, and WebSocket.
- **Lifecycle:**
  1. **Create**: On new WebSocket connection, a session is created and mapped.
  2. **Start**: Session is started with a system prompt, initializing the AILoop and dependencies.
  3. **Send Message**: User messages are routed to the session's AILoop.
  4. **Stop**: Session can be stopped gracefully.
  5. **Cleanup**: On disconnect or error, all resources are cleaned up.
- **Concurrency:** One session per WebSocket; session state is isolated.
- **Resource Management:** Sessions are cleaned up on disconnect or error to prevent leaks.

---

## 2. Delegate Bridge and Event Flow

- **DelegateBridge**: Routes events from the AILoop (AI chunk, tool call, status, error) to the WebSocket client as JSON-RPC notifications.
- **Event Mapping:**
  - AI chunk → `AIMessageChunkNotification`
  - Tool call → `ToolCallNotification`
  - Status → `SessionStatusNotification`
  - Error → `SessionStatusNotification` or error notification

---

## 3. Component Architecture

```
[WebSocket Endpoint]
      |
      v
[InteractiveSessionManager]
      |
      v
[InteractiveSession]
      |
      v
[InteractiveAI / AILoop]
      |
      +--> [DelegateManager / DelegateBridge] --(notifications)--> [WebSocket]
      +--> [ContextManager]
      +--> [ToolRegistry]
```

- **WebSocket Endpoint**: Handles incoming connections and JSON-RPC messages.
- **Session Manager**: Creates, tracks, and cleans up sessions.
- **InteractiveSession**: Owns the AILoop and all per-session state.
- **DelegateManager/Bridge**: Handles event routing and notification delivery.
- **ContextManager**: Manages conversation history and context.
- **ToolRegistry**: Provides tool information for tool calls.

---

## 4. Deployment and Scaling

- **Resource Limits:**
  - Max sessions: Tune via config/environment.
  - Memory: Monitor with metrics; each session consumes resources.
- **Scaling:**
  - Run multiple server processes behind a load balancer for high concurrency.
  - Ensure sticky sessions if session affinity is required.
- **Environment Variables:**
  - API keys, timeouts, and session limits can be set via `config.yaml` or environment.

---

## 5. Performance and Tuning

- **Session Timeouts:**
  - Configurable per session; see `config.yaml`.
- **Memory Usage:**
  - Monitored via metrics; clean up sessions promptly.
- **Concurrency:**
  - Test and tune max sessions for your deployment.
- **Metrics:**
  - See `project_dev/performance_metrics_report.md` for current performance data.

---

## 6. Cross-References

- **API Documentation:** See `docs/interactive_mode_api.md` for message formats and error codes.
- **Configuration:** See `docs/configuration.md` and `docs/config_examples.md` for settings.
- **AILoop Details:** See `docs/ai_loop_documentation.md` for loop internals and extension points.
