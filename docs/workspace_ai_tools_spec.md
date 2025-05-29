# Workspace AI Tools Specification

## Overview
This document outlines the implementation of AI tools for workspace file browsing and the enhancement of the tool tags/sets system in AIWhisperer.

## Current State Analysis

### Tool System Issues
1. **No Tool Tags on Existing Tools**
   - `ReadFileTool` and `WriteFileTool` don't define any tags
   - Tools won't be available to agents through tag filtering

2. **Tag Inconsistency**
   - Agent configurations use tags like `"filesystem"`, `"analysis"`, `"testing"`
   - Actual tools either have no tags or different tags
   - No standardized tag vocabulary

3. **No Tool Set Definitions**
   - No concept of predefined tool sets or groups
   - Each agent manually lists tags, leading to duplication

4. **Missing Integration**
   - The `allow_tools` and `deny_tools` features shown in tests aren't implemented
   - Tag filtering logic in tests isn't used in actual codebase

## Proposed Tool Tag System

### Standard Tag Categories

#### File Operations
- `filesystem` - General file system operations
- `file_read` - Reading file contents
- `file_write` - Writing/modifying files
- `file_search` - Searching for files by name/pattern
- `directory_browse` - Listing and exploring directories

#### Code Operations
- `code_analysis` - Analyzing code structure/content
- `code_generation` - Generating new code
- `code_execution` - Running commands/scripts

#### Planning & Analysis
- `planning` - Project planning operations
- `analysis` - General analysis capabilities
- `testing` - Test-related operations

#### General
- `general` - General purpose tools
- `utility` - Utility operations

### Tool Sets Concept
Predefined groups of related tools:

```yaml
tool_sets:
  file_operations:
    description: "Core file system operations"
    tags:
      - file_read
      - file_write
      - directory_browse
      - file_search
    
  code_tools:
    description: "Code manipulation and execution"
    tags:
      - code_analysis
      - code_execution
      - file_read
    
  planning_tools:
    description: "Project planning and analysis"
    tags:
      - filesystem
      - analysis
      - planning
      
  testing_tools:
    description: "Testing and validation"
    tags:
      - testing
      - code_execution
      - file_read
```

## New Tool Specifications

### 1. List Directory Tool
```python
name: "list_directory"
description: "List files and directories in a workspace path"
tags: ["filesystem", "directory_browse", "analysis"]
parameters:
  - path: string (optional, defaults to workspace root)
  - recursive: boolean (optional, defaults to false)
  - max_depth: integer (optional, defaults to 3)
  - include_hidden: boolean (optional, defaults to false)
```

### 2. Search Files Tool
```python
name: "search_files"
description: "Search for files by name pattern or content"
tags: ["filesystem", "file_search", "analysis"]
parameters:
  - pattern: string (glob pattern or regex)
  - search_type: "name" | "content" (defaults to "name")
  - file_types: array of strings (optional, e.g., [".py", ".js"])
  - max_results: integer (optional, defaults to 100)
```

### 3. Get File Content Tool
```python
name: "get_file_content"
description: "Read file content with advanced options"
tags: ["filesystem", "file_read", "analysis"]
parameters:
  - path: string (required)
  - start_line: integer (optional)
  - end_line: integer (optional)
  - preview_only: boolean (optional, returns first 200 lines)
```

### 4. Find Pattern Tool (grep-like)
```python
name: "find_pattern"
description: "Search for patterns within file contents"
tags: ["filesystem", "file_search", "code_analysis"]
parameters:
  - pattern: string (regex pattern)
  - paths: array of strings (files/dirs to search)
  - context_lines: integer (optional, lines before/after match)
  - max_matches: integer (optional)
```

## Tool Naming Conventions

Following patterns from successful AI tools:
- Use snake_case for tool names
- Be descriptive but concise
- Use common terminology (read_file, not fetch_file_contents)
- Group related operations with common prefixes

### Recommended Names
- `read_file` - Read file content
- `write_file` - Write content to file
- `list_directory` - List directory contents
- `search_files` - Search for files
- `find_pattern` - Search within files (grep-like)
- `get_file_tree` - Get directory tree structure

## @ Reference Integration

### File References
When a user includes `@file.py` in a message:
1. System validates file exists in workspace
2. Inserts first 200 lines into context
3. Adds metadata:
   ```json
   {
     "type": "file_reference",
     "path": "/workspace/file.py",
     "lines_included": 200,
     "total_lines": 500,
     "truncated": true
   }
   ```
4. AI tools can access full content via `read_file` tool

### Directory References
When a user includes `@src/components/` in a message:
1. System validates directory exists
2. Inserts directory tree (max depth 3)
3. Adds metadata:
   ```json
   {
     "type": "directory_reference",
     "path": "/workspace/src/components/",
     "file_count": 25,
     "total_size": "156KB"
   }
   ```

## Security Considerations

All tools must:
1. Validate paths through PathManager
2. Respect workspace boundaries
3. Not access files outside workspace
4. Not expose sensitive information
5. Rate limit file operations

## Agent Tool Assignment

### Updated Agent Configurations
```yaml
agents:
  alice:
    tool_tags: ["filesystem", "file_read", "file_search", "analysis", "general"]
    
  patricia:
    tool_tags: ["filesystem", "file_read", "directory_browse", "planning", "analysis"]
    tool_sets: ["planning_tools"]
    
  tessa:
    tool_tags: ["filesystem", "file_read", "file_write", "code_execution", "testing"]
    tool_sets: ["testing_tools"]
    
  code_generator:
    tool_tags: ["file_write", "file_read", "code_generation"]
    allow_tools: ["write_file", "read_file"]  # Explicit whitelist
```

## Implementation Phases

### Phase 1: Fix Existing Tools
- Add proper tags to existing tools
- Ensure tag filtering works correctly
- Update tests

### Phase 2: Implement Core Workspace Tools
- Create list_directory tool
- Create search_files tool
- Create get_file_content tool
- Register with tool registry

### Phase 3: Enhance Tool System
- Implement tool sets concept
- Add allow/deny list functionality
- Create tag validation
- Add tag documentation

### Phase 4: Advanced Features
- Implement find_pattern tool
- Add file preview capabilities
- Create workspace statistics tool
- Add caching for repeated operations