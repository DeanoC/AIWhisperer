# Tool Usage Guidelines - REVISED

## Tool Selection Matrix

| Task | Use This Tool | NOT This | Why |
|------|---------------|----------|-----|
| Find files by name/pattern | `search_files` | `execute_command` with find | Built-in, faster, safer |
| Check if file exists | `list_directory` | `read_file` (catch error) | Explicit check, no error noise |
| Modify few lines in file | `replace_in_file` | `write_file` | Preserves rest of file |
| View project structure | `get_project_structure` | Recursive `list_directory` | Optimized for overview |
| Find code patterns | `find_similar_code` | Complex regex search | Semantic understanding |
| Run tests | `execute_command` | Multiple tool calls | Direct execution |
| Check dependencies | `analyze_dependencies` | Read package files | Structured analysis |

## Tool Usage Patterns

### Pattern: File Discovery
```
1. list_directory(path) → Check if exists
2. search_files(pattern) → Find matches  
3. read_file(specific_path) → Examine content
```

### Pattern: Code Modification
```
1. read_file(path) → Understand current state
2. replace_in_file(search, replace) → Make changes
3. execute_command(lint/test) → Verify changes
```

### Pattern: Project Analysis
```
1. get_project_structure() → Overview
2. analyze_languages() → Tech stack
3. find_similar_code(pattern) → Examples
```

## Common Mistakes to Avoid

### 1. Wrong Tool for File Checks
❌ **BAD**: Try read_file, catch FileNotFoundError
✅ **GOOD**: list_directory(parent_path) first

### 2. Overwriting When Editing
❌ **BAD**: Read entire file, modify, write_file
✅ **GOOD**: replace_in_file with specific changes

### 3. Shell Commands for Built-in Operations
❌ **BAD**: execute_command("find . -name '*.py'")
✅ **GOOD**: search_files(pattern="*.py")

### 4. Multiple Tools When One Suffices
❌ **BAD**: list + read + analyze separately
✅ **GOOD**: get_project_structure() for overview

## Tool-Specific Best Practices

### read_file
- Always specify exact path
- Check existence first with list_directory
- Use line limits for large files

### write_file
- Create parent directories first
- Warn before overwriting
- Use for NEW files only

### replace_in_file
- Include enough context for unique match
- Test with small changes first
- Preserve formatting and indentation

### search_files
- Use simple patterns when possible
- Combine with path filters
- Check result count before processing

### execute_command
- Explain what command does
- Set appropriate timeout
- Capture both stdout and stderr

### list_directory
- Use recursive=false for large directories
- Filter by file type when needed
- Check permissions for access errors

## Performance Guidelines

1. **Batch Operations**: Combine related searches
2. **Cache Results**: Reuse file contents in same session
3. **Limit Scope**: Use path parameters to narrow searches
4. **Fail Fast**: Check prerequisites before heavy operations

## Error Handling

### File Not Found
1. Verify path with list_directory
2. Check for typos in filename
3. Suggest similar files if found

### Permission Denied
1. Check file permissions
2. Suggest alternative paths
3. Explain why access failed

### Tool Timeout
1. Break into smaller operations
2. Add progress indicators
3. Suggest background execution

## Tool Metrics Integration

Every tool use should track:
- Success/failure
- Execution time
- Error messages
- Selected parameters

This data improves:
- Tool selection accuracy
- Error message clarity
- Performance optimization
- Documentation updates