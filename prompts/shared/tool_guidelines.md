# Tool Selection Matrix

| If you need to... | Use this tool | NOT this |
|-------------------|---------------|----------|
| Find files by name/pattern | `search_files` | `execute_command` with 'find' |
| Check if file exists | `list_directory` | `read_file` (catches error) |
| Modify few lines | `replace_in_file` | `write_file` (entire file) |
| View project layout | `get_project_structure` | recursive `list_directory` |
| Find code patterns | `find_similar_code` | `search_files` with complex regex |
| Run Python snippets | `python_executor` | `execute_command` with 'python -c' |
| Create structured plans | `prepare_plan_from_rfc` | manual JSON construction |
| Check session status | `session_health` | multiple inspector calls |
| Debug tool failures | `session_inspector` | guessing from errors |

## Tool Usage Rules

1. **ONE tool per step** - Wait for results before next tool
2. **Check before write** - Verify paths exist before writing
3. **Batch when possible** - Group related operations
4. **Prefer specialized tools** - Use purpose-built over generic

## Common Mistakes

❌ **WRONG**: Chain 5 tools without checking results
✅ **RIGHT**: Execute, evaluate, then proceed

❌ **WRONG**: `write_file` without checking directory exists
✅ **RIGHT**: `list_directory` → create if needed → `write_file`

❌ **WRONG**: `execute_command("grep -r pattern")` 
✅ **RIGHT**: `search_files(pattern="pattern")`

❌ **WRONG**: Multiple `read_file` for related files
✅ **RIGHT**: `search_files` → batch read relevant results

## Performance Optimization

- **Cache results**: Don't re-read unchanged files
- **Limit scope**: Use path filters in search tools
- **Early termination**: Stop when sufficient info found
- **Async where possible**: Use batch operations

## Security Boundaries

- **Paths**: Stay within workspace/output directories
- **Commands**: No system modifications or network access
- **Secrets**: Never log API keys or passwords
- **Validation**: Sanitize all user inputs

## Tool Categories

### Discovery
`get_project_structure`, `list_directory`, `search_files`, `find_similar_code`

### Reading
`read_file`, `get_file_content`, `read_rfc`, `read_plan`

### Writing
`write_file`, `create_rfc`, `update_rfc`, `save_generated_plan`

### Execution
`execute_command`, `python_executor`, `batch_command`

### Analysis
`analyze_dependencies`, `analyze_languages`, `session_health`, `session_inspector`

### Transformation
`prepare_plan_from_rfc`, `format_for_external_agent`, `parse_external_result`