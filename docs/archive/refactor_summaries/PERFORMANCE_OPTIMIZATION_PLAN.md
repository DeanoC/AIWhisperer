# Performance Optimization Plan

## Current Performance Baseline

- **CLI Startup**: 0.13s (✅ Already fast)
- **Total Codebase Size**: 1168.4 KB
- **Large Files**: 1 file >50KB (python_ast_json_tool.py - 184.3 KB)
- **Heavy Importers**: 2 files with >20 imports
- **Third-party Dependencies**: 45 modules

## Optimization Targets

### 1. Large File Optimization
**File**: `ai_whisperer/tools/python_ast_json_tool.py` (184.3 KB)
- This file is 3x larger than any other file
- Contains 45 import statements
- Likely has multiple responsibilities

**Actions**:
- Split into smaller, focused modules
- Extract common patterns to shared utilities
- Consider moving test data to separate files

### 2. Import Optimization
**Heavy Importers**:
- `python_ast_json_tool.py`: 45 imports
- `python_executor_tool.py`: 25 imports

**Actions**:
- Implement lazy imports for rarely used modules
- Group related imports
- Remove unused imports
- Use TYPE_CHECKING for type-only imports

### 3. Tool Loading Optimization
The tools directory is the largest (744.4 KB with 54 files).

**Actions**:
- Implement lazy tool loading
- Load tools on-demand rather than at startup
- Create a tool manifest for faster discovery
- Cache tool metadata

### 4. Memory Usage Optimization
**Current**: ~13 MB after basic imports

**Actions**:
- Profile memory usage of large modules
- Implement singleton patterns where appropriate
- Clear caches when not needed
- Use generators instead of lists where possible

### 5. Async Performance
**Focus Areas**:
- WebSocket handling
- Batch processing
- AI service calls

**Actions**:
- Review async/await patterns
- Eliminate blocking I/O in async contexts
- Implement connection pooling
- Add request batching

## Implementation Order

### Phase 1: Quick Wins (1 day)
1. Remove unused imports
2. Implement TYPE_CHECKING imports
3. Add lazy imports to CLI entry points
4. Clean up large files

### Phase 2: Tool System Optimization (2 days)
1. Implement lazy tool loading
2. Create tool manifest system
3. Optimize tool discovery
4. Add tool caching

### Phase 3: Memory and Async (1-2 days)
1. Profile memory usage
2. Optimize data structures
3. Improve async patterns
4. Add connection pooling

## Success Metrics

- [ ] Maintain CLI startup <0.2s
- [ ] Reduce memory usage by 30%
- [ ] Reduce largest file to <100KB
- [ ] Implement lazy loading for 80% of tools
- [ ] Zero blocking I/O in async contexts

## Specific Optimizations to Implement

### 1. Lazy Tool Loading
```python
# Instead of loading all tools at startup
from .tool_registry import ToolRegistry
registry = ToolRegistry()
registry.register_all_tools()  # Loads everything

# Use lazy loading
class LazyToolRegistry:
    def __init__(self):
        self._tools = {}
        self._loaded = set()
    
    def get_tool(self, name):
        if name not in self._loaded:
            self._load_tool(name)
        return self._tools[name]
```

### 2. Import Optimization
```python
# Use TYPE_CHECKING for type-only imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from heavy_module import HeavyClass

# Lazy imports for heavy modules
def get_heavy_feature():
    from heavy_module import heavy_function
    return heavy_function()
```

### 3. Split Large Files
- Extract AST handling to `ast_handler.py`
- Move JSON conversion to `json_converter.py`
- Create `ast_patterns.py` for common patterns
- Keep main file as coordinator

### 4. Connection Pooling
```python
# Add connection pooling for AI services
class ConnectionPool:
    def __init__(self, max_connections=10):
        self._pool = []
        self._max = max_connections
    
    async def get_connection(self):
        # Reuse existing connections
        pass
```

## Next Steps

1. Start with removing unused imports
2. Profile `python_ast_json_tool.py` to understand its structure
3. Implement lazy tool loading
4. Measure impact after each optimization