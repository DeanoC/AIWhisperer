# Internal Process Documentation

This document describes the internal processes and components of the AI Whisperer system.

## Overall Architecture

AI Whisperer follows a multi-stage process to generate structured task plans and detailed subtasks:

1. **Orchestrator**: Generates the initial task plan YAML from requirements
2. **Subtask Generator**: Expands each step in the task plan into a detailed subtask
3. **Postprocessing Pipeline**: Enhances and standardizes the AI-generated content

## Orchestrator

The Orchestrator is responsible for:

1. Loading the prompt template
2. Calculating SHA-256 hashes of input files
3. Reading the requirements markdown content
4. Constructing a prompt with markdown content
5. Calling the OpenRouter API
6. Parsing and validating the YAML response
7. Adding required metadata (task_id, input_hashes) via postprocessing
8. Saving the validated YAML to the output directory

## Subtask Generator

The Subtask Generator is responsible for:

1. Loading the subtask prompt template
2. Preparing a prompt with the step information and overall context
3. Calling the OpenRouter API
4. Parsing and validating the YAML response
5. Adding required metadata (subtask_id) via postprocessing
6. Saving the validated YAML to the output directory

## Postprocessing Pipeline

The postprocessing pipeline enhances the reliability and format adherence of AI-generated YAML task files. It consists of:

1. **Scripted Phase**: A series of deterministic steps that apply transformations
2. **AI Improvements Phase**: (Future enhancement) An AI-based step for higher-level improvements

### Scripted Steps

#### clean_backtick_wrapper

Removes markdown code block wrappers from YAML content. This handles cases where the AI model returns YAML wrapped in markdown code blocks.

#### add_items_postprocessor

Automatically adds required items to the YAML output:

- **Top-level items**: Items added to the root of the YAML structure (e.g., task_id, input_hashes)
- **Step-level items**: Items added to each step/subtask in the YAML (e.g., subtask_id)

Configuration is done through the `result_data` parameter:

```python
result_data = {
    "items_to_add": {
        "top_level": {
            "task_id": "abc-123",
            "input_hashes": {"file1": "hash1", "file2": "hash2"}
        },
        "step_level": {
            "subtask_id": "xyz-789"
        },
        "step_container": "plan"  # Optional, defaults to "plan"
    }
}
```

## AI Prompt Guidelines

When creating or modifying AI prompts for the system:

1. **Focus on Content Generation**: The AI should focus on generating the substantive content (plan structure, instructions, validation criteria, etc.) without worrying about fixed items like task_id, input_hashes, or subtask_id.

2. **No Fixed Item Management**: Do not include instructions for the AI to generate, preserve, or manage fixed items like task_id, input_hashes, or subtask_id. These will be added automatically by the postprocessing pipeline.

3. **Schema Awareness**: Ensure the prompt accurately reflects the expected schema structure, but omit fixed items from schema examples or requirements.

4. **Clear Instructions**: Provide clear instructions for the AI to focus on the core task requirements and structure.

## Error Handling

The system includes comprehensive error handling for various scenarios:

- Configuration errors
- API interaction errors
- YAML parsing and validation errors
- File I/O errors
- Postprocessing errors

Each error type has a specific exception class that provides detailed information about the error.
