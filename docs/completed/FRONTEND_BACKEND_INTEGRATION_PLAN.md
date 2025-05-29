# Frontend-Backend Integration Plan

## Overview
This plan outlines the integration between the refactored backend session manager and the React frontend to achieve the UI design shown in the mockups.

## Current State Analysis

### Backend (Refactored)
- **Session Manager**: Handles multiple concurrent sessions with isolated agent contexts
- **Agent System**: Modular agents (Planner, Tester, Developer, Reviewer) with specialized handlers
- **JSON-RPC Methods**: 
  - `agent.list`, `session.switch_agent`, `session.current_agent`, `session.handoff`
  - `startSession`, `stopSession`, `sendUserMessage`
- **WebSocket**: Real-time communication with notifications

### Frontend (Current)
- Basic chat interface without agent personas
- Command-based agent switching via `/session.switch_agent`
- Simple message display without rich formatting
- Missing specialized views and context panels

### Target UI (From Mockups)
- Three-column layout with agent sidebar and context panel
- Rich content displays (JSON editor, code diffs, test results)
- Agent-specific styling and interactions
- Specialized views for different development tasks

## Implementation Phases

### Phase 1: Update WebSocket Integration (Week 1)
**Goal**: Align frontend with refactored backend API

1. **Update AIService class**:
   ```typescript
   // New methods to add
   async listAgents(): Promise<Agent[]>
   async switchAgent(agentId: string): Promise<void>
   async getCurrentAgent(): Promise<string>
   async handoffToAgent(agentId: string, context: any): Promise<void>
   ```

2. **Replace command-based switching**:
   - Update all agent switching calls to use new methods
   - Remove command parsing logic from backend
   - Add proper error handling for agent operations

3. **Add agent state synchronization**:
   - Fetch current agent on session start
   - Listen for agent change notifications
   - Update UI state to match backend

### Phase 2: Implement Agent System UI (Week 1-2)
**Goal**: Create the multi-agent chat experience

1. **AgentSidebar Component**:
   - Display all available agents with avatars
   - Show active/inactive status
   - Click-to-switch functionality
   - Agent role descriptions on hover

2. **Enhanced Message Display**:
   - Agent-specific message bubbles with colors
   - Avatar display in messages
   - "Talking to: [Agent]" indicator
   - Rich content rendering (code, JSON, etc.)

3. **Agent Context Management**:
   - Track conversation history per agent
   - Maintain agent-specific state
   - Handle agent handoffs smoothly

### Phase 3: Create Specialized Views (Week 2-3)
**Goal**: Implement view components for different content types

1. **View Router System**:
   - Create view switching mechanism
   - Maintain view state across agent switches
   - Implement view-specific toolbars

2. **JSONPlanView Component**:
   - Tree navigation for JSON structure
   - Line-numbered editor with syntax highlighting
   - Validation status indicators
   - Save/export functionality

3. **CodeChangesView Component**:
   - File list with change indicators
   - Side-by-side diff viewer
   - Syntax highlighting for multiple languages
   - Accept/reject buttons for changes

4. **TestResultsView Component**:
   - Hierarchical test suite display
   - Pass/fail/skip statistics
   - Detailed error messages
   - Re-run test functionality

### Phase 4: Layout and Context Panel (Week 3-4)
**Goal**: Implement the three-column responsive layout

1. **Responsive Layout System**:
   - Flexbox/Grid based three-column layout
   - Collapsible sidebars for mobile
   - Resizable panels
   - Persistent layout preferences

2. **ContextPanel Component**:
   - Dynamic sections based on current view
   - File browser with navigation
   - Related documentation links
   - Progress tracking displays

3. **Theme System**:
   - Agent-specific color schemes
   - Dark/light mode support
   - Consistent styling across components

### Phase 5: Integration and Polish (Week 4)
**Goal**: Complete integration and add finishing touches

1. **Full Integration Testing**:
   - Test all agent interactions
   - Verify view switching behavior
   - Ensure proper WebSocket handling
   - Test error scenarios

2. **Performance Optimization**:
   - Implement lazy loading for views
   - Optimize WebSocket message handling
   - Add proper loading states
   - Implement message pagination

3. **User Experience Enhancements**:
   - Keyboard shortcuts for agent switching
   - Drag-and-drop file support
   - Copy/paste functionality in editors
   - Contextual help tooltips

## Technical Implementation Details

### State Management
```typescript
interface AppState {
  session: SessionState
  agents: AgentState
  views: ViewState
  ui: UIState
}

interface AgentState {
  available: Agent[]
  current: string
  conversations: Map<string, Message[]>
  contexts: Map<string, AgentContext>
}

interface ViewState {
  current: 'chat' | 'json' | 'code' | 'test'
  data: ViewData
  history: ViewHistoryEntry[]
}
```

### Component Architecture
```
App
├── Layout
│   ├── AgentSidebar
│   │   └── AgentCard
│   ├── MainContent
│   │   ├── ChatView
│   │   │   ├── MessageList
│   │   │   └── MessageInput
│   │   ├── JSONPlanView
│   │   ├── CodeChangesView
│   │   └── TestResultsView
│   └── ContextPanel
│       ├── FileExplorer
│       ├── Documentation
│       └── Progress
└── StatusBar
```

### WebSocket Message Flow
1. **Agent Switch Request**:
   ```
   Frontend → { method: "session.switch_agent", params: { agent_id: "P" } }
   Backend → { result: { success: true, agent: "P" } }
   Backend → { method: "notification", params: { type: "agent_changed", agent: "P" } }
   ```

2. **Rich Content Message**:
   ```
   Backend → { 
     method: "notification", 
     params: { 
       type: "ai_message", 
       agent: "D",
       content: { 
         type: "code_changes",
         files: [...],
         diffs: [...]
       }
     }
   }
   ```

## Testing Strategy

### Unit Tests
- Component rendering tests
- State management logic
- WebSocket message handling
- View switching behavior

### Integration Tests
- Frontend-Backend communication
- Agent switching workflows
- Content rendering accuracy
- Error handling scenarios

### E2E Tests
- Complete user workflows
- Multi-agent conversations
- View interactions
- Performance under load

## Rollout Plan

1. **Alpha Release** (Internal Testing):
   - Core agent switching functionality
   - Basic view components
   - Limited to development team

2. **Beta Release** (Select Users):
   - All views implemented
   - Context panel functional
   - Performance optimizations

3. **Production Release**:
   - Full feature parity with mockups
   - Comprehensive testing complete
   - Documentation updated

## Success Metrics

- Agent switch time < 100ms
- Message rendering < 50ms
- View switch time < 200ms
- WebSocket reconnection < 2s
- 95% uptime for real-time features

## Risk Mitigation

1. **WebSocket Stability**:
   - Implement robust reconnection logic
   - Queue messages during disconnection
   - Provide offline mode capabilities

2. **Performance**:
   - Virtual scrolling for long conversations
   - Lazy load view components
   - Debounce frequent operations

3. **Browser Compatibility**:
   - Test on major browsers
   - Provide polyfills as needed
   - Graceful degradation for older browsers