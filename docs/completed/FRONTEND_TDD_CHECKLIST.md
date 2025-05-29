# Frontend TDD Implementation Checklist

## Phase 1: WebSocket/JSON-RPC Integration Tests First

### AIService Agent Methods
- [ ] Write test: `aiService.listAgents()` returns array of agents
- [ ] Write test: `aiService.switchAgent(agentId)` sends correct JSON-RPC
- [ ] Write test: `aiService.getCurrentAgent()` returns current agent ID
- [ ] Write test: `aiService.handoffToAgent(agentId, context)` with context
- [ ] Write test: Handle agent not found errors
- [ ] Write test: Handle session not initialized errors
- [ ] Implement `aiService` agent methods to pass tests
- [ ] Write test: Agent state sync on reconnection
- [ ] Implement reconnection agent sync

### WebSocket Agent Notifications
- [ ] Write test: Handle `agent_changed` notification
- [ ] Write test: Handle `agent_handoff` notification
- [ ] Write test: Handle `agent_context_update` notification
- [ ] Implement notification handlers in `useWebSocket`
- [ ] Write test: Queue notifications during disconnection
- [ ] Implement notification queueing

### Remove Legacy Command System
- [ ] Write test: Verify no `/session.switch_agent` commands sent
- [ ] Remove command-based agent switching from `App.tsx`
- [ ] Remove command parsing from `ChatWindow.tsx`
- [ ] Update all agent switch calls to use new methods

## Phase 2: Agent System Components

### AgentSidebar Component
- [ ] Write test: Renders list of agents from `agent.list`
- [ ] Write test: Shows current agent as active
- [ ] Write test: Click agent triggers `switchAgent`
- [ ] Write test: Disabled during agent switch
- [ ] Write test: Shows agent descriptions on hover
- [ ] Write test: Keyboard navigation (up/down arrows)
- [ ] Implement `AgentSidebar` component
- [ ] Write test: Agent status indicators (online/busy/offline)
- [ ] Implement status indicators

### AgentAvatar Component Enhancement
- [ ] Write test: Renders with agent-specific colors
- [ ] Write test: Shows agent initial or icon
- [ ] Write test: Different sizes (small/medium/large)
- [ ] Write test: Active state styling
- [ ] Write test: Loading state animation
- [ ] Enhance `AgentAvatar` component

### AgentMessageBubble Component
- [ ] Write test: Agent-specific background colors
- [ ] Write test: Avatar positioning (left for agent, right for user)
- [ ] Write test: Timestamp display
- [ ] Write test: "Thinking" indicator for streaming
- [ ] Write test: Code block syntax highlighting
- [ ] Write test: Collapsible long messages
- [ ] Implement `AgentMessageBubble` component

### MessageInput Enhancement
- [ ] Write test: Shows "Talking to: [Agent Name]"
- [ ] Write test: Agent-specific placeholder text
- [ ] Write test: Quick agent switch dropdown
- [ ] Write test: @ mention for agent switching
- [ ] Update `MessageInput` component

## Phase 3: View System Infrastructure

### ViewRouter Component
- [ ] Write test: Default view is 'chat'
- [ ] Write test: Switch between views maintains state
- [ ] Write test: View-specific route parameters
- [ ] Write test: Keyboard shortcuts (Ctrl+1,2,3,4)
- [ ] Write test: View transition animations
- [ ] Implement `ViewRouter` component

### ViewContext Hook
- [ ] Write test: `useViewContext` provides current view
- [ ] Write test: `setView` changes active view
- [ ] Write test: View history navigation
- [ ] Write test: View-specific data storage
- [ ] Implement `useViewContext` hook

## Phase 4: Specialized View Components

### JSONPlanView Component
- [ ] Write test: Renders JSON with syntax highlighting
- [ ] Write test: Collapsible tree nodes
- [ ] Write test: Line numbers display
- [ ] Write test: Search within JSON
- [ ] Write test: Edit mode toggle
- [ ] Write test: Validation errors display
- [ ] Write test: Save changes back to session
- [ ] Write test: Export as file
- [ ] Implement `JSONPlanView` component

### CodeChangesView Component
- [ ] Write test: File list with change indicators
- [ ] Write test: Click file shows diff
- [ ] Write test: Syntax highlighting by file type
- [ ] Write test: Side-by-side diff view
- [ ] Write test: Unified diff view toggle
- [ ] Write test: Accept/reject change buttons
- [ ] Write test: Add review comments
- [ ] Write test: Collapse unchanged sections
- [ ] Implement `CodeChangesView` component

### TestResultsView Component
- [ ] Write test: Test suite hierarchy display
- [ ] Write test: Pass/fail/skip counts
- [ ] Write test: Expand to show test details
- [ ] Write test: Error message formatting
- [ ] Write test: Stack trace display
- [ ] Write test: Re-run single test
- [ ] Write test: Re-run failed tests
- [ ] Write test: Filter by status
- [ ] Implement `TestResultsView` component

## Phase 5: Layout Components

### ThreeColumnLayout Component
- [ ] Write test: Renders three columns
- [ ] Write test: Collapse left sidebar
- [ ] Write test: Collapse right sidebar
- [ ] Write test: Responsive breakpoints
- [ ] Write test: Drag to resize panels
- [ ] Write test: Persist layout preferences
- [ ] Write test: Keyboard shortcuts for panel toggle
- [ ] Implement `ThreeColumnLayout` component

