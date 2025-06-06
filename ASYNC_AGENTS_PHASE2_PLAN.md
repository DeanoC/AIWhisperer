# Async Agents Phase 2: Agent Session Management

## Overview
Implement the AgentSessionManager to support multiple AI loop instances running in parallel.

## Current State
- ✅ Synchronous mail switching works (`send_mail_with_switch`)
- ✅ Agent switch handler manages context switches
- ✅ Per-agent debug logging implemented
- ❌ Only one agent can be active at a time
- ❌ No background agent execution

## Design Goals
1. Multiple agents running independent AI loops
2. Resource isolation between agents
3. Agent lifecycle controls (start/pause/resume/stop)
4. WebSocket notifications for agent state changes

## Implementation Tasks

### 1. Create AsyncAgentSessionManager
```python
class AsyncAgentSessionManager:
    def __init__(self):
        self.active_sessions = {}  # agent_id -> AgentSession
        self.agent_threads = {}    # agent_id -> Thread/Task
        
    async def start_agent(self, agent_id: str, config: dict):
        """Start a new agent with its own AI loop"""
        
    async def pause_agent(self, agent_id: str):
        """Pause agent execution"""
        
    async def resume_agent(self, agent_id: str):
        """Resume paused agent"""
        
    async def stop_agent(self, agent_id: str):
        """Stop agent and cleanup resources"""
        
    def get_agent_status(self, agent_id: str):
        """Get current agent state"""
```

### 2. Agent States
- **IDLE**: Agent created but not started
- **ACTIVE**: Agent running and processing
- **PAUSED**: Agent temporarily suspended
- **SLEEPING**: Agent waiting for wake event
- **STOPPED**: Agent terminated

### 3. Independent AI Loops
Each agent needs:
- Its own AI service instance
- Separate tool registry
- Independent context manager
- Isolated execution environment

### 4. WebSocket Notifications
Extend existing notifications:
- `agent.started`
- `agent.paused`
- `agent.resumed`
- `agent.stopped`
- `agent.state_changed`

### 5. Resource Management
- Memory limits per agent
- Execution time limits
- Concurrent agent limits
- Resource usage tracking

## File Structure
```
ai_whisperer/
  services/
    agents/
      async_session_manager.py    # New: Manages multiple agent sessions
      agent_session.py            # New: Individual agent session
      agent_state.py              # New: Agent state machine
  
interactive_server/
  async_agent_endpoints.py        # New: WebSocket endpoints for async agents
```

## Testing Strategy
1. Unit tests for each component
2. Integration tests for multi-agent scenarios
3. Stress tests for resource limits
4. Conversation replay tests for workflows

## Success Criteria
- [ ] Multiple agents can run simultaneously
- [ ] Each agent has isolated resources
- [ ] Agent lifecycle controls work correctly
- [ ] WebSocket notifications sent for all state changes
- [ ] No resource conflicts between agents
- [ ] Existing synchronous functionality still works

## Next Steps
1. Review this plan with the team
2. Create skeleton implementations
3. Implement core AsyncAgentSessionManager
4. Add WebSocket endpoints
5. Create comprehensive tests