# Documentation Generation Workflow

An intelligent multi-agent workflow for generating comprehensive, high-quality documentation. This workflow demonstrates how specialized agents collaborate to analyze code, write documentation, review content, and produce multi-format outputs.

## Features

- **Multi-format output generation** (Markdown, HTML, PDF, Docstrings)
- **Automatic outdated documentation detection**
- **Collaborative review and iteration process**
- **Style guide enforcement** (Google, NumPy, Sphinx)
- **Tutorial and guide generation** with exercises
- **Migration guide creation** with breaking change analysis
- **Batch documentation** for multiple targets
- **Cross-reference generation** for large projects

## Agent Roles

- **Alice (a)**: Code Analyst - Analyzes code structure, extracts APIs, maps relationships
- **Patricia (p)**: Documentation Writer - Creates well-structured technical documentation
- **Debbie (d)**: Documentation Debugger - Ensures accuracy and completeness
- **Eamonn (e)**: Example Generator - Creates practical code examples and tutorials
- **Tessa (t)**: Documentation Reviewer - Quality assurance and consistency checking

## Usage

### Basic API Documentation

```python
from examples.async_agents.documentation_workflow import DocumentationWorkflow
from ai_whisperer.services.agents.async_session_manager_v2 import AsyncAgentSessionManager

# Initialize workflow
workflow = DocumentationWorkflow(
    workspace_path=Path("/path/to/workspace"),
    output_path=Path("/path/to/output")
)

# Create session manager
session_manager = AsyncAgentSessionManager(config)

# Generate API documentation
config = {
    "target": {
        "type": "module",
        "path": "ai_whisperer/tools",
        "name": "Tool System"
    },
    "agents": ["a", "p"],  # Alice analyzes, Patricia writes
    "doc_type": "api"
}

result = await workflow.run(config, session_manager)
```

### Comprehensive Documentation

```python
config = {
    "target": {
        "type": "project",
        "path": ".",
        "name": "AIWhisperer"
    },
    "agents": ["a", "p", "d", "e", "t"],  # All agents contribute
    "doc_type": "comprehensive",
    "include_examples": True,
    "include_tests": True,
    "review_enabled": True,
    "review_iterations": 2,
    "style_guide": "google"
}
```

### Tutorial Generation

```python
config = {
    "target": {
        "type": "feature",
        "path": "ai_whisperer/tools/send_mail_tool.py",
        "name": "Mail System"
    },
    "agents": ["a", "p", "e"],  # Need Eamonn for examples
    "doc_type": "tutorial",
    "tutorial_config": {
        "difficulty": "beginner",
        "include_exercises": True,
        "step_by_step": True,
        "estimated_time": "30 minutes"
    }
}
```

### Migration Guide

```python
config = {
    "target": {
        "type": "migration",
        "from_version": "1.0",
        "to_version": "2.0",
        "name": "AIWhisperer Migration Guide"
    },
    "agents": ["a", "p", "d"],  # Debbie helps with compatibility
    "doc_type": "migration",
    "analyze_breaking_changes": True,
    "generate_migration_scripts": True
}
```

### Multi-Format Output

```python
config = {
    "target": target_info,
    "agents": ["a", "p", "e"],
    "doc_type": "api",
    "output_formats": ["markdown", "html", "pdf", "docstring"],
    "style_guide": "google"  # or "numpy", "sphinx"
}
```

## Configuration Options

### Core Options
- `target`: Target specification (type, path, name)
- `agents`: List of agent IDs to use
- `doc_type`: Type of documentation (api/comprehensive/tutorial/migration/technical)
- `output_formats`: List of output formats to generate
- `style_guide`: Documentation style guide to follow

### Content Options
- `include_examples`: Add code examples
- `include_tests`: Include testing documentation
- `check_existing`: Check for outdated documentation
- `update_mode`: How to handle updates ("auto"/"manual")

### Review Options
- `review_enabled`: Enable review process
- `review_iterations`: Number of review rounds
- `incorporate_feedback`: Automatically apply review feedback

### Advanced Options
- `analyze_breaking_changes`: For migration guides
- `generate_migration_scripts`: Create automated migration scripts
- `fallback_to_partial`: Continue on errors with partial docs
- `parallel_generation`: Process multiple targets in parallel

## Documentation Types

### API Documentation
- Class and method signatures
- Parameter descriptions
- Return value documentation
- Usage examples
- Type annotations

### Comprehensive Documentation
- Project overview
- Architecture diagrams
- API reference
- Usage examples
- Testing guide
- Troubleshooting section

### Tutorial Documentation
- Step-by-step instructions
- Prerequisites
- Learning objectives
- Practical exercises
- Common pitfalls
- Further reading

### Migration Guide
- Breaking changes analysis
- Step-by-step migration process
- Automated migration scripts
- Compatibility tables
- Rollback procedures

### Technical Documentation
- Implementation details
- Design decisions
- Performance considerations
- Security implications
- Best practices

## Result Structure

```python
{
    "status": "completed",
    "target_name": "Tool System",
    "doc_type": "api",
    "sections_generated": ["overview", "api_reference", "examples"],
    "agent_contributions": {
        "a": {"role": "code_analysis", "findings": {...}},
        "p": {"role": "documentation_writing", "sections": [...]}
    },
    "output_files": [
        {"format": "markdown", "path": "docs/output.md", "size": 5120},
        {"format": "html", "path": "docs/output.html", "size": 5120}
    ],
    "review_performed": true,
    "review_feedback": [...],
    "style_guide_applied": "google",
    "execution_time": "12.5s"
}
```

## Batch Documentation

Generate documentation for multiple targets:

```python
config = {
    "targets": [
        {"type": "module", "path": "ai_whisperer/tools", "name": "Tools"},
        {"type": "module", "path": "ai_whisperer/services", "name": "Services"},
        {"type": "module", "path": "ai_whisperer/core", "name": "Core"}
    ],
    "agents": ["a", "p"],
    "doc_type": "api",
    "parallel_generation": True,
    "consistent_style": True
}
```

## Outdated Documentation Detection

The workflow can automatically detect outdated documentation:

```python
config = {
    "target": target_info,
    "agents": ["a", "d"],
    "check_existing": True,
    "update_mode": "auto"  # Automatically update outdated sections
}

# Result includes:
# - outdated_sections: List of sections needing updates
# - update_recommendations: Specific changes needed
# - changes_detected: Code changes since last update
```

## Best Practices

1. **Start with API docs**: Use Alice + Patricia for basic documentation
2. **Add examples**: Include Eamonn for practical code examples
3. **Enable review**: Use Tessa for quality assurance on important docs
4. **Use style guides**: Ensure consistency across documentation
5. **Check existing docs**: Detect outdated documentation regularly
6. **Batch similar targets**: Process related modules together
7. **Iterate with review**: Multiple review rounds improve quality

## Integration with Async Agents

This workflow leverages the async agents architecture:

- **Parallel analysis**: Multiple agents analyze different aspects simultaneously
- **Mailbox communication**: Agents share findings via the mailbox system
- **Event-driven updates**: Agents notify others when sections are ready
- **Resource efficiency**: Agents sleep when not actively working

## Error Handling

The workflow includes robust error handling:
- Failed agents don't stop documentation generation
- Partial documentation can be generated on errors
- Confidence levels indicate documentation completeness
- Detailed error reporting for troubleshooting