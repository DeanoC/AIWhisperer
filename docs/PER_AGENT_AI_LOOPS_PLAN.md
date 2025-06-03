# Per-Agent AI Loops Implementation Plan

## Overview
Transform AIWhisperer from a shared single AI loop architecture to per-agent AI loops, enabling each agent to use different AI models and configurations. This is a prerequisite for future async multi-agent workflows.

## Current Architecture
- Single shared AI loop (likely singleton or globally accessed)
- All agents use the same AI model and configuration
- Agent switching maintains the same AI context
- Model configuration is global

## Target Architecture
- Each agent has its own dedicated AI loop instance
- Agents can specify preferred AI models (GPT-4, Claude, etc.)
- AI loop configuration is per-agent (temperature, max tokens, etc.)
- Clean separation between agents' AI interactions

## Phase 1: Break the Singleton Pattern

### Goals
- Make AILoop instantiable without singleton constraints
- Support multiple concurrent AI loop instances
- Maintain backward compatibility during transition

### Tasks
1. **Analyze Current AI Loop Usage** ✅
   - Find all references to AI loop in codebase
   - Identify singleton/global access patterns
   - Document dependencies

2. **Create AILoopFactory**
   - Factory class for creating AI loop instances
   - Configuration object for AI loop settings
   - Support for different AI service backends

3. **Refactor AILoop Class**
   - Remove singleton pattern
   - Make configuration instance-specific
   - Ensure thread-safety for concurrent use

4. **Update Access Patterns**
   - Replace global access with dependency injection
   - Pass AI loop instances where needed
   - Update tests to create instances

### Files to Modify
- `ai_whisperer/services/execution/ai_loop.py`
- `ai_whisperer/services/agents/base.py`
- `ai_whisperer/services/agents/stateless.py`
- Related test files

## Phase 2: Agent-Specific Configuration

### Goals
- Each agent specifies its AI model preferences
- Automatic AI loop creation based on agent config
- Seamless switching between agent-specific AI loops

### Tasks
1. **Extend Agent Configuration**
   ```yaml
   # Example agent config
   alice:
     name: "Alice the AI Assistant"
     ai_config:
       model: "gpt-4"
       temperature: 0.7
       max_tokens: 4000
   
   debbie:
     name: "Debbie the Debugger"
     ai_config:
       model: "gpt-3.5-turbo"  # Faster, cheaper for debugging
       temperature: 0.3
       max_tokens: 2000
   ```

2. **Implement AILoopManager**
   - Registry of agent ID → AI loop instance
   - Lazy creation of AI loops
   - Resource management (connection pooling)
   - Cleanup on agent unload

3. **Update Agent Initialization**
   - Create dedicated AI loop during agent setup
   - Store reference to agent's AI loop
   - Handle missing/invalid configurations

4. **Modify Agent Switching**
   - Switch both agent and its AI loop
   - Update context to use new AI loop
   - Ensure clean handoff between agents

### Files to Create/Modify
- `ai_whisperer/services/agents/ai_loop_manager.py` (new)
- `ai_whisperer/services/agents/config.py`
- `ai_whisperer/services/agents/factory.py`
- Agent configuration files in `config/agents/`

## Testing Strategy

### Unit Tests
- Test AI loop factory with various configurations
- Test multiple AI loop instances running concurrently
- Test agent-specific AI loop assignment
- Test configuration validation and fallbacks

### Integration Tests
- Test agent switching with different AI models
- Test resource limits and cleanup
- Test error handling for unavailable models
- Test configuration hot-reloading

## Migration Path

1. **Step 1**: Implement factory pattern alongside existing singleton
2. **Step 2**: Gradually migrate code to use factory
3. **Step 3**: Add per-agent configuration support
4. **Step 4**: Remove singleton pattern completely
5. **Step 5**: Optimize and add advanced features

## Success Criteria

- [ ] AI loop can be instantiated multiple times with different configs
- [ ] Each agent has its own AI loop instance
- [ ] Agents can use different AI models simultaneously
- [ ] No regression in existing functionality
- [ ] Performance comparable or better than current
- [ ] Clean, maintainable architecture for future async work

## Risks and Mitigation

**Risk 1**: Increased memory usage from multiple AI loops
- **Mitigation**: Lazy initialization, connection pooling, resource limits

**Risk 2**: Complex state management during agent switching
- **Mitigation**: Clear ownership model, proper cleanup procedures

**Risk 3**: Breaking existing functionality
- **Mitigation**: Gradual migration, comprehensive testing, feature flags

## Future Considerations

This work enables:
- Async multi-agent workflows (agents working in parallel)
- Cost optimization (cheap models for simple tasks)
- Specialized models for specific domains
- A/B testing different models for same agent
- Dynamic model switching based on task complexity

## Implementation Order

1. Analyze and document current AI loop usage
2. Create basic factory pattern
3. Refactor AI loop to remove singleton
4. Add configuration support
5. Create AILoopManager
6. Extend agent configurations
7. Wire up per-agent AI loops
8. Add comprehensive tests
9. Document new architecture

---

*Created: 2025-06-03*
*Status: Planning Phase*