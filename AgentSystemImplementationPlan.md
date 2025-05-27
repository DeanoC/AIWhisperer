# Agent System Implementation Plan for AIWhisperer

## Overview

This document outlines the implementation plan for transitioning from CLI-based tools to an interactive multi-agent chat system. The first agent to be implemented is "Patricia the Planner" who will handle initial plan generation through conversation.

## Architecture Overview

The agent system will integrate with existing infrastructure:
- **Tool Registry**: Use tags to group tools for each agent
- **Prompt System**: Load agent-specific system prompts from files
- **Chat Interface**: Extend to support agent selection and switching
- **Context Management**: Agent-aware context building

## Component Design

### 1. Agent Registry (Backend)

```python
# filepath: src/ai_whisperer/agents/registry.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class Agent:
    """Represents a specialized AI agent with specific capabilities"""
    agent_id: str  # Single letter ID (P, T, C, etc.)
    name: str  # Full name (Pat the Planner)
    role: str  # Role identifier (planner, tester, coder)
    description: str  # User-facing description
    tool_tags: List[str]  # Tags to filter tools from registry
    prompt_file: str  # Filename in prompts directory
    context_sources: List[str]  # Types of context to include
    color: str  # UI color for agent identification
    
    @property
    def shortcut(self) -> str:
        """Returns the keyboard shortcut for this agent"""
        return f"[{self.agent_id}]"

class AgentRegistry:
    """Manages available agents and their configurations"""
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._agents: Dict[str, Agent] = {}
        self._load_default_agents()
    
    def _load_default_agents(self):
        """Load the default agent configurations"""
        # Default agents configuration
        pass
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self._agents.get(agent_id.upper())
    
    def list_agents(self) -> List[Agent]:
        """List all available agents"""
        return list(self._agents.values())
```

### 2. Agent Context Manager (Backend)

```python
# filepath: src/ai_whisperer/agents/context_manager.py
from typing import List, Dict, Any
from ..context_manager import ContextManager
from .registry import Agent

class AgentContextManager(ContextManager):
    """Context manager specialized for agent-specific needs"""
    
    def __init__(self, agent: Agent, workspace_path: Path):
        super().__init__()
        self.agent = agent
        self.workspace_path = workspace_path
        self._initialize_agent_context()
    
    def _initialize_agent_context(self):
        """Load context based on agent's context_sources"""
        for source in self.agent.context_sources:
            if source == "workspace_structure":
                self._add_workspace_structure()
            elif source == "existing_schemas":
                self._add_existing_schemas()
            elif source == "recent_changes":
                self._add_recent_changes()
            # Add more context sources as needed
    
    def _add_workspace_structure(self):
        """Add workspace directory structure to context"""
        # Implementation
        pass
```

### 3. Agent Handler Interface (Backend)

```python
# filepath: src/ai_whisperer/agents/base_handler.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgentHandler(ABC):
    """Base class for all agent handlers"""
    
    def __init__(self, agent: Agent, engine: Any):
        self.agent = agent
        self.engine = engine
        self.context_manager = AgentContextManager(agent, engine.workspace_path)
    
    @abstractmethod
    async def handle_message(self, message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle a user message and return agent response"""
        pass
    
    @abstractmethod
    def can_handoff(self, conversation_history: List[Dict]) -> Optional[str]:
        """Check if agent should handoff to another agent"""
        pass
```

### 4. Chat Session Manager (Backend)

```python
# filepath: src/ai_whisperer/agents/session_manager.py
class AgentSession:
    """Manages a chat session with agent switching capabilities"""
    
    def __init__(self, registry: AgentRegistry, engine: Any):
        self.registry = registry
        self.engine = engine
        self.current_agent: Optional[Agent] = None
        self.agent_handlers: Dict[str, BaseAgentHandler] = {}
        self.conversation_history: List[Dict] = []
        self.agent_contexts: Dict[str, List[Dict]] = {}  # Per-agent conversation history
    
    async def switch_agent(self, agent_id: str) -> bool:
        """Switch to a different agent"""
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return False
        
        # Save current agent's context
        if self.current_agent:
            self.agent_contexts[self.current_agent.agent_id] = self.conversation_history.copy()
        
        # Load new agent
        self.current_agent = agent
        if agent_id in self.agent_contexts:
            self.conversation_history = self.agent_contexts[agent_id]
        else:
            self.conversation_history = []
        
        # Initialize handler if needed
        if agent_id not in self.agent_handlers:
            self.agent_handlers[agent_id] = self._create_handler(agent)
        
        return True
```

