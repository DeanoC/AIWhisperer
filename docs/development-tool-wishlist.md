# Development Tool Wishlist

This document tracks tools that would be helpful for AI assistants working on the AIWhisperer codebase. These were identified during real development tasks.

## Date: 2025-05-31
**Identified during**: Agent E implementation analysis (Subtask 1)

### 1. Dependency Graph Tool
**Purpose**: Visualize relationships between components
**Use Case**: Understanding how Agent P, StatelessAgent, AILoop, and ToolRegistry interconnect
**Potential Implementation**: 
- Static analysis of imports
- Runtime dependency tracking
- Visual graph generation (mermaid, graphviz)

### 2. Cross-Reference Tool
**Purpose**: Find all usages of a class/function across the codebase
**Use Case**: Finding where StatelessAgent is instantiated, where specific methods are called
**Potential Implementation**:
- Language server protocol integration
- AST-based analysis
- Index of symbols and references

### 3. Architecture Diagram Generator
**Purpose**: Create visual representation of system architecture from code
**Use Case**: Documenting findings about agent architecture for team understanding
**Potential Implementation**:
- Parse code structure and generate PlantUML/Mermaid diagrams
- Extract class relationships and data flow
- Generate component interaction diagrams

### 4. Symbol Definition Finder
**Purpose**: Jump directly to where classes/functions are defined
**Use Case**: Quickly navigating from usage to definition (e.g., finding where AITool base class is defined)
**Potential Implementation**:
- Enhanced grep with language awareness
- Integration with ctags/etags
- Smart navigation based on import statements

### 5. Test Coverage Tool
**Purpose**: See which parts of a component have test coverage
**Use Case**: Understanding which parts of Agent P are well-tested vs. need more tests
**Potential Implementation**:
- Integration with pytest-cov
- Visual overlay of coverage on code
- Coverage trends over time

## MCP Tools Integration Note

As mentioned, Claude Code supports MCP (Model Context Protocol) tools. These tools could potentially be implemented as MCP tools to enhance the development experience for AI assistants working on the codebase.

## Benefits

These tools would:
1. Reduce investigation time
2. Improve understanding of complex systems
3. Enable better documentation generation
4. Help maintain architectural consistency
5. Support more effective refactoring

## Priority Ranking

1. **High**: Cross-Reference Tool - Most frequently needed
2. **High**: Symbol Definition Finder - Basic navigation necessity
3. **Medium**: Architecture Diagram Generator - Valuable for documentation
4. **Medium**: Test Coverage Tool - Important for quality assurance
5. **Low**: Dependency Graph Tool - Useful but less critical