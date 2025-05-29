# Agent Context Tracking Design

## Overview

This document outlines the design for an agent context tracking system that:
1. Automatically loads @ mentioned files into agent context
2. Tracks which files (and portions) are in an agent's context
3. Manages context freshness to prevent stale file data issues
4. Provides context history and analytics

## Problem Statement

### Current Issues
- Agents work with file content that may become stale during long conversations
- No visibility into what files/sections an agent is "aware of"
- No automatic refresh of file content when files change
- Context can become cluttered with outdated information
- Difficult to debug why an agent made certain decisions

### Goals
- Automatic context management for @ mentioned files
- Track context lifetime and freshness
- Provide UI to show current agent context
- Enable context refresh strategies
- Support partial file context (specific sections/functions)

## Proposed Architecture

### 1. Context Tracking System

```python
class ContextItem:
    """Represents a single item in agent context."""
    id: str
    type: Literal["file", "file_section", "directory", "command_output"]
    path: str
    content: str
    line_range: Optional[Tuple[int, int]]  # For file sections
    timestamp: datetime
    last_modified: datetime  # File's last modified time
    hash: str  # Content hash for change detection
    metadata: Dict[str, Any]  # Additional info

class AgentContext:
    """Manages context for a single agent."""
    agent_id: str
    items: List[ContextItem]
    max_size: int  # Token/character limit
    max_age: timedelta  # How old context can be
    
    def add_item(self, item: ContextItem) -> None
    def remove_item(self, item_id: str) -> None
    def refresh_stale_items(self) -> List[ContextItem]
    def get_summary(self) -> ContextSummary
    def export_context(self) -> Dict[str, Any]
```

### 2. Context Loading Strategies

#### Automatic Loading
When a user mentions a file with @:
1. Parse the reference (file path, line numbers if specified)
2. Load content into context with metadata
3. Track the file for changes
4. Add to agent's context history

#### Smart Section Loading
For large files:
- Load only relevant sections (functions, classes)
- Use AST parsing for code files
- Support line range specifications (@file.py:10-50)
- Compress/summarize non-critical sections

#### Context Refresh
- Monitor files for changes using file watchers
- Refresh context when files are modified
- Mark stale content visually in UI
- Option for manual refresh

### 3. Database Schema

```sql
-- Context items table
CREATE TABLE context_items (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    path TEXT NOT NULL,
    content TEXT,
    line_start INTEGER,
    line_end INTEGER,
    file_hash VARCHAR(64),
    created_at TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP,
    last_modified TIMESTAMP,
    metadata JSONB,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Context access log
CREATE TABLE context_access_log (
    id UUID PRIMARY KEY,
    context_item_id UUID NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    access_type VARCHAR(50), -- 'read', 'refresh', 'expire'
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (context_item_id) REFERENCES context_items(id)
);

-- Indexes for performance
CREATE INDEX idx_context_session_agent ON context_items(session_id, agent_id);
CREATE INDEX idx_context_path ON context_items(path);
CREATE INDEX idx_context_created ON context_items(created_at);
```

### 4. API Endpoints

```typescript
// Add file to context
POST /api/context/add
{
  "session_id": "uuid",
  "agent_id": "string",
  "type": "file",
  "path": "src/main.py",
  "line_range": [10, 50]  // optional
}

// Get agent context
GET /api/context/{session_id}/{agent_id}
Response: {
  "items": [...],
  "summary": {
    "total_items": 5,
    "total_size": 15000,
    "oldest_item": "2024-01-29T10:00:00Z",
    "stale_items": 2
  }
}

// Refresh stale context
POST /api/context/refresh
{
  "session_id": "uuid",
  "agent_id": "string",
  "item_ids": ["uuid1", "uuid2"]  // optional, refreshes all if empty
}

// Get context history
GET /api/context/history/{session_id}/{agent_id}
```

### 5. UI Components

#### Context Panel
```typescript
interface ContextPanelProps {
  sessionId: string;
  agentId: string;
  onRefresh: (itemId?: string) => void;
  onRemove: (itemId: string) => void;
}

// Shows:
// - List of files/sections in context
// - Freshness indicators (green/yellow/red)
// - File size and last modified
// - Quick actions (refresh, remove, view)
```

#### Context Timeline
```typescript
interface ContextTimelineProps {
  sessionId: string;
  agentId: string;
  timeRange: [Date, Date];
}

// Visualizes:
// - When files were added/removed
// - File modifications over time
// - Context size changes
// - Agent switches
```

### 6. Implementation Phases

#### Phase 1: Core Tracking
- [ ] Create context tracking data models
- [ ] Implement basic add/remove/list operations
- [ ] Add database tables and migrations
- [ ] Create API endpoints

#### Phase 2: @ Mention Integration
- [ ] Hook into @ mention system
- [ ] Auto-load mentioned files
- [ ] Support line range syntax
- [ ] Add to agent context automatically

#### Phase 3: Freshness Management
- [ ] Implement file watching
- [ ] Add staleness detection
- [ ] Create refresh mechanisms
- [ ] Add freshness indicators to UI

#### Phase 4: UI Components
- [ ] Create context panel component
- [ ] Add to agent inspector
- [ ] Implement context timeline
- [ ] Add context analytics

#### Phase 5: Advanced Features
- [ ] Smart section extraction
- [ ] Context compression/summarization
- [ ] Context templates
- [ ] Cross-agent context sharing

## Usage Examples

### Example 1: Auto-loading @ mentioned file
```typescript
// User message: "Can you review @src/main.py:45-90 and suggest improvements?"

// System automatically:
1. Extracts file reference: src/main.py, lines 45-90
2. Loads content into context
3. Tracks file for changes
4. Shows in context panel
```

### Example 2: Handling stale context
```typescript
// File modified externally while in agent context

// System:
1. Detects file change via file watcher
2. Marks context item as stale
3. Shows yellow indicator in UI
4. Offers one-click refresh
5. Can auto-refresh based on settings
```

### Example 3: Context history view
```typescript
// Developer wants to see what files agent used

// UI shows:
- Timeline of all files accessed
- Duration each file was in context  
- Modifications/refreshes
- Context size over time
```

## Benefits

1. **Transparency**: Users can see exactly what files/content agents are working with
2. **Freshness**: Prevents agents from using outdated file content
3. **Efficiency**: Manages context size automatically
4. **Debugging**: Helps understand agent behavior through context history
5. **Control**: Users can manually manage context when needed

## Technical Considerations

### Performance
- Index frequently accessed paths
- Cache file content where appropriate
- Lazy load context items in UI
- Batch refresh operations

### Security
- Validate file access permissions
- Sanitize file paths
- Respect workspace boundaries
- Audit context access

### Scalability
- Implement context size limits
- Archive old context items
- Use efficient storage for large files
- Consider content deduplication

## Future Enhancements

1. **Smart Context Loading**
   - ML-based relevance scoring
   - Automatic related file discovery
   - Context recommendations

2. **Context Templates**
   - Save/restore context sets
   - Share contexts between sessions
   - Context presets for common tasks

3. **Advanced Analytics**
   - Context usage patterns
   - File access heatmaps
   - Agent performance correlation

4. **Integration Features**
   - Git integration (show diffs)
   - IDE synchronization
   - External tool context sharing