# @ Command File Reference Technical Specification

## Overview
The @ command system allows users to reference files in their messages, similar to Claude Code's functionality. This provides context-aware file inclusion for AI agents.

## User Experience Flow

### 1. Triggering @ Command
```
User types: "Can you help me fix the bug in @"
            ↓
    FilePicker appears
            ↓
User selects: "ai_whisperer/main.py"
            ↓
Message shows: "Can you help me fix the bug in @ai_whisperer/main.py"
```

### 2. Keyboard Navigation
- **@** - Trigger file picker
- **↑↓** - Navigate file list
- **Enter** - Select file
- **Esc** - Cancel selection
- **Tab** - Expand/collapse directories
- **Ctrl+Enter** - Select and add line range

### 3. Mouse Interaction
- Click to select file
- Double-click to select and close
- Hover for file preview
- Right-click for context menu (add with line range, copy path)

## Technical Implementation

### Frontend Components

#### Enhanced MessageInput Component
```typescript
interface MessageInputState {
  value: string;
  showFilePicker: boolean;
  cursorPosition: number;
  atCommandStart: number | null;
  searchQuery: string;
}

// Detect @ character
const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
  const { value, selectionStart } = e.target;
  
  // Check if @ was just typed
  if (value[selectionStart - 1] === '@') {
    setShowFilePicker(true);
    setAtCommandStart(selectionStart - 1);
  }
  
  // Update search query if picker is open
  if (showFilePicker && atCommandStart !== null) {
    const query = value.slice(atCommandStart + 1, selectionStart);
    setSearchQuery(query);
  }
};
```

#### FilePicker Component Structure
```typescript
interface FilePickerProps {
  isOpen: boolean;
  searchQuery: string;
  onSelect: (file: FileReference) => void;
  onCancel: () => void;
  anchorPosition: { x: number; y: number };
}

interface FileReference {
  path: string;
  name: string;
  type: 'file' | 'directory';
  preview?: string;
  lineCount?: number;
}
```

### Backend Support

#### File Search Endpoint
```python
@router.post("/workspace.searchFiles")
async def search_files(
    query: str,
    limit: int = 20,
    file_types: Optional[List[str]] = None
) -> List[FileInfo]:
    """
    Search files with fuzzy matching
    - Score by relevance
    - Filter by file types
    - Return with previews
    """
```

#### File Preview Endpoint
```python
@router.post("/workspace.getFilePreview")
async def get_file_preview(
    file_path: str,
    lines: int = 5
) -> FilePreview:
    """
    Get first N lines of file for preview
    """
```

### Message Processing

#### File Reference Format in Messages
```json
{
  "type": "message",
  "content": "Fix the bug in @{file:ai_whisperer/main.py}",
  "fileReferences": [
    {
      "id": "ref-1",
      "path": "ai_whisperer/main.py",
      "startLine": null,
      "endLine": null
    }
  ]
}
```

#### AI Context Enhancement
When processing messages with file references:
1. Extract file references from message
2. Load file contents using FileReferenceTool
3. Add to AI context with clear markers
4. Process enhanced prompt

### Advanced Features

#### Line Range Selection
```
@ai_whisperer/main.py:10-25  # Lines 10-25
@config.yaml:15               # Line 15 only
@README.md                    # Entire file
```

#### Multiple File References
```
"Compare @frontend/App.tsx with @frontend/App.test.tsx"
```

#### Smart Suggestions
- Recently accessed files
- Files in current directory
- Files related to current context
- Files modified recently

## State Management

### Frontend State
```typescript
interface FilePickerState {
  recentFiles: FileReference[];
  searchResults: FileReference[];
  selectedIndex: number;
  expandedPaths: Set<string>;
  loading: boolean;
  error: string | null;
}
```

### Session State
```python
class SessionFileContext:
    referenced_files: List[str]
    file_access_count: Dict[str, int]
    last_accessed: Dict[str, datetime]
```

## Performance Optimizations

1. **Debounced Search** - 150ms delay on typing
2. **Virtualized List** - For large file lists
3. **Cached File Tree** - Refresh on file system changes
4. **Lazy Loading** - Load directory contents on expand
5. **Preview Caching** - Cache file previews for 5 minutes

## Error Handling

### User-Friendly Messages
- "File not found: @invalid/path.py"
- "Permission denied: @../outside/workspace.txt"
- "File too large to reference: @huge_file.bin"

### Graceful Degradation
- If file picker fails, allow manual path entry
- If file can't be read, show path without content
- If search times out, show partial results

## Accessibility

1. **Screen Reader Support**
   - Announce file picker opening
   - Read file names and types
   - Announce selection

2. **Keyboard Only Navigation**
   - Full functionality without mouse
   - Clear focus indicators
   - Logical tab order

3. **High Contrast Mode**
   - Clear file type indicators
   - Visible selection state
   - Readable in all themes

## Testing Scenarios

1. **Unit Tests**
   - @ detection in various positions
   - File search algorithm
   - Path validation
   - State management

2. **Integration Tests**
   - Full @ command flow
   - File loading and display
   - Multi-file references
   - Error scenarios

3. **E2E Tests**
   - User completes file reference
   - AI processes file context
   - File updates during session
   - Performance with many files