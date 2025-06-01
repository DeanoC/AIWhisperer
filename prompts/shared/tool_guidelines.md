# Tool Usage Guidelines

When using tools in AIWhisperer, follow these guidelines to ensure effective and safe operations.

## General Principles

1. **Right Tool for the Job**: Choose the most appropriate tool for each task
2. **Validate Before Execution**: Check parameters and expected outcomes
3. **Handle Errors Gracefully**: Anticipate and handle potential failures
4. **Respect System Boundaries**: Stay within allowed directories and permissions
5. **Efficiency First**: Minimize tool calls while maintaining effectiveness

## Tool Selection Guide

### File Operations
- `read_file`: Read existing files
- `write_file`: Create or overwrite files
- `get_file_content`: Get specific file content with line numbers
- `list_directory`: List directory contents
- `search_files`: Search for patterns in files

### Project Analysis
- `get_project_structure`: View project organization
- `analyze_dependencies`: Understand project dependencies
- `analyze_languages`: Identify languages and frameworks
- `find_similar_code`: Find code patterns

### Planning and RFC
- `create_rfc`: Create new RFC documents
- `list_rfcs`: View existing RFCs
- `read_rfc`: Read specific RFC content
- `update_rfc`: Modify existing RFCs
- `prepare_plan_from_rfc`: Convert RFC to plan

### Code Execution
- `execute_command`: Run shell commands safely
- `python_executor`: Execute Python code snippets
- `batch_command`: Run batch operations

### Session Management
- `session_inspector`: View session state
- `session_health`: Check session health
- `session_analysis`: Analyze session performance

## Best Practices

### 1. Path Management
Always use PathManager-compliant paths:
```python
# Good
"output/generated_file.py"  # Relative to output directory

# Bad
"/home/user/project/file.py"  # Absolute path
```

### 2. Error Handling
Always anticipate potential failures:
```python
# Check file exists before reading
# Validate directory exists before writing
# Handle command execution failures gracefully
```

### 3. Tool Chaining
Efficiently chain tools for complex operations:
1. List directory → Filter results → Read specific files
2. Search files → Analyze patterns → Generate report
3. Create RFC → Convert to plan → Execute plan

### 4. Performance Considerations
- Batch operations when possible
- Use search tools before reading many files
- Cache results when appropriate
- Avoid redundant tool calls

### 5. Security Practices
- Never execute untrusted commands
- Validate all user inputs
- Stay within sandbox boundaries
- Don't expose sensitive information

## Common Patterns

### Pattern 1: File Discovery and Analysis
```
1. Use get_project_structure to understand layout
2. Use search_files to find relevant files
3. Use read_file to examine specific files
4. Use analyze_dependencies for deeper insights
```

### Pattern 2: RFC to Implementation
```
1. Use create_rfc or read_rfc to establish requirements
2. Use prepare_plan_from_rfc to generate plan
3. Use execute_command to implement
4. Use write_file to save outputs
```

### Pattern 3: Code Generation
```
1. Use analyze_languages to understand project conventions
2. Use find_similar_code to match patterns
3. Use write_file to generate new code
4. Use python_executor to validate
```

## Tool-Specific Notes

### execute_command
- Always explain what commands do
- Use appropriate timeouts
- Capture and handle output properly

### write_file
- Always check if file exists first
- Create directories if needed
- Use appropriate file extensions

### search_files
- Use efficient regex patterns
- Limit scope when possible
- Handle large result sets

## Debugging Tools

When things go wrong:
1. Use session_inspector to check state
2. Use session_health for diagnostics
3. Review tool execution logs
4. Check file permissions and paths
5. Validate tool parameters