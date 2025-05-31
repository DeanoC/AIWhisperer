# Structured Output Integration for Patricia Agent

## Overview

Patricia (Agent P) now supports OpenAI-style structured output for generating valid JSON plans when using compatible models. This ensures plans are always properly formatted and follow the required schema.

## How It Works

### 1. Automatic Detection
The system automatically detects when Patricia is generating a plan and enables structured output if:
- The active agent is Patricia
- The model supports structured output (e.g., openai/gpt-4o-mini)
- The message contains plan generation keywords

### 2. Plan Generation Flow

```
User Request → Patricia → prepare_plan_from_rfc → 
System enables structured output → Patricia generates JSON → 
save_generated_plan → Plan saved
```

### 3. Model Compatibility

Structured output is enabled for:
- ✅ openai/gpt-4o
- ✅ openai/gpt-4o-mini
- ❌ anthropic/claude-* (falls back to text parsing)
- ❌ google/gemini-* (falls back to text parsing)

## Implementation Details

### Session Manager Enhancement
The `StatelessSessionManager` now includes:
- `_should_use_structured_output_for_plan()` - Detects plan generation context
- `_get_plan_generation_schema()` - Loads and prepares the schema
- Automatic injection of `response_format` when appropriate

### Tool Updates
- **prepare_plan_from_rfc**: Updated instructions for structured output
- **save_generated_plan**: Ready to accept JSON objects directly

### Patricia's System Prompt
Enhanced to instruct Patricia to generate pure JSON when structured output is available.

## Usage Example

### User Interaction
```
User: Please create a plan from the dark-mode RFC

Patricia: I'll convert the dark mode RFC into an executable plan.
[Uses prepare_plan_from_rfc tool]

System: [Detects plan generation, enables structured output]

Patricia: [Generates pure JSON plan following the schema]
{
  "plan_type": "initial",
  "title": "Implement Dark Mode Support",
  "tdd_phases": {
    "red": [...],
    "green": [...],
    "refactor": [...]
  },
  "tasks": [...],
  "validation_criteria": [...]
}

Patricia: [Uses save_generated_plan with the JSON object]
I've created a structured plan with 12 tasks following TDD principles...
```

## Benefits

1. **Guaranteed Valid JSON**: No parsing errors or malformed plans
2. **Schema Compliance**: Plans always follow the required structure
3. **Better User Experience**: Cleaner output, fewer errors
4. **Fallback Support**: Works seamlessly with non-supporting models

## Configuration

No configuration needed! The system automatically:
- Detects compatible models
- Enables structured output when appropriate
- Falls back gracefully for unsupported models

## Testing

1. Run `test_structured_output.py` for low-level validation
2. Use `test_patricia_structured_plan.py` to set up test RFCs
3. Test with the interactive server for full integration

## Technical Notes

- Uses `"strict": false` mode due to OpenRouter limitations
- Removes `$schema` field before sending to API
- Schema loaded from `schemas/plan_generation_schema.json`
- Validates against `rfc_plan_schema.json` after generation

## Future Enhancements

1. Support for more model providers as they add structured output
2. Additional schemas for different plan types
3. Structured output for other agent tools
4. Schema versioning and migration support