# File Browser & AI Tools Implementation Checklist

## Phase 1: Fix Existing Tools ⏳

### Tool Tag Updates
- [ ] Add tags to `ReadFileTool`
  - [ ] Tags: `["filesystem", "file_read", "analysis"]`
  - [ ] Update docstring with tag information
  - [ ] Add tests for tag filtering
  
- [ ] Add tags to `WriteFileTool`
  - [ ] Tags: `["filesystem", "file_write"]`
  - [ ] Update docstring with tag information
  - [ ] Add tests for tag filtering

- [ ] Add tags to `ExecuteCommandTool`
  - [ ] Tags: `["code_execution", "utility"]`
  - [ ] Update docstring with tag information
  - [ ] Add tests for tag filtering

### Tool Registry Integration
- [ ] Verify tools are properly registered in `PlanRunner._register_tools()`
- [ ] Test that agents can access tools via tag filtering
- [ ] Update integration tests to verify tag-based tool access

## Phase 2: Implement Core Workspace Tools ⏳

### List Directory Tool
- [ ] Create `ai_whisperer/tools/list_directory_tool.py`
  - [ ] Extend `AITool` base class
  - [ ] Implement parameters: path, recursive, max_depth, include_hidden
  - [ ] Use PathManager for validation
  - [ ] Add proper tags: `["filesystem", "directory_browse", "analysis"]`
  - [ ] Write comprehensive docstring
  
- [ ] Write tests for list_directory tool
  - [ ] Test basic directory listing
  - [ ] Test recursive listing with depth limits
  - [ ] Test path validation (no escape from workspace)
  - [ ] Test hidden file filtering
  - [ ] Test error handling for non-existent paths

### Search Files Tool
- [ ] Create `ai_whisperer/tools/search_files_tool.py`
  - [ ] Extend `AITool` base class
  - [ ] Implement parameters: pattern, search_type, file_types, max_results
  - [ ] Support both name and content search
  - [ ] Use PathManager for validation
  - [ ] Add proper tags: `["filesystem", "file_search", "analysis"]`
  
- [ ] Write tests for search_files tool
  - [ ] Test file name pattern matching (glob)
  - [ ] Test content search (if implemented)
  - [ ] Test file type filtering
  - [ ] Test result limiting
  - [ ] Test performance with large directories

### Get File Content Tool
- [ ] Create `ai_whisperer/tools/get_file_content_tool.py`
  - [ ] Extend `AITool` base class
  - [ ] Implement parameters: path, start_line, end_line, preview_only
  - [ ] Add preview mode (first 200 lines)
  - [ ] Use PathManager for validation
  - [ ] Add proper tags: `["filesystem", "file_read", "analysis"]`
  
- [ ] Write tests for get_file_content tool
  - [ ] Test full file reading
  - [ ] Test line range reading
  - [ ] Test preview mode
  - [ ] Test large file handling
  - [ ] Test binary file detection

### Tool Registration
- [ ] Register all new tools in tool registry
- [ ] Update `PlanRunner._register_tools()` if needed
- [ ] Verify tools appear in `get_all_tools()`

## Phase 3: Enhance Tool System ⏳

### Tool Sets Implementation
- [ ] Create tool sets configuration structure
  - [ ] Define in `ai_whisperer/tools/tool_sets.yaml`
  - [ ] Create `ToolSet` class if needed
  - [ ] Support tool set inheritance

- [ ] Update ToolRegistry
  - [ ] Add `register_tool_set()` method
  - [ ] Add `get_tools_by_set()` method
  - [ ] Support resolving tool sets to tool lists

### Agent Configuration Updates
- [ ] Update agent configurations in `agents.yaml`
  - [ ] Add tool_sets support to agents
  - [ ] Update existing agents with appropriate tags
  - [ ] Test mixed tag and tool_set configuration

### Allow/Deny List Implementation
- [ ] Add to Agent base class
  - [ ] Add `allow_tools` property
  - [ ] Add `deny_tools` property
  - [ ] Implement filtering logic in tool access

- [ ] Update tool filtering
  - [ ] Respect allow_tools whitelist
  - [ ] Respect deny_tools blacklist
  - [ ] Ensure proper precedence (deny > allow > tags)

### Documentation
- [ ] Create tool tag documentation
  - [ ] List all available tags with descriptions
  - [ ] Provide examples of tag usage
  - [ ] Document tool set definitions

- [ ] Update agent documentation
  - [ ] Explain tool access patterns
  - [ ] Document allow/deny list usage
  - [ ] Provide configuration examples

## Phase 4: Advanced Features 🔮

### Find Pattern Tool (grep-like)
- [ ] Create `ai_whisperer/tools/find_pattern_tool.py`
  - [ ] Support regex patterns
  - [ ] Add context lines feature
  - [ ] Implement result limiting
  - [ ] Optimize for performance

### Workspace Statistics Tool
- [ ] Create tool for workspace analysis
  - [ ] File count by type
  - [ ] Directory size analysis
  - [ ] Recent file changes

### Caching Layer
- [ ] Implement caching for repeated operations
  - [ ] Cache directory listings
  - [ ] Cache file metadata
  - [ ] Add cache invalidation

## Integration with @ References ✅

### Backend Support
- [x] File validation in workspace handler
- [x] Content extraction for file references
- [x] Directory tree generation for directory references
- [x] Metadata generation for references

### Frontend Support
- [x] @ command detection in MessageInput
- [x] File picker modal
- [x] File/directory reference rendering
- [x] Reference metadata in messages

## Testing Strategy ⏳

### Unit Tests
- [ ] Individual tool tests
- [ ] Tool registry tests
- [ ] Tag filtering tests
- [ ] Tool set resolution tests

### Integration Tests
- [ ] Agent-tool interaction tests
- [ ] End-to-end tool usage tests
- [ ] @ reference to tool usage flow
- [ ] Performance tests with large workspaces

### Security Tests
- [ ] Path traversal prevention
- [ ] Workspace boundary enforcement
- [ ] Rate limiting verification
- [ ] Permission validation

## Progress Summary

- **Phase 1**: 0% - Ready to start
- **Phase 2**: 0% - Pending Phase 1
- **Phase 3**: 0% - Pending Phase 2  
- **Phase 4**: 0% - Future enhancement
- **@ Reference Integration**: 90% - Backend ready, frontend complete

## Next Steps

1. Start with Phase 1: Add tags to existing tools
2. Implement core workspace tools (Phase 2)
3. Enhance tool system with sets and permissions (Phase 3)
4. Consider advanced features based on user feedback (Phase 4)

## Notes

- All file operations must use PathManager for security
- Tools should handle large files gracefully
- Consider performance implications of recursive operations
- Maintain backward compatibility with existing tool usage