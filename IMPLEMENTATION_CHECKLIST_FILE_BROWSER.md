# File Browser Implementation Checklist

## 🚀 Quick Start (Day 1)

### Backend - Minimal File Service
- [ ] Create `interactive_server/services/file_service.py`
  ```python
  from ai_whisperer.utils import build_ascii_directory_tree
  from ai_whisperer.path_management import PathManager
  
  class FileService:
      def __init__(self, path_manager: PathManager):
          self.path_manager = path_manager
      
      async def get_tree_ascii(self, path: str = ".") -> str:
          return build_ascii_directory_tree(
              self.path_manager.resolve_path(path)
          )
  ```

- [ ] Add JSON-RPC handler in `interactive_server/handlers/workspace_handler.py`
  ```python
  @router.post("/workspace.getTree")
  async def get_workspace_tree(params: Dict) -> str:
      return await file_service.get_tree_ascii(params.get("path", "."))
  ```

- [ ] Register handler in main.py

### Frontend - Display ASCII Tree
- [ ] Update Sidebar.tsx to fetch tree on mount
- [ ] Display tree in `<pre>` tag with monospace font
- [ ] Add loading state

## 📋 Week 1 Tasks

### Day 2-3: Structured File Data
- [ ] Create `FileNode` type definition
- [ ] Enhance file service with structured data:
  - [ ] `list_directory(path, recursive)`
  - [ ] `search_files(query, types)`
- [ ] Add caching for directory listings
- [ ] Write unit tests for file service

### Day 4-5: Basic @ Command
- [ ] Add @ detection in MessageInput.tsx
- [ ] Create simple FilePicker modal
- [ ] Implement basic keyboard navigation:
  - [ ] Up/Down arrows
  - [ ] Enter to select
  - [ ] Escape to cancel
- [ ] Insert file reference on selection

## 📋 Week 2 Tasks

### Day 1-2: AI Tools
- [ ] Create WorkspaceExplorerTool:
  - [ ] `list_files(pattern, recursive)`
  - [ ] `get_directory_tree(format)`
  - [ ] `find_files(query)`
- [ ] Create FileContextTool:
  - [ ] `read_file(path, lines)`
  - [ ] `get_file_summary(path)`
- [ ] Register tools with agents
- [ ] Write integration tests

### Day 3-4: Enhanced File Picker
- [ ] Add fuzzy search to FilePicker
- [ ] Implement file type filtering
- [ ] Add recent files section
- [ ] Show file previews on hover
- [ ] Improve styling and animations

### Day 5: Performance & Polish
- [ ] Implement virtual scrolling for large directories
- [ ] Add debounced search
- [ ] Cache file listings
- [ ] Add comprehensive error handling

## 📋 Week 3 Tasks

### Enhanced Features
- [ ] Multi-file selection with Ctrl/Cmd
- [ ] Drag and drop file references
- [ ] Git status indicators
- [ ] File icons by type
- [ ] Breadcrumb navigation
- [ ] Context menu (copy path, open, etc.)

### Testing & Documentation
- [ ] Complete unit test coverage
- [ ] Add E2E tests for @ command flow
- [ ] Performance testing with large repos
- [ ] Update user documentation
- [ ] Create video demo

## 🔒 Security Checklist
- [ ] All paths validated through PathManager
- [ ] No directory traversal possible
- [ ] Symlinks handled safely
- [ ] Hidden files respect .gitignore
- [ ] Rate limiting on file operations

## 🎯 Definition of Done
- [ ] File browser shows in sidebar
- [ ] @ command works in message input
- [ ] Files can be selected with keyboard/mouse
- [ ] AI agents can explore workspace
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No security vulnerabilities

## 📊 Success Metrics
- [ ] Tree loads in < 500ms for typical project
- [ ] @ command responds in < 100ms
- [ ] Search returns results in < 200ms
- [ ] Memory usage < 50MB for 10k files
- [ ] 95%+ test coverage on new code

## 🚦 Go/No-Go Criteria for Each Phase
### Phase 1 (ASCII Tree)
- Tree displays correctly
- No performance issues
- PathManager integration working

### Phase 2 (@ Command)
- File selection works reliably
- Keyboard navigation smooth
- File references render correctly

### Phase 3 (Full Features)
- All core features implemented
- Performance acceptable
- Security review passed
- User feedback positive

## 🎨 UI Components Needed
1. `FileBrowser.tsx` - Tree view component
2. `FilePicker.tsx` - Modal for @ command
3. `FileNode.tsx` - Individual file/folder item
4. `FilePreview.tsx` - Preview tooltip
5. `FileReference.tsx` - Inline file reference pill

## 🔧 Backend Services Needed
1. `FileService` - Core file operations
2. `WorkspaceHandler` - JSON-RPC endpoints
3. `FileCache` - Caching layer
4. `FileWatcher` - File change notifications

## 📝 Configuration Needed
```yaml
file_browser:
  max_depth: 10
  max_files: 10000
  ignore_patterns:
    - "*.pyc"
    - "__pycache__"
    - "node_modules"
  cache_ttl: 300  # 5 minutes
```

## 🎉 Celebration Milestones
- [ ] First file displayed in sidebar! 🎊
- [ ] First @ command file selection! 🎯
- [ ] First AI agent using workspace tool! 🤖
- [ ] Performance goals met! 🚀
- [ ] Feature complete! 🏆