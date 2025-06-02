# AI Whisperer UI Improvements Implementation Plan

## Overview
This document outlines the implementation plan for four key UI improvements to the AI Whisperer application.

## Priority Order & Task Breakdown

### TASK 1: Fix Chat UI Message Box (HIGH PRIORITY)
**Goal:** Replace single-line input with multi-line textarea supporting word wrap

**Current State:**
- `MessageInput.tsx` uses `<input type="text">` (line ~47)
- Single scrolling line, no word wrap
- Has command suggestions and @ symbol file picker integration

**Implementation Steps:**
1. Replace `<input>` with `<textarea>` in MessageInput component
2. Adjust styling for multi-line display
3. Handle Enter key behavior (Shift+Enter for new line, Enter to send)
4. Maintain existing @ symbol file picker functionality
5. Preserve command suggestions system
6. Test word wrap and scrolling behavior

**Files to Modify:**
- `/frontend/src/MessageInput.tsx`
- Possibly `/frontend/src/styles/` (CSS adjustments)

**Estimated Effort:** 2-4 hours

---

### TASK 2: Connect Plan Viewer to Real Plans (MEDIUM PRIORITY)
**Goal:** Connect JSONPlanView component to real plans from .WHISPER folder

**Current State:**
- `JSONPlanView.tsx` uses hardcoded placeholder data
- Backend has robust plan management tools (`list_plans_tool.py`, `read_plan_tool.py`)
- Plans stored in `.WHISPER/plans/` with `in_progress/` and `archived/` subdirectories

**Implementation Steps:**
1. Create API endpoint to fetch plan list from backend
2. Create API endpoint to fetch individual plan content
3. Update JSONPlanView to fetch real plan data
4. Add loading states and error handling
5. Implement plan refresh functionality
6. Add plan status indicators (in_progress vs archived)

**Files to Modify:**
- `/frontend/src/components/JSONPlanView.tsx`
- `/interactive_server/handlers/` (new plan API handlers)
- Backend routing configuration

**Backend Integration Points:**
- Utilize existing `list_plans_tool.py` and `read_plan_tool.py`
- Create JSON-RPC handlers for plan operations
- Handle workspace context for plan access

**Estimated Effort:** 6-8 hours

---

### TASK 3: Implement Browse Button Functionality (MEDIUM PRIORITY)
**Goal:** Hook up browse button in create workspace dialog to select project paths

**Current State:**
- `ProjectSelector.tsx` has browse button with placeholder alert
- Existing `FilePicker` component could be enhanced
- Backend has `WorkspaceHandler` with file operations

**Implementation Steps:**
1. Create directory browser component (or enhance FilePicker)
2. Add directory selection API endpoint
3. Replace placeholder alert with real browser
4. Implement path validation
5. Update workspace creation flow
6. Add recent/favorite directories feature

**Files to Modify:**
- `/frontend/src/components/ProjectSelector.tsx`
- `/frontend/src/components/FilePicker.tsx` (enhancement)
- `/interactive_server/handlers/workspace_handler.py` (new endpoints)

**Estimated Effort:** 4-6 hours

---

### TASK 4: Implement Real Terminal (LOWER PRIORITY)
**Goal:** Make terminal placeholder in left column a real bash terminal

**Current State:**
- `Sidebar.tsx` has terminal navigation item pointing to '/terminal' path
- No existing terminal component found
- Need to implement terminal emulator

**Implementation Steps:**
1. Research terminal emulator libraries (xterm.js recommended)
2. Create Terminal component with WebSocket connection
3. Implement backend terminal session handler
4. Add terminal route to frontend routing
5. Handle terminal lifecycle (create/destroy sessions)
6. Add terminal tabs for multiple sessions

**Files to Create/Modify:**
- `/frontend/src/components/Terminal.tsx` (new)
- `/frontend/src/App.tsx` (add route)
- `/interactive_server/handlers/terminal_handler.py` (new)
- `/frontend/package.json` (add xterm.js dependency)

**Technical Dependencies:**
- xterm.js for terminal emulation
- WebSocket connection for real-time communication
- Backend process management for shell sessions

**Estimated Effort:** 8-12 hours

---

## Implementation Sequence

### Phase 1: Quick Wins (High Impact, Low Effort)
1. **Chat UI Message Box Fix** - Most immediate user impact
2. **Browse Button Functionality** - Essential for workspace management

### Phase 2: Core Features (Medium Effort, High Value)
3. **Plan Viewer Integration** - Connects UI to core functionality

### Phase 3: Advanced Features (High Effort, Nice-to-Have)
4. **Real Terminal Implementation** - Complex but valuable for power users

---

## Technical Considerations

### Frontend Architecture
- React TypeScript components
- Existing state management patterns
- Monaco editor integration (for plan viewer)
- WebSocket connections (for terminal)

### Backend Integration
- JSON-RPC handler pattern
- Existing tool system in `ai_whisperer/tools/`
- Workspace context management
- File system operations

### Dependencies to Add
- `xterm.js` and `@xterm/addon-fit` for terminal
- Possibly `react-textarea-autosize` for better textarea handling
- Directory tree component library (if not building custom)

### Testing Strategy
- Unit tests for new components
- Integration tests for API endpoints
- Manual testing for UI interactions
- Cross-browser compatibility testing

---

## Risk Assessment

### Low Risk
- Chat UI message box fix (isolated change)
- Browse button implementation (existing patterns)

### Medium Risk
- Plan viewer integration (depends on backend stability)

### High Risk
- Terminal implementation (complex WebSocket handling, process management)

---

## Success Metrics

1. **Chat UI:** Users can type multi-line messages with proper word wrap
2. **Plan Viewer:** Users can see and navigate real plans from their workspace
3. **Browse Button:** Users can select project directories through native file browser
4. **Terminal:** Users can execute shell commands in embedded terminal

---

## Next Steps

1. Review and approve this implementation plan
2. Set up development environment
3. Begin with Phase 1 tasks (Chat UI and Browse Button)
4. Create feature branches for each task
5. Implement in priority order with testing at each step
