# Workspace AI Tools Specification

## Overview
This document specifies AI tools that enable agents to explore and interact with the workspace file system, particularly useful for planner agents and code analysis tasks.

## Tool Specifications

### 1. WorkspaceExplorerTool

#### Purpose
Allows AI agents to explore the project structure, find files, and understand the codebase organization.

#### Implementation
```python
from typing import List, Dict, Optional
from ai_whisperer.tools.base_tool import BaseTool
from ai_whisperer.path_management import PathManager

class WorkspaceExplorerTool(BaseTool):
    """Tool for exploring workspace file structure"""
    
    name = "workspace_explorer"
    description = "Explore project files and directory structure"
    
    def __init__(self, path_manager: PathManager):
        super().__init__()
        self.path_manager = path_manager
    
    async def list_files(
        self, 
        directory: str = ".",
        pattern: Optional[str] = None,
        recursive: bool = True,
        max_depth: Optional[int] = None,
        file_types: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        List files in the workspace.
        
        Args:
            directory: Starting directory (relative to workspace root)
            pattern: Glob pattern to match files (e.g., "*.py", "test_*.js")
            recursive: Whether to search subdirectories
            max_depth: Maximum directory depth to search
            file_types: List of extensions to filter (e.g., [".py", ".js"])
            
        Returns:
            List of file info dicts with path, name, size, modified
        """
        
    async def get_directory_tree(
        self,
        directory: str = ".",
        max_depth: int = 3,
        show_hidden: bool = False,
        format: str = "ascii"
    ) -> str:
        """
        Generate a visual directory tree.
        
        Args:
            directory: Starting directory
            max_depth: Maximum depth to display
            show_hidden: Include hidden files/directories
            format: Output format ("ascii", "json", "markdown")
            
        Returns:
            Formatted directory tree string
        """
        
    async def find_files(
        self,
        query: str,
        search_type: str = "name",
        case_sensitive: bool = False,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """
        Search for files by name or content.
        
        Args:
            query: Search query
            search_type: "name" or "content"
            case_sensitive: Whether search is case-sensitive
            limit: Maximum results to return
            
        Returns:
            List of matches with relevance scores
        """
        
    async def analyze_structure(self) -> Dict[str, any]:
        """
        Analyze project structure and return insights.
        
        Returns:
            Dict with:
            - total_files: int
            - total_directories: int
            - file_types: Dict[str, int] (extension -> count)
            - largest_files: List[Dict]
            - deepest_paths: List[str]
            - suggestions: List[str] (organizational suggestions)
        """
```

### 2. FileContextTool

#### Purpose
Provides file content and context to AI agents, with intelligent chunking and summarization for large files.

#### Implementation
```python
class FileContextTool(BaseTool):
    """Tool for getting file content and context"""
    
    name = "file_context"
    description = "Read and analyze file contents"
    
    async def read_file(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        context_lines: int = 3
    ) -> Dict[str, any]:
        """
        Read file content with optional line range.
        
        Args:
            file_path: Path to file
            start_line: Starting line number (1-indexed)
            end_line: Ending line number
            context_lines: Extra lines before/after range
            
        Returns:
            Dict with:
            - content: str
            - total_lines: int
            - language: str (detected language)
            - encoding: str
        """
        
    async def get_file_summary(
        self,
        file_path: str,
        include_structure: bool = True
    ) -> Dict[str, any]:
        """
        Get AI-generated summary of file.
        
        Args:
            file_path: Path to file
            include_structure: Include structural analysis
            
        Returns:
            Dict with:
            - summary: str (brief description)
            - main_purpose: str
            - dependencies: List[str]
            - exports: List[str] (for modules)
            - key_functions: List[Dict] (name, purpose)
        """
        
    async def compare_files(
        self,
        file1: str,
        file2: str,
        comparison_type: str = "full"
    ) -> Dict[str, any]:
        """
        Compare two files.
        
        Args:
            file1: First file path
            file2: Second file path
            comparison_type: "full", "structure", "summary"
            
        Returns:
            Comparison results with differences highlighted
        """
```

