# Plan Refinement Prompt

You are refining an initial plan into a detailed overview plan with subtasks. Your goal is to break down high-level tasks into concrete, actionable subtasks while maintaining the TDD approach and RFC traceability.

## Key Principles

1. **Maintain TDD Structure**: Preserve the Red-Green-Refactor cycle in subtasks
2. **RFC Traceability**: Each subtask should trace back to specific RFC requirements
3. **Atomic Tasks**: Break tasks into the smallest meaningful units of work
4. **Clear Outcomes**: Each subtask should have a clear, verifiable outcome

## Subtask Guidelines

### For Test Generation Tasks (Red Phase):
Break into specific test categories:
- Unit tests for individual functions/methods
- Integration tests for component interactions
- Edge case tests for boundary conditions
- Error handling tests
- Performance tests (if applicable)

### For Implementation Tasks (Green Phase):
Break into logical implementation steps:
- Data model/structure creation
- Core logic implementation
- API/interface development
- Integration with existing code
- Configuration setup

### For Refactoring Tasks (Refactor Phase):
Break into specific improvements:
- Code structure optimization
- Performance improvements
- Design pattern application
- Code documentation
- Technical debt reduction

## Subtask Structure

Each subtask should include:
```json
{
  "name": "Specific, actionable task name",
  "description": "Detailed description of what to do and why",
  "agent_type": "appropriate agent type",
  "dependencies": ["dependencies within this task group"],
  "validation_criteria": [
    "Specific success criteria",
    "Measurable outcomes"
  ],
  "estimated_duration": "estimated time (e.g., '30 minutes', '2 hours')",
  "rfc_reference": "Which RFC requirement this addresses",
  "tdd_phase": "red|green|refactor",
  "technical_details": {
    "files_to_modify": ["list of files"],
    "technologies": ["relevant technologies"],
    "patterns": ["design patterns to apply"]
  }
}
```

## Breaking Down Common Task Types

### "Write tests for feature X" becomes:
1. "Create test file structure for feature X"
2. "Write unit tests for X input validation"
3. "Write unit tests for X core logic"
4. "Write integration tests for X with database"
5. "Write edge case tests for X error conditions"
6. "Write performance tests for X under load"

### "Implement feature X" becomes:
1. "Define data models for feature X"
2. "Implement X validation logic"
3. "Implement X core business logic"
4. "Create X API endpoints"
5. "Integrate X with existing services"
6. "Add X configuration options"

### "Refactor module Y" becomes:
1. "Extract common patterns in Y to utilities"
2. "Apply dependency injection to Y"
3. "Optimize Y database queries"
4. "Add comprehensive logging to Y"
5. "Update Y documentation and comments"

## Dependency Management

- Subtasks within a task should have internal dependencies
- Maintain the original task's external dependencies
- Ensure no circular dependencies
- Test subtasks must complete before implementation subtasks

## RFC Context Integration

For each subtask, consider:
- Which specific RFC requirement it addresses
- Any technical considerations from the RFC
- Acceptance criteria that apply
- Open questions that might affect implementation

## Quality Checks

Each refined plan should ensure:
- Complete coverage of the original task's goals
- No missing steps in the workflow
- Clear validation for each subtask
- Reasonable time estimates
- Proper TDD cycle maintenance