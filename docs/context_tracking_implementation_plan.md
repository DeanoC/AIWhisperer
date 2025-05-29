# Context Tracking Implementation Plan

## Phase 1: Core Context Tracking (Week 1)

### 1. Create Context Models

#### File: `ai_whisperer/context/context_item.py`
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal, Dict, Any, Tuple
import hashlib

@dataclass
class ContextItem:
    """Represents a single item in agent context."""
    id: str
    session_id: str
    agent_id: str
    type: Literal["file", "file_section", "directory_summary", "reference"]
    path: str
    content: str
    line_range: Optional[Tuple[int, int]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    file_modified_time: Optional[datetime] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_hash(self) -> str:
        """Calculate content hash for change detection."""
        return hashlib.sha256(self.content.encode()).hexdigest()
    
    def is_stale(self, current_modified_time: datetime) -> bool:
        """Check if context item is stale."""
        if self.file_modified_time and current_modified_time:
            return current_modified_time > self.file_modified_time
        return False
```

#### File: `ai_whisperer/context/context_manager.py`
```python
class AgentContextManager:
    """Manages context items for agents in a session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.contexts: Dict[str, List[ContextItem]] = {}
        self.max_context_size = 50000  # characters
        self.max_context_age = timedelta(hours=24)
    
    def add_file_reference(
        self, 
        agent_id: str, 
        file_path: str, 
        line_range: Optional[Tuple[int, int]] = None
    ) -> ContextItem:
        """Add a file reference to agent context."""
        pass
    
    def get_agent_context(self, agent_id: str) -> List[ContextItem]:
        """Get all context items for an agent."""
        pass
    
    def refresh_stale_items(self, agent_id: str) -> List[ContextItem]:
        """Refresh any stale context items."""
        pass
    
    def remove_item(self, agent_id: str, item_id: str) -> bool:
        """Remove a context item."""
        pass
```

### 2. Integrate with @ Mention System

#### Update: `interactive_server/handlers/workspace_handler.py`
Add context tracking to file reference handling:

```python
async def handle_file_reference(self, reference: str, session_id: str, agent_id: str):
    """Handle @ file reference and add to context."""
    # Parse reference (existing code)
    file_path, line_range = parse_file_reference(reference)
    
    # Load file content (existing code)
    content = await self.load_file_content(file_path, line_range)
    
    # NEW: Add to agent context
    context_manager = self.get_context_manager(session_id)
    context_item = context_manager.add_file_reference(
        agent_id=agent_id,
        file_path=file_path,
        line_range=line_range
    )
    
    # Return enriched response
    return {
        "content": content,
        "context_item_id": context_item.id,
        "metadata": context_item.metadata
    }
```

### 3. Add Storage Layer

#### File: `ai_whisperer/context/storage.py`
```python
class ContextStorage:
    """Handles persistence of context items."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "context.db"
        self._init_db()
    
    def save_context_item(self, item: ContextItem) -> None:
        """Save context item to storage."""
        pass
    
    def load_session_context(self, session_id: str) -> Dict[str, List[ContextItem]]:
        """Load all context for a session."""
        pass
    
    def update_item_access(self, item_id: str) -> None:
        """Update last accessed timestamp."""
        pass
```

### 4. Create API Endpoints

#### File: `interactive_server/handlers/context_handler.py`
```python
class ContextHandler:
    """Handles context-related API requests."""
    
    async def get_agent_context(self, request: GetContextRequest) -> GetContextResponse:
        """Get current context for an agent."""
        context_manager = self.get_context_manager(request.session_id)
        items = context_manager.get_agent_context(request.agent_id)
        
        return GetContextResponse(
            items=[self._serialize_item(item) for item in items],
            summary=self._create_summary(items)
        )
    
    async def refresh_context(self, request: RefreshContextRequest) -> RefreshContextResponse:
        """Refresh stale context items."""
        pass
    
    async def remove_context_item(self, request: RemoveContextRequest) -> RemoveContextResponse:
        """Remove item from context."""
        pass
```

### 5. Update Frontend Components

#### File: `frontend/src/components/ContextPanel.tsx`
```typescript
interface ContextPanelProps {
    sessionId: string;
    agentId: string;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({ sessionId, agentId }) => {
    const [contextItems, setContextItems] = useState<ContextItem[]>([]);
    const [loading, setLoading] = useState(true);
    
    // Fetch context items
    useEffect(() => {
        fetchAgentContext(sessionId, agentId);
    }, [sessionId, agentId]);
    
    return (
        <div className="context-panel">
            <h3>Agent Context</h3>
            <div className="context-items">
                {contextItems.map(item => (
                    <ContextItemCard key={item.id} item={item} />
                ))}
            </div>
        </div>
    );
};
```

## Phase 2: File Watching & Freshness (Week 2)

### 1. Implement File Watcher
- Use watchdog library for file system monitoring
- Track modifications to files in context
- Queue refresh operations

### 2. Add Freshness Indicators
- Calculate staleness based on file modification times
- Add visual indicators (green/yellow/red)
- Show time since last refresh

### 3. Implement Auto-refresh
- Configurable auto-refresh policies
- Batch refresh operations
- Notify UI of updates via WebSocket

## Phase 3: Advanced Features (Week 3)

### 1. Smart Section Loading
- AST parsing for code files
- Function/class extraction
- Relevant section identification

### 2. Context Analytics
- Track context usage patterns
- Measure context effectiveness
- Generate insights

### 3. Context Templates
- Save/load context sets
- Share between sessions
- Quick context switching

## Testing Strategy

### Unit Tests
- Context item creation and validation
- Context manager operations
- Storage layer functionality
- Freshness calculations

### Integration Tests
- @ mention to context flow
- File watching integration
- API endpoint testing
- WebSocket notifications

### E2E Tests
- Full user flow from @ mention to context display
- Refresh operations
- Context panel interactions

## Rollout Plan

1. **Internal Testing**: Deploy to development environment
2. **Beta Testing**: Limited rollout with monitoring
3. **Gradual Rollout**: Phased deployment with feature flags
4. **Full Release**: Enable for all users

## Success Metrics

- Context loading time < 200ms
- Stale context detection accuracy > 95%
- User engagement with context panel
- Reduction in stale file issues
- Agent performance improvement

## Risk Mitigation

### Performance
- Implement caching for frequently accessed files
- Limit context size per agent
- Use pagination for large context lists

### Storage
- Implement context expiration
- Archive old context data
- Monitor storage usage

### Security
- Validate all file paths
- Respect workspace boundaries
- Audit context access

## Next Steps

1. Review and approve design
2. Set up development branch
3. Create context model classes
4. Implement storage layer
5. Add @ mention integration
6. Create basic UI components
7. Test and iterate