# RFC: Asynchronous Agents Feature

**RFC ID**: RFC-2025-06-04-0001
**Status**: in_progress
**Created**: 2025-06-04 18:19:55
P25-06-04 18:21:23
**Author**: User

## Summary
This RFC proposes the implementation of asynchronous capabilities for agents to improve performance and responsiveness by enabling concurrent task execution and optional sleep/wake monitoring.
## Background

*To be defined during refinement*

## Requirements
- [ ]
- Enable multiple separate tasks to be run concurrently.
- Agents can optionally sleep and wake to monitor activities and other agents.
## Technical Considerations

- **Shared Resource Management**:
    - Auto-pausing mechanism for short, non-blocking operations.
    - Optional locking protocol for longer, resource-intensive operations to prevent conflicts.
- **Error Handling & Debugging**: Requires a dedicated design phase to define strategies for identifying, handling, and debugging issues across multiple asynchronous agents.

## Existing Components Requiring Refactoring

- **Backend AI Loops**: Currently 1 per agent, will be extended to support multiple concurrent loops per agent.
- **Frontend UI**: Needs updates to support both group chats and 1-1 chats with specific agents.
- **Mailbox System**: Requires improvements to support asynchronous communication and message handling for async agents.

## Conceptual Framework: Independent Agent AI Loops with Mailbox Coordination

This feature will implement a revolutionary architecture where each agent runs its own AI loop independently, enabling true parallel multi-agent workflows. This includes:

- **Agent Capabilities**:
    - **Sleep/Wake Control**: Agents can sleep on timers or events, waking up to check progress.
    - **Async Mailbox Communication**: Agents will communicate asynchronously via the mailbox system.
    - **Progress Monitoring**: Agents can monitor the progress of other agents or tasks.
    - **Parallel Execution**: Multiple agents will work simultaneously on different aspects.
    - **Agent Coordination**: Agents can request help, delegate tasks, and collaborate.

- **Technical Architecture**:
    - Independent AI session per agent.
    - Async task queues and event systems.
    - Agent sleep/wake scheduling.
    - Mailbox-driven inter-agent communication.
    - Conflict resolution for shared resources.
    - Agent lifecycle management.
## Implementation Approach

*To be defined during refinement*

## Open Questions

- [ ] *Questions will be added during refinement*

## Acceptance Criteria

- **Concurrent Tasks**: Tasks executed concurrently by asynchronous agents must remain isolated from each other, interacting only via explicitly defined tools (e.g., the mailbox system).
- **Agent Sleep/Wake**: Agents should be able to enter a sleep state and wake up based on periodic functions (e.g., monitoring activities every 30 minutes, similar to Debbie's monitoring).
- **Shared Resources**: Small operations on shared resources will use auto-pausing. Longer operations will implement an optional locking protocol.

## Related RFCs

*None identified yet*

## Refinement History
- 2025-06-04 18:27:24: Added to technical considerations section
- 2025-06-04 18:27:24: Added to acceptance criteria section
- 2025-06-04 18:24:32: Added refactoring details and conceptual framework for async agents
- 2025-06-04 18:21:23: Updated summary with new details
- 2025-06-04 18:21:23: Added asynchronous agent capabilities

- 2025-06-04 18:19:55: RFC created with initial idea

---
*This RFC was created by AIWhisperer's Agent P (Patricia)*