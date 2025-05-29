# AIWhisperer Stateless Architecture

## Overview

This document describes the current stateless architecture of AIWhisperer, focusing on the modular agent system, direct streaming support, and WebSocket-based interactive mode.

---

## 1. Stateless Session Management

### StatelessSessionManager & StatelessInteractiveSession
- **StatelessSessionManager**: Manages multiple interactive sessions without delegate dependencies
- **StatelessInteractiveSession**: Encapsulates agents, contexts, and WebSocket communication with direct streaming
- **Key Features:**
  - No delegate system - direct function callbacks for streaming
  - Agent-based architecture with hot-swappable agents
  - Isolated session state with proper resource cleanup
- **Session Lifecycle:**
  1. **Create**: WebSocket connection creates a new session
  2. **Start**: Default agent (Alice) is initialized with introduction
  3. **Agent Switching**: Users can switch between agents (Alice, Patricia, Tessa)
  4. **Message Processing**: Direct streaming from AI to WebSocket
  5. **Cleanup**: Graceful resource cleanup on disconnect

---

## 2. Direct Streaming Architecture

- **Stream Callbacks**: Direct function callbacks replace the delegate system
- **Event Flow:**
  - User message → Agent → StatelessAILoop → OpenRouter API
  - AI response chunks → Stream callback → WebSocket → Client
- **Notification Types:**
  - `AIMessageChunkNotification`: Streaming AI responses
  - `ToolCallNotification`: Tool execution events
  - `agent.switched`: Agent change notifications
  - `SessionStatusNotification`: Session state changes

---

## 3. Component Architecture

```
[WebSocket Endpoint]
      |
      v
[StatelessSessionManager]
      |
      v
[StatelessInteractiveSession]
      |
      +--> [Agent System]
      |     |
      |     +--> [StatelessAgent (Alice/Patricia/Tessa)]
      |     +--> [AgentContext]
      |     +--> [AgentRegistry]
      |
      +--> [StatelessAILoop] --(stream callbacks)--> [WebSocket]
      +--> [ToolRegistry]
```

### Key Components:
- **WebSocket Endpoint**: FastAPI WebSocket handler for JSON-RPC 2.0
- **StatelessSessionManager**: Manages session lifecycle and WebSocket mapping
- **Agent System**: Modular agents with specialized capabilities
- **StatelessAILoop**: Direct streaming without delegates
- **AgentContext**: Per-agent conversation history and state
- **ToolRegistry**: Pluggable tools with permission system

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

## 5. Agent System

### Available Agents:
- **Alice the Assistant (A)**: General development support and guidance
- **Patricia the Planner (P)**: Creates structured implementation plans
- **Tessa the Tester (T)**: Generates comprehensive test suites

### Agent Configuration:
- Defined in `ai_whisperer/agents/config/agents.yaml`
- System prompts in `prompts/agents/`
- Hot-swappable during active sessions
- Each agent maintains isolated context

## 6. Performance and Scalability

### Optimizations:
- **Direct Streaming**: Eliminates delegate overhead
- **Stateless Design**: Easier horizontal scaling
- **Resource Management**: Automatic cleanup on disconnect
- **Memory Efficiency**: Per-agent context isolation

### Metrics:
- Session count and duration tracking
- Memory usage per session
- Response latency monitoring
- WebSocket connection stability

---

## 7. Cross-References

- **Stateless Implementation:** See [stateless_architecture.md](stateless_architecture.md)
- **Prompt System:** See [prompt_system.md](prompt_system.md) for agent prompts
- **Agent Development:** See agent configuration in `CLAUDE.md`
- **API Documentation:** JSON-RPC message formats in `interactive_server/message_models.py`
- **Configuration:** See `docs/configuration.md` for settings
