# File Browser Implementation Plan

## Overview
This plan outlines the implementation of workspace file browsing, selection, and integration features for AIWhisperer, including:
- File browser UI in the sidebar
- @ command for file references in chat
- Backend APIs for file listing and searching
- AI tools for workspace exploration

## Architecture Components

### 1. Frontend Components

#### 1.1 File Browser Component (`frontend/src/components/FileBrowser.tsx`)
- Tree view display of workspace files
- Expand/collapse directories
- File icons based on type
- Search/filter functionality
- Integration with existing Sidebar component

#### 1.2 File Picker Modal (`frontend/src/components/FilePicker.tsx`)
- Triggered by @ command in MessageInput
- Fuzzy search for files
- Keyboard navigation (arrow keys, enter to select)
- Mouse selection support
- Recent files section

#### 1.3 @ Command Handler (enhance `frontend/src/MessageInput.tsx`)
- Detect @ character input
- Show file picker dropdown/modal
- Insert selected file reference into message
- Visual indication of file references (pill/tag style)

### 2. Backend APIs

#### 2.1 File Service (`interactive_server/services/file_service.py`)
```python
class FileService:
    async def list_directory(self, path: str, recursive: bool = False) -> FileTree
    async def search_files(self, query: str, file_types: List[str] = None) -> List[FileInfo]
    async def get_file_tree(self, max_depth: int = None) -> FileTree
    async def get_file_content(self, path: str) -> FileContent
```

#### 2.2 JSON-RPC Methods
- `workspace.listDirectory` - List files in a directory
- `workspace.searchFiles` - Search for files by name/content
- `workspace.getFileTree` - Get complete workspace tree
- `workspace.getFileContent` - Get file content (respecting permissions)

### 3. AI Tools

#### 3.1 Workspace Explorer Tool (`ai_whisperer/tools/workspace_explorer_tool.py`)
```python
class WorkspaceExplorerTool(BaseTool):
    def list_files(self, pattern: str = None, file_types: List[str] = None) -> List[str]
    def get_directory_tree(self, path: str = ".", max_depth: int = 3) -> str
    def find_files(self, query: str) -> List[FileMatch]
```

#### 3.2 File Reference Tool (`ai_whisperer/tools/file_reference_tool.py`)
```python
class FileReferenceTool(BaseTool):
    def add_file_to_context(self, file_path: str) -> FileContent
    def get_file_snippet(self, file_path: str, start_line: int, end_line: int) -> str
```

## Implementation Phases

### Phase 1: Backend Infrastructure (Week 1)
1. Implement FileService with basic listing capabilities
2. Add JSON-RPC methods for file operations
3. Create workspace utility functions (tree generation, file filtering)
4. Add tests for file service

### Phase 2: Basic File Browser UI (Week 1-2)
1. Create FileBrowser component with tree view
2. Integrate with existing Sidebar
3. Connect to backend APIs
4. Add loading states and error handling

### Phase 3: @ Command System (Week 2)
1. Enhance MessageInput with @ detection
2. Create FilePicker modal component
3. Implement keyboard navigation
4. Add file reference rendering in messages

### Phase 4: AI Tools (Week 2-3)
1. Implement WorkspaceExplorerTool
2. Create FileReferenceTool
3. Register tools with agent system
4. Add tool tests

### Phase 5: Enhanced Features (Week 3)
1. File search functionality
2. File type filtering
3. Recent files tracking
4. File preview on hover
5. Drag-and-drop support

## Technical Details

### File Tree Data Structure
```typescript
interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  size?: number;
  modified?: string;
  extension?: string;
}
```

### Message File Reference Format
```typescript
interface FileReference {
  path: string;
  displayName: string;
  lineRange?: [number, number];
}
```

### WebSocket Message Flow
1. Client requests file tree: `{"method": "workspace.getFileTree", "params": {"maxDepth": 3}}`
2. Server responds with tree structure
3. Client renders tree in sidebar
4. User selects file via @ command
5. File reference added to message
6. AI receives file context when processing message

## Security Considerations
- All file operations must respect PathManager restrictions
- No access outside workspace boundaries
- File content filtering for sensitive data
- Rate limiting on file operations

## UI/UX Considerations
- Lazy loading for large directories
- Virtual scrolling for performance
- Keyboard shortcuts (Ctrl+P for quick file search)
- Visual feedback for file operations
- Responsive design for different screen sizes

## Testing Strategy
- Unit tests for all components
- Integration tests for file operations
- E2E tests for @ command flow
- Performance tests for large workspaces
- Security tests for path traversal attempts

## Dependencies
- Frontend: Additional packages for tree view (react-arborist or similar)
- Backend: No new dependencies required
- Use existing PathManager for all file operations

## Migration Path
- Existing sidebar remains functional
- New features added incrementally
- No breaking changes to current APIs
- Gradual rollout with feature flags if needed