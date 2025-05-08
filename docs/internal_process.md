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

## JSON Plan Ingestion and Parsing

The AI Whisperer runner is capable of ingesting, validating, and parsing JSON-defined execution plans. This process is primarily handled by the `PlanParser` class located in [`src/ai_whisperer/plan_parser.py`](src/ai_whisperer/plan_parser.py:1).

The process involves the following key stages:

1. **Initialization**:
    - An instance of `PlanParser` is created with the path to the main JSON plan file.
    - The parser immediately checks if the main plan file exists. If not, a `PlanFileNotFoundError` is raised.

2. **Main Plan Loading and Validation**:
    - The `_load_and_validate_main_plan` method is called.
    - It reads the main plan file using `_read_json_file`. If the file contains malformed JSON, a `PlanInvalidJSONError` is raised.
    - Custom validation logic is then applied to the parsed JSON data:
        - It checks for required top-level fields such as `task_id`, `natural_language_goal`, `input_hashes`, and `plan`.
        - It verifies that the `plan` field is a list and `input_hashes` is an object with its own required fields.
        - Each step within the `plan` array is validated to ensure it's a dictionary and contains required fields like `step_id`, `description`, and `agent_spec`.
        - The `agent_spec` within each step is also validated for its required fields (e.g., `type`, `instructions`).
    - If any of these custom validations fail, a `PlanValidationError` is raised with a descriptive message.

3. **Subtask Loading and Validation (if applicable)**:
    - The `_load_and_validate_subtasks` method is called.
    - It iterates through each step in the main plan. If a step contains a `file_path` key (indicating an external subtask JSON file):
        - The path to the subtask file is resolved (handling both relative and absolute paths).
        - The subtask JSON file is read using `_read_json_file`.
            - If the subtask file is not found, a `SubtaskFileNotFoundError` is raised.
            - If the subtask file contains malformed JSON, a `SubtaskInvalidJSONError` is raised.
        - The content of the subtask JSON is then validated against the `subtask_schema.json` using the `validate_subtask` function from [`src/ai_whisperer/json_validator.py`](src/ai_whisperer/json_validator.py:1).
            - If schema validation fails, a `SubtaskValidationError` is raised.
        - If successfully loaded and validated, the content of the subtask is embedded directly into the main plan's step data under the key `loaded_subtask_content`.

4. **Accessing Parsed Data**:
    - Once parsing is complete, the fully parsed and validated plan (with embedded subtasks) can be retrieved using the `get_parsed_plan()` method.
    - Helper methods like `get_all_steps()` and `get_task_dependencies()` are also available.

**Error Handling**:
The `PlanParser` defines several custom exception classes (e.g., `PlanFileNotFoundError`, `PlanInvalidJSONError`, `PlanValidationError`, `SubtaskFileNotFoundError`, `SubtaskInvalidJSONError`, `SubtaskValidationError`) to provide specific error information during the ingestion and parsing process. This allows the runner to catch and handle these issues gracefully.

This structured approach ensures that only valid and complete JSON plans are processed by the runner's execution engine.

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