### ContextPanel Component
- [ ] Write test: Shows relevant files for current view
- [ ] Write test: Documentation links section
- [ ] Write test: Progress indicators
- [ ] Write test: Dynamic content based on agent
- [ ] Write test: File navigation triggers file open
- [ ] Write test: Search within context
- [ ] Implement `ContextPanel` component

### FileExplorer Component
- [ ] Write test: Directory tree structure
- [ ] Write test: File type icons
- [ ] Write test: Expand/collapse folders
- [ ] Write test: File selection
- [ ] Write test: Multi-select with Ctrl/Shift
- [ ] Write test: Right-click context menu
- [ ] Implement `FileExplorer` component

## Phase 6: Rich Content Components

### InlineJSONDisplay Component
- [ ] Write test: Inline JSON in messages
- [ ] Write test: Expand/collapse toggle
- [ ] Write test: Copy button
- [ ] Write test: Syntax highlighting
- [ ] Write test: Max height with scroll
- [ ] Implement `InlineJSONDisplay` component

### CodeBlock Component
- [ ] Write test: Language detection
- [ ] Write test: Syntax highlighting
- [ ] Write test: Line numbers optional
- [ ] Write test: Copy button
- [ ] Write test: Language label
- [ ] Write test: Word wrap toggle
- [ ] Implement enhanced `CodeBlock` component

### ProgressBar Component
- [ ] Write test: Percentage display
- [ ] Write test: Animated fill
- [ ] Write test: Color by status
- [ ] Write test: Label text
- [ ] Write test: Indeterminate state
- [ ] Implement `ProgressBar` component

## Phase 7: State Management

### Agent State Management
- [ ] Write test: Agent reducer handles LIST_AGENTS
- [ ] Write test: Agent reducer handles SET_CURRENT_AGENT
- [ ] Write test: Agent reducer handles AGENT_HANDOFF
- [ ] Write test: Conversation history per agent
- [ ] Write test: Agent context persistence
- [ ] Implement agent state reducer

### View State Management
- [ ] Write test: View reducer handles SET_VIEW
- [ ] Write test: View reducer handles VIEW_DATA_UPDATE
- [ ] Write test: View history tracking
- [ ] Write test: View-specific state isolation
- [ ] Implement view state reducer

### Session State Enhancement
- [ ] Write test: Session includes current agent
- [ ] Write test: Session includes view state
- [ ] Write test: Session persistence to localStorage
- [ ] Write test: Session restoration on reload
- [ ] Enhance session state management

## Phase 8: Integration Tests

### Agent Switching Flow
- [ ] Write test: Full agent switch flow
- [ ] Write test: Message history preservation
- [ ] Write test: Context handoff between agents
- [ ] Write test: UI updates during switch

### View Switching Flow
- [ ] Write test: Chat → JSON view with data
- [ ] Write test: JSON → Code view transition
- [ ] Write test: View state preservation
- [ ] Write test: Keyboard shortcut navigation

### Error Scenarios
- [ ] Write test: WebSocket disconnection handling
- [ ] Write test: Agent unavailable error
- [ ] Write test: Session timeout recovery
- [ ] Write test: Invalid JSON handling

### Performance Tests
- [ ] Write test: Message rendering < 16ms
- [ ] Write test: View switch < 100ms
- [ ] Write test: Large JSON rendering
- [ ] Write test: 1000+ message history

## Phase 9: Polish & UX

### Animations
- [ ] Write test: Message appear animation
- [ ] Write test: Agent switch transition
- [ ] Write test: View slide transitions
- [ ] Write test: Loading skeletons
- [ ] Implement animations with Framer Motion

### Keyboard Shortcuts
- [ ] Write test: Ctrl+K for command palette
- [ ] Write test: Alt+1-4 for agents
- [ ] Write test: Ctrl+Enter to send
- [ ] Write test: Escape to close panels
- [ ] Implement keyboard shortcut system

### Accessibility
- [ ] Write test: Screen reader announcements
- [ ] Write test: Focus management
- [ ] Write test: ARIA labels
- [ ] Write test: Keyboard-only navigation
- [ ] Implement accessibility features

### Dark Mode
- [ ] Write test: Theme toggle
- [ ] Write test: System preference detection
- [ ] Write test: Theme persistence
- [ ] Write test: Agent colors in dark mode
- [ ] Implement dark mode support

## Phase 10: Final Integration

### Full E2E Tests
- [ ] Write Playwright test: Complete agent conversation
- [ ] Write Playwright test: Multi-view workflow
- [ ] Write Playwright test: File editing flow
- [ ] Write Playwright test: Test execution flow

### Performance Optimization
- [ ] Implement React.memo for components
- [ ] Add useMemo/useCallback where needed
- [ ] Implement virtual scrolling
- [ ] Add lazy loading for views

### Documentation
- [ ] Update component documentation
- [ ] Create Storybook stories
- [ ] Write integration guide
- [ ] Update README with new features

## Completion Checklist
- [ ] All tests passing
- [ ] No console errors/warnings
- [ ] Lighthouse score > 90
- [ ] Bundle size < 500KB
- [ ] Works in Chrome, Firefox, Safari
- [ ] Mobile responsive
- [ ] Matches mockup designs