### 5. Frontend Components

```typescript
// filepath: src/frontend/src/components/AgentSelector.tsx
interface Agent {
  agentId: string;
  name: string;
  description: string;
  color: string;
  shortcut: string;
}

interface AgentSelectorProps {
  agents: Agent[];
  currentAgent: Agent | null;
  onAgentSelect: (agentId: string) => void;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  agents,
  currentAgent,
  onAgentSelect
}) => {
  // Component implementation
};
```

## TDD Implementation Checklist

### Phase 1: Core Agent Infrastructure

**Backend Tests First:**
- [x] `test_agent_registry.py`
  - [x] Test Agent dataclass creation
  - [x] Test loading default agents
  - [x] Test get_agent by ID
  - [x] Test list_agents functionality
  - [x] Test invalid agent ID handling

- [x] `test_agent_context_manager.py`
  - [x] Test context initialization for different agents
  - [x] Test workspace structure context loading
  - [x] Test schema context loading
  - [x] Test context filtering by agent needs

**Backend Implementation:**
- [x] Implement Agent dataclass
- [x] Implement AgentRegistry class
- [x] Implement AgentContextManager
- [x] Create default agent configurations (hardcoded, config override supported)
- [x] Create agent-specific prompt files

**Frontend Tests First:**
- [x] `AgentSelector.test.tsx`
  - [x] Test agent list rendering
  - [x] Test current agent highlighting
  - [x] Test agent selection callback
  - [x] Test keyboard shortcuts display

**Frontend Implementation:**
- [ ] Create AgentSelector component
- [x] Create AgentAvatar component
- [x] Update chat interface to show current agent
- [x] Add agent switching UI

### Phase 2: Patricia the Planner Agent

**Backend Tests First:**
- [x] `test_planner_handler.py`
  - [x] Test requirement extraction from conversation
  - [x] Test plan generation trigger detection
  - [x] Test plan preview generation
  - [x] Test plan confirmation flow
  - [x] Test plan JSON generation

- [x] `test_planner_tools.py`
  - [x] Test workspace analysis tools
  - [x] Test schema reading tools
  - [x] Test plan validation

**Backend Implementation:**
- [x] Create PlannerAgentHandler class
- [x] Implement conversation-based requirement extraction
- [ ] Adapt InitialPlanGenerator for conversational use
- [x] Create planner-specific tool wrappers
- [x] Add plan preview functionality

**Frontend Tests First:**
- [x] `PlanPreview.test.tsx`
  - [x] Test plan JSON rendering
  - [x] Test plan section expansion/collapse
  - [x] Test plan confirmation UI
  - [x] Test plan export functionality

**Frontend Implementation:**
- [x] Create PlanPreview component
- [x] Create PlanConfirmation dialog
- [x] Add plan visualization features
- [x] Update chat to handle plan responses

### Phase 3: Agent Session Management

**Backend Tests First:**
- [ ] `test_session_manager.py`
  - [ ] Test agent switching
  - [ ] Test conversation history preservation
  - [ ] Test agent handoff detection
  - [ ] Test multi-agent session state

- [ ] `test_agent_communication.py`
  - [ ] Test handoff protocol
  - [ ] Test context transfer between agents
  - [ ] Test agent recommendation system

**Backend Implementation:**
- [ ] Implement AgentSession class
- [ ] Create agent handoff protocol
- [ ] Implement conversation history management
- [ ] Add WebSocket support for agent switching

**Frontend Tests First:**
- [ ] `ChatSession.test.tsx`
  - [ ] Test agent switching UI
  - [ ] Test conversation history per agent
  - [ ] Test handoff notifications
  - [ ] Test agent transition animations

