# Feature Request: Subtask Generator

## Goal

This feature generates a detailed and refined YAML subtask definition from a specific subtask provided by the orchestrator. The generated YAML must clearly outline implementation details relevant only to the provided subtask, explicitly excluding unrelated information.

Configuration files must include distinct prompts for each job type. The existing prompt configuration item should clearly separate orchestrator and subtask_generator prompts. Default prompts should follow the naming convention `{config_name}_default.md`. All default prompts must reside within the `prompts` folder. The initial subtask_generator_default.md can use the prompts/orchestrator_default.md as a templete but specialised to this task.

The input will be a single step (subtask) from the multi-step task list. The overall format of the input step is defined in `prompts/orchestrator_default.md`. The terms "step" and "subtask" are used interchangeably throughout this document and the project.

The input subtask will be sent to OpenRouter using the `subtask_generator` prompt to produce the refined YAML output.

`ai_whisperer` is a Python 3.12-based project and strictly adheres to Test Driven Development (TDD) methodology.

## Requirements

- Accept a specific subtask (in the required YAML step format defined in `prompts/orchestrator_default.md`) as input.
- Analyze the provided subtask and extract relevant context and implementation details based on the current project structure.
- Provide additional context, such as the workspace directory structure and relevant files or modules, to assist the AI in generating accurate subtasks.
- Use the AI with the `subtask_generator` prompt to refine and expand the provided subtask.
- Generate a refined YAML subtask definition that explicitly includes:
  - Clearly defined, actionable subtasks derived directly from the input.
  - Detailed implementation instructions and context relevant only to the provided subtask.
  - Explicit exclusion of any information unrelated to the provided subtask.
- Validate that the generated YAML strictly conforms to the project's defined YAML subtask schema and format (schema definition location should be explicitly documented).

## Acceptance Criteria

- The output must pass validation against the project's YAML subtask schema.
- The generated YAML file must be saved in the designated `output` folder.
- The filename must clearly reflect the specific subtask content or purpose, following a consistent and descriptive naming convention. The filename must include the `task_id` from the orchestrator task list.
- Errors or validation failures must be clearly logged or reported to facilitate debugging and correction.