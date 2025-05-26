
# Interactive Mode Infrastructure Scaffolding Checklist (Test-First/TDD)


This checklist guides the process of scaffolding the interactive mode backend infrastructure using a test-first (TDD) approach. For each feature, write and run tests before implementing the feature. Update this document as you progress.

---


## 1. Project Setup

- [x] **Create a new FastAPI application for interactive mode**
  - [x] Write tests for project structure and entrypoint existence
  - [x] Set up project structure (e.g., `interactive_server/` or similar)
  - [x] Add dependencies: `fastapi`, `uvicorn`, `pydantic`
  - [x] Prepare a main entrypoint script (e.g., `main.py`)

---


## 2. WebSocket Endpoint

- [ ] **Implement a WebSocket endpoint**
  - [x] Write tests for WebSocket connection, multiple clients, and lifecycle events
  - [x] Define a `/ws` or `/interactive` route for WebSocket connections
  - [x] Accept and manage multiple client connections
  - [x] Handle connection lifecycle (connect, disconnect, error)

---


## 3. JSON-RPC Protocol Handling

- [ ] **Design JSON-RPC message dispatch**
  - [x] Write tests for JSON-RPC request parsing, routing, notifications, and error handling
  - [x] Parse incoming JSON-RPC requests from clients
  - [x] Route requests to appropriate handler functions
  - [x] Support JSON-RPC notifications and responses
  - [x] Handle invalid requests and send error responses

---


## 4. Message Model Integration

- [ ] **Define Pydantic models for messages**
  - [x] Write tests for message model validation and serialization
  - [x] Generate or manually create models from `InteractiveAPI.def` (manually created for echo/add)
  - [x] Use these models for request validation and serialization

---


## 5. Mocked AILoop Integration

- [ ] **Implement mock AILoop responses**
  - [x] Write tests for mocked responses, streaming, and tool call/result flows
  - [x] For each supported JSON-RPC method, return a simulated response
  - [x] Simulate streaming responses for AI message chunks
  - [x] Simulate tool call/result flows
  - [x] Log or print received requests for debugging

---


## 6. Notification & Streaming Support

- [ ] **Implement server-to-client notifications**
  - [x] Write tests for server-to-client notifications and async streaming
  - [x] Send JSON-RPC notifications for events (e.g., AI message chunk, session status)
  - [x] Ensure notifications can be sent asynchronously to connected clients

---


## 7. Basic Testing

- [ ] **Test WebSocket and JSON-RPC flow**
  - [x] Write integration tests for end-to-end WebSocket and JSON-RPC flow
  - [x] Use a simple WebSocket client (e.g., `websocat`, Python script, or browser) to connect and send requests
  - [x] Verify correct responses and notifications are received
  - [x] Test error handling for invalid/malformed requests

---


## 8. Documentation

- [ ] **Document the interactive mode API**
  - [x] Write documentation tests/examples for API usage
  - [x] List available JSON-RPC methods and expected message formats
  - [x] Document connection and usage instructions for frontend developers

---



## 9. Ready for Integration

- [x] **Review code and checklist**
- [x] Confirm all tests pass and checklist items are complete
- [x] Confirm infrastructure is ready for real AILoop integration and frontend development

---


**Tips:**

- For each feature, write and run tests before implementing the feature (TDD).
- Keep AILoop logic mocked/stubbed for now—focus on protocol and infrastructure.
- Use logging and clear error messages for easier debugging.
- Update this checklist as you complete each step.

---
