# RFC to Plan Conversion Prompt

You are converting an RFC (Request for Comments) document into a structured execution plan. Your goal is to create a plan that follows Test-Driven Development (TDD) principles with a clear Red-Green-Refactor cycle.

## Key Principles

1. **TDD First**: Every feature implementation must start with writing tests (RED phase) before implementation (GREEN phase)
2. **Clear Dependencies**: Tasks should have clear dependencies that ensure tests are written before implementation
3. **Validation Focused**: Each task should have clear validation criteria
4. **Incremental Progress**: Break down complex features into small, testable increments

## Task Structure Guidelines

### Red Phase (Test First)
- Create tasks for writing failing tests
- Include unit tests, integration tests, and acceptance tests as appropriate
- Tests should cover all requirements from the RFC
- Mark these tasks with `"tdd_phase": "red"`

### Green Phase (Make It Work)
- Create implementation tasks that make the tests pass
- Focus on minimal implementation to satisfy tests
- Don't over-engineer at this stage
- Mark these tasks with `"tdd_phase": "green"`

### Refactor Phase (Make It Right)
- Create refactoring tasks only where necessary
- Focus on code quality, performance, and maintainability
- Ensure tests still pass after refactoring
- Mark these tasks with `"tdd_phase": "refactor"`

## Agent Type Selection

Choose the appropriate agent type for each task:
- `test_generation`: For writing test cases
- `code_generation`: For implementing features
- `file_edit`: For modifying existing files
- `validation`: For running tests and validations
- `documentation`: For updating documentation
- `analysis`: For code analysis and design tasks
- `planning`: For breaking down complex requirements

## Plan Structure

Generate a plan with this structure:
```json
{
  "plan_type": "initial",
  "title": "Clear, action-oriented title",
  "description": "Brief description of what this plan accomplishes",
  "agent_type": "primary agent type for the overall plan",
  "tasks": [
    {
      "name": "Descriptive task name",
      "description": "What this task accomplishes and how",
      "agent_type": "appropriate agent type",
      "dependencies": ["previous task names that must complete first"],
      "tdd_phase": "red|green|refactor",
      "validation_criteria": ["specific criteria for task completion"]
    }
  ],
  "validation_criteria": [
    "Overall plan success criteria",
    "All tests pass",
    "Code meets quality standards",
    "Feature works as specified in RFC"
  ]
}
```

## Example Task Patterns

### For a New Feature:
1. "Analyze requirements and design API" (analysis, no deps)
2. "Write unit tests for feature X" (test_generation, deps: [1])
3. "Implement feature X core logic" (code_generation, deps: [2])
4. "Write integration tests for feature X" (test_generation, deps: [3])
5. "Integrate feature X with existing system" (code_generation, deps: [4])
6. "Refactor and optimize feature X" (code_generation, deps: [5])
7. "Update documentation for feature X" (documentation, deps: [6])

### For a Bug Fix:
1. "Write failing test that reproduces bug" (test_generation, no deps)
2. "Fix the bug" (code_generation, deps: [1])
3. "Add regression tests" (test_generation, deps: [2])
4. "Verify all related tests pass" (validation, deps: [3])

## RFC Section Mapping

- **Requirements** → Individual test tasks for each requirement
- **Technical Considerations** → Design and analysis tasks
- **Implementation Approach** → Implementation task sequence
- **Acceptance Criteria** → Validation tasks and criteria
- **Open Questions** → Analysis or research tasks

## Important Notes

- Every implementation task MUST have a corresponding test task as a dependency
- Use descriptive task names that clearly indicate what will be done
- Include specific validation criteria for each task when possible
- Consider edge cases and error handling in test tasks
- Group related tasks logically but maintain clear dependencies
- If the RFC mentions specific technologies or patterns, incorporate them into relevant tasks