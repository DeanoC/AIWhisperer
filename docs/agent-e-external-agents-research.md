# Agent E External Agents Research Summary

## Date: 2025-05-31
**Research Purpose**: Understanding how Agent E can integrate with Claude Code, RooCode, and GitHub Copilot for the human-in-the-middle external agent feature.

## Executive Summary

**Key Finding**: None of the three external agents (Claude Code, RooCode, GitHub Copilot) offer traditional REST APIs. They are all IDE or CLI-based tools that require human interaction and approval. This validates the RFC's "human-in-the-middle" approach.

## Detailed Findings

### Claude Code

**Type**: Command-line interface (CLI) tool  
**Integration Method**: Shell commands with JSON output  
**Key Features**:
- Direct bash integration: `claude -p "<prompt>" --json | next_command`
- MCP (Model Context Protocol) support for extensibility
- Prompt templates in `.claude/commands` folder
- Configuration via `.mcp.json` files

**Best Practices**:
- Read files first before writing code
- Explicit Test-Driven Development (TDD) approach
- Avoid mock implementations
- Use for git operations and codebase exploration

**Example Task Format**:
```bash
claude -p "Write unit tests for the UserService class in src/services/user.ts. The tests should cover all public methods and edge cases. Use Jest framework." --json
```

### RooCode (formerly Roo Cline)

**Type**: VS Code extension  
**Integration Method**: IDE chat interface  
**Key Features**:
- Open source and customizable
- Supports multiple AI providers (OpenRouter, Anthropic, OpenAI)
- API Configuration Profiles for different settings
- MCP support for custom tools
- Permission-based command execution

**Best Practices**:
- Optimized for Claude 3.7 Sonnet model
- Configure appropriate API profiles for different task types
- Use permission gating for sensitive operations

**Task Packaging**: Tasks must be formatted as chat messages within VS Code, no external API available.

### GitHub Copilot Agent Mode

**Type**: IDE agent mode (VS Code, Visual Studio, others)  
**Integration Method**: IDE chat interface with agent mode  
**Key Features**:
- Autonomous multi-step task execution
- Iterates until completion, inferring necessary subtasks
- Built-in tools: workspace search, file ops, terminal, error checking
- MCP support rolling out
- Available across multiple IDEs

**Best Practices**:
- Provide sufficient context with related files open
- Use meaningful function names and comments
- Be specific about language and framework
- VS Code team prefers Claude Sonnet for agent mode

**Workflow**:
1. Switch to "Agent" mode in Copilot chat
2. Describe the complex task
3. Agent works autonomously but requires approval

## Common Integration Patterns

### 1. Task Packaging Structure
All agents benefit from tasks that include:
- **Clear objective**: What needs to be accomplished
- **Context**: Relevant files, dependencies, constraints
- **Success criteria**: How to verify completion
- **Technology stack**: Language, framework, libraries
- **Test requirements**: Expected test coverage

### 2. Prompt Engineering Patterns

**TDD Pattern** (especially for Claude Code):
```
1. "Write failing tests for [feature]"
2. "Run tests and confirm they fail"
3. "Implement code to make tests pass"
4. "Refactor while keeping tests green"
```

**Context Building Pattern**:
```
1. "Read and analyze [files]"
2. "Identify patterns used in the codebase"
3. "Implement [feature] following existing patterns"
```

**Iterative Enhancement Pattern**:
```
1. "Create basic implementation"
2. "Add error handling"
3. "Add tests"
4. "Add documentation"
```

### 3. Model Context Protocol (MCP)

Both Claude Code and RooCode support MCP, which could be a future integration point:
- Allows custom tool integration
- Enables extended capabilities
- Provides standardized communication

## Implications for Agent E Implementation

### 1. Task Decomposition Requirements

Agent E must create tasks that are:
- **Self-contained**: Include all necessary context
- **Executable**: Can be run as standalone prompts
- **Verifiable**: Include clear success criteria
- **Agent-optimized**: Formatted for specific agent strengths

### 2. Task Metadata Structure

```json
{
  "task_id": "unique-id",
  "description": "Human-readable task description",
  "agent_recommendations": {
    "claude_code": {
      "suitable": true,
      "prompt": "claude -p \"...\" --json",
      "strengths": ["TDD", "git operations", "exploration"]
    },
    "roocode": {
      "suitable": true,
      "prompt": "Formatted for VS Code chat",
      "strengths": ["multi-file refactoring", "VS Code integration"]
    },
    "copilot": {
      "suitable": true,
      "prompt": "Agent mode task description",
      "strengths": ["autonomous iteration", "multi-step tasks"]
    }
  },
  "context": {
    "files": ["file1.ts", "file2.ts"],
    "dependencies": ["jest", "typescript"],
    "constraints": ["maintain backward compatibility"]
  },
  "success_criteria": [
    "All tests pass",
    "No linting errors",
    "Documentation updated"
  ]
}
```

### 3. Human-in-the-Middle Workflow

Since all agents require human interaction:

1. **Task Presentation**: Agent E presents decomposed task to user
2. **Agent Selection**: User chooses which external agent to use
3. **Prompt Delivery**: User copies formatted prompt to chosen agent
4. **Execution Monitoring**: User observes agent execution
5. **Result Reporting**: User reports back to Agent E
6. **Progress Tracking**: Agent E updates task status

### 4. Future Considerations

- **MCP Integration**: Could provide deeper integration in future
- **Automation**: Monitor for API availability from these tools
- **Template Library**: Build agent-specific prompt templates
- **Performance Metrics**: Track which agents work best for which tasks

## Conclusion

The research confirms that the RFC's human-in-the-middle approach is not just practical but necessary given current tooling. Agent E should focus on creating high-quality, self-contained task descriptions that can be executed through these CLI/IDE interfaces, with human oversight ensuring quality and safety.