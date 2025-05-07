# Default Prompts Analysis: Fixed Items Requirements

This document identifies the specific rules, instructions, or examples within the default prompts that explicitly mention or require the inclusion of fixed items like hashes, task_id, and subtask_id.

## Orchestrator Default Prompt (`prompts/orchestrator_default.md`)

The orchestrator prompt currently requires the AI to include input hashes and task_id in its output. The following sections should be removed or modified:

### Input Hashes Requirement

The prompt instructs the AI to include input hashes in the YAML output:

```
You MUST include the input_hashes dictionary exactly as provided in your YAML output.
This is critical for data provenance and verification.
```

And later in the prompt:

```
- input_hashes: The dictionary of SHA-256 hashes provided in the prompt (MUST be included exactly as provided)
```

### Task ID Requirement

The prompt instructs the AI to generate and include a task_id:

```
- task_id: A unique identifier for this task (generate a UUID)
```

## Subtask Generator Default Prompt (`prompts/subtask_generator_default.md`)

The subtask generator prompt currently requires the AI to include step_id in its output. The following sections should be removed or modified:

### Step ID Requirement

The prompt instructs the AI to include the step_id from the input:

```
You MUST preserve the step_id from the input YAML in your output.
```

And later in the prompt:

```
- step_id: The unique identifier for this step (MUST match the input step_id)
```

## Recommended Changes

### For Orchestrator Default Prompt

1. Remove the instruction to include input hashes
2. Remove the instruction to generate a task_id
3. Remove these fields from any example YAML structures in the prompt
4. Remove validation checks related to these fields

### For Subtask Generator Default Prompt

1. Remove the instruction to preserve the step_id
2. Remove validation checks related to this field

These modifications will allow the AI to focus on generating the substantive content without worrying about these fixed items, which will be added by the new postprocessing step.
