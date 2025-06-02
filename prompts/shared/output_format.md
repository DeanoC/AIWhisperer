# Output Format Requirements

When generating structured outputs, follow these formatting requirements to ensure consistency and parseability.

## JSON Output Standards

### General Rules
1. Always produce valid JSON (use proper escaping)
2. Include all required fields according to schema
3. Use consistent property naming (camelCase or snake_case)
4. Provide meaningful values (avoid empty strings unless valid)
5. Include type-appropriate values (strings, numbers, booleans, arrays, objects)

### Common JSON Structures

#### Task/Plan Format
```json
{
  "task_id": "unique-identifier",
  "title": "Clear, descriptive title",
  "description": "Detailed description of the task",
  "type": "feature|bugfix|refactor|test|docs",
  "priority": "high|medium|low",
  "estimated_hours": 4,
  "dependencies": ["task-id-1", "task-id-2"],
  "subtasks": [
    {
      "id": "subtask-1",
      "title": "Subtask title",
      "description": "What needs to be done",
      "status": "pending|in_progress|completed"
    }
  ],
  "acceptance_criteria": [
    "Criterion 1",
    "Criterion 2"
  ]
}
```

#### RFC Format
```json
{
  "rfc_id": "RFC-YYYY-MM-DD-title",
  "title": "RFC Title",
  "status": "draft|review|approved|implemented",
  "author": "Agent name",
  "created_date": "YYYY-MM-DD",
  "summary": "Brief overview",
  "problem_statement": "What problem does this solve?",
  "proposed_solution": "How will we solve it?",
  "alternatives_considered": [
    {
      "option": "Alternative approach",
      "pros": ["Advantage 1"],
      "cons": ["Disadvantage 1"],
      "reason_rejected": "Why not chosen"
    }
  ],
  "implementation_plan": {
    "phases": ["Phase 1", "Phase 2"],
    "estimated_effort": "2 weeks",
    "risks": ["Risk 1", "Risk 2"]
  }
}
```

#### Tool Response Format
```json
{
  "tool": "tool_name",
  "status": "success|error|partial",
  "result": {
    "data": "Tool-specific result data",
    "metadata": {
      "execution_time": 0.123,
      "items_processed": 42
    }
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context"
  }
}
```

## Markdown Output Standards

### Document Structure
```markdown
# Main Title

## Overview
Brief introduction paragraph.

## Section 1
Content for section 1.

### Subsection 1.1
Detailed content.

## Section 2
Content for section 2.

## Conclusion
Summary and next steps.
```

### Code Blocks
Always specify language for syntax highlighting:
```python
def example_function():
    """Include docstrings"""
    return "Use proper indentation"
```

### Lists and Tables
Use consistent formatting:
- Bullet points for unordered lists
- Numbers for ordered lists
- Tables for structured data

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |

## Error Messages

### User-Facing Errors
```json
{
  "error": {
    "title": "Brief error title",
    "message": "Clear explanation of what went wrong",
    "suggestion": "How to fix or work around the issue",
    "technical_details": "Optional: Stack trace or system info"
  }
}
```

### Validation Errors
```json
{
  "validation_errors": [
    {
      "field": "field_name",
      "message": "What's wrong with this field",
      "expected": "What was expected",
      "received": "What was actually provided"
    }
  ]
}
```

## Progress Updates

When reporting progress:
```json
{
  "status": "in_progress",
  "current_task": "What's happening now",
  "progress": {
    "percentage": 45,
    "completed": 9,
    "total": 20,
    "elapsed_time": "00:02:34",
    "estimated_remaining": "00:03:21"
  },
  "recent_actions": [
    "Completed action 1",
    "Completed action 2"
  ],
  "next_actions": [
    "Upcoming action 1",
    "Upcoming action 2"
  ]
}
```

## Important Formatting Rules

1. **Escape Special Characters**: Always escape quotes, newlines, and other special characters in JSON strings
2. **Consistent Naming**: Use the same naming convention throughout
3. **No Trailing Commas**: JSON doesn't allow trailing commas
4. **Proper Nesting**: Ensure proper indentation for readability
5. **Schema Compliance**: Always validate against the expected schema
6. **Timestamps**: Use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
7. **File Paths**: Use forward slashes, relative paths when possible
8. **Empty Values**: Use null, empty arrays [], or empty objects {} appropriately

## Structured Output Mode

When using OpenAI's structured output mode:
1. Response will automatically conform to the provided schema
2. All required fields will be present
3. Types will be enforced
4. No additional formatting needed
5. Focus on content quality rather than format compliance