**Frontend Implementation:**
- [ ] Update ChatWindow for multi-agent support
- [ ] Create AgentTransition component
- [ ] Add agent-specific styling
- [ ] Implement handoff UI flow

### Phase 4: Tool Registry Integration

**Backend Tests First:**
- [ ] `test_agent_tools.py`
  - [ ] Test tool filtering by tags
  - [ ] Test tool availability per agent
  - [ ] Test tool execution with agent context
  - [ ] Test tool result formatting

**Backend Implementation:**
- [ ] Extend ToolRegistry with tag filtering
- [ ] Create agent-specific tool wrappers
- [ ] Implement tool permission system
- [ ] Add tool usage logging per agent

### Phase 5: API Endpoints

**Backend Tests First:**
- [ ] `test_agent_endpoints.py`
  - [ ] Test GET /api/agents endpoint
  - [ ] Test POST /api/session/switch-agent
  - [ ] Test GET /api/session/current-agent
  - [ ] Test POST /api/session/handoff

**Backend Implementation:**
- [ ] Create agent-related FastAPI endpoints
- [ ] Add session management endpoints
- [ ] Implement WebSocket agent events
- [ ] Add agent metrics endpoints

**Frontend Integration Tests:**
- [ ] Test full agent switching flow
- [ ] Test conversation persistence
- [ ] Test handoff user journey
- [ ] Test error handling

## Configuration Files

### Agent Configuration

```yaml
# filepath: src/ai_whisperer/agents/config/agents.yaml
agents:
  P:
    name: "Patricia the Planner"
    role: "planner"
    description: "Creates structured implementation plans from feature requests"
    tool_tags:
      - "filesystem"
      - "analysis"
      - "planning"
    prompt_file: "agent_planner.md"
    context_sources:
      - "workspace_structure"
      - "existing_schemas"
      - "recent_changes"
    color: "#4CAF50"
  
  T:
    name: "Tessa the Tester"
    role: "tester"
    description: "Generates comprehensive test suites and test plans"
    tool_tags:
      - "filesystem"
      - "testing"
      - "analysis"
    prompt_file: "agent_tester.md"
    context_sources:
      - "existing_tests"
      - "code_coverage"
      - "test_patterns"
    color: "#2196F3"
```

### Agent System Prompts

```markdown
# filepath: prompts/agent_planner.md
You are Pat the Planner, an AI assistant specialized in creating structured implementation plans for software features.

Your role is to:
1. Engage in conversation to understand feature requirements
2. Ask clarifying questions to gather all necessary details
3. Analyze the existing codebase structure
4. Create detailed, actionable implementation plans in JSON format

When creating plans, you should:
- Break down features into logical tasks
- Identify dependencies between tasks
- Suggest appropriate file locations
- Consider existing patterns in the codebase
- Include test requirements

Your responses should be friendly but professional. Guide users through the planning process step by step.
```

## Success Criteria

1. **Agent System**
   - [ ] Users can see available agents and their descriptions
   - [ ] Users can switch between agents with shortcuts or UI
   - [ ] Each agent maintains its own conversation context
   - [ ] Agents use only their assigned tools

2. **Pat the Planner**
   - [ ] Converts natural language requests to structured plans
   - [ ] Provides interactive requirement gathering
   - [ ] Generates valid plan JSON matching existing schema
   - [ ] Offers plan preview before finalization

3. **User Experience**
   - [ ] Clear visual indication of current agent
   - [ ] Smooth transitions between agents
   - [ ] Persistent conversation history per agent
   - [ ] Intuitive handoff suggestions

4. **Technical Requirements**
   - [ ] All tests pass before implementation
   - [ ] Type safety maintained throughout
   - [ ] WebSocket real-time updates
   - [ ] Proper error handling and recovery

## Future Agents

After successful implementation of Patricia the Planner, the following agents are planned:

- **Tessa the Tester**: Generates comprehensive test suites
- **Charlie the Coder**: Implements features from plans
- **Rachel the Reviewer**: Performs code reviews
- **Dana the Documenter**: Creates and updates documentation
- **Sam the Security Analyst**: Reviews security implications
- **Andy the Architect**: Helps with system design decisions

Each agent will follow the same pattern established with Patricia the Planner, ensuring consistency and