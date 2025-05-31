# Patricia's RFC-to-Plan Conversion Guide

## Overview

Agent Patricia (Agent P) is your RFC and Plan specialist in AIWhisperer. She helps you transform ideas into well-structured RFC documents and then convert those RFCs into executable plans following Test-Driven Development (TDD) principles.

## Quick Start

### 1. Create an RFC
```
User: I want to add a dark mode feature to our application

Patricia: I'll help you create an RFC for the dark mode feature. Let me start by checking existing RFCs and understanding the project structure.

[Patricia creates an RFC and asks clarifying questions]
```

### 2. Refine the RFC
```
User: It should follow system preferences and persist user choice

Patricia: Great! I'll update the RFC with these requirements.
[Updates RFC with technical details]
```

### 3. Convert to Plan
```
User: The RFC looks complete. Can we create a plan?

Patricia: Excellent! The dark mode RFC has all the necessary details. I'll convert it into an executable plan following TDD principles.

[Patricia generates a structured plan with RED-GREEN-REFACTOR phases]
```

## Understanding TDD in Plans

Patricia ensures all plans follow Test-Driven Development:

### RED Phase (Write Tests First)
- Write tests that will initially fail
- Define expected behavior through tests
- Focus on edge cases and error conditions

### GREEN Phase (Make Tests Pass)
- Implement minimal code to pass tests
- Focus on functionality, not optimization
- Resist adding extra features

### REFACTOR Phase (Improve Code)
- Clean up code while keeping tests green
- Extract common patterns
- Optimize performance
- Improve documentation

## Plan Structure

Every plan Patricia generates includes:

```json
{
  "plan_type": "initial",
  "title": "Implement Dark Mode Support",
  "description": "Plan for adding dark mode functionality",
  "agent_type": "planning",
  "tdd_phases": {
    "red": ["Write theme context tests", "Write component theme tests"],
    "green": ["Implement theme context", "Add dark mode styles"],
    "refactor": ["Optimize theme switching", "Extract theme utilities"]
  },
  "tasks": [
    {
      "name": "Write theme context tests",
      "description": "Create tests for theme provider",
      "agent_type": "test_generation",
      "dependencies": [],
      "tdd_phase": "red",
      "validation_criteria": ["Tests should fail initially"]
    }
    // ... more tasks
  ],
  "validation_criteria": ["All tests pass", "Theme persists on reload"]
}
```

## Common Workflows

### Basic RFC to Plan
1. Create RFC: `"Create an RFC for [feature]"`
2. Refine RFC: Answer Patricia's questions
3. Generate Plan: `"Convert this RFC to a plan"`
4. Review Plan: `"Show me the plan"`

### Updating Plans When RFCs Change
1. Update RFC: `"Update the RFC to include [new requirement]"`
2. Sync Plan: `"Update the plan to reflect the RFC changes"`
3. Patricia will detect changes and regenerate affected sections

### Managing Multiple Plans
```
User: List all my plans
Patricia: [Shows in-progress and archived plans]

User: Archive the completed authentication plan
Patricia: [Moves plan to archived status]

User: Delete the old test plan
Patricia: Are you sure you want to permanently delete this plan? This cannot be undone. Type 'yes' to confirm.
```

## Best Practices

### For RFCs
1. **Be Specific**: Include concrete requirements
2. **Technical Details**: Specify technologies and approaches
3. **Acceptance Criteria**: Define what success looks like
4. **Dependencies**: Identify related systems

### For Plans
1. **Start with Tests**: Always follow RED-GREEN-REFACTOR
2. **Clear Dependencies**: Tasks should have logical order
3. **Validation Criteria**: Each task needs success metrics
4. **Appropriate Agents**: Use the right agent type for each task

## Agent Types in Plans

- `planning`: High-level planning and coordination
- `test_generation`: Writing test cases
- `code_generation`: Implementing features
- `file_edit`: Modifying existing files
- `validation`: Verifying functionality
- `documentation`: Creating/updating docs
- `analysis`: Analyzing code or requirements

## Structured Output Support

When using compatible models (GPT-4o, GPT-4o-mini), Patricia automatically generates valid JSON plans without parsing errors. For other models, she ensures proper formatting through careful prompting.

## Tips for Success

1. **Complete RFCs First**: Don't rush to plan generation
2. **Answer Questions**: Patricia's questions help create better plans
3. **Review Generated Plans**: Ensure they match your expectations
4. **Keep RFCs Updated**: Plans can be regenerated when requirements change
5. **Use Archival**: Archive completed work instead of deleting

## Common Commands

### RFC Management
- `"Create an RFC for [feature]"`
- `"Update the RFC with [details]"`
- `"Show me the RFC"`
- `"List all RFCs"`
- `"Archive the RFC"`

### Plan Management
- `"Convert this RFC to a plan"`
- `"Show me the plan"`
- `"List all plans"`
- `"Update the plan from the RFC"`
- `"Archive the plan"`
- `"Delete the plan"` (requires confirmation)

## Troubleshooting

### Plan Generation Fails
- Ensure RFC has sufficient detail
- Check that requirements are clear
- Verify technical approach is defined

### Plan Doesn't Follow TDD
- Patricia always generates TDD plans
- If structure seems wrong, regenerate
- Report issues for model improvements

### Can't Find RFC/Plan
- Use `"List RFCs"` or `"List plans"`
- Check if archived: `"List archived RFCs"`
- Plans are named after their RFC

## Example Conversation

```
User: I need to add user authentication to our app

Patricia: I'll help you create an RFC for user authentication. Let me start by 
checking existing RFCs and understanding the project structure.

[Creates RFC]

I've created user-auth-2025-05-31.md. To refine this RFC, I'd like to understand:
1. What authentication method do you prefer (JWT, sessions, OAuth)?
2. Do you need social login support?
3. Should it include password reset functionality?

User: JWT with email/password, no social login, yes to password reset

Patricia: Perfect! I'll update the RFC with these specifications.

[Updates RFC]

User: This looks good. Can you create a plan from it?

Patricia: Excellent! The user authentication RFC has all the necessary details. 
I'll convert it into an executable plan following TDD principles.

[Generates plan with 15 tasks across RED-GREEN-REFACTOR phases]

I've created a structured plan with 15 tasks following the Red-Green-Refactor cycle:

**RED Phase (Tests First):**
- Write unit tests for user registration
- Write tests for JWT token generation
- Write tests for password reset flow

**GREEN Phase (Implementation):**
- Implement user model and database schema
- Create authentication endpoints
- Implement JWT token handling

**REFACTOR Phase:**
- Optimize database queries
- Extract authentication middleware
- Improve error handling

Would you like me to show you the detailed task breakdown with dependencies?
```

## Advanced Features

### Multiple Plans from One RFC
Patricia can create multiple plans for complex RFCs:
- Phase 1: Basic implementation
- Phase 2: Advanced features
- Phase 3: Performance optimization

### Plan Templates
Patricia learns from your patterns and can suggest similar structures for related features.

### Validation
All plans are validated against the schema ensuring:
- Proper TDD structure
- Valid task dependencies
- Complete validation criteria
- Appropriate agent assignments

## Getting Help

If you need assistance:
1. Ask Patricia to explain any part of the process
2. Request examples of similar RFCs/plans
3. Ask for best practices for your specific use case

Patricia is designed to make the RFC-to-plan process collaborative and productive, reducing ambiguity and saving development time through clear, actionable plans.