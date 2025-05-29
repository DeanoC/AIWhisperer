# Tool Sets and Tags Documentation

## Overview

AIWhisperer uses a flexible tool access control system based on **tags** and **tool sets**. This system allows fine-grained control over which tools each agent can access, supporting security, specialization, and capability management.

## Tool Tags

Tags are labels attached to tools that describe their capabilities and categories. Tools can have multiple tags.

### Available Tags

- **Filesystem Tags**
  - `filesystem` - General file system operations
  - `file_read` - Reading file contents
  - `file_write` - Writing/modifying files
  - `directory_browse` - Listing and navigating directories
  - `file_search` - Searching for files by name or content

- **Execution Tags**
  - `code_execution` - Running code or system commands
  - `utility` - General utility operations
  - `dangerous` - Operations that could be risky

- **Analysis Tags**
  - `analysis` - Code or data analysis capabilities
  - `testing` - Test-related operations
  - `planning` - Planning and design operations

- **General Tags**
  - `general` - General-purpose tools
  - `automation` - CI/CD and automation tools

### Using Tags

Agents can specify which tags they need in their configuration:

```yaml
agents:
  analyst:
    tool_tags: ["filesystem", "file_read", "analysis"]
```

## Tool Sets

Tool sets are predefined collections of tools that can be assigned to agents. They support inheritance and provide a more maintainable way to manage tool access.

### Tool Set Structure

Tool sets are defined in `ai_whisperer/tools/tool_sets.yaml`:

```yaml
base_sets:
  readonly_filesystem:
    description: "Read-only file system access tools"
    tools:
      - read_file
      - list_directory
      - search_files
    tags:
      - filesystem
      - file_read
      - analysis

agent_sets:
  analyst:
    description: "Tools for code analysis"
    inherits:
      - readonly_filesystem
    tools: []  # Additional tools
    tags: []   # Additional tags
```

### Available Tool Sets

#### Base Sets
- **readonly_filesystem** - Read-only file access
- **write_filesystem** - File modification tools
- **code_execution** - Code/command execution tools

#### Agent Sets
- **analyst** - For analysis agents (read-only)
- **planner** - For planning agents (read-only)
- **tester** - For testing agents (includes execution)
- **developer** - Full development tools
- **documenter** - Documentation tools

#### Specialized Sets
- **minimal** - Minimal file reading only
- **secure_readonly** - Secure read-only without execution
- **ci_cd** - CI/CD pipeline tools

### Tool Set Inheritance

Tool sets can inherit from other sets:

```yaml
agent_sets:
  developer:
    inherits:
      - readonly_filesystem
      - write_filesystem
      - code_execution
```

The `developer` set will include all tools and tags from the inherited sets.

## Agent Configuration

Agents can use tool sets, tags, or both:

```yaml
agents:
  p:
    name: "Patricia the Planner"
    tool_sets: ["planner"]           # Use planner tool set
    tool_tags: ["planning"]          # Additional tags
    allow_tools: ["specific_tool"]   # Explicit allow list
    deny_tools: ["dangerous_tool"]   # Explicit deny list
```

### Tool Access Precedence

The system follows this precedence (highest to lowest):
1. **deny_tools** - Always blocks access
2. **allow_tools** - If specified, only these tools are allowed
3. **tool_sets/tool_tags** - Normal tool resolution

Example:
```yaml
agents:
  secure_agent:
    tool_sets: ["developer"]        # Includes many tools
    allow_tools: ["read_file"]      # But only allow this one
    deny_tools: []                  # None explicitly denied
    # Result: Only read_file is accessible
```

## Examples

### Read-Only Agent
```yaml
agents:
  reader:
    tool_sets: ["readonly_filesystem"]
    # Can read files but not modify them
```

### Testing Agent
```yaml
agents:
  tester:
    tool_sets: ["tester"]
    # Can read files and execute tests
```

### Secure Agent
```yaml
agents:
  secure:
    tool_sets: ["secure_readonly"]
    deny_tools: ["execute_command"]
    # Extra security: no execution even if inherited
```

### Custom Agent
```yaml
agents:
  custom:
    tool_tags: ["filesystem", "analysis"]
    allow_tools: ["read_file", "analyze_code"]
    # Very specific tool access
```

## Best Practices

1. **Use Tool Sets for Common Patterns**
   - Define tool sets for common agent roles
   - Use inheritance to avoid duplication

2. **Principle of Least Privilege**
   - Give agents only the tools they need
   - Use `deny_tools` for extra security

3. **Combine Sets and Tags**
   - Use tool sets for base capabilities
   - Add tags for specific additional tools

4. **Document Tool Requirements**
   - Clearly document why each agent needs specific tools
   - Review tool access periodically

## Adding New Tool Sets

To add a new tool set:

1. Edit `ai_whisperer/tools/tool_sets.yaml`
2. Add your set under appropriate section:
   - `base_sets` for reusable components
   - `agent_sets` for agent-specific sets
   - `specialized_sets` for special cases

3. Define the set:
```yaml
my_custom_set:
  description: "Description of the set"
  inherits: ["base_set"]  # Optional
  tools: ["tool1", "tool2"]
  tags: ["tag1", "tag2"]
  deny_tags: ["dangerous"]  # Optional
```

4. Use in agent configuration:
```yaml
agents:
  my_agent:
    tool_sets: ["my_custom_set"]
```

## Security Considerations

1. **Execution Tools**: Be careful with `code_execution` tag
2. **File Write Access**: Limit `file_write` to trusted agents
3. **Path Validation**: All file operations use PathManager
4. **Deny Lists**: Use `deny_tools` for critical restrictions

## Troubleshooting

### Agent Can't Access Expected Tools

1. Check tool set inheritance
2. Verify no `allow_tools` restriction
3. Ensure tool not in `deny_tools`
4. Confirm tool is registered

### Tool Set Not Found

1. Check spelling in configuration
2. Ensure tool_sets.yaml is loaded
3. Verify inheritance chain

### Circular Inheritance Error

1. Check tool set definitions
2. Ensure no set inherits from itself
3. Break circular dependencies