# AIWhisperer Refactor Stage 3 Phase 0: Documentation Modernization

## Overview
Before improving test coverage, we need to modernize documentation to be more LLM-friendly and ensure accuracy. This phase focuses on creating a navigable, up-to-date documentation system that helps both humans and AI understand the codebase quickly.

## Goals
1. Create bidirectional mapping between docs and code
2. Move API documentation to code (docstrings)
3. Add concise file headers for quick understanding
4. Build hierarchical navigation for LLMs

## Phase 0: Documentation Modernization (3-4 days)

### Step 1: Documentation-to-Code Mapping (Day 1)
**Goal**: Understand which docs refer to which code

1. **Create mapping tool** (`scripts/analyze_doc_code_mapping.py`)
   - Parse all markdown files in docs/
   - Extract code references (file paths, class names, function names)
   - Build reverse mapping: code file → docs that mention it
   - Identify orphaned docs (no code references)
   - Identify undocumented code (no doc references)

2. **Generate mapping report**
   - List of docs by code coverage
   - List of code files by documentation coverage
   - Staleness indicators (doc age vs code modification)

### Step 2: API Documentation Migration (Day 2)
**Goal**: Move API docs to code as docstrings

1. **Create migration tool** (`scripts/migrate_api_docs_to_code.py`)
   - For each Python file with doc references:
     - Extract API documentation from markdown
     - Generate proper docstrings (Google style)
     - Add to classes/functions/modules
     - Mark markdown sections as migrated

2. **Docstring standards**:
   ```python
   """Brief one-line description.
   
   Longer description if needed, focusing on purpose and usage.
   
   Args:
       param1: Description
       param2: Description
       
   Returns:
       Description of return value
       
   Raises:
       ExceptionType: When this happens
   """
   ```

### Step 3: File Header Descriptions (Day 2-3)
**Goal**: Add 100-line max headers to Python files

1. **Create header generation tool** (`scripts/generate_file_headers.py`)
   - Analyze file content (classes, functions, imports)
   - Generate concise module description
   - List major APIs with one-line descriptions
   - Include usage examples where helpful

2. **Header template**:
   ```python
   """
   Module: ai_whisperer.agents.base_handler
   Purpose: Base class for all agent handlers in the system
   
   This module provides the foundational Handler class that all agents extend.
   It manages message routing, tool access, and session state.
   
   Key Components:
   - Handler: Base class with message processing pipeline
   - handle_message(): Main entry point for processing user messages
   - get_tools(): Returns tools available to this handler
   - format_response(): Standardizes response format
   
   Usage:
       class MyHandler(Handler):
           def handle_message(self, message: str) -> str:
               # Custom processing
               return self.format_response(result)
   
   Dependencies:
   - ai_whisperer.tools: Tool system integration
   - ai_whisperer.context: Context management
   
   Related:
   - See docs/architecture/agents.md for agent system overview
   - See prompts/agents/ for agent-specific prompts
   """
   ```

### Step 4: Hierarchical Code Map (Day 3)
**Goal**: Create navigable code structure for LLMs

1. **Create map generator** (`scripts/generate_code_map.py`)
   - Generate `CODE_MAP.md` at project root
   - Create `code_map.md` in each major directory
   - Include test coverage indicators
   - Add cross-references to related components

2. **Root CODE_MAP.md structure**:
   ```markdown
   # AIWhisperer Code Map
   
   ## Core Systems
   
   ### AI Loop System (`ai_whisperer/ai_loop/`)
   Manages AI model interactions and response streaming.
   - **Key Files**: ai_loopy.py, stateless_ai_loop.py
   - **Tests**: 85% coverage
   - **Details**: [ai_loop/code_map.md](ai_whisperer/ai_loop/code_map.md)
   
   ### Agent System (`ai_whisperer/agents/`)
   Modular agent handlers with specialized capabilities.
   - **Key Files**: base_handler.py, factory.py, registry.py
   - **Tests**: 45% coverage (needs improvement)
   - **Details**: [agents/code_map.md](ai_whisperer/agents/code_map.md)
   
   ### Tool System (`ai_whisperer/tools/`)
   Pluggable tools for file operations and integrations.
   - **Key Files**: base_tool.py, tool_registry.py
   - **Tests**: 72% coverage
   - **Details**: [tools/code_map.md](ai_whisperer/tools/code_map.md)
   
   ## Quick Navigation
   - Configuration: `config/` (hierarchical YAML structure)
   - Interactive Mode: `interactive_server/` (FastAPI + WebSocket)
   - Frontend: `frontend/` (React TypeScript)
   - Batch Processing: `ai_whisperer/batch/`
   ```

3. **Directory-level code maps**:
   ```markdown
   # AI Loop System Code Map
   
   ## Overview
   Handles all AI model interactions with streaming support.
   
   ## Core Components
   
   ### stateless_ai_loop.py
   Main AI interaction loop with stateless design.
   - `process_request()`: Entry point for AI requests
   - `stream_response()`: Handles streaming responses
   - Tests: `test_stateless_ailoop.py` (95% coverage)
   
   ### ai_loopy.py
   Legacy AI loop (being phased out).
   - Still used by: batch mode
   - Migration status: 60% complete
   ```

### Step 5: Documentation Cleanup (Day 3-4)
**Goal**: Archive outdated docs, update valid ones

1. **Create cleanup tool** (`scripts/cleanup_stale_docs.py`)
   - Use mapping from Step 1
   - Archive docs with no code references
   - Update docs with minor staleness
   - Flag docs needing major updates

2. **New documentation structure**:
   ```
   docs/
   ├── README.md           # Project overview
   ├── QUICK_START.md      # Getting started
   ├── architecture/       # System design docs
   ├── api/               # API references (if not in code)
   ├── guides/            # User guides
   └── archive/           # Old/outdated docs
   ```

## Implementation Order

1. **Day 1**: Build mapping tool and analyze current state
2. **Day 2**: Migrate API docs to code + start file headers
3. **Day 3**: Complete file headers + build code maps
4. **Day 4**: Clean up stale docs + verify everything

## Success Metrics
- [ ] 100% of API docs moved to code
- [ ] 100% of Python files have descriptive headers
- [ ] Hierarchical code map complete
- [ ] Stale documentation reduced by 80%+
- [ ] All active docs have valid code references

## Benefits for LLMs
1. **Quick Context**: File headers provide immediate understanding
2. **Navigation**: Code maps allow efficient exploration
3. **Accuracy**: Docstrings are always up-to-date with code
4. **Discoverability**: Clear structure helps find relevant code

## Example Workflow for LLMs
```
1. Read CODE_MAP.md → Understand system structure
2. Navigate to relevant subsystem via code_map.md
3. Read file header → Understand module purpose
4. Read docstrings → Understand API details
5. Examine code → Implement changes
```

## Tools to Create
1. `analyze_doc_code_mapping.py` - Map docs to code
2. `migrate_api_docs_to_code.py` - Move docs to docstrings
3. `generate_file_headers.py` - Create file headers
4. `generate_code_map.py` - Build navigation maps
5. `cleanup_stale_docs.py` - Archive old docs

This phase directly supports AI-assisted development and makes the codebase self-documenting.