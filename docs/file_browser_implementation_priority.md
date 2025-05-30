# File Browser Implementation Priority Guide

## Quick Start Priority List

### Week 1: Foundation
1. **Backend File Service** (2 days) [DONE]
   - Basic directory listing API
   - File content retrieval
   - PathManager integration
   - JSON-RPC endpoints

2. **Basic File Browser UI** (2 days) [DONE]
   - Simple tree view in sidebar
   - Expand/collapse directories
   - Connect to backend API
   - Loading states

3. **Initial AI Tool** (1 day)
   - WorkspaceExplorerTool with basic list_files
   - Register with agent system
   - Basic tests

### Week 2: Core Features
1. **@ Command Implementation** (3 days) [DONE]
   - Detect @ in MessageInput
   - Basic FilePicker modal
   - File selection and insertion
   - Keyboard navigation

2. **Enhanced AI Tools** (2 days)
   - Complete WorkspaceExplorerTool
   - Add FileContextTool
   - Integration tests

### Week 3: Polish & Advanced
1. **Search & Filtering** (2 days) [PARTIALY-DONE]
   - File search in picker
   - Fuzzy matching
   - Recent files

2. **UX Enhancements** (2 days)
   - File previews
   - Better keyboard shortcuts
   - Drag & drop support

3. **Performance & Testing** (1 day)
   - Optimize for large workspaces
   - Complete test coverage
   - Documentation

## MVP Features (Must Have)
- ✅ View files in sidebar
- ✅ @ command to reference files
- ✅ AI tools can list files
- ✅ Basic keyboard navigation
- ✅ Respect PathManager security

## Nice to Have Features (Can Defer)
- 🔄 File content search
- 🔄 Git status indicators
- 🔄 File preview on hover
- 🔄 Multiple file selection
- 🔄 Breadcrumb navigation

## Critical Path Dependencies
```
PathManager → FileService → JSON-RPC Methods → Frontend Components
                    ↓
              AI Tools → Agent Integration
```

## Risk Mitigation
1. **Performance Risk**: Start with max depth limits
2. **Security Risk**: Always use PathManager, never direct paths
3. **UX Risk**: Get early feedback on @ command behavior
4. **Integration Risk**: Test with existing agents early

## Success Metrics
- File browser loads in < 500ms
- @ command responds in < 100ms
- Agents can successfully use workspace tools
- No security violations in path access
- 90%+ test coverage on new code