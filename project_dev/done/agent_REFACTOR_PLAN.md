# AIWhisperer Refactor Plan

## Overview

This document outlines a comprehensive refactor of the AIWhisperer codebase to clean up the context/agent/ailoop architecture while maintaining functionality and using Test-Driven Development (TDD) methodology.

## Current Issues

1. Mixed responsibilities between AILoop, ContextManager, and AgentContextManager
2. Unclear ownership of context and session state
3. Redundant context management implementations
4. Complex coupling through delegate managers
5. Inconsistent agent management across sessions

## Target Architecture

### Core Principles

- **Single Responsibility**: Each class has one clear job
- **Clear Ownership**: Each agent owns its context, each session owns its agents
- **Testable Components**: All components are easily unit testable
- **Maintained Streaming**: Keep existing JSON-RPC streaming functionality during transition

### Final Architecture Overview

```
Frontend -> JSON-RPC -> InteractiveSession -> Agent -> AILoop -> AIService
                                           \-> AgentContext
```

## Phases

### Phase 1: Foundation - Context Management Refactor

**Goal**: Unify context management with a single, testable implementation

### Phase 2: Agent Architecture Refactor  

**Goal**: Create clean Agent abstraction that owns its context

### Phase 3: Session Management Cleanup

**Goal**: Simplify session management to use new Agent structure

### Phase 4: AILoop Simplification

**Goal**: Remove delegate manager and simplify AILoop interface

### Phase 5: Integration and Cleanup

**Goal**: Final integration testing and removal of deprecated code

---

## Detailed Phase Breakdown

## Phase 1: Foundation - Context Management Refactor

### Objectives

- Create unified context management interface
- Replace AgentContextManager with standard ContextManager usage
- Establish testing patterns for context management

### Key Components

- `ContextProvider` interface
- `AgentContext` implementation
- Context serialization/persistence

### Success Criteria

- All context operations use single implementation
- Full test coverage for context management
- Backward compatibility maintained

---

## Phase 2: Agent Architecture Refactor

### Objectives  

- Create clean Agent abstraction
- Each agent owns its context and configuration
- Maintain existing AILoop integration (with delegates)

### Key Components

- `Agent` class with clear responsibilities
- `AgentConfig` for agent-specific settings
- `AgentFactory` for creating configured agents

### Success Criteria

- Agents are self-contained and testable
- Context ownership is clear
- Existing functionality preserved

---

## Phase 3: Session Management Cleanup

### Objectives

- Simplify InteractiveSession to manage agents cleanly
- Remove redundant session logic
- Improve session lifecycle management

### Key Components

- Refactored `InteractiveSession`
- Cleaned up `InteractiveSessionManager`
- Session persistence improvements

### Success Criteria

- Clear session/agent relationships
- Simplified session API
- Improved error handling and cleanup

---

## Phase 4: AILoop Simplification

### Objectives

- Remove delegate manager dependency
- Make AILoop stateless regarding conversation context
- Direct result returns instead of delegate callbacks
- Maintain streaming via direct JSON-RPC

### Key Components

- Simplified `AILoop` interface
- Direct streaming implementation
- Removal of bridge classes

### Success Criteria

- AILoop is stateless and reusable
- Streaming functionality maintained
- Simplified call chain

---

## Phase 5: Integration and Cleanup

### Objectives

- End-to-end integration testing
- Performance validation
- Remove deprecated code
- Documentation updates

### Key Components

- Integration test suite
- Performance benchmarks
- API documentation
- Migration guide

### Success Criteria

- All functionality working as before
- Performance maintained or improved
- Clean, maintainable codebase