### 3. WorkspaceSearchTool

#### Purpose
Advanced search capabilities across the entire workspace with semantic understanding.

#### Implementation
```python
class WorkspaceSearchTool(BaseTool):
    """Advanced workspace search tool"""
    
    name = "workspace_search"
    description = "Search across files with advanced queries"
    
    async def semantic_search(
        self,
        query: str,
        file_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, any]]:
        """
        Search using natural language queries.
        
        Example queries:
        - "functions that handle authentication"
        - "React components with state"
        - "database connection code"
        
        Returns:
            Ranked results with snippets and relevance scores
        """
        
    async def find_references(
        self,
        identifier: str,
        search_type: str = "all"
    ) -> List[Dict[str, any]]:
        """
        Find all references to an identifier.
        
        Args:
            identifier: Name to search for
            search_type: "function", "class", "variable", "all"
            
        Returns:
            List of references with context
        """
        
    async def find_similar_code(
        self,
        code_snippet: str,
        threshold: float = 0.7
    ) -> List[Dict[str, any]]:
        """
        Find code similar to given snippet.
        
        Useful for finding duplicate code or patterns.
        """
```

## Integration with Agents

### Agent Configuration
```yaml
agents:
  alice:
    name: "Alice - AI Assistant"
    tools:
      - workspace_explorer
      - file_context
      - workspace_search
    capabilities:
      - "Explore project structure"
      - "Find and analyze files"
      - "Understand codebase organization"
```

### Usage Examples

#### Planner Agent Using Tools
```python
# In planner_handler.py
async def analyze_project(self):
    # Get project structure
    tree = await self.tools.workspace_explorer.get_directory_tree(max_depth=2)
    
    # Find test files
    test_files = await self.tools.workspace_explorer.list_files(
        pattern="test_*.py",
        recursive=True
    )
    
    # Analyze main module
    main_info = await self.tools.file_context.get_file_summary("main.py")
    
    # Search for configuration
    config_files = await self.tools.workspace_search.semantic_search(
        "configuration files"
    )
```

## Tool Registration

### In tool_registry.py
```python
def register_workspace_tools(registry: ToolRegistry, path_manager: PathManager):
    """Register workspace exploration tools"""
    
    registry.register(WorkspaceExplorerTool(path_manager))
    registry.register(FileContextTool(path_manager))
    registry.register(WorkspaceSearchTool(path_manager))
```

## Performance Considerations

1. **Caching Strategy**
   - Cache directory structures for 60 seconds
   - Cache file summaries until file modification
   - Use Redis for distributed caching

2. **Large File Handling**
   - Stream large files in chunks
   - Summarize files over 10,000 lines
   - Warn before processing binary files

3. **Search Optimization**
   - Build search index on startup
   - Update index on file changes
   - Use parallel search for large workspaces

## Security

1. **Path Validation**
   - All paths validated through PathManager
   - No access outside workspace
   - Symlink resolution with security checks

2. **Resource Limits**
   - Maximum file size for reading: 50MB
   - Maximum search results: 1000
   - Rate limiting on expensive operations

3. **Sensitive Data**
   - Skip files matching .gitignore
   - Filter environment files
   - Redact detected secrets

## Testing

### Unit Tests
```python
def test_workspace_explorer_list_files():
    """Test file listing with various filters"""
    
def test_file_context_read_partial():
    """Test reading file with line ranges"""
    
def test_workspace_search_semantic():
    """Test semantic search accuracy"""
```

### Integration Tests
- Test with real project structures
- Verify PathManager integration
- Test error handling for invalid paths
- Performance tests with large codebases

## Future Enhancements

1. **Git Integration**
   - Show file history
   - Find recently changed files
   - Blame information

2. **Dependency Analysis**
   - Import/export tracking
   - Dependency graphs
   - Circular dependency detection

3. **Code Intelligence**
   - Symbol extraction
   - Type information
   - Documentation extraction

4. **Workspace Insights**
   - Code complexity metrics
   - Test coverage integration
   - Technical debt indicators