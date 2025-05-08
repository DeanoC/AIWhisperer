# JSON Plan Ingestion and Parsing Design

## Overview

This document outlines the design for the JSON plan ingestion and parsing feature of the AI Whisperer runner. The runner will read a JSON plan file, validate it against the actual structure of the plan and subtask files, parse it into an internal representation, and handle any errors that occur during the process.

## Requirements

1. The runner can read a JSON plan file.
2. The runner can parse the JSON into an internal representation of tasks.
3. The runner validates the JSON against the actual structure of the plan and subtask files and reports errors if invalid.

## Design

### 1. Read the JSON Plan File

- The runner will read the JSON plan file from a specified path.
- The file will be read as a string and parsed into a JSON object.

### 2. Validate the JSON Plan

- The JSON plan will be validated against the actual structure of the plan file.
- The validation will check for the presence of required fields like `natural_language_goal`, `overall_context`, `plan`, `task_id`, and `input_hashes`.
- The `plan` array will be checked to ensure each step has `step_id`, `file_path`, `depends_on`, `type`, `input_artifacts`, `output_artifacts`, and `completed`.

### 3. Parse the JSON Plan

- The JSON plan will be parsed into an internal representation of tasks and steps.
- The internal representation will be a data structure that mirrors the JSON structure but is optimized for the runner's use.

### 4. Handle Subtasks

- The runner will read the subtask files referenced in the `file_path` of each step.
- The subtask files will be validated against their actual structure.
- The validation will check for the presence of required fields like `description`, `depends_on`, `agent_spec`, `step_id`, `task_id`, and `subtask_id`.
- The `agent_spec` will be checked to ensure it has `type`, `input_artifacts`, `output_artifacts`, `instructions`, `constraints`, and `validation_criteria`.

### 5. Error Handling

- The runner will handle errors gracefully, providing detailed error messages to help the user fix the issues.

## Implementation Details

- The runner will use a JSON parsing library to read and parse the JSON plan file.
- The validation will be done using custom validation logic based on the actual structure of the plan and subtask files.
- The internal representation will be a set of classes that mirror the JSON structure.

## Conclusion

This design provides a clear path for implementing the JSON plan ingestion and parsing feature. The runner will be able to read, validate, and parse JSON plans, and handle any errors that occur during the process.
